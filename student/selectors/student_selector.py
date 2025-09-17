from typing import Optional, Union, Dict, Any, List
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db import models
from django.db.models import QuerySet, F, Value, CharField, Q
from django.db.models.functions import Concat
from student.models import Student
from account import choices as account_choices


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
    
    @staticmethod
    def get_students_for_dropdown(
        user=None,
        academy_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> QuerySet:
        """
        Get students for dropdown based on user role.
        
        Args:
            user: The current authenticated user
            academy_id: Optional filter for a specific academy
            search: Optional search term for name or student_id
            
        Returns:
            QuerySet of students with optimized fields for dropdown
        """
        # Start with an optimized query using select_related for user data
        query = Student.objects.select_related('user', 'school').only(
            'student_id', 'school_id', 'user__first_name', 'user__last_name'
        )
        
        # Apply search filter if provided
        if search:
            query = query.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(student_id__icontains=search)
            )
        
        #  Apply role-based filtering
        if user:
            # Only active students
            query = query.filter(user__is_active=True)

            # Check if user is from an academy
            if user.role.name == account_choices.ACADEMY:
                if hasattr(user, 'academy') and user.academy.exists():
                    # Filter students based on academy enrollment
                    academy_id = academy_id or user.academy.first().id
                    query = query.filter(
                        batchenrollment__batch__course__academy_id=academy_id
                    ).distinct()
        
        # Annotate with full name
        query = query.annotate(
            full_name=Concat(
                'user__first_name', 
                Value(' '), 
                'user__last_name',
                output_field=CharField()
            )
        )
        
        # Order by name for better usability
        return query.order_by('user__first_name', 'user__last_name')