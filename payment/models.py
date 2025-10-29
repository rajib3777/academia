from django.db import models
from classmate.models import ClassMateModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from payment.choices import PAYMENT_METHOD_CHOICES, CASH, PAYMENT_STATUS_CHOICES, PAYMENT_STATUS_PENDING

class Payment(ClassMateModel):
    """
    Represents a payment transaction in the system.
    Supports flexible payer and target using generic relations.
    """
    payer_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='payment_payer_type',
        help_text='Content type of the payer (Student, Academy, Admin, etc.).',
        db_index=True
    )
    payer_object_id = models.PositiveIntegerField(
        help_text='ID of the payer object.',
        db_index=True
    )
    payer = GenericForeignKey('payer_content_type', 'payer_object_id')
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='payment_target_type',
        help_text='Content type of the payment target (Enrollment, Service, etc.).',
        db_index=True
    )
    target_object_id = models.PositiveIntegerField(
        help_text='ID of the payment target object.',
        db_index=True
    )
    target = GenericForeignKey('target_content_type', 'target_object_id')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Amount paid in this transaction.'
    )
    date = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when the payment was made.'
    )
    method = models.CharField(
        max_length=20,
        default=CASH,
        choices=PAYMENT_METHOD_CHOICES,
        help_text='Method used for payment.'
    )
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_STATUS_PENDING,
        help_text='Current status of the payment.',
        db_index=True
    )
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='External transaction/reference ID, if applicable.',
        db_index=True
    )
    remarks = models.TextField(
        blank=True,
        help_text='Optional remarks or notes about the payment.'
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text='Reference ID from external payment system.'
    )
    is_refunded = models.BooleanField(
        default=False,
        help_text='Indicates if the payment has been refunded.'
    )
    refund_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date when the payment was refunded.'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional metadata for the payment.'
    )

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['payer_content_type', 'payer_object_id']),
            models.Index(fields=['target_content_type', 'target_object_id']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_id']),
        ]

    def __str__(self) -> str:
        return (
            f'Payment of {self.amount} by {self.payer} for {self.target}'
        )