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
            batch_id=data['batch_id'],
            student_id=data['student_id'],
            is_active=data.get('is_active', True),
            remarks=data.get('remarks', '')
        )
        return enrollment

    @transaction.atomic
    def update(self, request_user: User, enrollment_id: int, data: Dict[str, Any]) -> BatchEnrollment:
        self._validate_permission(request_user)
        enrollment = BatchEnrollmentSelector.get_by_id(enrollment_id)
        if not enrollment:
            raise ValidationError('BatchEnrollment not found.')
        for field in ['batch_id', 'student_id', 'is_active', 'remarks']:
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