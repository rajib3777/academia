from rest_framework import serializers
from academy.models import Grade
from student.models import Student

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
                'name': str(instance.student),
            },
            'batch': {
                'id': instance.batch.id,
                'name': str(instance.batch),
            },
            'enrollment_date': instance.enrollment_date,
            'completion_date': instance.completion_date,
            'is_active': instance.is_active,
            'attendance_percentage': instance.attendance_percentage,
            'final_grade': str(instance.final_grade) if instance.final_grade else None,
            'remarks': instance.remarks,
        }