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

        try:
            # Validate required fields
            required_fields = ['batch_enrollment_id', 'student_id', 'amount', 'method', 'status']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f'Missing required field: {field}')
                
            if data['amount'] <= 0:
                raise ValidationError('Amount must be greater than zero.')
                
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
            
            # Additional validation can be added here (e.g., amount > 0, valid method/status, etc.)
        except ValidationError as e:
            logger.exception(f"Error in create_student_payment: {str(e)}")
            raise ValidationError(f"Invalid data: {str(e)}")
        except Exception as e:
            logger.exception(f"Unexpected error in create_student_payment: {str(e)}")
            raise e



    @staticmethod
    def update_student_payment(payment: StudentPayment, payment_data: Dict[str, Any]) -> StudentPayment:
        try:
            for field in [
                'amount', 'method', 'status', 'transaction_id', 'reference',
                'remarks', 'is_refunded', 'refund_date', 'metadata'
            ]:
                if field in payment_data:
                    setattr(payment, field, payment_data[field])
            payment.save()
            return payment
        except ValidationError as e:
            logger.exception(f"Error in update_student_payment: {str(e)}")
            raise ValidationError(f"Invalid data: {str(e)}")
        except Exception as e:
            logger.exception(f"Unexpected error in update_student_payment: {str(e)}")
            raise e

    @staticmethod
    def delete_student_payment(payment: StudentPayment) -> None:
        payment.delete()