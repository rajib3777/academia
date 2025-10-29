from typing import Optional, Any
from django.contrib.contenttypes.models import ContentType
from payment.models import Payment

class PaymentService:
    """
    Service for Payment business logic and write operations.
    """

    @staticmethod
    def create_payment(
        payer_obj,
        target_obj,
        amount: float,
        method: str,
        status: str,
        transaction_id: str = '',
        reference: str = '',
        remarks: str = ''
    ) -> Payment:
        """
        Create a new Payment record.
        """
        payer_ct = ContentType.objects.get_for_model(type(payer_obj))
        target_ct = ContentType.objects.get_for_model(type(target_obj))
        return Payment.objects.create(
            payer_content_type=payer_ct,
            payer_object_id=payer_obj.id,
            target_content_type=target_ct,
            target_object_id=target_obj.id,
            amount=amount,
            method=method,
            status=status,
            transaction_id=transaction_id,
            reference=reference,
            remarks=remarks
        )

    @staticmethod
    def update_payment(
        payment: Payment,
        amount: Optional[float] = None,
        method: Optional[str] = None,
        status: Optional[str] = None,
        transaction_id: Optional[str] = None,
        reference: Optional[str] = None,
        remarks: Optional[str] = None,
        is_refunded: Optional[bool] = None,
        refund_date: Optional[Any] = None
    ) -> Payment:
        """
        Update fields of an existing Payment record.
        Only provided fields will be updated.
        """
        if amount is not None:
            payment.amount = amount
        if method is not None:
            payment.method = method
        if status is not None:
            payment.status = status
        if transaction_id is not None:
            payment.transaction_id = transaction_id
        if reference is not None:
            payment.reference = reference
        if remarks is not None:
            payment.remarks = remarks
        if is_refunded is not None:
            payment.is_refunded = is_refunded
        if refund_date is not None:
            payment.refund_date = refund_date

        payment.save()
        return payment

    @staticmethod
    def delete_payment(payment: Payment) -> None:
        """
        Delete a Payment record.
        """
        payment.delete()