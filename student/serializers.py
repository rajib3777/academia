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
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'password']

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
        read_only_fields = ['student_id']  # prevent manual input

    def generate_student_id(self, school):
        # Example: SC1234-UUID segment
        return f"{school.id}-{uuid.uuid4().hex[:6].upper()}"

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['username'] = user_data.get('phone', user_data['phone'])
        password = user_data.pop('password')

        # Check username & phone uniqueness
        if User.objects.filter(username=user_data['username']).exists():
            raise serializers.ValidationError({'username': 'Username already exists.'})
        if User.objects.filter(phone=user_data['phone']).exists():
            raise serializers.ValidationError({'phone': 'Phone number already exists.'})

        user = User(**user_data)
        user.set_password(password)
        user.save()

        # Assign 'student' role
        student_role, _ = Role.objects.get_or_create(name='student')
        user.roles.add(student_role)

        student = Student.objects.create(user=user, **validated_data)
        return student

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            for attr, value in user_data.items():
                if attr == 'password':
                    instance.user.set_password(value)
                else:
                    setattr(instance.user, attr, value)
            instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
