from typing import Dict, Any
from django.db import transaction
from academy.models import Batch, Course
from django.core.exceptions import ValidationError

class BatchService:
    """
    Service class for Batch model to handle all write operations.
    """
    
    def __init__(self, user):
        """
        Initialize with the current user for permission checks.
        
        Args:
            user: The user performing the operation
        """
        self.user = user
    
    def _validate_user_permission(self, course_id: int) -> None:
        """
        Validate if user has permission to manage batches for a course.
        
        Args:
            course_id: ID of the course
            
        Raises:
            ValidationError: If user doesn't have permission
        """
        if not self.user.is_admin and not self.user.is_staff:
            try:
                course = Course.objects.select_related('academy').get(id=course_id)
                if not self.user.academy.filter(id=course.academy.id).exists():
                    raise ValidationError("You don't have permission to manage batches for this course.")
            except Course.DoesNotExist:
                raise ValidationError(f"Course with ID {course_id} does not exist.")
    
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
        self._validate_user_permission(data['course_id'])
        
        # Create batch
        batch = Batch.objects.create(
            name=data['name'],
            course_id=data['course_id'],
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            description=data.get('description', ''),
            is_active=data.get('is_active', True)
        )
        
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
        self._validate_user_permission(batch.course_id)
        
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
            self._validate_user_permission(data['course_id'])
            batch.course_id = data['course_id']
        
        # Validate end date is after start date
        if batch.end_date and batch.start_date and batch.end_date < batch.start_date:
            raise ValidationError('End date cannot be before start date.')
        
        batch.save()
        return batch