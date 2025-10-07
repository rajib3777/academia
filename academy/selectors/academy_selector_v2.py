from typing import Dict, List, Optional, Tuple, Any
from django.db.models import QuerySet, Count, Prefetch, Q, F
from django.core.paginator import Paginator
from account import choices as account_choices
from academy.models import Academy, Batch, BatchEnrollment, Course
from account.models import User


class AcademySelector:
    """
    Selector for Academy model to handle all read operations with optimized queries.
    """

    def get_by_user(self, user: User) -> Academy:
        return Academy.objects.select_related('user').get(user=user)
    
    @staticmethod
    def get_page_range_with_ellipsis(current_page: int, total_pages: int, delta: int = 2) -> List:
        """
        Generate pagination list with ellipsis.
        
        Args:
            current_page: Current page number
            total_pages: Total number of pages
            delta: Number of pages to show on each side of current page
            
        Returns:
            List with page numbers and ellipsis placeholders
        """
        range_with_ellipsis = []
        left = max(1, current_page - delta)
        right = min(total_pages, current_page + delta)

        if left > 1:
            range_with_ellipsis.append(1)
            if left > 2:
                range_with_ellipsis.append("...")

        for i in range(left, right + 1):
            range_with_ellipsis.append(i)

        if right < total_pages:
            if right < total_pages - 1:
                range_with_ellipsis.append("...")
            range_with_ellipsis.append(total_pages)

        return range_with_ellipsis

    @staticmethod
    def get_all_academies(request_user: Any, academy_id: Optional[int] = None) -> QuerySet:
        """
        Get all academies with optimized related data loading.
        
        Returns:
            QuerySet of all academies
        """
        # Role-based filtering
        if request_user.role.name == account_choices.ACADEMY:
            if hasattr(request_user, 'academy') and request_user.academy.exists():
                academy_id = request_user.academy.first().id
                queryset = Academy.objects.filter(id=academy_id).select_related('user', 'division', 'district', 'upazila')
            else:
                return Academy.objects.none()
        elif academy_id and (request_user.is_admin or request_user.is_staff):
            queryset = Academy.objects.filter(id=academy_id).select_related('user', 'division', 'district', 'upazila')
        elif request_user.is_admin or request_user.is_staff:
            queryset = Academy.objects.all().select_related('user', 'division', 'district', 'upazila')
        else:
            return Academy.objects.none()

        # Add annotations for counts
        queryset = queryset.annotate(course_count=Count('courses', distinct=True))

        # Optimized select_related for foreign keys
        queryset = queryset.select_related('user', 'division', 'district', 'upazila')

        # Optimize with prefetch_related for related collections with nested prefetches
        batch_enrollments = Prefetch(
            'batchenrollment_set',
            queryset=BatchEnrollment.objects.select_related('student', 'student__user', 'final_grade')
        )
        
        batches = Prefetch(
            'batches',
            queryset=Batch.objects.select_related('course')
                        .prefetch_related(batch_enrollments)
                        .annotate(enrollment_count=Count('batchenrollment'))
        )
        
        courses = Prefetch(
            'courses',
            queryset=Course.objects.prefetch_related(batches)
                        .annotate(batch_count=Count('batches', distinct=True))
        )

        queryset = queryset.prefetch_related(courses)
        return queryset
    
    @staticmethod
    def apply_list_filters(queryset: QuerySet, filters: Dict) -> QuerySet:
        """
        Apply filters to the academy queryset.
        
        Args:
            queryset: Base queryset to filter
            filters: Dictionary of filter parameters
            
        Returns:
            Filtered queryset
        """
        if filters.get('division'):
            queryset = queryset.filter(division_id=filters['division'])
        if filters.get('district'):
            queryset = queryset.filter(district_id=filters['district'])
        if filters.get('upazila'):
            queryset = queryset.filter(upazila_id=filters['upazila'])
        if 'is_active' in filters:
            queryset = queryset.filter(is_active=filters['is_active'])
        if filters.get('established_year'):
            queryset = queryset.filter(established_year=filters['established_year'])
        
        return queryset
    
    @staticmethod
    def apply_list_ordering(queryset: QuerySet, ordering: str) -> QuerySet:
        """
        Apply ordering to the academy queryset.
        
        Args:
            queryset: Base queryset to order
            ordering: Field to order by
            
        Returns:
            Ordered queryset
        """
        if ordering:
            if ordering.startswith('-'):
                field = ordering[1:]
                if field in ['id', 'name', 'created_at', 'established_year']:
                    queryset = queryset.order_by(ordering)
            else:
                if ordering in ['id', 'name', 'created_at', 'established_year']:
                    queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('name')  # Default ordering
        
        return queryset
    
    @staticmethod
    def apply_list_search(queryset: QuerySet, search_query: str) -> QuerySet:
        # Apply search
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(contact_number__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query)
            )
            return queryset
        return queryset
    
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
    def list_academies(
        request_user: Any,
        academy_id: Optional[int] = None,
        filters: Dict[str, Any] = None,
        search_query: Optional[str] = None,
        ordering: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[QuerySet, Dict[str, Any]]:
        """
        List academies with optimized query and pagination.
        
        Args:
            user: Current user for permission filtering
            search_query: Search text to filter academies
            filters: Dictionary of filter parameters
            ordering: Field to order results by
            page: Page number
            page_size: Items per page
        
        Returns:
            Tuple of (academies, total count, paginator, page object, page range)
        """
        # Get base queryset with optimized joins
        queryset = AcademySelector.get_all_academies(request_user, academy_id)

        # Apply filters
        queryset = AcademySelector.apply_list_filters(queryset, filters)

        # Apply search
        queryset = AcademySelector.apply_list_search(queryset, search_query)

        # Apply ordering
        queryset = AcademySelector.apply_list_ordering(queryset, ordering)

        # Apply pagination
        paginated_data = AcademySelector.paginate_queryset(queryset, page_size, page)
        
        return paginated_data

    def get_academy_by_id(self, academy_id: int) -> Optional[Academy]:
        """
        Get academy by ID with optimized related data loading.
        
        Args:
            academy_id: ID of the academy to retrieve
            
        Returns:
            Academy instance or None if not found
        """
        try:
            # Similar optimized query as in list_academies
            academy = Academy.objects.select_related(
                'user', 'division', 'district', 'upazila'
            ).prefetch_related(
                Prefetch(
                    'courses',
                    queryset=Course.objects.prefetch_related(
                        Prefetch(
                            'batches',
                            queryset=Batch.objects.prefetch_related(
                                Prefetch(
                                    'batchenrollment_set',
                                    queryset=BatchEnrollment.objects.select_related(
                                        'student', 'student__user', 'final_grade'
                                    )
                                )
                            ).annotate(enrollment_count=Count('batchenrollment'))
                        )
                    ).annotate(batch_count=Count('batches', distinct=True))
                )
            ).annotate(
                course_count=Count('courses', distinct=True)
            ).get(id=academy_id)
            
            return academy
        except Academy.DoesNotExist:
            return None