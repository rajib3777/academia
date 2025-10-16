from typing import Optional, Dict, Any
from django.db.models import QuerySet, Q
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
            return None
        
    @staticmethod
    def get_all_enrollments() -> QuerySet[BatchEnrollment]:
        return BatchEnrollment.objects.select_related(
            'student', 'batch', 'batch__course', 'batch__course__academy', 'final_grade'
        ).all()

    @staticmethod
    def list_enrollments(
        request_user: User,
        filters: Dict[str, Any] = None,
        search: Optional[str] = None
    ) -> QuerySet:
        filters = filters or {}
        qs = BatchEnrollment.objects.select_related(
            'student', 'batch', 'batch__course', 'batch__course__academy', 'final_grade'
        )

        # Role-based filtering
        if request_user.is_admin():
            pass  # Admin sees all
        elif request_user.is_academy():
            academy_id = getattr(request_user.academy.first(), 'id', None)
            if academy_id:
                qs = qs.filter(batch__course__academy_id=academy_id)
            else:
                qs = qs.none()
        elif request_user.is_student():
            qs = qs.filter(student_id=request_user.student.id, is_active=True)
        else:
            qs = qs.none()

        # Filters
        if filters.get('academy_id'):
            qs = qs.filter(batch__course__academy_id=filters['academy_id'])
        if filters.get('course_id'):
            qs = qs.filter(batch__course_id=filters['course_id'])
        if filters.get('course_type'):
            qs = qs.filter(batch__course__course_type=filters['course_type'])
        if filters.get('batch_id'):
            qs = qs.filter(batch_id=filters['batch_id'])
        if filters.get('batch_start_date'):
            qs = qs.filter(batch__start_date__gte=filters['batch_start_date'])
        if filters.get('batch_end_date'):
            qs = qs.filter(batch__end_date__lte=filters['batch_end_date'])
        if filters.get('batch_is_active') is not None:
            qs = qs.filter(batch__is_active=filters['batch_is_active'])
        if filters.get('enrollment_date'):
            qs = qs.filter(enrollment_date=filters['enrollment_date'])
        if filters.get('completion_date'):
            qs = qs.filter(completion_date=filters['completion_date'])
        if filters.get('is_active') is not None:
            qs = qs.filter(is_active=filters['is_active'])
        if filters.get('final_grade'):
            qs = qs.filter(final_grade__grade__icontains=filters['final_grade'])

        # Search
        if search:
            qs = qs.filter(
                Q(student__name__icontains=search) |
                Q(batch__name__icontains=search) |
                Q(batch__course__name__icontains=search) |
                Q(batch__course__course_type__icontains=search) |
                Q(batch__course__academy__name__icontains=search) |
                Q(final_grade__grade__icontains=search) |
                Q(remarks__icontains=search)
            )

        return qs.order_by('-enrollment_date')