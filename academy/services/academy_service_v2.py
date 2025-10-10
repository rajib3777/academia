from typing import Dict, Any, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from functools import cached_property

from academy.models import Academy, Course, Batch, BatchEnrollment
from account.models import User
from academy.selectors.academy_selector_v2 import AcademySelector
from utils.models import Division, District, Upazila
from account.services.user_service import UserService
from utils.services.sms_service import SMSService
from utils.utils import save_sms_history
from utils.choices import ACCOUNT, QUEUE
from account.choices import ACADEMY

class AcademyService:
    """
    Service class for Academy model to handle all write operations and business logic.
    """
    
    def __init__(self):
        """Initialize the AcademyService."""
        self.user_service = UserService()
        self.sms_service = SMSService()

    @cached_property
    def academy_selector(self) -> AcademySelector:
        """
        Lazy initialization of AcademySelector.
        
        Returns:
            AcademySelector instance
        """
        return AcademySelector()
    
    @transaction.atomic
    def create_academy(self, data: Dict[str, Any]) -> Academy:
        """
        Create a new academy with user data.
        
        Args:
            data: Dictionary containing academy and user data
        
        Returns:
            Newly created Academy instance
            
        Raises:
            ValidationError: If validation fails
        """
        user_data = data.pop('user')
        
        # Check if academy with the same name already exists
        if Academy.objects.filter(name=data.get('name')).exists():
            raise ValidationError(f"Academy with name '{data.get('name')}' already exists.")
        
        # Get foreign key objects
        division_id = data.pop('division', None)
        district_id = data.pop('district', None)
        upazila_id = data.pop('upazila', None)
        
        if division_id:
            try:
                division = Division.objects.get(id=division_id)
                data['division'] = division
            except Division.DoesNotExist:
                raise ValidationError(f"Division with ID {division_id} does not exist.")
                
        if district_id:
            try:
                district = District.objects.get(id=district_id)
                data['district'] = district
            except District.DoesNotExist:
                raise ValidationError(f"District with ID {district_id} does not exist.")
                
        if upazila_id:
            try:
                upazila = Upazila.objects.get(id=upazila_id)
                data['upazila'] = upazila
            except Upazila.DoesNotExist:
                raise ValidationError(f"Upazila with ID {upazila_id} does not exist.")
        
        # Create user
        user, password = self.user_service.create_user(user_data, ACADEMY)

        # Create academy
        academy = Academy.objects.create(user=user, **data)

        # Send SMS with login credentials
        self.sms_service.save_sms_history(
            created_by=None,
            created_for=user,
            phone_number=user.phone,
            message=f"Your academy account has been created. Phone Number: {user.username}, Password: {password}",
            sms_type=ACCOUNT,
            status=QUEUE
        )
        return academy

    @transaction.atomic
    def update_academy(self, academy_id: int, data: Dict[str, Any]) -> Optional[Academy]:
        """
        Update an existing academy with user data.
        
        Args:
            academy_id: ID of academy to update
            data: Dictionary containing updated academy and user data
        
        Returns:
            Updated Academy instance or None if academy doesn't exist
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            academy = Academy.objects.get(id=academy_id)
        except Academy.DoesNotExist:
            return None
        
        # Check name uniqueness if changing name
        if 'name' in data and data['name'] != academy.name:
            if Academy.objects.filter(name=data['name']).exclude(id=academy_id).exists():
                raise ValidationError(f"Academy with name '{data['name']}' already exists.")
        
        # Update user data if provided
        user_data = data.pop('user', None)
        if user_data:
            user = academy.user
            
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
            
            # Handle password separately if provided
            if 'password' in user_data and user_data['password']:
                user.set_password(user_data['password'])
            
            user.save()
        
        # Handle foreign keys
        if 'division' in data:
            division_id = data.pop('division')
            if division_id:
                try:
                    academy.division = Division.objects.get(id=division_id)
                except Division.DoesNotExist:
                    raise ValidationError(f"Division with ID {division_id} does not exist.")
            else:
                academy.division = None
                
        if 'district' in data:
            district_id = data.pop('district')
            if district_id:
                try:
                    academy.district = District.objects.get(id=district_id)
                except District.DoesNotExist:
                    raise ValidationError(f"District with ID {district_id} does not exist.")
            else:
                academy.district = None
                
        if 'upazila' in data:
            upazila_id = data.pop('upazila')
            if upazila_id:
                try:
                    academy.upazila = Upazila.objects.get(id=upazila_id)
                except Upazila.DoesNotExist:
                    raise ValidationError(f"Upazila with ID {upazila_id} does not exist.")
            else:
                academy.upazila = None
        
        # Update academy data
        for attr, value in data.items():
            setattr(academy, attr, value)
        
        academy.save()
        return academy

    @transaction.atomic
    def delete_academy(self, academy_id: int) -> bool:
        """
        Delete an academy and all related data except Students.
        
        Args:
            academy_id: ID of academy to delete
        
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            academy = Academy.objects.get(id=academy_id)
            
            # Delete BatchEnrollments for all batches of this academy
            BatchEnrollment.objects.filter(batch__course__academy=academy).delete()
            
            # Delete all Batches for courses of this academy
            Batch.objects.filter(course__academy=academy).delete()
            
            # Delete all Courses for this academy
            Course.objects.filter(academy=academy).delete()
            
            # Finally delete the academy
            academy.delete()
            
            return True
        except Academy.DoesNotExist:
            return False
        except Exception as e:
            # Log the exception
            print(f"Error deleting academy: {e}")
            return False

    def update_academy_account(self, academy: Academy, data: dict) -> None:
        # Resolve FK fields to instances
        fk_fields = {
            'division': Division,
            'district': District,
            'upazila': Upazila,
        }
        for field, model_cls in fk_fields.items():
            if field in data and isinstance(data[field], int):
                instance = model_cls.objects.filter(pk=data[field]).first()
                if not instance:
                    raise ValueError(f'Invalid {field} id: {data[field]}')
                data[field] = instance
        
        # Assign all other fields
        for field, value in data.items():
            setattr(academy, field, value)
        academy.full_clean()
        academy.save()

