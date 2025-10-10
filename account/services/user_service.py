from typing import Dict, Any, Optional
from django.db import transaction
from account.models import User, Role
from django.core.cache import cache
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from account.utils import generate_secure_password
from account.selectors.user_selector import UserSelector


class UserService:
    """
    Service class to handle all write operations for User model.
    Contains business logic for creating and updating users.
    """

    def __init__(self):
        self.user_selector = UserSelector()

    @transaction.atomic
    def create_user(self, user_data: Dict[str, Any], role: str) -> User:
        """
        Creates a new user with a secure password.
        
        Args:
            user_data: Dictionary containing user information
            role: Role to assign to the user

        Returns:
            User: Created user instance
        """
        password=user_data.get('password', generate_secure_password())
        username = user_data.get('username')
        phone = user_data.get('phone')

        # Check for duplicate username
        if username and User.objects.filter(username=username).exists():
            raise DjangoValidationError('A user with this username already exists.')

        # Check for duplicate phone
        if phone and User.objects.filter(phone=phone).exists():
            raise DjangoValidationError('A user with this phone number already exists.')

        try:
            user = User(**user_data)
            user.set_password(password)
            user.role, _ = Role.objects.get_or_create(name=role)
            user.save()
            return user, password
        except DjangoValidationError as e:
            # Re-raise for serializer/view to handle
            raise
        except IntegrityError as e:
            # Handle any other DB integrity errors
            raise DjangoValidationError({'detail': f'Integrity error: {str(e)}'})
        except Exception as e:
            # General fallback
            raise DjangoValidationError({'detail': f'Error creating user: {str(e)}'})

    @transaction.atomic
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> User:
        """
        Updates an existing user without changing password.
        
        Args:
            user_id: ID of the user to update
            user_data: Dictionary containing updated user information
            
        Returns:
            User: Updated user instance
        """
        user = self.user_selector.get_user_by_id(user_id)
        
        # Update only the provided fields
        for attr, value in user_data.items():
            setattr(user, attr, value)
        
        user.save()
        return user
    
    @transaction.atomic
    def update_password(self, user_id: int, new_password: str) -> User:
        """
        Updates a user's password.
        
        Args:
            user_id: ID of the user whose password will be updated
            new_password: New password for the user
            
        Returns:
            User: Updated user instance
        """
        user = self.user_selector.get_user_by_id(user_id)
        user.set_password(new_password)
        user.save()
        return user

    def update_own_user(self, user: User, data: dict) -> None:
        for field, value in data.items():
            setattr(user, field, value)
        user.full_clean()
        user.save()

    def set_password(self, user: User, new_password: str) -> None:
        user.set_password(new_password)
        user.full_clean()
        user.save()


class NavbarService:
    """
    Service to manage navbar account info cache.
    """
    @staticmethod
    def invalidate_navbar_account_info_cache(user_id: int) -> None:
        cache_key = f'navbar_account_info_{user_id}'
        cache.delete(cache_key)