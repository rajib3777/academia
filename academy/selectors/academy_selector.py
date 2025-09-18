from typing import List, Optional, Dict, Any
from django.db.models import QuerySet, Q
from academy.models import Academy
from account import choices as account_choices


class AcademySelector:
    """
    Selector class for Academy model to handle all read operations.
    """
    
    @staticmethod
    def get_academies_for_dropdown(
        search_query: Optional[str] = None,
        request_user=None,
        is_active: bool = True
    ) -> QuerySet:
        """
        Get optimized academy data for dropdown selection.
        
        Args:
            search_query: Optional search term for academy name
            user: Current user for permission-based filtering
            is_active: Filter by active status
            
        Returns:
            QuerySet with only necessary fields for dropdown
        """
        # Start with an optimized query using only() for the fields we need
        query = Academy.objects.only('id', 'name')
        
        # Apply active filter if specified
        if is_active:
            query = query.filter(user__is_active=True)
            
        # Apply search filter if provided
        if search_query:
            query = query.filter(name__icontains=search_query)
        
        # Apply permission-based filtering
        if request_user and request_user.role.name == account_choices.ACADEMY:
            # Regular users can only see their own academies
            if hasattr(request_user, 'academy') and request_user.academy.exists():
                query = query.filter(user=request_user)

        # Order by name for user convenience
        return query.order_by('name')