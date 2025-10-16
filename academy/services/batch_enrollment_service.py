from typing import Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError
from academy.models import BatchEnrollment
from academy.selectors.batch_enrollment_selector import BatchEnrollmentSelector
from account.models import User

class BatchEnrollmentService:
    """
    Service for BatchEnrollment writes.
    """

    @staticmethod
    def _validate_permission(request_user: User) -> None:
        if not (request_user.is_admin() or request_user.is_academy()):
            raise ValidationError('You do not have permission to perform this action.')

    @transaction.atomic
    def create(self, request_user: User, data: Dict[str, Any]) -> BatchEnrollment:
        self._validate_permission(request_user)
        if BatchEnrollment.objects.filter(
            student_id=data['student_id'],
            batch_id=data['batch_id']
        ).exists():
            raise ValidationError('Student already enrolled in this batch.')
        enrollment = BatchEnrollment.objects.create(
            student_id=data['student_id'],
            batch_id=data['batch_id'],
            completion_date=data.get('completion_date'),
            is_active=data.get('is_active', True),
            attendance_percentage=data.get('attendance_percentage'),
            final_grade_id=data.get('final_grade_id'),
            remarks=data.get('remarks', '')
        )
        return enrollment

    @transaction.atomic
    def update(self, request_user: User, enrollment_id: int, data: Dict[str, Any]) -> BatchEnrollment:
        self._validate_permission(request_user)
        enrollment = BatchEnrollmentSelector.get_by_id(enrollment_id)
        if not enrollment:
            raise ValidationError('BatchEnrollment not found.')
        for field in ['completion_date', 'is_active', 'attendance_percentage', 'final_grade_id', 'remarks']:
            if field in data:
                setattr(enrollment, field, data[field])
        enrollment.save()
        return enrollment

    @transaction.atomic
    def delete(self, request_user: User, enrollment_id: int) -> None:
        self._validate_permission(request_user)
        enrollment = BatchEnrollmentSelector.get_by_id(enrollment_id)
        if not enrollment:
            raise ValidationError('BatchEnrollment not found.')
        enrollment.delete()