from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination
from utils.choices import ROLE_CACHE_TIMEOUT, ROLE_CACHE
from .models import Role


def get_or_update_role_cache():
    """Fetch role data from cache or update it if not available."""
    role_mapping = cache.get(ROLE_CACHE)  # Try to get from cache

    if not role_mapping:  # If cache is empty or expired
        role_mapping = {role.name: role.id for role in Role.objects.all()}
        cache.set(ROLE_CACHE, role_mapping, timeout=ROLE_CACHE_TIMEOUT)

    return role_mapping

def force_update_role_cache():
    """Forcefully update the cache (used in signals or admin updates)."""
    role_mapping = {role.name: role.id for role in Role.objects.all()}
    cache.set(ROLE_CACHE, role_mapping, timeout=ROLE_CACHE_TIMEOUT)


class UserListPaginationClass(PageNumberPagination):
    page_size = 20  # Number of items per page
    page_size_query_param = 'page_size'  # Allow client to set page size
    max_page_size = 100  # Maximum limit for page size 