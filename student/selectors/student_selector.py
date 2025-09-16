from typing import Optional, Union, Dict, Any
from django.db import models
from django.db.models import QuerySet
from student.models import Student


class StudentSelector:
    """
    Selector class for Student model to handle all read operations.
    """
    
    @staticmethod
    def get_student_by_id(student_id: int) -> Optional[Student]:
        """
        Get a student by ID with optimized prefetches.
        
        Args:
            student_id: The ID of the student
            
        Returns:
            Student instance or None if not found
        """
        try:
            return Student.objects.select_related('user', 'school').get(id=student_id)
        except Student.DoesNotExist:
            return None
    
    @staticmethod
    def get_students(
        search: Optional[str] = None,
        school_id: Optional[int] = None,
        active_only: bool = True
    ) -> QuerySet:
        """
        Get students with filters and optimized prefetches.
        
        Args:
            search: Search term for name, email, phone or student_id
            school_id: Filter by school ID
            active_only: Only return active students
            
        Returns:
            QuerySet of Student instances
        """
        # Start with optimized query
        query = Student.objects.select_related('user', 'school')
        
        # Apply filters
        if active_only:
            query = query.filter(user__is_active=True)
            
        if school_id:
            query = query.filter(school_id=school_id)
            
        if search:
            query = query.filter(
                models.Q(user__first_name__icontains=search) |
                models.Q(user__last_name__icontains=search) |
                models.Q(user__email__icontains=search) |
                models.Q(user__phone__icontains=search) |
                models.Q(student_id__icontains=search)
            )
            
        return query