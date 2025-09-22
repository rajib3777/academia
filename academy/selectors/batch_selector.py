from typing import Optional, Dict, Any, List, Tuple
from django.db.models import QuerySet, Q, Count, Prefetch, F, ExpressionWrapper, IntegerField, Case, When, Value, CharField
from django.db.models.functions import Extract
from django.utils import timezone
from django.core.paginator import Paginator
from academy.models import Batch, Course
from account import choices as account_choices

class BatchSelector:
    """
    Selector class for Batch model to handle all read operations.
    """
    
    @staticmethod
    def get_batch_by_id(batch_id: int) -> Optional[Batch]:
        """
        Get a batch by ID with related data.
        
        Args:
            batch_id: The ID of the batch to retrieve
            
        Returns:
            Batch instance or None if not found
        """
        try:
            return Batch.objects.select_related('course', 'course__academy').get(id=batch_id)
        except Batch.DoesNotExist:
            return None
        
    @staticmethod
    def get_batches() -> QuerySet:
        queryset = Batch.objects.select_related(
            'course', 'course__academy'
        ).annotate(
            student_count=Count('students'),
            duration_days=Extract(
                F('end_date') - F('start_date'),
                'day',  # Extract days component
                output_field=IntegerField()
            ),
            status=Case(
                When(start_date__gt=timezone.now().date(), then=Value('Upcoming')),
                When(end_date__lt=timezone.now().date(), then=Value('Completed')),
                default=Value('Ongoing'),
                output_field=CharField()
            )
        ).prefetch_related('students')
        return queryset
    
    @staticmethod
    def apply_list_permission_filtering(queryset: QuerySet, request) -> QuerySet:
        """Apply permission-based filtering to the queryset."""
        request_user = request.user

        # Check if user is from an academy
        if request_user.is_academy():
            if hasattr(request_user, 'academy') and request_user.academy.exists():
                # Filter students based on academy enrollment
                academy_id = request_user.academy.first().id
                queryset = queryset.filter(course__academy_id=academy_id)
            else:
                # No academy associated, return empty queryset
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"User {request_user.id} has academy role but no academy association. "
                    "This may indicate incomplete user setup or data inconsistency."
                )
                return queryset.none()
        elif request_user.is_student():
            # Students can only see batches they are enrolled in
            queryset = queryset.filter(students__user__id=request_user.id)
            
        # Admins and other roles can see all batches
        return queryset
    
    @staticmethod
    def apply_list_filter(queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """Apply filtering based on provided filter parameters."""
        if filters.get('academy_id'):
            queryset = queryset.filter(course__academy_id=filters['academy_id'])
            
        if filters.get('course_id'):
            queryset = queryset.filter(course_id=filters['course_id'])

        if filters.get('course__course_type'):
            queryset = queryset.filter(course__course_type=filters['course__course_type'])
            
        if filters.get('name'):
            queryset = queryset.filter(name__icontains=filters['name'])
            
        if filters.get('is_active') is not None:
            is_active = filters['is_active'].lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
            
        if filters.get('start_date_from'):
            queryset = queryset.filter(start_date__gte=filters['start_date_from'])
            
        if filters.get('start_date_to'):
            queryset = queryset.filter(start_date__lte=filters['start_date_to'])
            
        if filters.get('end_date_from'):
            queryset = queryset.filter(end_date__gte=filters['end_date_from'])
            
        if filters.get('end_date_to'):
            queryset = queryset.filter(end_date__lte=filters['end_date_to'])
            
        if filters.get('has_students') is not None:
            has_students = filters['has_students'].lower() == 'true'
            if has_students:
                queryset = queryset.filter(student_count__gt=0)
            else:
                queryset = queryset.filter(student_count=0)
                
        return queryset
    
    @staticmethod
    def apply_list_search(queryset, search_query):
        """Apply search across multiple fields"""

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(course__name__icontains=search_query) |
                Q(course__academy__name__icontains=search_query)
            ).distinct()

        return queryset

    @staticmethod
    def apply_list_ordering(queryset, ordering):
        """Apply ordering with multiple fields support"""
        ordering = ordering or '-start_date'

        # Define allowed ordering fields
        allowed_fields = [
            'name', 'start_date', 'end_date', 'course__name', 'student_count'
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
        return queryset.order_by('-start_date')
    
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
    def list_batches(
        request,
        filters: Dict[str, Any] = None,
        search_query: Optional[str] = None,
        ordering: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[QuerySet, Dict[str, Any]]:
        """
        List batches with advanced filtering options.
        
        Args:
            request: The current request object for permission-based filtering
            filters: Dictionary of filter parameters
            search_query: Optional search term
            ordering: Optional field to order by
            page: Page number for pagination
            page_size: Number of items per page
            
        Returns:
            Tuple of (queryset, pagination_info)
        """
        # Base queryset with optimized joins
        queryset = BatchSelector.get_batches()

        # Apply permission filtering
        queryset = BatchSelector.apply_list_permission_filtering(queryset, request)

        # Apply filters
        queryset = BatchSelector.apply_list_filter(queryset, filters)
        
        # Apply search
        queryset = BatchSelector.apply_list_search(queryset, search_query)
        
        # Apply ordering
        queryset = BatchSelector.apply_list_ordering(queryset, ordering)
        
        # Apply pagination
        paginated_data = BatchSelector.paginate_queryset(queryset, page_size, page)
        
        return paginated_data