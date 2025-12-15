from typing import Optional, List, Dict, Any, Tuple
from django.db.models import QuerySet, F, Value, CharField, Q
from django.db.models.functions import Concat
from student.models import School
from account import choices as account_choices
from django.core.paginator import Paginator

class SchoolSelector:
    """
    Selector class for Student model to handle all read operations.
    """

    @staticmethod
    def get_by_id(school_id: int) -> Optional[School]:
        return School.objects.filter(id=school_id).first()
    
    @staticmethod
    def paginate_queryset(queryset, page_size, page):
        """Apply pagination"""
        page_size = int(page_size)
        page_number = int(page)
        
        # Limit page size to prevent abuse
        max_page_size = 2000
        page_size = min(page_size, max_page_size)

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
    def apply_list_search(queryset, search_query):
        """Apply search across multiple fields"""

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(address__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(contact_number__icontains=search_query) |
                Q(website__icontains=search_query)
            )
        return queryset

    @staticmethod
    def list_schools(
            search_query: Optional[str] = None,
            page: int = 1,
            page_size: int = 20
        ) -> Tuple[QuerySet, Dict[str, Any]]:
        queryset = School.objects.all().order_by('name')

        # Apply search
        queryset = SchoolSelector.apply_list_search(queryset, search_query)

        # Apply pagination
        paginated_data = SchoolSelector.paginate_queryset(queryset, page_size, page)

        return paginated_data

    @staticmethod
    def get_schools_for_dropdown(
        search: Optional[str] = None,
    ) -> QuerySet:
        """
        Get schools for dropdown based on user role.

        Args:
            user: The current authenticated user
            academy_id: Optional filter for a specific academy
            search: Optional search term for name or school_id

        Returns:
            QuerySet of schools with optimized fields for dropdown
        """
        # Start with an optimized query using select_related for user data
        query = School.objects.only(
            'id', 'name'
        )

        if not search:
            query = query.filter(name__icontains='rajshahi')

        # Apply search filter if provided
        if search:
            query = query.filter(
                Q(name__icontains=search) |
                Q(id__icontains=search)
            )
        
        # Order by name for better usability
        return query.order_by('name')[:500]
