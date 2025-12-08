from django.contrib import admin
from django.utils.html import format_html
from utils.models import SMSHistory, OTPVerification, Division, District, Upazila


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    # list_display = ('phone_number', 'otp', 'created_at', 'expires_at', 'is_verified', 'is_expired_display')
    list_display = ('phone_number', 'otp', 'created_at', 'expires_at', 'is_verified')
    search_fields = ('phone_number', 'otp')
    list_filter = ('is_verified', ('created_at', admin.DateFieldListFilter))
    # readonly_fields = ('created_at', 'expires_at', 'is_expired_display')
    ordering = ('-created_at',)

    # def is_expired_display(self, obj):
    #     return obj.is_expired()
    # is_expired_display.boolean = True
    # is_expired_display.short_description = "Is Expired?"


@admin.register(SMSHistory)
class SMSHistoryAdmin(admin.ModelAdmin):
    list_display = ('created_for', 'created_by', 'phone_number', 'sms_type', 'status_badge', 'created_at', 'sent_at', 'response_at', 'failed_reason_short')
    search_fields = ('phone_number', 'message', 'failed_reason', 'failed_status_code')
    list_filter = ('sms_type', 'status', ('sent_at', admin.DateFieldListFilter))
    readonly_fields = ('created_at', 'sent_at', 'updated_at', 'response_at', 'status_badge', 'failed_reason_short')
    ordering = ('-sent_at',)
    autocomplete_fields = ['created_by', 'created_for']  # Enable autocomplete for user fields

    fieldsets = (
        (None, {
            'fields': (
                ('created_for', 'created_by', ),
                ('phone_number', 'sms_type', 'status', 'message', ),
                ('failed_reason', 'failed_status_code')
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at', 'response_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        color = {
            'queue': 'gray',
            'sent': 'green',
            'failed': 'red',
            'delivered': 'blue',
        }.get(obj.status.lower(), 'black')
        return format_html('<span style="color: white; background-color: {}; padding: 2px 6px; border-radius: 4px;">{}</span>', color, obj.status.capitalize())
    status_badge.short_description = "Status"

    def failed_reason_short(self, obj):
        if obj.failed_reason:
            return (obj.failed_reason[:50] + '...') if len(obj.failed_reason) > 50 else obj.failed_reason
        return "-"
    failed_reason_short.short_description = "Failure Reason"

    actions = ['mark_as_sent', 'mark_as_failed']

    def mark_as_sent(self, request, queryset):
        updated = queryset.update(status='sent')
        self.message_user(request, f"{updated} message(s) marked as Sent.")
    mark_as_sent.short_description = "Mark selected as Sent"

    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f"{updated} message(s) marked as Failed.")
    mark_as_failed.short_description = "Mark selected as Failed"


class UpazilaInline(admin.TabularInline):
    model = Upazila
    extra = 1
    show_change_link = True


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'division')
    list_filter = ('division',)
    search_fields = ('name', 'division__name')
    inlines = [UpazilaInline]
    autocomplete_fields = ['division']  # Enable autocomplete for district field


class DistrictInline(admin.TabularInline):
    model = District
    extra = 1
    show_change_link = True


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [DistrictInline]


@admin.register(Upazila)
class UpazilaAdmin(admin.ModelAdmin):
    list_display = ('name', 'district')
    list_filter = ('district',)
    search_fields = ('name',)
    search_fields = ('name', 'district__name', 'district__division__name')
    autocomplete_fields = ['district']  # Enable autocomplete for district field