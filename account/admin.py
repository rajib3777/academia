from django.contrib import admin
from account.models import User, Role
from classmate.admin import ClassMateAdmin

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'mobile_number', 'email', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'roles')
    search_fields = ('full_name', 'mobile_number', 'email')
    filter_horizontal = ('roles',)
    ordering = ('full_name',)


