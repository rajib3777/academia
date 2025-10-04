from rest_framework import serializers
from typing import Dict, Any, List

from academy.models import Academy, Course, Batch, BatchEnrollment, Grade
from account.models import User


class UserSerializer(serializers.Serializer):
    """Serializer for user data in academy operations."""
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False)
    phone = serializers.CharField(max_length=15, required=False)


class AcademyCreateUpdateSerializer(serializers.Serializer):
    """Serializer for academy creation and update operations."""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    logo = serializers.ImageField(required=False, allow_null=True)
    website = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    contact_number = serializers.CharField(max_length=15)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
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
    final_grade = GradeSerializer(read_only=True, allow_null=True)
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
    website = serializers.URLField(read_only=True, allow_null=True)
    contact_number = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True, allow_null=True)
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
    
    def to_representation(self, instance: Academy) -> Dict[str, Any]:
        """
        Custom representation to optimize field access and avoid 
        repeated attribute lookups.
        """
        data = {
            'id': instance.id,
            'name': instance.name,
            'description': instance.description,
            'logo': instance.logo.url if instance.logo else None,
            'website': instance.website,
            'contact_number': instance.contact_number,
            'email': instance.email,
            'established_year': instance.established_year,
            'area_or_union': instance.area_or_union,
            'street_address': instance.street_address,
            'postal_code': instance.postal_code,
            'course_count': getattr(instance, 'course_count', 0),
        }
        
        # Add division data if available
        if instance.division:
            data.update({
                'division_id': instance.division.id,
                'division_name': instance.division.name,
            })
        else:
            data.update({
                'division_id': None,
                'division_name': None,
            })
            
        # Add district data if available
        if instance.district:
            data.update({
                'district_id': instance.district.id,
                'district_name': instance.district.name,
            })
        else:
            data.update({
                'district_id': None,
                'district_name': None,
            })
            
        # Add upazila data if available
        if instance.upazila:
            data.update({
                'upazila_id': instance.upazila.id,
                'upazila_name': instance.upazila.name,
            })
        else:
            data.update({
                'upazila_id': None,
                'upazila_name': None,
            })
            
        # Add user data
        user = instance.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': getattr(user, 'phone', ''),
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
                                
                                # Add grade data if available
                                if enrollment.final_grade:
                                    enrollment_data['final_grade'] = {
                                        'id': enrollment.final_grade.id,
                                        'grade': enrollment.final_grade.grade
                                    }
                                else:
                                    enrollment_data['final_grade'] = None
                                    
                                batch_data['enrollments'].append(enrollment_data)
                                
                        course_data['batches'].append(batch_data)
                        
                courses_data.append(course_data)
                
        data['courses'] = courses_data
            
        return data