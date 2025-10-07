from typing import Optional
from django.db.models import QuerySet, F, Value, CharField, Q
from django.db.models.functions import Concat
from student.models import School
from account import choices as account_choices


class SchoolSelector:
    """
    Selector class for Student model to handle all read operations.
    """

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

        # Apply search filter if provided
        if search:
            query = query.filter(
                Q(name__icontains=search) |
                Q(id__icontains=search)
            )
        
        # Order by name for better usability
        return query.order_by('name')
