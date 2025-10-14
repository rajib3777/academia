from typing import Optional, Dict, Any
from academy.models import BatchEnrollment
from django.db.models import QuerySet

class BatchEnrollmentSelector:
    """
    Selector for BatchEnrollment ORM reads and permission checks.
    """

    @staticmethod
    def get_by_id(enrollment_id: int) -> Optional[BatchEnrollment]:
        try:
            return BatchEnrollment.objects.select_related('student', 'batch', 'final_grade').get(id=enrollment_id)
        except BatchEnrollment.DoesNotExist:
            return None

    @staticmethod
    def list_enrollments(filters: Dict[str, Any] = None) -> QuerySet:
        qs = BatchEnrollment.objects.select_related('student', 'batch', 'final_grade')
        filters = filters or {}
        if filters.get('batch_id'):
            qs = qs.filter(batch_id=filters['batch_id'])
        if filters.get('student_id'):
            qs = qs.filter(student_id=filters['student_id'])
        if filters.get('is_active') is not None:
            qs = qs.filter(is_active=filters['is_active'])
        return qs.order_by('-enrollment_date')