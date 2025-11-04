from typing import Dict, Any, Optional, List
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from academy.models import BatchEnrollment
from academy.selectors.batch_enrollment_selector import BatchEnrollmentSelector
from payment.services.student_payment_service import StudentPaymentService
from payment.selectors.student_payment_selector import StudentPaymentSelector
from account.models import User

class BatchEnrollmentService:
    """
    Service for BatchEnrollment writes.
    """

    def __init__(self):
        self.payment_service = StudentPaymentService()
        self.payment_selector = StudentPaymentSelector()

    @staticmethod
    def _validate_permission(request_user: User) -> None:
        if not (request_user.is_admin() or request_user.is_academy()):
            raise ValidationError('You do not have permission to perform this action.')

    @transaction.atomic
    def create_enrollment(self, request_user: User, enrollment_data: Dict[str, Any], payments_data: Optional[List[Dict[str, Any]]] = None) -> BatchEnrollment:
        try:
            self._validate_permission(request_user)

            if BatchEnrollment.objects.filter(
                student_id=enrollment_data['student_id'],
                batch_id=enrollment_data['batch_id']
            ).exists():
                raise ValidationError('Student already enrolled in this batch.')
            
            enrollment = BatchEnrollment.objects.create(
                batch_id=enrollment_data['batch_id'],
                student_id=enrollment_data['student_id'],
                is_active=enrollment_data.get('is_active', True),
                remarks=enrollment_data.get('remarks', '')
            )

            # Create payments if provided
            if payments_data:
                # payment_service = StudentPaymentService()
                for payment_info in payments_data:
                    self.payment_service.create_student_payment({
                        **payment_info,
                        'batch_enrollment_id': enrollment.id
                    })

            return enrollment
        except ValidationError as e:
            raise ValidationError(f"Invalid data: {str(e)}")
        except Exception as e:
            raise e

    @transaction.atomic
    def update_enrollment(self, request_user: User, enrollment: BatchEnrollment, enrollment_data: Dict[str, Any], payments_data: Optional[List[Dict[str, Any]]] = None) -> BatchEnrollment:
        try:
            self._validate_permission(request_user)

            for field in ['batch_id', 'student_id', 'is_active', 'remarks']:
                if field in enrollment_data:
                    setattr(enrollment, field, enrollment_data[field])
            enrollment.save()

            # Update payments if provided
            if payments_data:
                for payment_data in payments_data:
                    payment_id = payment_data.pop('id', None)
                    if payment_id:
                        # Update existing payment
                        payment = self.payment_selector.get_by_id(payment_id)
                        self.payment_service.update_student_payment(payment, payment_data)
                    else:
                        # Create new payment
                        try:
                            self.payment_service.create_student_payment({
                                **payment_data,
                                'batch_enrollment_id': enrollment.id
                            })
                        except IntegrityError as e:
                            raise ValidationError(f"Error creating payment: {str(e)}")
        except ValidationError as e:
            raise ValidationError(f"Invalid data: {str(e)}")
        except Exception as e:
            raise e

        return enrollment

    @transaction.atomic
    def delete_enrollment(self, request_user: User, enrollment_id: int) -> None:
        self._validate_permission(request_user)
        enrollment = BatchEnrollmentSelector.get_by_id(enrollment_id)
        if not enrollment:
            raise ValidationError('BatchEnrollment not found.')
        enrollment.delete()