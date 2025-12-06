from typing import Dict, List, Optional, Tuple, Any
from django.db.models import QuerySet, Count, Avg, Prefetch, Q, F
from django.core.paginator import Paginator
from landingpage.models import (
    AcademyGallery, 
    AcademyFacility, 
    AcademyProgram,
    AcademyReview,

)

from academy.models import (
    Academy, 
    Course,
    Batch,
    BatchEnrollment
)

class LandingPageAcademySelector:
    """
    Selector for landing page academy operations.
    Handles public-facing academy data retrieval.
    """
    
    @staticmethod
    def get_featured_academies(limit: int = 6) -> QuerySet:
        """
        Get featured academies for the main landing page.
        
        Args:
            limit: Maximum number of academies to return
            
        Returns:
            QuerySet of featured academies with optimized data
        """
        return Academy.objects.filter(
            is_featured=True,
            user__is_active=True
        ).select_related(
            'division', 
            'district', 
            'upazila'
        ).order_by('-created_at')[:limit]
        # .prefetch_related(
        #     'programs'
        # ).annotate(
        #     total_student=Count(
        #         'courses__batches__batchenrollment',
        #         filter=Q(courses__batches__batchenrollment__is_active=True),
        #         distinct=True
        #     ),
        #     average_rating=Avg(
        #         'reviews__rating',
        #         filter=Q(
        #             reviews__is_approved=True,
        #             reviews__is_active=True
        #         )
        #     ),
        #     review_count=Count(
        #         'reviews',
        #         filter=Q(
        #             reviews__is_approved=True,
        #             reviews__is_active=True
        #         )
        #     )
        # ).order_by('-created_at')[:limit]
    
    @staticmethod
    def get_all_academies_for_listing(
        search_query: Optional[str] = None,
        program_filter: Optional[str] = None,
        division_id: Optional[int] = None,
        district_id: Optional[int] = None,
        min_rating: Optional[float] = None,
        page: int = 1,
        page_size: int = 12
    ) -> Dict[str, Any]:
        """
        Get all academies for the academies listing page with filters.
        
        Args:
            search_query: Search term for academy name/description
            program_filter: Filter by program name
            division_id: Filter by division
            district_id: Filter by district
            min_rating: Minimum rating filter
            page: Page number
            page_size: Number of items per page
            
        Returns:
            Dictionary with paginated results and metadata
        """
        # Base queryset
        queryset = Academy.objects.filter(
            user__is_active=True
        ).select_related(
            'division', 
            'district', 
            'upazila'
        ).prefetch_related(
            'programs'
        ).annotate(
            # total_students=Count(
            #     'courses__batches__batchenrollment',
            #     filter=Q(courses__batches__batchenrollment__is_active=True),
            #     distinct=True
            # ),
            average_ratings=Avg(
                'reviews__rating',
                filter=Q(
                    reviews__is_approved=True,
                    reviews__is_active=True
                )
            ),
            # review_count=Count(
            #     'reviews',
            #     filter=Q(
            #         reviews__is_approved=True,
            #         reviews__is_active=True
            #     )
            # )
        )
        
        # Apply search filter
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(short_description__icontains=search_query)
            )
        
        # Apply program filter
        if program_filter:
            queryset = queryset.filter(
                programs__name__icontains=program_filter,
                programs__is_active=True
            ).distinct()
        
        # Apply location filters
        if division_id:
            queryset = queryset.filter(division_id=division_id)
        
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        
        # Apply rating filter
        if min_rating:
            queryset = queryset.filter(average_ratings__gte=min_rating)
        
        # Order by featured first, then by rating
        queryset = queryset.order_by('-is_featured', '-average_ratings', '-created_at')
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        return {
            'results': page_obj.object_list,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
                'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
            }
        }
    
    @staticmethod
    def get_academy_details_for_landing(academy_id: int) -> Optional[Academy]:
        """
        Get detailed academy information for the academy details page.
        
        Args:
            academy_id: ID of the academy
            
        Returns:
            Academy instance with all related data or None
        """
        try:
            return Academy.objects.filter(
                id=academy_id,
                user__is_active=True
            ).select_related(
                'division',
                'district',
                'upazila'
            ).prefetch_related(
                Prefetch(
                    'gallery_images',
                    queryset=AcademyGallery.objects.filter(is_active=True).order_by('order')
                ),
                Prefetch(
                    'facilities',
                    queryset=AcademyFacility.objects.filter(is_active=True)
                ),
                Prefetch(
                    'programs',
                    queryset=AcademyProgram.objects.filter(is_active=True)
                ),
                Prefetch(
                    'reviews',
                    queryset=AcademyReview.objects.filter(
                        is_approved=True,
                        is_active=True
                    ).order_by('-created_at')[:10],  # Latest 10 reviews
                    to_attr='latest_reviews'  # Store in a separate attribute
                ),
                Prefetch(
                    'courses',
                    queryset=Course.objects.prefetch_related(
                        Prefetch(
                            'batches',
                            queryset=Batch.objects.filter(is_active=True)
                        )
                    )
                )
            ).first()
            # .annotate(
            #     total_students=Count(
            #         'courses__batches__batchenrollment',
            #         filter=Q(courses__batches__batchenrollment__is_active=True),
            #         distinct=True
            #     ),
            #     average_rating=Avg(
            #         'reviews__rating',
            #         filter=Q(
            #             reviews__is_approved=True,
            #             reviews__is_active=True
            #         )
            #     ),
            #     review_count=Count(
            #         'reviews',
            #         filter=Q(
            #             reviews__is_approved=True,
            #             reviews__is_active=True
            #         )
            #     )
            # ).first()
        except Academy.DoesNotExist:
            return None
    
    @staticmethod
    def get_available_programs() -> List[str]:
        """
        Get list of all unique program names for filter dropdown.
        
        Returns:
            List of program names
        """
        return AcademyProgram.objects.filter(
            is_active=True
        ).values_list('name', flat=True).distinct().order_by('name')
