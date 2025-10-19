from typing import Optional, Dict, Any
from django.db.models import QuerySet, Q
from django.core.paginator import Paginator
from account.models import User
from academy.models import BatchEnrollment
from django.db.models import QuerySet

class BatchEnrollmentSelector:
    """
    Selector for BatchEnrollment ORM reads and permission checks.
    """

    @staticmethod
    def get_by_id(enrollment_id: int) -> Optional[BatchEnrollment]:
        try:
            return BatchEnrollment.objects.select_related(
                'student', 'batch', 'batch__course', 'batch__course__academy', 'final_grade'
            ).get(id=enrollment_id)
        except BatchEnrollment.DoesNotExist:
            return BatchEnrollment.objects.none()
        
    @staticmethod
    def get_all_enrollments() -> QuerySet[BatchEnrollment]:
        try:
            return BatchEnrollment.objects.select_related(
                'student', 'batch', 'batch__course', 'batch__course__academy', 'final_grade'
            ).all()
        except Exception as e:
            return BatchEnrollment.objects.none()

    @staticmethod
    def get_role_based_filtering(queryset: QuerySet, request_user: User) -> QuerySet:
        if request_user.is_admin():
            return queryset  # Admin sees all
        elif request_user.is_academy():
            academy_id = getattr(request_user.academy.first(), 'id', None)
            if academy_id:
                return queryset.filter(batch__course__academy_id=academy_id)
            else:
                return queryset.none()
        elif request_user.is_student():
            return queryset.filter(student_id=request_user.student.id, is_active=True)
        else:
            return queryset.none()

    @staticmethod
    def apply_list_filters(
        queryset: QuerySet,
        filters: Dict[str, Any]
    ) -> QuerySet:
        if filters.get('academy_id'):
            queryset = queryset.filter(batch__course__academy_id=filters['academy_id'])
        if filters.get('course_id'):
            queryset = queryset.filter(batch__course_id=filters['course_id'])
        if filters.get('course_type'):
            queryset = queryset.filter(batch__course__course_type=filters['course_type'])
        if filters.get('batch_id'):
            queryset = queryset.filter(batch_id=filters['batch_id'])
        if filters.get('batch_start_date_from'):
            queryset = queryset.filter(batch__start_date__gte=filters['batch_start_date_from'])
        if filters.get('batch_start_date_to'):
            queryset = queryset.filter(batch__start_date__lte=filters['batch_start_date_to'])
        if filters.get('batch_end_date_from'):
            queryset = queryset.filter(batch__end_date__gte=filters['batch_end_date_from'])
        if filters.get('batch_end_date_to'):
            queryset = queryset.filter(batch__end_date__lte=filters['batch_end_date_to'])
        if filters.get('batch_is_active') is not None:
            queryset = queryset.filter(batch__is_active=filters['batch_is_active'])
        if filters.get('enrollment_date_from'):
            queryset = queryset.filter(enrollment_date__gte=filters['enrollment_date_from'])
        if filters.get('enrollment_date_to'):
            queryset = queryset.filter(enrollment_date__lte=filters['enrollment_date_to'])
        if filters.get('completion_date_from'):
            queryset = queryset.filter(completion_date__gte=filters['completion_date_from'])
        if filters.get('completion_date_to'):
            queryset = queryset.filter(completion_date__lte=filters['completion_date_to'])
        if filters.get('is_active') is not None:
            is_active = filters['is_active'].lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        if filters.get('final_grade'):
            queryset = queryset.filter(final_grade__grade__icontains=filters['final_grade'])

        return queryset
    
    @staticmethod
    def apply_list_search(
        queryset: QuerySet,
        search: Optional[str]
    ) -> QuerySet:
        if search:
            queryset = queryset.filter(
                Q(student__user__first_name__icontains=search) |
                Q(student__user__last_name__icontains=search) |
                Q(batch__name__icontains=search) |
                Q(batch__course__name__icontains=search) |
                Q(batch__course__course_type__icontains=search) |
                Q(batch__course__academy__name__icontains=search) |
                Q(remarks__icontains=search)
            )
        return queryset.order_by('-enrollment_date')

    @staticmethod
    def apply_list_ordering(
        queryset: QuerySet,
        ordering: Optional[str]
    ) -> QuerySet:
        if ordering:
            queryset = queryset.order_by(*ordering.split(','))
        return queryset.order_by('-enrollment_date')
    
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
    def list_enrollments(
        request_user: User,
        filters: Dict[str, Any] = None,
        search_query: Optional[str] = None,
        ordering: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> QuerySet:
        filters = filters or {}
        # Get base optimized queryset
        queryset = BatchEnrollmentSelector.get_all_enrollments()

        # Role-based filtering
        queryset = BatchEnrollmentSelector.get_role_based_filtering(queryset, request_user)

        # Apply filters
        queryset = BatchEnrollmentSelector.apply_list_filters(queryset, filters)

        # Apply Search
        queryset = BatchEnrollmentSelector.apply_list_search(queryset, search_query)

        # Apply Ordering
        queryset = BatchEnrollmentSelector.apply_list_ordering(queryset, ordering)

        # Pagination
        paginated_data = BatchEnrollmentSelector.paginate_queryset(queryset, page_size, page)

        return paginated_data