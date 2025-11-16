from rest_framework import serializers
from typing import Dict, Any, List
from academy.models import Academy, Course, Batch, BatchEnrollment
from utils.models import Division, District, Upazila
from account.serializers import UserSerializer


class AcademyCreateUpdateSerializer(serializers.Serializer):
    """Serializer for academy creation and update operations."""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    logo = serializers.ImageField(required=False, allow_null=True)
    website = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    contact_number = serializers.CharField(max_length=15)
    established_year = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    division = serializers.IntegerField(required=False, allow_null=True)
    district = serializers.IntegerField(required=False, allow_null=True)
    upazila = serializers.IntegerField(required=False, allow_null=True)
    area_or_union = serializers.CharField(max_length=100)
    street_address = serializers.CharField(max_length=255)
    postal_code = serializers.CharField(max_length=10)
    user = UserSerializer()

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate academy data for creation/update operations."""
        # Custom validation logic if needed
        # Example: Validate contact number format
        contact_number = data.get('contact_number')
        if contact_number and not contact_number.startswith('+'):
            data['contact_number'] = f'+{contact_number}'
            
        return data


class GradeSerializer(serializers.Serializer):
    """Serializer for grade information."""
    id = serializers.IntegerField(read_only=True)
    grade = serializers.CharField(max_length=2, read_only=True)


class BatchEnrollmentSerializer(serializers.Serializer):
    """Serializer for batch enrollment information."""
    id = serializers.IntegerField(read_only=True)
    student_id = serializers.IntegerField(source='student.id', read_only=True)
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    enrollment_date = serializers.DateField(read_only=True)
    completion_date = serializers.DateField(read_only=True, allow_null=True)
    is_active = serializers.BooleanField(read_only=True)
    attendance_percentage = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True, 
        allow_null=True
    )
    remarks = serializers.CharField(read_only=True, allow_null=True)


class BatchSerializer(serializers.Serializer):
    """Serializer for batch information."""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    start_date = serializers.DateField(read_only=True, allow_null=True)
    end_date = serializers.DateField(read_only=True, allow_null=True)
    description = serializers.CharField(read_only=True, allow_null=True)
    is_active = serializers.BooleanField(read_only=True)
    enrollments = BatchEnrollmentSerializer(source='batchenrollment_set', many=True, read_only=True)
    enrollment_count = serializers.IntegerField(read_only=True)


class CourseSerializer(serializers.Serializer):
    """Serializer for course information."""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    course_type = serializers.CharField(read_only=True)
    batches = BatchSerializer(many=True, read_only=True)
    batch_count = serializers.IntegerField(read_only=True)


class AcademyListSerializer(serializers.Serializer):
    """Serializer for listing academies with all related data."""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True, allow_null=True)
    logo = serializers.ImageField(read_only=True, allow_null=True)
    academy_id = serializers.CharField(read_only=True, allow_null=True)
    website = serializers.URLField(read_only=True, allow_null=True)
    contact_number = serializers.CharField(read_only=True)
    established_year = serializers.CharField(read_only=True, allow_null=True)
    
    # Address fields
    division_id = serializers.IntegerField(source='division.id', read_only=True, allow_null=True)
    division_name = serializers.CharField(source='division.name', read_only=True, allow_null=True)
    district_id = serializers.IntegerField(source='district.id', read_only=True, allow_null=True)
    district_name = serializers.CharField(source='district.name', read_only=True, allow_null=True)
    upazila_id = serializers.IntegerField(source='upazila.id', read_only=True, allow_null=True)
    upazila_name = serializers.CharField(source='upazila.name', read_only=True, allow_null=True)
    area_or_union = serializers.CharField(read_only=True)
    street_address = serializers.CharField(read_only=True)
    postal_code = serializers.CharField(read_only=True)
    
    # Related data
    user = UserSerializer(read_only=True)
    courses = CourseSerializer(many=True, read_only=True)
    course_count = serializers.IntegerField(read_only=True)

    def get_logo(self, obj) -> str:
        request = self.context.get('request')
        if obj.logo and hasattr(obj.logo, 'url'):
            url = obj.logo.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None
    
    def to_representation(self, instance: Academy) -> Dict[str, Any]:
        """
        Custom representation to optimize field access and avoid 
        repeated attribute lookups.
        """
        data = {
            'id': instance.id,
            'name': instance.name,
            'description': instance.description,
            'logo': self.get_logo(instance),
            'academy_id': instance.academy_id,
            'website': instance.website,
            'contact_number': instance.contact_number,
            'established_year': instance.established_year,
            'area_or_union': instance.area_or_union,
            'street_address': instance.street_address,
            'postal_code': instance.postal_code,
            'course_count': getattr(instance, 'course_count', 0),
        }
        
        # Add division data if available
        if instance.division:
            data['division'] = {
                'id': instance.division.id,
                'name': instance.division.name,
            }
        else:
            data['division'] = {
                'id': None,
                'name': None,
            }
            
        # Add district data if available
        if instance.district:
            data['district'] = {
                'id': instance.district.id,
                'name': instance.district.name,
            }
        else:
            data['district'] = {
                'id': None,
                'name': None,
            }

        # Add upazila data if available
        if instance.upazila:
            data['upazila'] = {
                'id': instance.upazila.id,
                'name': instance.upazila.name,
            }
        else:
            data['upazila'] = {
                'id': None,
                'name': None,
            }

        # Add user data
        user = instance.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'phone': getattr(user, 'phone', ''),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
            'is_active': user.is_active,
        }
        
        # Add courses data if available
        courses_data = []
        if hasattr(instance, 'courses'):
            for course in instance.courses.all():
                course_data = {
                    'id': course.id,
                    'name': course.name,
                    'description': course.description,
                    'fee': course.fee,
                    'course_type': course.course_type,
                    'batch_count': getattr(course, 'batch_count', 0),
                    'batches': []
                }
                
                # Add batches data if available
                if hasattr(course, 'batches'):
                    for batch in course.batches.all():
                        batch_data = {
                            'id': batch.id,
                            'name': batch.name,
                            'start_date': batch.start_date,
                            'end_date': batch.end_date,
                            'description': batch.description,
                            'is_active': batch.is_active,
                            'enrollment_count': getattr(batch, 'enrollment_count', 0),
                            'enrollments': []
                        }
                        
                        # Add enrollments data if available
                        if hasattr(batch, 'batchenrollment_set'):
                            for enrollment in batch.batchenrollment_set.all():
                                student = enrollment.student
                                enrollment_data = {
                                    'id': enrollment.id,
                                    'student_id': student.id,
                                    'student_name': f"{student.user.first_name} {student.user.last_name}".strip(),
                                    'enrollment_date': enrollment.enrollment_date,
                                    'completion_date': enrollment.completion_date,
                                    'is_active': enrollment.is_active,
                                    'attendance_percentage': enrollment.attendance_percentage,
                                    'remarks': enrollment.remarks,
                                }
                                    
                                batch_data['enrollments'].append(enrollment_data)
                                
                        course_data['batches'].append(batch_data)
                        
                courses_data.append(course_data)
                
        data['courses'] = courses_data
            
        return data


class AcademyAccountUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating academy user account and academy profile.
    """
    user = serializers.DictField(required=False)
    academy = serializers.DictField(required=False)

    def validate_user(self, value: dict) -> dict:
        # Whitelist allowed user fields
        allowed = {'first_name', 'last_name', 'email', 'phone'}
        return {k: v for k, v in value.items() if k in allowed}

    def validate_academy(self, value: dict) -> dict:
        # Validate FK IDs early
        for fk_field, model_cls in [
            ('division', Division),
            ('district', District),
            ('upazila', Upazila),
        ]:
            if fk_field in value and isinstance(value[fk_field], int):
                if not model_cls.objects.filter(pk=value[fk_field]).exists():
                    raise serializers.ValidationError({fk_field: f'Invalid {fk_field} id: {value[fk_field]}'})
                
        # Whitelist allowed academy fields
        allowed = {
            'name', 'description', 'logo', 'website', 'contact_number', 'email',
            'established_year', 'division', 'district', 'upazila',
            'area_or_union', 'street_address', 'postal_code'
        }
        return {k: v for k, v in value.items() if k in allowed}


class AcademyAccountDetailSerializer(serializers.Serializer):
    """
    Serializer for detailed academy information.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    logo = serializers.ImageField(allow_null=True)
    website = serializers.URLField(allow_blank=True)
    contact_number = serializers.CharField()
    established_year = serializers.CharField()
    academy_id = serializers.CharField()
    division_id = serializers.IntegerField(source='division.id', allow_null=True)
    division_name = serializers.CharField(source='division.name', allow_null=True)
    district_id = serializers.IntegerField(source='district.id', allow_null=True)
    district_name = serializers.CharField(source='district.name', allow_null=True)
    upazila_id = serializers.IntegerField(source='upazila.id', allow_null=True)
    upazila_name = serializers.CharField(source='upazila.name', allow_null=True)
    area_or_union = serializers.CharField()
    street_address = serializers.CharField()
    postal_code = serializers.CharField()
    user = UserSerializer()

    def get_logo(self, obj) -> str:
        request = self.context.get('request')
        if obj.logo and hasattr(obj.logo, 'url'):
            url = obj.logo.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None
    

class YearChoiceSerializer(serializers.Serializer):
    """Serializer for year choice data."""
    
    value = serializers.CharField(help_text="Year value")
    display_name = serializers.CharField(help_text="Year display name")
    
    def to_representation(self, instance):
        """Convert tuple to dict format."""
        if isinstance(instance, tuple) and len(instance) == 2:
            return {
                'id': instance[0],
                'name': instance[1]
            }
        return super().to_representation(instance)