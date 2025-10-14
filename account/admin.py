from django.contrib import admin
from account.models import User, Role, Permission, Menu, RoleMenuPermission
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
        (_("Basic Info"), {'fields': [('username', 'first_name', 'last_name', 'email', 'phone', 'otp')]}),
        (_("Permissions"), {'fields': [('is_active', 'is_staff', 'is_superuser'), ('role'), ('groups')]}),
        (_("Password"), {'fields': ('password',)}),
        (_("Important Dates"), {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (_("Create User"), {
            'classes': ('wide',),
            'fields': [
                ('first_name', 'last_name',),
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


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'order', 'remarks')
    search_fields = ('name',)
    list_filter = ('parent',)

@admin.register(RoleMenuPermission)
class RoleMenuPermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'menu', 'remarks')
    filter_horizontal = ('permissions',)
    search_fields = ('role__name', 'menu__name')
    list_filter = ('role', )
