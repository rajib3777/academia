import logging
from typing import Optional, Any, Dict
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from payment.models import StudentPayment

logger = logging.getLogger(__name__)

class StudentPaymentService:
    """
    Service for StudentPayment business logic and write operations.
    """
    @staticmethod
    def create_student_payment(data: Dict[str, Any]) -> StudentPayment:
        return StudentPayment.objects.create(
            batch_enrollment_id=data['batch_enrollment_id'],
            student_id=data['student_id'],
            amount=data['amount'],
            method=data['method'],
            status=data['status'],
            transaction_id=data.get('transaction_id', ''),
            reference=data.get('reference', ''),
            remarks=data.get('remarks', ''),
            is_refunded=data.get('is_refunded', False),
            refund_date=data.get('refund_date'),
            metadata=data.get('metadata', {})
        )

    @staticmethod
    def update_student_payment(payment: StudentPayment, data: Dict[str, Any]) -> StudentPayment:
        for field in [
            'amount', 'method', 'status', 'transaction_id', 'reference',
            'remarks', 'is_refunded', 'refund_date', 'metadata'
        ]:
            if field in data:
                setattr(payment, field, data[field])
        payment.save()
        return payment

    @staticmethod
    def delete_student_payment(payment: StudentPayment) -> None:
        payment.delete()