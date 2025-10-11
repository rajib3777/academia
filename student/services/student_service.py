from typing import Dict, Any, Optional, List
from django.db import transaction
from django.core.exceptions import ValidationError
from functools import cached_property
from account.choices import STUDENT
from account.services.user_service import UserService
from utils.services.sms_service import SMSService
from account.models import User
from student.models import Student, School
from student.selectors.student_selector import StudentSelector
from utils.choices import ACCOUNT, QUEUE

class StudentService:
    """
    Service class for Student model to handle all write operations and business logic.
    """
    
    def __init__(self):
        """Initialize the StudentService."""
        self.user_service = UserService()
        self.sms_service = SMSService()
    
    @cached_property
    def student_selector(self) -> StudentSelector:
        """
        Lazy initialization of StudentSelector.
        
        Returns:
            StudentSelector instance
        """
        return StudentSelector()
    
    @transaction.atomic
    def create_student(self, data: Dict[str, Any]) -> Student:
        """
        Create a new student with associated user account.
        
        Args:
            data: Dictionary containing user and student information
                user: dict
                    username: str
                    email: str
                    first_name: str
                    last_name: str
                    phone: str
                student: dict
                    school_id: int
                    birth_registration_number: str (optional)
                    date_of_birth: date (optional)
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
        
        # Create user
        user_data = {
            'username': data.get('phone'),
            'email': data.pop('email'),
            'first_name': data.pop('first_name'),
            'last_name': data.pop('last_name'),
            'phone': data.pop('phone'),
            'password': data.pop('password', None),
        }

        # Create user
        user, password = self.user_service.create_user(user_data, STUDENT)
        
        # Check if birth registration number already exists
        if data['birth_registration_number'] and Student.objects.filter(
            birth_registration_number=data['birth_registration_number']
        ).exists():
            raise ValidationError(
                f"Student with birth registration number '{data['birth_registration_number']}' already exists."
            )
        
        # Validate school exists
        school_id = data.pop('school_id', None)
        if school_id:
            try:
                school = School.objects.get(id=school_id)
                data['school'] = school
            except School.DoesNotExist:
                raise ValidationError(f"School with ID {school_id} does not exist.")

        # Create student
        student = Student.objects.create(user=user, **data)

        # Send SMS with login credentials
        self.sms_service.save_sms_history(
            created_by=None,
            created_for=user,
            phone_number=user.phone,
            message=f"Your student account has been created. Phone Number: {user.username}, Password: {password}",
            sms_type=ACCOUNT,
            status=QUEUE
        )

        return student
    
    @transaction.atomic
    def update_student(self, student_id: int, data: Dict[str, Any]) -> Student:
        """
        Update an existing student and its associated user.
        
        Args:
            student_id: ID of the student to update
            data: Dictionary containing user and student information to update (optional)
                
        Returns:
            Updated Student instance
            
        Raises:
            ValidationError: If validation fails or student not found
        """
        # Get student
        student = self.student_selector.get_student_by_id(student_id)
        if not student:
            raise ValidationError(f"Student with ID {student_id} not found.")
        
        if data:
            user = student.user
            user_data = {
                'username': data.get('phone', user.username),
                'first_name': data.pop('first_name'),
                'last_name': data.pop('last_name'),
                'email': data.pop('email'),
                'phone': data.pop('phone'),
            }
            # Update user
            try:
                user = self.user_service.update_user(user.id, user_data)
                student.user = user
            except ValidationError as e:
                raise ValidationError(f"Failed to update user: {e}")

        # Update school if provided
        try:
            school = School.objects.get(id=data['school_id'])
            student.school = school
        except School.DoesNotExist:
            raise ValidationError(f"School with ID {data['school_id']} does not exist.")
            
        # Check birth registration number uniqueness
        if 'birth_registration_number' in data and data['birth_registration_number'] != student.birth_registration_number:
            if data['birth_registration_number'] and Student.objects.filter(
                birth_registration_number=data['birth_registration_number']
            ).exclude(id=student.id).exists():
                raise ValidationError(
                    f"Student with birth registration number '{data['birth_registration_number']}' already exists."
                )
            student.birth_registration_number = data['birth_registration_number']

        # Update other student fields
        if 'date_of_birth' in data:
            student.date_of_birth = data['date_of_birth']
        if 'guardian_name' in data:
            student.guardian_name = data['guardian_name']
        if 'guardian_phone' in data:
            student.guardian_phone = data['guardian_phone']
        if 'guardian_email' in data:
            student.guardian_email = data['guardian_email']
        if 'guardian_relationship' in data:
            student.guardian_relationship = data['guardian_relationship']
        if 'address' in data:
            student.address = data['address']

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
        student = self.student_selector.get_student_by_id(student_id)
        if not student:
            raise ValidationError(f"Student with ID {student_id} not found.")

        student.user.is_active = True
        student.user.save()
        
        return student
    
    @transaction.atomic
    def delete_student(self, student_id: int) -> bool:
        """
        Delete a student and all related data.
        
        Args:
            student_id: ID of student to delete
        
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            student = Student.objects.get(id=student_id)
            student.delete()
            return True
        except Student.DoesNotExist:
            return False
        except Exception as e:
            # Log the exception
            print(f"Error deleting student: {e}")
            return False
    
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