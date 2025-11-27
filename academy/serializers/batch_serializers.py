
from rest_framework import serializers
from academy.models import Batch, Course
from datetime import date

class BatchSerializer(serializers.Serializer):
    """
    Serializer for batch data with validation.
    """
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(required=True, max_length=100)
    course_id = serializers.IntegerField(required=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)
    is_active = serializers.BooleanField(default=True)
    
    def validate_course_id(self, value):
        """Validate that course exists."""
        try:
            Course.objects.get(id=value)
        except Course.DoesNotExist:
            raise serializers.ValidationError(f"Course with ID {value} does not exist.")
        return value
    
    def validate(self, data):
        """Validate start and end dates."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("End date cannot be before start date.")
            
        return data
    
    def to_representation(self, instance):
        """
        Custom representation for optimized batch response.
        """
        course = instance.course
        academy = course.academy
                
        return {
            'id': instance.id,
            'name': instance.name,
            'start_date': instance.start_date,
            'end_date': instance.end_date,
            'description': instance.description,
            'is_active': instance.is_active,
            'course': {
                'id': course.id,
                'name': course.name,
                'subject': course.subject,
                'fee': float(course.fee),
            },
            'academy': {
                'id': academy.id,
                'name': academy.name,
            },
            'enrolled_students_count': getattr(instance, 'student_count', instance.students.count()),
            'status': instance.status if hasattr(instance, 'status') else None,
            'duration_days': instance.duration_days if hasattr(instance, 'duration_days') else None,
            'created_at': instance.created_at,
            'modified_at': instance.modified_at,
        }


class BatchDropdownSerializer(serializers.Serializer):
    """
    Serializer for batch dropdown data with minimal fields.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()

    def to_representation(self, instance):
        """
        Customize representation for dropdown options.
        """
        return {
            'id': instance.id,
            'name': instance.name
        }