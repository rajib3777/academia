from rest_framework import serializers
from academy.models import Grade
from student.models import Student
from payment.serializers.student_payment_serializer import StudentPaymentSerializer


class BatchEnrollmentSerializer(serializers.Serializer):
    """
    Serializer for BatchEnrollment data.
    """
    id = serializers.IntegerField(read_only=True)
    student_id = serializers.IntegerField()
    batch_id = serializers.IntegerField()
    enrollment_date = serializers.DateField(read_only=True)
    completion_date = serializers.DateField(required=False, allow_null=True)
    is_active = serializers.BooleanField(default=True)
    attendance_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True
    )
    final_grade_id = serializers.IntegerField(required=False, allow_null=True)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    payments = serializers.ListField(
            child=StudentPaymentSerializer(),
            required=False
        )
    def validate_student_id(self, value: int) -> int:
        if not Student.objects.filter(id=value).exists():
            raise serializers.ValidationError('Student does not exist.')
        return value

    def validate_final_grade_id(self, value: int) -> int:
        if value and not Grade.objects.filter(id=value).exists():
            raise serializers.ValidationError('Grade does not exist.')
        return value

    def validate(self, data: dict) -> dict:
        # Add custom cross-field validation if needed
        return data

    def to_representation(self, instance) -> dict:
        return {
            'id': instance.id,
            'student': {
                'id': instance.student.id,
                'student_id': instance.student.student_id,
                'name': f"{instance.student.user.first_name} {instance.student.user.last_name} - {instance.student.student_id}",
            },
            'academy': {
                'id': instance.batch.course.academy.id,
                'academy_id': instance.batch.course.academy.academy_id,
                'name': str(instance.batch.course.academy),
            },
            'course': {
                'id': instance.batch.course.id,
                'course_id': instance.batch.course.course_id,
                'name': str(instance.batch.course.name),
                'course_fee': instance.batch.course.fee,
            },
            'batch': {
                'id': instance.batch.id,
                'batch_id': instance.batch.batch_id,
                'name': str(instance.batch.name),
            },
            'fee': {
                'actual_fee': instance.batch.course.fee,
                'discounted_fee': instance.discounted_fee,
                'effective_fee': instance.effective_fee,
                'discount_amount': instance.discount_amount,
                'total_paid': getattr(instance, 'total_paid', 0) or 0,
                'outstanding_fee': (instance.effective_fee - (getattr(instance, 'total_paid', 0) or 0)),
            },
            'enrollment_date': instance.enrollment_date,
            'is_active': instance.is_active,
            'remarks': instance.remarks,
            'payments': [
                StudentPaymentSerializer(payment).data for payment in instance.student_payments.all()
            ],
        }