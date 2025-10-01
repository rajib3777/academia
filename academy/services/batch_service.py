from typing import Dict, Any
from django.db import transaction
from academy.models import Batch, Course
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from academy.selectors.course_selector import CourseSelector
from academy.selectors.batch_selector import BatchSelector

class BatchService:
    """
    Service class for Batch model to handle all write operations.
    """
    
    def __init__(self, request_user):
        """
        Initialize with the current user for permission checks.
        
        Args:
            user: The user performing the operation
        """
        self.request_user = request_user
    
    def _validate_user_permission(request_user, batch_id: int) -> None:
        """
        Validate if user has permission to manage batches for a course.
        
        Args:
            course_id: ID of the course
            
        Raises:
            ValidationError: If user doesn't have permission
        """

        if request_user.is_academy() or request_user.is_admin():
            try:
                batch = BatchSelector.get_batch_by_id(batch_id)
                if not hasattr(request_user, 'academy') or not request_user.academy.exists():
                    raise ValidationError('User is not associated with any academy')
                
                academy = request_user.academy.first()
                if batch.course.academy_id != academy.id:
                    raise ValidationError('You do not have permission to delete this batch')
            except Batch.DoesNotExist:
                raise ValidationError(f"Batch with ID {batch_id} does not exist.")
        else:
            raise ValidationError("You don't have permission to manage batches.")

    @transaction.atomic
    def delete_batch(self, batch_id: int) -> Dict[str, Any]:
        """
        Delete a batch if it has no students enrolled.
        
        Args:
            batch_id: ID of the batch to delete
            
        Returns:
            Dict with success status and message
            
        Raises:
            ValidationError: If batch has students or user lacks permission
        """
        #TODO after final QA add this validation.
        # BatchService._validate_user_permission(self.request_user, batch_id)
        
        # Check if batch has any enrolled students
        has_students = BatchSelector.batch_has_students(batch_id)
        
        if has_students:
            raise ValidationError(
                'Cannot delete this batch because it has enrolled students. '
                'Please unenroll all students before deleting.'
            )
        
        # Get batch for return message
        batch = BatchSelector.get_batch_by_id(batch_id)
        batch_name = batch.name
        course_name = batch.course.name
        
        # Delete the batch
        batch.delete()
        
        return {
            'success': True,
            'message': f'Batch "{batch_name}" from course "{course_name}" has been successfully deleted'
        }
    
    @transaction.atomic
    def create_batch(self, data: Dict[str, Any]) -> Batch:
        """
        Create a new batch.
        
        Args:
            data: Dictionary containing batch data
            
        Returns:
            Newly created batch instance
        """
        # Validate user permission
        #TODO after final QA add this validation.
        # course_selector = CourseSelector()
        # course_selector.validate_user_permission(self.request.user, data['course_id'])

        try:
            # Create batch
            batch = Batch.objects.create(
                name=data['name'],
                course_id=data['course_id'],
                start_date=data.get('start_date'),
                end_date=data.get('end_date'),
                description=data.get('description', ''),
                is_active=data.get('is_active', True)
            )
        except IntegrityError as e:
            if 'academy_batch_name_course_id' in str(e):
                batch_name = data.get('name', 'Unknown')
                raise ValidationError(f"Batch with name '{batch_name}' already exists for this course.")
            raise
        
        return batch
    
    @transaction.atomic
    def update_batch(self, batch_id: int, data: Dict[str, Any]) -> Batch:
        """
        Update an existing batch.
        
        Args:
            batch_id: ID of the batch to update
            data: Dictionary containing updated batch data
            
        Returns:
            Updated batch instance
        """
        # Get batch
        try:
            batch = Batch.objects.select_related('course').get(id=batch_id)
        except Batch.DoesNotExist:
            raise ValidationError(f"Batch with ID {batch_id} does not exist.")
        
        # Validate user permission
        #TODO after final QA add this validation.
        # self._validate_user_permission(batch.course_id)
        
        # Update batch fields
        if 'name' in data:
            batch.name = data['name']
        if 'start_date' in data:
            batch.start_date = data['start_date']
        if 'end_date' in data:
            batch.end_date = data['end_date']
        if 'description' in data:
            batch.description = data['description']
        if 'is_active' in data:
            batch.is_active = data['is_active']
        if 'course_id' in data:
            # Additional validation for course change
            #TODO after final QA add this validation.
            # self._validate_user_permission(data['course_id'])
            batch.course_id = data['course_id']
        
        # Validate end date is after start date
        if batch.end_date and batch.start_date and batch.end_date < batch.start_date:
            raise ValidationError('End date cannot be before start date.')
        
        batch.save()
        return batch