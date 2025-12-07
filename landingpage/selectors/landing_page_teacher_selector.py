from django.db.models import Q, Count, Avg, Prefetch
from teacher.models import Teacher
from django.core.paginator import Paginator
from landingpage.models import TeacherSubject, TeacherEducation, TeacherAchievement, TeacherReview
from academy.models import Academy

class LandingPageTeacherSelector:
    @staticmethod
    def get_featured_teachers(limit=4):
        """
        Get featured teachers for landing page
        """
        return Teacher.objects.filter(
            is_active=True,
            is_featured=True,
            academy__user__is_active=True
        ).select_related(
            'academy'
        ).prefetch_related(
            'subjects',
            Prefetch(
                'reviews',
                queryset=TeacherReview.objects.filter(is_approved=True, is_active=True)
            )
        ).order_by('-created_at')[:limit]


    @staticmethod
    def get_all_teachers_with_filters(
        search=None, 
        subject=None, 
        min_experience=None, 
        max_experience=None, 
        min_rating=None, 
        is_available=None,
        page=1,
        page_size=12
    ):
        """
        Get all teachers with optional filters
        """
        queryset = Teacher.objects.filter(
            is_active=True,
            academy__user__is_active=True
        ).select_related(
            'academy'
        ).prefetch_related(
            'subjects',
            Prefetch(
                'reviews',
                queryset=TeacherReview.objects.filter(is_approved=True, is_active=True)
            )
        )
        
        # Search filter (name, title, bio)
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(title__icontains=search) |
                Q(bio__icontains=search)
            )
        
        # Subject filter
        if subject:
            queryset = queryset.filter(subjects__subject=subject).distinct()
        
        # Experience filters
        if min_experience is not None:
            queryset = queryset.filter(experience_years__gte=min_experience)
        
        if max_experience is not None:
            queryset = queryset.filter(experience_years__lte=max_experience)
        
        # Availability filter
        if is_available is not None:
            queryset = queryset.filter(is_available=is_available)
        
        # Rating filter (requires annotation)
        if min_rating is not None:
            queryset = queryset.annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True, reviews__is_active=True))
            ).filter(avg_rating__gte=min_rating)
        
        queryset = queryset.order_by('-is_featured', '-created_at')
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
    def get_teacher_by_id(teacher_id):
        """
        Get teacher details by ID
        """
        return Teacher.objects.filter(
            id=teacher_id,
            is_active=True,
            academy__user__is_active=True
        ).select_related(
            'academy',
            'academy__division',
            'academy__district',
            'academy__upazila'
        ).prefetch_related(
            'subjects',
            'educations',
            'achievements',
            Prefetch(
                'reviews',
                queryset=TeacherReview.objects.filter(
                    is_approved=True, 
                    is_active=True
                ).order_by('-reviewed_at')
            )
        ).first()


    @staticmethod
    def get_subject_filter_options():
        """
        Get all unique subjects taught by active teachers for filter options
        """
        from academy.choices_fields import SUBJECT_TYPE_CHOICES
        
        # Get subjects that are actually being taught
        active_subjects = TeacherSubject.objects.filter(
            teacher__is_active=True,
            teacher__academy__user__is_active=True
        ).values_list('subject', flat=True).distinct()
        
        # Return only the subjects that are active
        return [
            {'value': subject[0], 'label': subject[1]}
            for subject in SUBJECT_TYPE_CHOICES
            if subject[0] in active_subjects
        ]

