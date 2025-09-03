import django_filters
from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Student
from datetime import date, datetime

def generate_student_id(prefix: str = "STD") -> str:
    count = Student.objects.count() + 1
    padded_number = str(count).zfill(6)
    return f"{prefix}-{padded_number}"


class StudentFilter(filters.FilterSet):
    """
        # Basic list
        GET /api/v1/students/

        # Filter by school
        GET /api/v1/students/?school=1

        # Filter by school name
        GET /api/v1/students/?school_name=high

        # Search across multiple fields
        GET /api/v1/students/?search=john

        # Filter by user status
        GET /api/v1/students/?is_active=true

        # Filter by age range
        GET /api/v1/students/?age_from=10&age_to=15

        # Filter by date of birth range
        GET /api/v1/students/?date_of_birth_from=2010-01-01&date_of_birth_to=2015-12-31

        # Filter by creation date
        GET /api/v1/students/?created_at_from=2024-01-01T00:00:00Z

        # Filter students with guardian email
        GET /api/v1/students/?has_guardian_email=true

        # Filter by multiple schools
        GET /api/v1/students/?schools=1,2,3

        # Ordering (single field)
        GET /api/v1/students/?ordering=-created_at

        # Ordering (multiple fields)
        GET /api/v1/students/?ordering=user__first_name,-created_at

        # Pagination
        GET /api/v1/students/?page=2&page_size=10

        # Complex query combining multiple filters
        GET /api/v1/students/?school=1&search=john&age_from=10&age_to=15&ordering=user__first_name&page=1&page_size=20&has_guardian_email=true
    """
    # Basic filters
    school = filters.NumberFilter(field_name='school__id')
    school_name = filters.CharFilter(field_name='school__name', lookup_expr='icontains')
    
    # User filters
    username = filters.CharFilter(field_name='user__username', lookup_expr='icontains')
    email = filters.CharFilter(field_name='user__email', lookup_expr='icontains')
    phone = filters.CharFilter(field_name='user__phone', lookup_expr='icontains')
    first_name = filters.CharFilter(field_name='user__first_name', lookup_expr='icontains')
    last_name = filters.CharFilter(field_name='user__last_name', lookup_expr='icontains')
    is_active = filters.BooleanFilter(field_name='user__is_active')
    
    # Student specific filters
    student_id = filters.CharFilter(field_name='student_id', lookup_expr='icontains')
    birth_registration_number = filters.CharFilter(field_name='birth_registration_number', lookup_expr='icontains')
    guardian_name = filters.CharFilter(field_name='guardian_name', lookup_expr='icontains')
    guardian_phone = filters.CharFilter(field_name='guardian_phone', lookup_expr='icontains')
    guardian_email = filters.CharFilter(field_name='guardian_email', lookup_expr='icontains')
    guardian_relationship = filters.CharFilter(field_name='guardian_relationship', lookup_expr='icontains')
    address = filters.CharFilter(field_name='address', lookup_expr='icontains')
    
    # Date filters
    date_of_birth = filters.DateFilter(field_name='date_of_birth')
    date_of_birth_from = filters.DateFilter(field_name='date_of_birth', lookup_expr='gte')
    date_of_birth_to = filters.DateFilter(field_name='date_of_birth', lookup_expr='lte')
    
    created_at = filters.DateTimeFilter(field_name='created_at')
    created_at_from = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_to = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    modified_at = filters.DateTimeFilter(field_name='modified_at')
    modified_at_from = filters.DateTimeFilter(field_name='modified_at', lookup_expr='gte')
    modified_at_to = filters.DateTimeFilter(field_name='modified_at', lookup_expr='lte')
    
    # Age range filters
    age_from = filters.NumberFilter(method='filter_age_from')
    age_to = filters.NumberFilter(method='filter_age_to')
    
    # Advanced filters
    has_guardian_email = filters.BooleanFilter(method='filter_has_guardian_email')
    has_guardian_phone = filters.BooleanFilter(method='filter_has_guardian_phone')
    has_birth_registration = filters.BooleanFilter(method='filter_has_birth_registration')
    
    # Multiple school filter
    schools = filters.BaseInFilter(field_name='school__id', lookup_expr='in')
    
    class Meta:
        model = Student
        fields = []
    
    def filter_age_from(self, queryset, name, value):
        if value is not None:
            target_date = date.today().replace(year=date.today().year - value)
            return queryset.filter(date_of_birth__lte=target_date)
        return queryset
    
    def filter_age_to(self, queryset, name, value):
        if value is not None:
            target_date = date.today().replace(year=date.today().year - value - 1)
            return queryset.filter(date_of_birth__gt=target_date)
        return queryset
    
    def filter_has_guardian_email(self, queryset, name, value):
        if value:
            return queryset.filter(guardian_email__isnull=False).exclude(guardian_email='')
        else:
            return queryset.filter(Q(guardian_email__isnull=True) | Q(guardian_email=''))
    
    def filter_has_guardian_phone(self, queryset, name, value):
        if value:
            return queryset.filter(guardian_phone__isnull=False).exclude(guardian_phone='')
        else:
            return queryset.filter(Q(guardian_phone__isnull=True) | Q(guardian_phone=''))
    
    def filter_has_birth_registration(self, queryset, name, value):
        if value:
            return queryset.filter(birth_registration_number__isnull=False).exclude(birth_registration_number='')
        else:
            return queryset.filter(Q(birth_registration_number__isnull=True) | Q(birth_registration_number=''))

