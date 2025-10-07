from typing import Dict, Any, Optional, List
from django.db import transaction
from django.core.exceptions import ValidationError
from functools import cached_property

from account.models import User, Role
from student.models import Student, School
from student.selectors.student_selector import StudentSelector


class StudentService:
    """
    Service class for Student model to handle all write operations and business logic.
    """
    
    def __init__(self):
        """Initialize the StudentService."""
        pass
    
    @cached_property
    def student_selector(self) -> StudentSelector:
        """
        Lazy initialization of StudentSelector.
        
        Returns:
            StudentSelector instance
        """
        return StudentSelector()
    
    @transaction.atomic
    def create_student(self, 
                      user_data: Dict[str, Any], 
                      student_data: Dict[str, Any]) -> Student:
        """
        Create a new student with associated user account.
        
        Args:
            user_data: Dictionary containing user information
                username: str
                email: str
                first_name: str
                last_name: str
                phone: str
                password: str
            student_data: Dictionary containing student information
                school_id: int
                birth_registration_number: str (optional)
                date_of_birth: date (optional)
                guardian_name: str (optional)
                guardian_phone: str (optional)
                guardian_email: str (optional)
                guardian_relationship: str (optional)
                address: str (optional)
                
        Returns:
            Newly created Student instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate school exists
        school_id = student_data.get('school_id')
        try:
            school = School.objects.get(id=school_id)
        except School.DoesNotExist:
            raise ValidationError(f"School with ID {school_id} does not exist.")
        
        # Get or create student role
        student_role, _ = Role.objects.get_or_create(name='student')
        
        # Create user
        user_fields = {
            'username': user_data.get('username'),
            'email': user_data.get('email'),
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'phone': user_data.get('phone'),
            'role': student_role,
        }
        
        # Check if user with username or email already exists
        if User.objects.filter(username=user_fields['username']).exists():
            raise ValidationError(f"User with username '{user_fields['username']}' already exists.")
        
        if User.objects.filter(email=user_fields['email']).exists():
            raise ValidationError(f"User with email '{user_fields['email']}' already exists.")
            
        # Create user with password
        user = User.objects.create_user(
            **user_fields,
            password=user_data.get('password')
        )
        
        # Create student
        student_fields = {
            'user': user,
            'school': school,
            'birth_registration_number': student_data.get('birth_registration_number'),
            'date_of_birth': student_data.get('date_of_birth'),
            'guardian_name': student_data.get('guardian_name'),
            'guardian_phone': student_data.get('guardian_phone'),
            'guardian_email': student_data.get('guardian_email'),
            'guardian_relationship': student_data.get('guardian_relationship'),
            'address': student_data.get('address'),
        }
        
        # Check if birth registration number already exists
        if student_fields['birth_registration_number'] and Student.objects.filter(
            birth_registration_number=student_fields['birth_registration_number']
        ).exists():
            raise ValidationError(
                f"Student with birth registration number '{student_fields['birth_registration_number']}' already exists."
            )
        
        # Create student
        student = Student.objects.create(**student_fields)
        
        return student
    
    @transaction.atomic
    def update_student(self, 
                      student_id: int, 
                      user_data: Optional[Dict[str, Any]] = None, 
                      student_data: Optional[Dict[str, Any]] = None) -> Student:
        """
        Update an existing student and its associated user.
        
        Args:
            student_id: ID of the student to update
            user_data: Dictionary containing user information to update (optional)
            student_data: Dictionary containing student information to update (optional)
                
        Returns:
            Updated Student instance
            
        Raises:
            ValidationError: If validation fails or student not found
        """
        # Get student
        student = self.student_selector.get_student_by_id(student_id)
        if not student:
            raise ValidationError(f"Student with ID {student_id} not found.")
        
        if user_data:
            user = student.user
            
            # Check username uniqueness
            if 'username' in user_data and user_data['username'] != user.username:
                if User.objects.filter(username=user_data['username']).exists():
                    raise ValidationError(f"User with username '{user_data['username']}' already exists.")
                user.username = user_data['username']
            
            # Check email uniqueness
            if 'email' in user_data and user_data['email'] != user.email:
                if User.objects.filter(email=user_data['email']).exists():
                    raise ValidationError(f"User with email '{user_data['email']}' already exists.")
                user.email = user_data['email']
            
            # Update other user fields
            if 'first_name' in user_data:
                user.first_name = user_data['first_name']
            if 'last_name' in user_data:
                user.last_name = user_data['last_name']
            if 'phone' in user_data:
                user.phone = user_data['phone']
            if 'password' in user_data:
                user.set_password(user_data['password'])
            
            user.save()
        
        if student_data:
            # Update school if provided
            if 'school_id' in student_data:
                try:
                    school = School.objects.get(id=student_data['school_id'])
                    student.school = school
                except School.DoesNotExist:
                    raise ValidationError(f"School with ID {student_data['school_id']} does not exist.")
            
            # Check birth registration number uniqueness
            if 'birth_registration_number' in student_data and student_data['birth_registration_number'] != student.birth_registration_number:
                if student_data['birth_registration_number'] and Student.objects.filter(
                    birth_registration_number=student_data['birth_registration_number']
                ).exclude(id=student.id).exists():
                    raise ValidationError(
                        f"Student with birth registration number '{student_data['birth_registration_number']}' already exists."
                    )
                student.birth_registration_number = student_data['birth_registration_number']
            
            # Update other student fields
            if 'date_of_birth' in student_data:
                student.date_of_birth = student_data['date_of_birth']
            if 'guardian_name' in student_data:
                student.guardian_name = student_data['guardian_name']
            if 'guardian_phone' in student_data:
                student.guardian_phone = student_data['guardian_phone']
            if 'guardian_email' in student_data:
                student.guardian_email = student_data['guardian_email']
            if 'guardian_relationship' in student_data:
                student.guardian_relationship = student_data['guardian_relationship']
            if 'address' in student_data:
                student.address = student_data['address']
            
            student.save()
        
        return student

    def update_student_account(self, student: Student, data: dict) -> None:
        # Resolve FK fields to instances
        fk_fields = {
            'school': School,
        }
        for field, model_cls in fk_fields.items():
            if field in data and isinstance(data[field], int):
                instance = model_cls.objects.filter(pk=data[field]).first()
                if not instance:
                    raise ValueError(f'Invalid {field} id: {data[field]}')
                data[field] = instance

        # Assign all other fields
        for field, value in data.items():
            setattr(student, field, value)
        student.full_clean()
        student.save()

    def deactivate_student(self, student_id: int) -> Student:
        """
        Deactivate a student by setting the associated user to inactive.
        
        Args:
            student_id: ID of the student to deactivate
                
        Returns:
            Deactivated Student instance
            
        Raises:
            ValidationError: If student not found
        """
        student = self.student_selector.get_student_by_id(student_id)
        if not student:
            raise ValidationError(f"Student with ID {student_id} not found.")
        
        student.user.is_active = False
        student.user.save()
        
        return student
    
    def activate_student(self, student_id: int) -> Student:
        """
        Activate a student by setting the associated user to active.
        
        Args:
            student_id: ID of the student to activate
                
        Returns:
            Activated Student instance
            
        Raises:
            ValidationError: If student not found
        """
        # Using direct query since selector might filter out inactive users
        try:
            student = Student.objects.select_related('user', 'school').get(id=student_id)
        except Student.DoesNotExist:
            raise ValidationError(f"Student with ID {student_id} not found.")
        
        student.user.is_active = True
        student.user.save()
        
        return student
    
    def bulk_create_students(self, students_data: List[Dict[str, Any]]) -> List[Student]:
        """
        Create multiple students at once.
        
        Args:
            students_data: List of dictionaries, each containing:
                user_data: Dictionary with user information
                student_data: Dictionary with student information
                
        Returns:
            List of created Student instances
            
        Raises:
            ValidationError: If validation fails for any student
        """
        created_students = []
        
        with transaction.atomic():
            for data in students_data:
                user_data = data.get('user_data', {})
                student_data = data.get('student_data', {})
                
                student = self.create_student(
                    user_data=user_data,
                    student_data=student_data
                )
                created_students.append(student)
        
        return created_students