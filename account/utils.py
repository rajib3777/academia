import random
import string
import secrets
from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.core.validators import RegexValidator
from utils.choices import ROLE_CACHE_TIMEOUT, ROLE_CACHE


def get_or_update_role_cache():
    from account.models import Role
    """Fetch role data from cache or update it if not available."""
    role_mapping = cache.get(ROLE_CACHE)  # Try to get from cache

    if not role_mapping:  # If cache is empty or expired
        role_mapping = {role.name: role.id for role in Role.objects.all()}
        cache.set(ROLE_CACHE, role_mapping, timeout=ROLE_CACHE_TIMEOUT)

    return role_mapping

def force_update_role_cache():
    from account.models import Role
    """Forcefully update the cache (used in signals or admin updates)."""
    role_mapping = {role.name: role.id for role in Role.objects.all()}
    cache.set(ROLE_CACHE, role_mapping, timeout=ROLE_CACHE_TIMEOUT)


class UserListPaginationClass(PageNumberPagination):
    page_size = 20  # Number of items per page
    page_size_query_param = 'page_size'  # Allow client to set page size
    max_page_size = 100  # Maximum limit for page size


    def get_paginated_response(self, data):
        """Return a paginated response with additional metadata."""
        return_data = {
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'custom_metadata': 'value',
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'page_size': self.get_page_size(self.request),
            'current_page_url': self.request.build_absolute_uri(self.request.path),
            'request_method': self.request.method,
            'request_headers': dict(self.request.headers),
            'request_query_params': dict(self.request.query_params),
        }

        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return_data['request_body'] = self.request.data

        if self.request.user.is_authenticated:
            return_data['request_user'] = {
                'id': self.request.user.id,
                'name': self.request.user.name,
                'email': self.request.user.email,
                'phone': self.request.user.phone,
            }
            return_data['request_user_roles'] = [role.name for role in self.request.user.roles.all()]
            return_data['request_user_groups'] = [group.name for group in self.request.user.groups.all()]
            return_data['request_user_is_staff'] = self.request.user.is_staff
            return_data['request_user_is_superuser'] = self.request.user.is_superuser
            return_data['request_user_is_active'] = self.request.user.is_active

        return Response(return_data)
    


phone_validator = RegexValidator(
    regex=r'^\+?\d{7,15}$',
    message='Enter a valid contact number.'
)



def generate_secure_password(length=10):
    """
    Alternative implementation using secrets module for cryptographically secure passwords.
    """    
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Ensure at least one character from each category
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special_chars)
    ]
    
    # Fill remaining positions
    all_chars = uppercase + lowercase + digits + special_chars
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Shuffle the password
    random.shuffle(password)
    
    return ''.join(password)