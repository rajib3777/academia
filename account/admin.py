from django.contrib import admin
from account.models import User, Role
from classmate.admin import ClassMateAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('username', 'phone', 'email', 'is_superuser', 'is_active', 'is_staff', 'role', 'get_groups')
    list_filter = ('is_active', 'is_staff', 'role')
    search_fields = ('username', 'phone', 'email')
    ordering = ('username',)
    readonly_fields = ('otp',)

    fieldsets = (
        (_("Basic Info"), {'fields': [('username', 'email', 'phone', 'otp')]}),
        (_("Permissions"), {'fields': [('is_active', 'is_staff', 'is_superuser'), ('role'), ('groups')]}),
        (_("Password"), {'fields': ('password',)}),
        (_("Important Dates"), {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (_("Create User"), {
            'classes': ('wide',),
            'fields': [
                ('username', 'phone', 'email',),
                ('password1', 'password2', ),
                ('is_active', 'is_staff', 'is_superuser',),
                ('role', ),
                ('groups', ),
            ],
        }),
    )

    filter_horizontal = ('groups',)

    def get_groups(self, obj):
        return ", ".join(group.name for group in obj.groups.all())
    get_groups.short_description = "Groups"


