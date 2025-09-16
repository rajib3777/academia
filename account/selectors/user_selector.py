from typing import Optional, List, Dict, Any, Tuple
from django.db.models import Q, QuerySet
from django.core.paginator import Paginator
from django.http import Http404

from account.models import User


class UserSelector:
    """
    Selector class to handle all read operations for User model.
    Contains methods to query and retrieve user data.
    """
    
    def get_user_by_id(self, user_id: int) -> User:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID to query
            
        Returns:
            User: User instance
            
        Raises:
            Http404: If user does not exist
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise Http404(f"User with ID {user_id} does not exist")
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: Email to query
            
        Returns:
            Optional[User]: User instance or None if not found
        """
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    def get_user_by_phone(self, phone: str) -> Optional[User]:
        """
        Get a user by phone number.
        
        Args:
            phone: Phone number to query
            
        Returns:
            Optional[User]: User instance or None if not found
        """
        try:
            return User.objects.get(phone=phone)
        except User.DoesNotExist:
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            username: Username to query
            
        Returns:
            Optional[User]: User instance or None if not found
        """
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
    
    def list_users(self, **filters) -> QuerySet:
        """
        List users with optional filtering.
        
        Args:
            **filters: Optional filters to apply
            
        Returns:
            QuerySet: Filtered queryset of users
        """
        queryset = User.objects.all().order_by('id')
        
        # Apply filters if provided
        if 'role' in filters and filters['role']:
            queryset = queryset.filter(role__name=filters['role'])
            
        if 'search' in filters and filters['search']:
            search_term = filters['search']
            queryset = queryset.filter(
                Q(username__icontains=search_term) | 
                Q(email__icontains=search_term) | 
                Q(phone__icontains=search_term) |
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term)
            )
            
        return queryset
    
    def check_email_exists(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if a user with given email exists.
        
        Args:
            email: Email to check
            exclude_id: Optional user ID to exclude from check
            
        Returns:
            bool: True if exists, False otherwise
        """
        queryset = User.objects.filter(email=email)
        if exclude_id:
            queryset = queryset.exclude(pk=exclude_id)
        return queryset.exists()
    
    def check_phone_exists(self, phone: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if a user with given phone exists.
        
        Args:
            phone: Phone number to check
            exclude_id: Optional user ID to exclude from check
            
        Returns:
            bool: True if exists, False otherwise
        """
        queryset = User.objects.filter(phone=phone)
        if exclude_id:
            queryset = queryset.exclude(pk=exclude_id)
        return queryset.exists()