
from rest_framework import serializers
from academy.models import Course, Batch, Academy

class BatchInCourseSerializer(serializers.Serializer):
    """
    Serializer for batch data when included in course responses.
    """
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(required=True, max_length=100)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)
    is_active = serializers.BooleanField(default=True)
    
    def to_representation(self, instance):
        """
        Custom representation for batch in course detail.
        """
        # Use the annotated count if available, otherwise fall back to count()
        enrolled_students_count = getattr(instance, 'student_count', None)
        if enrolled_students_count is None:
            enrolled_students_count = instance.students.count()

        return {
            'id': instance.id,
            'name': instance.name,
            'start_date': instance.start_date,
            'end_date': instance.end_date,
            'description': instance.description,
            'is_active': instance.is_active,
            'enrolled_students_count': enrolled_students_count
        }

class CourseSerializer(serializers.Serializer):
    """
    Serializer for course data with validation.
    """
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(required=True, max_length=255)
    description = serializers.CharField(required=True)
    fee = serializers.DecimalField(required=True, max_digits=10, decimal_places=2)
    course_type = serializers.CharField(required=True, max_length=50)
    academy_id = serializers.IntegerField(required=True)
    batches = BatchInCourseSerializer(many=True, required=False)
    
    def validate_academy_id(self, value):
        """Validate that academy exists."""
        try:
            Academy.objects.get(id=value)
        except Academy.DoesNotExist:
            raise serializers.ValidationError(f"Academy with ID {value} does not exist.")
        return value
    
    def validate(self, data):
        """Additional validation logic."""
        # Check if user has permission to create/update courses for this academy
        request = self.context.get('request')
        if request and request.user:
            user = request.user
            if not user.is_admin and not user.is_staff:
                if 'academy_id' in data:
                    # Check if user is associated with this academy
                    if not user.academy.filter(id=data['academy_id']).exists():
                        raise serializers.ValidationError("You don't have permission to create courses for this academy.")
        
        return data

    def to_representation(self, instance):
        """
        Custom representation for optimized course response.
        """
        return {
            'id': instance.id,
            'name': instance.name,
            'description': instance.description,
            'fee': float(instance.fee),
            'course_type': instance.course_type,
            'academy': {
                'id': instance.academy.id,
                'name': instance.academy.name,
            },
            'batches': [
                BatchInCourseSerializer().to_representation(batch)
                for batch in instance.batches.all()
            ],
            'created_at': instance.created_at,
            'modified_at': instance.modified_at,
        }

class CourseCreateSerializer(serializers.Serializer):
    """
    Serializer for course creation with nested batch data.
    """
    name = serializers.CharField(required=True, max_length=255)
    description = serializers.CharField(required=True)
    fee = serializers.DecimalField(required=True, max_digits=10, decimal_places=2)
    academy_id = serializers.IntegerField(required=True)
    course_type = serializers.CharField(required=True)
    batches = serializers.ListField(
        child=BatchInCourseSerializer(),
        required=False
    )
    
    def validate_academy_id(self, value):
        """Validate that academy exists."""
        try:
            Academy.objects.get(id=value)
        except Academy.DoesNotExist:
            raise serializers.ValidationError(f"Academy with ID {value} does not exist.")
        return value
    

class CourseDropdownSerializer(serializers.Serializer):
    """
    Serializer for course dropdown data.
    Only includes the fields needed for the dropdown.
    """
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    
    def to_representation(self, instance):
        """
        Customize representation for dropdown options.
        """
        return {
            'id': instance.id,
            'name': instance.name
        }


class CourseTypeDropdownSerializer(serializers.Serializer):
    """
    Serializer for course type choices.

    This serializer represents course type choices as id-name pairs.
    """
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)

