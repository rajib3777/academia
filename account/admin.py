from django.contrib import admin
from django.contrib import messages
from django.test import Client
from account.models import User, Role, Permission, Menu, RoleMenuPermission, RecoveryOTP
from classmate.admin import ClassMateAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import HttpResponse
import csv
import io
from openpyxl import Workbook
from account.choices import NOT_USED, USED, BLOCKED
from django.utils.translation import gettext_lazy as _
from account.forms import GenerateOTPActionForm

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


@admin.action(description="Block selected OTPs")
def block_selected_otps(modeladmin, request, queryset):
    queryset.update(status=BLOCKED) 
    modeladmin.message_user(request, "Selected OTPs have been blocked.")


@admin.action(description="Unblock selected OTPs")
def unblock_selected_otps(modeladmin, request, queryset):
    queryset.update(status=NOT_USED) 
    modeladmin.message_user(request, "Selected OTPs have been unblocked.")


@admin.action(description="Download selected OTPs as TXT")
def download_txt(modeladmin, request, queryset):
    content = "\n".join(str(obj.code) for obj in queryset)
    response = HttpResponse(content, content_type="text/plain")
    response["Content-Disposition"] = 'attachment; filename="recovery_otps.txt"'
    return response


@admin.action(description="Download selected OTPs as CSV/Excel (50 per column)")
def download_excel(modeladmin, request, queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Recovery OTPs"

    otps = [str(obj.code) for obj in queryset]

    # 50 OTP per column
    col = 1
    row = 1
    counter = 0

    for otp in otps:
        ws.cell(row=row, column=col).value = otp
        row += 1
        counter += 1

        if counter == 50:
            col += 1
            row = 1
            counter = 0

    # write to response
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="recovery_otps.xlsx"'

    wb.save(response)
    return response


@admin.action(description="Generate OTP by Academy ID")
def action_generate_otp(modeladmin, request, queryset):
    # If page loaded without action selected → do nothing
    action = request.POST.get("action")
    if action != "action_generate_otp":
        return

    academy_id = request.POST.get("academy_id")

    if not academy_id:
        messages.error(request, "Academy ID is required.")
        return

    # Only super admin can call this
    if not request.user.is_superuser and not request.user.is_admin():
        messages.error(request, "Only super admin can generate OTP.")
        return

    # --- IMPORTANT FIX ---
    # Django Admin requires a queryset
    # If none were selected, create an empty queryset
    queryset = modeladmin.model.objects.none()

    # Call the internal API using Django test client
    client = Client()
    client.force_login(request.user)

    api_url = f"/api/generate-recovery-otp/?academy_id={academy_id}"
    response = client.get(api_url)

    if response.status_code == 200:
        otp_data = response.json()
        messages.success(request, f"OTP Generated: {otp_data.get('otp')}")
    else:
        messages.error(request, f"API Error: {response.content}")

    return

@admin.register(RecoveryOTP)
class RecoveryOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "phone", "status", "created_at", "expires_at", "created_by")
    list_filter = ("status", "created_at", "user", "expires_at", "created_by")
    search_fields = ("user__username", "user__phone", "code", "phone")
    fieldsets = (
        (_("Basic Info"), {
            'fields': (
                ('user', 'code', 'phone', 'status', ),
                ('created_at', 'expires_at', 'created_by'),
            )
        }),
    )
    readonly_fields = ('code', 'created_at', 'expires_at', 'created_by')
    action_form = GenerateOTPActionForm
    actions = [action_generate_otp, block_selected_otps, unblock_selected_otps, download_txt, download_excel]
