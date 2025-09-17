from rest_framework import serializers
from student.models import School, Student
from account.models import User, Role
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
import uuid


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = '__all__'

    def validate_name(self, value):
        # For create
        if self.instance is None and School.objects.filter(name=value).exists():
            raise serializers.ValidationError("A school with this name already exists.")
        
        # For update
        if self.instance and School.objects.filter(name=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Another school with this name already exists.")
        
        return value
    

class SchoolNameListSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'phone', 'password']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value


class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Student
        fields = [
            'id', 'user', 'birth_registration_number', 'school', 'student_id', 'date_of_birth',
            'guardian_name', 'guardian_phone', 'guardian_email',
            'guardian_relationship', 'address'
        ]
        read_only_fields = ['student_id']


class StudentDetailSerializer(serializers.Serializer):
    # Student fields
    id = serializers.IntegerField(read_only=True)
    student_id = serializers.CharField(read_only=True)
    birth_registration_number = serializers.CharField(allow_null=True)
    date_of_birth = serializers.DateField(allow_null=True)
    guardian_name = serializers.CharField(allow_null=True)
    guardian_phone = serializers.CharField(allow_null=True)
    guardian_email = serializers.EmailField(allow_null=True)
    guardian_relationship = serializers.CharField(allow_null=True)
    address = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)
    
    # School fields
    school_id = serializers.IntegerField()
    school_name = serializers.CharField()
    
    # User fields
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    is_active = serializers.BooleanField()
    
    # Computed fields
    age = serializers.IntegerField()
    full_name = serializers.CharField()
    
    def to_representation(self, instance):
        """
        Custom representation to optimize field access and avoid 
        repeated attribute lookups.
        """
        # Using already prefetched data
        user = instance.user
        school = instance.school
        
        # Calculate age
        age = None
        if instance.date_of_birth:
            from datetime import date, datetime
            today = date.today()
            
            # Handle case where date_of_birth might be a string
            birth_date = instance.date_of_birth
            if isinstance(birth_date, str):
                try:
                    # Parse the string to a date object
                    birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                except ValueError:
                    # If parsing fails, leave age as None
                    birth_date = None
                    
            if birth_date:
                age = today.year - birth_date.year - (
                    (today.month, today.day) < 
                    (birth_date.month, birth_date.day)
                )
            
        return {
            # Student fields
            'id': instance.id,
            'student_id': instance.student_id,
            'birth_registration_number': instance.birth_registration_number,
            'date_of_birth': instance.date_of_birth,
            'guardian_name': instance.guardian_name,
            'guardian_phone': instance.guardian_phone,
            'guardian_email': instance.guardian_email,
            'guardian_relationship': instance.guardian_relationship,
            'address': instance.address,
            'created_at': instance.created_at,
            'modified_at': instance.modified_at,
            
            # School fields
            'school_id': school.id,
            'school_name': school.name,
            
            # User fields
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': user.phone,
            'is_active': user.is_active,
            
            # Computed fields
            'age': age,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
        }


class StudentCreateSerializer(serializers.ModelSerializer):
    # Nested user fields for creation
    username = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    phone = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8, default='adminmilon')
    
    class Meta:
        model = Student
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone', 'password',
            'school', 'birth_registration_number', 'date_of_birth',
            'guardian_name', 'guardian_phone', 'guardian_email',
            'guardian_relationship', 'address'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'birth_registration_number': {'required': False},
        }

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_birth_registration_number(self, value):
        if value and Student.objects.filter(birth_registration_number=value).exists():
            raise serializers.ValidationError("A student with this birth registration number already exists.")
        return value

    def create(self, validated_data):

        # Add student role (assuming you have a Role model)
        try:
            from account.models import Role
            student_role, created = Role.objects.get_or_create(name='student')
        except ImportError:
            # If Role model doesn't exist, you might handle this differently
            pass
        # Extract user data
        user_data = {
            'username': validated_data.pop('username'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'email': validated_data.pop('email'),
            'phone': validated_data.pop('phone'),
            'role': student_role,
            'password': validated_data.pop('password'),
        }
        
        # Create user
        user = User.objects.create_user(**user_data)
        
        # Create student
        student = Student.objects.create(
            user=user,
            **validated_data
        )
        
        return student


class StudentUpdateSerializer(serializers.ModelSerializer):
    # User fields for updating
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=True)
    password = serializers.CharField(required=False, min_length=8)
    
    class Meta:
        model = Student
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone', 'password',
            'school', 'birth_registration_number', 'date_of_birth',
            'guardian_name', 'guardian_phone', 'guardian_email',
            'guardian_relationship', 'address'
        ]
        extra_kwargs = {
            'school': {'required': False},
            'birth_registration_number': {'required': False},
            'date_of_birth': {'required': False},
            'guardian_name': {'required': False},
            'guardian_phone': {'required': False},
            'guardian_email': {'required': False},
            'guardian_relationship': {'required': False},
            'address': {'required': False},
        }

    def validate_username(self, value):
        # Get current instance
        instance = self.instance
        
        # Check if username is being changed
        if instance and instance.user.username == value:
            return value  # Same username, no validation needed
        
        # Check if another user has this username
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        
        return value

    def validate_email(self, value):
        # Get current instance
        instance = self.instance
        
        # Check if email is being changed
        if instance and instance.user.email == value:
            return value  # Same email, no validation needed
        
        # Check if another user has this email
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        return value

    def validate_birth_registration_number(self, value):
        # Get current instance
        instance = self.instance
        
        # Skip validation if no value provided
        if not value:
            return value
        
        # Check if birth registration number is being changed
        if instance and instance.birth_registration_number == value:
            return value  # Same number, no validation needed
        
        # Check if another student has this birth registration number
        if Student.objects.filter(birth_registration_number=value).exists():
            raise serializers.ValidationError("A student with this birth registration number already exists.")
        
        return value

    def update(self, instance, validated_data):
        # Extract user-related fields
        user_fields = ['username', 'email', 'first_name', 'phone', 'last_name', 'password']
        user_data = {}
        
        for field in user_fields:
            if field in validated_data:
                user_data[field] = validated_data.pop(field)
        
        # Update user if there's user data to update
        if user_data:
            user = instance.user
            
            # Update user fields
            for field, value in user_data.items():
                if field == 'password':
                    user.set_password(value)
                else:
                    setattr(user, field, value)
            
            user.save()
        
        # Update student fields
        for field, value in validated_data.items():
            setattr(instance, field, value)
        
        instance.save()
        return instance
    

class StudentListSerializer(serializers.ModelSerializer):
    """Serializer for listing students with related data"""
    user = serializers.SerializerMethodField()
    school = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'user', 'school', 'student_id', 'birth_registration_number',
            'date_of_birth', 'age', 'guardian_name', 'guardian_phone',
            'guardian_email', 'guardian_relationship', 'address',
            'created_at', 'modified_at'
        ]
    
    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'phone': obj.user.phone,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'full_name': f"{obj.user.first_name} {obj.user.last_name}".strip(),
            'is_active': obj.user.is_active,
        }
    
    def get_school(self, obj):
        return {
            'id': obj.school.id,
            'name': obj.school.name if hasattr(obj.school, 'name') else str(obj.school),
        }
    
    def get_age(self, obj):
        if obj.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - obj.date_of_birth.year - ((today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day))
        return None


class StudentDropdownSerializer(serializers.Serializer):
    """
    Serializer for student dropdown data.
    Only includes the fields needed for the dropdown.
    """
    student_id = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    
    def to_representation(self, instance):
        """
        Customize representation for dropdown options.
        """
        # If we're using the annotated queryset from the selector
        if hasattr(instance, 'full_name'):
            return {
                'student_id': instance.student_id,
                'full_name': instance.full_name
            }
        
        # Fallback if the queryset doesn't have the annotation
        user = instance.user
        return {
            'student_id': instance.student_id,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username
        }