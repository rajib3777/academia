from typing import Dict, Any
from django.db import transaction
from academy.models import BatchEnrollment
from django.core.exceptions import ValidationError

class BatchEnrollmentService:
    """
    Service for BatchEnrollment writes.
    """

    @transaction.atomic
    def create(self, data: Dict[str, Any]) -> BatchEnrollment:
        # Prevent duplicate enrollment
        if BatchEnrollment.objects.filter(student_id=data['student_id'], batch_id=data['batch_id']).exists():
            raise ValidationError('Student already enrolled in this batch.')
        enrollment = BatchEnrollment.objects.create(
            student_id=data['student_id'],
            batch_id=data['batch_id'],
            completion_date=data.get('completion_date'),
            is_active=data.get('is_active', True),
            attendance_percentage=data.get('attendance_percentage'),
            final_grade_id=data.get('final_grade_id'),
            remarks=data.get('remarks', ''),
        )
        return enrollment

    @transaction.atomic
    def update(self, enrollment_id: int, data: Dict[str, Any]) -> BatchEnrollment:
        enrollment = BatchEnrollment.objects.get(id=enrollment_id)
        for field in ['completion_date', 'is_active', 'attendance_percentage', 'final_grade_id', 'remarks']:
            if field in data:
                setattr(enrollment, field, data[field])
        enrollment.save()
        return enrollment

    @transaction.atomic
    def delete(self, enrollment_id: int) -> None:
        enrollment = BatchEnrollment.objects.get(id=enrollment_id)
        enrollment.delete()