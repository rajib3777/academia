from typing import Dict, Any, List, Optional
from functools import cached_property
from django.db import transaction
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from academy.models import Course, Batch
from account import choices as account_choices

class CourseService:
    """
    Service class for Course model to handle all write operations.
    """
    
    def __init__(self, user):
        """
        Initialize with the current user for permission checks.
        
        Args:
            user: The user performing the operation
        """
        self.user = user

    def _get_authorized_academy_id(self, requested_academy_id: Optional[int] = None) -> int:
        """
        Validate user permission and return the appropriate academy ID.
        
        For academy users: returns their own academy ID
        For admin users: returns the requested academy ID
        For other users: raises permission error
        
        Args:
            requested_academy_id: Academy ID requested in the operation
                
        Returns:
            int: The authorized academy ID
            
        Raises:
            ValidationError: If user doesn't have permission
        """
        # Check if user is from an academy
        if self.user.role.name == account_choices.ACADEMY:
            if hasattr(self.user, 'academy') and self.user.academy.exists():
                return self.user.academy.first().id
            else:
                raise ValidationError("You are not associated with any academy.")
        
        # Check if user is an admin
        elif self.user.role.name == account_choices.ADMIN:
            if requested_academy_id is None:
                raise ValidationError("Academy ID is required for admin operations.")
            return requested_academy_id
        
        # Other roles don't have permission
        else:
            raise ValidationError("You don't have permission to manage courses.")
    
    @cached_property
    def batch_service(self):
        """Lazy initialization of BatchService."""
        from academy.services.batch_service import BatchService
        return BatchService(user=self.user)
    
    def create_course(self, data: Dict[str, Any], batches_data: Optional[List[Dict[str, Any]]] = None) -> Course:
        """
        Create a course with optional batch data.
        
        Args:
            data: Dictionary containing course data
            batches_data: Optional list of dictionaries containing batch data
            
        Returns:
            Newly created course instance
        """
        try:
            with transaction.atomic():
                # Validate permissions and get authorized academy ID
                authorized_academy_id = self._get_authorized_academy_id(data.get('academy_id'))

                # Override academy_id with authorized one
                data['academy_id'] = authorized_academy_id

                # Create course
                course = Course.objects.create(
                    name=data['name'],
                    description=data.get('description', ''),
                    fee=data['fee'],
                    academy_id=data['academy_id']
                )
                
                # Create batches if provided
                if batches_data:
                    for batch_data in batches_data:
                        try:
                            self.batch_service.create_batch({
                                **batch_data,
                                'course_id': course.id
                            })
                        except IntegrityError as e:
                            if 'academy_batch_name_course_id' in str(e):
                                batch_name = batch_data.get('name', 'Unknown')
                                raise ValidationError(f"Batch with name '{batch_name}' already exists for this course.")
                            raise
                
                return course
        except IntegrityError as e:
            if 'unique_course_name_per_academy' in str(e):
                raise ValidationError("A course with the same name already exists for this academy.")
            raise
    
    def update_course(self, course_id: int, data: Dict[str, Any], batches_data: Optional[List[Dict[str, Any]]] = None) -> Course:
        """
        Update a course with optional batch data.
        
        Args:
            course_id: ID of the course to update
            data: Dictionary containing updated course data
            batches_data: Optional list of dictionaries containing batch data
            
        Returns:
            Updated course instance
        """
        try:
            with transaction.atomic():
                # Validate permissions and get authorized academy ID
                authorized_academy_id = self._get_authorized_academy_id(data.get('academy_id'))

                # Override academy_id with authorized one
                data['academy_id'] = authorized_academy_id
                
                # Get course
                course = Course.objects.get(id=course_id)
                
                # Update course fields
                if 'name' in data:
                    course.name = data['name']
                if 'description' in data:
                    course.description = data['description']
                if 'fee' in data:
                    course.fee = data['fee']
                if 'academy_id' in data:
                    course.academy_id = data['academy_id']
                
                course.save()
                
                # Update batches if provided
                if batches_data:
                    for batch_data in batches_data:
                        batch_id = batch_data.pop('id', None)
                        if batch_id:
                            # Update existing batch
                            self.batch_service.update_batch(batch_id, batch_data)
                        else:
                            # Create new batch
                            try:
                                self.batch_service.create_batch({
                                    **batch_data,
                                    'course_id': course.id
                                })
                            except IntegrityError as e:
                                if 'academy_batch_name_course_id' in str(e):
                                    batch_name = batch_data.get('name', 'Unknown')
                                    raise ValidationError(f"Batch with name '{batch_name}' already exists for this course.")
                                raise
                
                return course
        except IntegrityError as e:
            if 'unique_course_name_per_academy' in str(e):
                raise ValidationError("A course with the same name already exists for this academy.")
            raise