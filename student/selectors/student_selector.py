from typing import Optional, Union, Dict, Any, List, Tuple
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db import models
from django.db.models import QuerySet, F, Value, CharField, Q
from django.db.models.functions import Concat
from student.models import Student
from student.utils import StudentFilter
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
    def get_all_active_students() -> QuerySet:
        """
        Get all active students with optimized prefetches.
        
        Returns:
            QuerySet of active Student instances
        """
        return Student.objects.select_related('user', 'school').filter(user__is_active=True)

    @staticmethod
    def apply_list_filters(queryset, filters):
        """Apply filters using django-filter"""
        filterset = StudentFilter(filters, queryset=queryset)
        if filterset.is_valid():
            return filterset.qs
        return queryset

    @staticmethod
    def apply_list_search(queryset, search_query):
        """Apply search across multiple fields"""

        if search_query:
            # Check if search query contains only digits (likely a phone number search)
            is_numeric_search = search_query.isdigit()
            
            # If searching for numbers that could be part of a phone number
            if is_numeric_search and len(search_query) >= 8:
                # Try direct phone number contains search first
                phone_matches = queryset.filter(
                    Q(user__phone__contains=search_query) |
                    Q(guardian_phone__contains=search_query) | 
                    Q(birth_registration_number__contains=search_query)
                )
                
                # If we found phone matches, return them
                if phone_matches.exists():
                    return phone_matches
                
            # Use full-text search for better performance on large datasets
            search_query_obj = SearchQuery(search_query)

            # Create search vectors for each searchable field
            search_vectors = (
                SearchVector('user__username', weight='A') +
                SearchVector('user__email', weight='A') +
                SearchVector('user__first_name', weight='A') +
                SearchVector('user__last_name', weight='A') +
                SearchVector('user__phone', weight='A') +
                SearchVector('student_id', weight='A') +
                SearchVector('birth_registration_number', weight='B') +
                SearchVector('guardian_name', weight='B') +
                SearchVector('guardian_phone', weight='B') +
                SearchVector('guardian_email', weight='B') +
                SearchVector('address', weight='C') +
                SearchVector('school__name', weight='B')
            )

            # First try exact match
            exact_query_results = queryset.annotate(
                search=search_vectors,
                rank=SearchRank(search_vectors, search_query_obj)
            ).filter(search=search_query_obj).order_by('-rank')

            # If no results from exact match, try with minimum threshold
            if not exact_query_results.exists():
                minimum_query_results = queryset.annotate(
                    search_rank=SearchRank(search_vectors, search_query_obj)
                ).filter(search_rank__gte=0.1).order_by('-search_rank')

                if not minimum_query_results.exists():
                    return queryset.filter(
                        Q(user__username__icontains=search_query) |
                        Q(user__email__icontains=search_query) |
                        Q(user__first_name__icontains=search_query) |
                        Q(user__last_name__icontains=search_query) |
                        Q(student_id__icontains=search_query) |
                        Q(birth_registration_number__icontains=search_query) |
                        Q(guardian_name__icontains=search_query) |
                        Q(guardian_phone__icontains=search_query) |
                        Q(guardian_email__icontains=search_query) |
                        Q(address__icontains=search_query) |
                        Q(school__name__icontains=search_query)
                    )
                
                return minimum_query_results

            return exact_query_results

        return queryset

    @staticmethod
    def apply_list_ordering(queryset, ordering):
        """Apply ordering with multiple fields support"""
        ordering = ordering or '-created_at'

        # Define allowed ordering fields
        allowed_fields = [
            'id', 'student_id', 'created_at', 'modified_at', 'date_of_birth',
            'user__username', 'user__email', 'user__first_name', 'user__last_name',
            'school__name', 'guardian_name'
        ]
        
        # Handle multiple ordering fields
        if ordering:
            order_fields = [field.strip() for field in ordering.split(',')]
            valid_fields = []
            
            for field in order_fields:
                # Remove '-' prefix for validation
                field_name = field.lstrip('-')
                if field_name in allowed_fields:
                    valid_fields.append(field)
            
            if valid_fields:
                return queryset.order_by(*valid_fields)
        
        # Default ordering
        return queryset.order_by('-created_at')

    @staticmethod
    def paginate_queryset(queryset, page_size, page):
        """Apply pagination"""
        page_size = int(page_size)
        page_number = int(page)
        
        # Limit page size to prevent abuse
        page_size = min(page_size, 20)
        
        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)
        
        return {
            'results': page.object_list,
            'pagination': {
                'page': page_number,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page.has_next(),
                'has_previous': page.has_previous(),
                'next_page': page.next_page_number() if page.has_next() else None,
                'previous_page': page.previous_page_number() if page.has_previous() else None,
            }
        }
    
    
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
        
        # Apply search filter if provided
        if search:
            query = query.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(student_id__icontains=search)
            )
        
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
    
    @staticmethod
    def list_students(
        filters: Dict[str, Any] = None,
        search_query: Optional[str] = None,
        ordering: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[QuerySet, Dict[str, Any]]:
        """
        Get filtered, searched, ordered, and paginated list of students.
        
        Args:
            filters: Dictionary of filter parameters
            search_query: Optional search term
            ordering: Optional ordering string (comma-separated field names)
            page: Page number for pagination
            page_size: Number of items per page
            
        Returns:
            Tuple[QuerySet, Dict]: Queryset of student objects and pagination info
        """
        # Get base queryset with optimized joins
        queryset = StudentSelector.get_all_active_students()
        
        # Apply filters
        queryset = StudentSelector.apply_list_filters(queryset, filters)
        
        # Apply search
        queryset = StudentSelector.apply_list_search(queryset, search_query)
        
        # Apply ordering
        queryset = StudentSelector.apply_list_ordering(queryset, ordering)

        # Apply pagination
        paginated_data = StudentSelector.paginate_queryset(queryset, page_size, page)

        return paginated_data