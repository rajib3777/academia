from typing import Optional, Dict, Any, List, Tuple
from django.db.models import QuerySet, Prefetch, Q, Count
from django.core.paginator import Paginator
from academy.models import Course, Batch
from student.models import Student
from account import choices as account_choices
from academy.choices_fields import SUBJECT_TYPE_CHOICES

class CourseSelector:
    """
    Selector class for Course model to handle all read operations.
    """
    
    @staticmethod
    def get_course_by_id(course_id: int, include_batches: bool = True) -> Optional[Course]:
        """
        Get a course by ID with optional batch details.
        
        Args:
            course_id: The ID of the course to retrieve
            include_batches: Whether to include batch details
            
        Returns:
            Course instance or None if not found
        """
        query = Course.objects.filter(id=course_id)
        
        if include_batches:
            query = query.prefetch_related('batches')
            
        try:
            return query.get()
        except Course.DoesNotExist:
            return None
    
    @staticmethod
    def get_courses_with_batches(request: Any) -> QuerySet:
        """
        Get courses with batch details, with optional filtering for active batches.
        
        Args:
            request_user: User making the request for permission checks
            academy_id: Optional academy ID to filter courses
            active_batches: Filter for batch activity status
                            None (default): show all batches
                            True: show only active batches
                            False: show only inactive batches
        
        Returns:
            QuerySet of Course objects with prefetched batches
        """
        request_user = request.user

        academy_id = request.query_params.get('academy_id')
        active_batches = True if request.query_params.get('active_batches') == 'true' else (
            False if request.query_params.get('active_batches') == 'false' else None
        )   

        # Build base batch queryset with annotations
        batch_queryset = Batch.objects.annotate(student_count=Count('students')).order_by('start_date')

        # Apply active batch filter if specified
        if active_batches is not None:
            batch_queryset = batch_queryset.filter(is_active=active_batches)

        # Check if user is from an academy
        if request_user.is_academy():
            if hasattr(request_user, 'academy') and request_user.academy.exists():
                # Filter students based on academy enrollment
                academy_id = request_user.academy.first().id
                return Course.objects.select_related('academy').prefetch_related(
                        Prefetch(
                            'batches',
                            queryset=batch_queryset
                        )
                    ).filter(academy_id=academy_id).distinct()
            
        elif request_user.is_student():
            batch_queryset = batch_queryset.filter(students__user__id=request_user.id)
            course_queryset = Course.objects.filter(
                        batches__students__user__id=request_user.id
                ).select_related('academy').prefetch_related(
                    Prefetch(
                        'batches',
                        queryset=batch_queryset
                    )
                ).distinct()
            
            if academy_id:
                course_queryset = course_queryset.filter(academy_id=academy_id)

            return course_queryset
            
        # If admin or staff, return all courses or filter by provided academy_id
        elif academy_id and (request_user.is_admin() or request_user.is_staff):
            return Course.objects.select_related('academy').prefetch_related(
                Prefetch(
                    'batches',
                    queryset=batch_queryset
                )
            ).filter(academy_id=academy_id).distinct()
        
        # If admin or staff, return all courses
        elif request_user.is_admin or request_user.is_staff:
            return Course.objects.select_related('academy').prefetch_related(
                    Prefetch(
                        'batches',
                        queryset=batch_queryset
                    )
                )
        else:
            return Course.objects.none()
    
    @staticmethod
    def apply_list_filter(queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """
        Apply filtering to the queryset based on provided filters.
        
        Args:
            queryset: The base queryset to filter
            filters: Dictionary of filter parameters
            
        Returns:
            Filtered queryset
        """
        course_type = filters.get('course_type')
        min_fee = filters.get('min_fee')
        max_fee = filters.get('max_fee')

        if course_type is not None:
            queryset = queryset.filter(course_type=course_type)

        if min_fee is not None:
            queryset = queryset.filter(fee__gte=min_fee)

        if max_fee is not None:
            queryset = queryset.filter(fee__lte=max_fee)

        return queryset
    
    @staticmethod
    def apply_list_search(queryset, search_query):
        """Apply search across multiple fields"""

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(academy__name__icontains=search_query)
            ).distinct()

        return queryset

    @staticmethod
    def apply_list_ordering(queryset, ordering):
        """Apply ordering with multiple fields support"""
        ordering = ordering or '-created_at'

        # Define allowed ordering fields
        allowed_fields = [
            'name', 'fee', 'created_at', 'academy__name'
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
    def list_courses(
        request: Any,
        filters: Dict[str, Any] = None,
        search_query: Optional[str] = None,
        ordering: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[QuerySet, Dict[str, Any]]:
        """
        List courses with optional filtering, searching, and pagination.
        Args:
            request_user: The current user for permission-based filtering
            filters: Optional dictionary of filter parameters
            search_query: Optional search term for course name or description
            ordering: Optional field to order by
            page: Page number for pagination
            page_size: Number of items per page
            
        Returns:
            Tuple of (queryset, pagination_info)
        """
        # Base queryset with optimized prefetch
        queryset = CourseSelector.get_courses_with_batches(request)
        
        # Apply filters
        queryset = CourseSelector.apply_list_filter(queryset, filters)
        
        # Apply search
        queryset = CourseSelector.apply_list_search(queryset, search_query)
        
        # Apply ordering
        queryset = CourseSelector.apply_list_ordering(queryset, ordering)

        # Apply pagination
        paginated_data = CourseSelector.paginate_queryset(queryset, page_size, page)

        return paginated_data

    @staticmethod
    def get_courses_for_dropdown(
        request=None,
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
        request_user = request.user
        # Start with an optimized query using select_related for user data
        query = Course.objects.select_related('academy').only(
            'id', 'name', 'academy_id'
        )

        # Check if user is from an academy
        if request_user.is_academy():
            if hasattr(request_user, 'academy') and request_user.academy.exists():
                # Filter students based on academy enrollment
                academy_id = academy_id or request_user.academy.first().id
                query = query.filter(
                    academy_id=academy_id
                ).distinct()
            else:
                return query.none()
            
        elif request_user.is_student():
            # Find courses where student is enrolled in at least one batch
            try:
                student = Student.objects.get(user=request_user)
                # Filter courses through the batch relationship
                query = query.filter(batches__students=student)
                
                # Apply academy filter if provided
                if academy_id:
                    query = query.filter(academy_id=academy_id)
                    
                return query.distinct()
            except Student.DoesNotExist:
                return query.none()
        elif request_user.is_admin() or request_user.is_staff():
            if academy_id:
                query = query.filter(
                    academy_id=academy_id
                ).distinct()
            query = query.distinct()
        else:
            return query.none()

        # Apply search filter if provided
        if search:
            query = query.filter(
                Q(name__icontains=search)
            )
        
        # Order by name for better usability
        return query.order_by('name', )
    
    @staticmethod
    def course_has_students(course_id: int) -> bool:
        """
        Check if a course has any students enrolled in any of its batches.
        
        Args:
            course_id: ID of the course to check
            
        Returns:
            Boolean indicating if the course has any students
        """
        try:
            # Check if any batches in the course have students
            return Course.objects.filter(
                id=course_id,
                batches__students__isnull=False
            ).distinct().exists()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error checking if course {course_id} has students: {str(e)}")
            # Default to True to prevent accidental deletion in case of error
            return True
    

class SubjectSelector:
    """
    Selector for course type choices.
    
    This selector provides methods to retrieve course type data
    from the predefined choices.
    """
    
    @staticmethod
    def list_course_types() -> List[Dict[str, str]]:
        """
        Get all available course types.
        
        Returns:
            List of dictionaries with course type values and display names
        """
        return [
            {'id': value, 'name': display_name} 
            for value, display_name in SUBJECT_TYPE_CHOICES
        ]
