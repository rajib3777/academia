from typing import Any, Dict
from rest_framework import serializers
from academy.models import BatchEnrollment
from student.models import Student
from django.contrib.contenttypes.models import ContentType
from payment.choices import PAYMENT_METHOD_CHOICES, PAYMENT_STATUS_CHOICES

class StudentPaymentSerializer(serializers.Serializer):
    batch_enrollment_id = serializers.IntegerField(required=True)
    student_id = serializers.IntegerField(required=True)
    created_by_id = serializers.IntegerField(required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    date = serializers.DateTimeField(read_only=True)
    method = serializers.ChoiceField(choices=PAYMENT_METHOD_CHOICES)
    status = serializers.ChoiceField(choices=PAYMENT_STATUS_CHOICES)
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    reference = serializers.CharField(required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True)
    is_refunded = serializers.BooleanField(required=False)
    refund_date = serializers.DateTimeField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        batch_enrollment_id = attrs.get('batch_enrollment_id')
        student_id = attrs.get('student_id')

        # Validate BatchEnrollment exists
        try:
            batch_enrollment = BatchEnrollment.objects.select_related('batch', 'student').get(id=batch_enrollment_id)
        except BatchEnrollment.DoesNotExist:
            raise serializers.ValidationError({'batch_enrollment_id': 'Batch enrollment does not exist.'})

        # Validate Student exists
        try:
            student = Student.objects.select_related('user').get(id=student_id)
        except Student.DoesNotExist:
            raise serializers.ValidationError({'student_id': 'Student does not exist.'})

        # Ensure the student matches the batch enrollment
        if batch_enrollment.student_id != student_id:
            raise serializers.ValidationError({'student_id': 'Student does not match the batch enrollment.'})

        attrs['batch_enrollment'] = batch_enrollment
        attrs['student'] = student
        return attrs
    
    def to_representation(self, instance: Any) -> Dict[str, Any]:
        data = super().to_representation(instance)
        
        # Add batch name
        batch_enrollment = getattr(instance, 'batch_enrollment', None)
        if batch_enrollment and hasattr(batch_enrollment, 'batch'):
            data['batch_name'] = batch_enrollment.batch.name
        else:
            data['batch_name'] = None

        # Add student name and student id
        student = getattr(instance, 'student', None)
        if student and hasattr(student, 'user'):
            data['student_name'] = student.user.get_full_name()
            data['student_profile_id'] = student.student_id
        else:
            data['student_name'] = None
            data['student_profile_id'] = None

        # Format amount and dates
        data['amount'] = f'{instance.amount:.2f}'
        if instance.refund_date:
            data['refund_date'] = instance.refund_date.strftime('%Y-%m-%d %H:%M:%S')
        if instance.date:
            data['date'] = instance.date.strftime('%Y-%m-%d %H:%M:%S')

        # Status display
        status_dict = dict(PAYMENT_STATUS_CHOICES)
        data['status_display'] = status_dict.get(instance.status, instance.status)

        # Method display
        method_dict = dict(PAYMENT_METHOD_CHOICES)
        data['method_display'] = method_dict.get(instance.method, instance.method)

        return data
    

class PaymentMethodDropdownSerializer(serializers.Serializer):
    """
    Serializer for payment method choices.

    This serializer represents payment method choices as id-name pairs.
    """
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


class PaymentStatusDropdownSerializer(serializers.Serializer):
    """
    Serializer for payment status choices.

    This serializer represents payment status choices as id-name pairs.
    """
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)