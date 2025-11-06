from django.db import models
from classmate.models import ClassMateModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from payment.choices import PAYMENT_METHOD_CHOICES, CASH, PAYMENT_STATUS_CHOICES, PAYMENT_STATUS_PAID
from academy.models import BatchEnrollment
from student.models import Student


class StudentPayment(ClassMateModel):
    """
    Represents a payment transaction in the system.
    Supports flexible payer and target using generic relations.
    """
    batch_enrollment = models.ForeignKey(
        BatchEnrollment,
        on_delete=models.CASCADE,
        related_name='student_payments',
        help_text='The batch enrollment this payment is for.'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text='The student making the payment.'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Amount paid in this transaction.'
    )
    date = models.DateTimeField(
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
        default=PAYMENT_STATUS_PAID,
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
        verbose_name = 'Student Payment'
        verbose_name_plural = 'Student Payments'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['batch_enrollment']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_id']),
        ]

    def __str__(self) -> str:
        return (
            f'{self.id} StudentPayment of {self.amount} by {self.student} for {self.batch_enrollment}'
        )