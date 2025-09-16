from typing import Dict, Any, Optional
from django.db import transaction
from account.models import User
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
    def create_user(self, user_data: Dict[str, Any]) -> User:
        """
        Creates a new user with a secure password.
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            User: Created user instance
        """
        password = generate_secure_password()
        user = User(**user_data)
        user.set_password(password)
        user.save()
        return user

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