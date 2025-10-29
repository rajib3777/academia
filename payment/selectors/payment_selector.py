from typing import Any
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from payment.models import Payment

class PaymentSelector:
    """
    Selector for Payment ORM read operations.
    """

    @staticmethod
    def payments_for_payer(payer_obj: Any) -> QuerySet:
        """
        Get all payments for a given payer object.
        """
        payer_ct = ContentType.objects.get_for_model(type(payer_obj))
        return Payment.objects.filter(
            payer_content_type=payer_ct,
            payer_object_id=payer_obj.id
        )

    @staticmethod
    def payments_for_target(target_obj: Any) -> QuerySet:
        """
        Get all payments for a given target object.
        """
        target_ct = ContentType.objects.get_for_model(type(target_obj))
        return Payment.objects.filter(
            target_content_type=target_ct,
            target_object_id=target_obj.id
        )

    @staticmethod
    def all_payments() -> QuerySet:
        """
        Get all payments.
        """
        return Payment.objects.all()