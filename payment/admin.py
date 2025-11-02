from django.contrib import admin
from django.db import models
from django import forms
from payment.models import StudentPayment

@admin.register(StudentPayment)
class StudentPaymentAdmin(admin.ModelAdmin):
    """
    Admin configuration for StudentPayment model.
    """
    list_display = (
        'batch_enrollment',
        'student',
        'amount',
        'method',
        'status',
        'date',
        'transaction_id',
        'is_refunded',
    )
    list_filter = (
        'method',
        'date',
        'status',
        'is_refunded',
        'refund_date',
        'batch_enrollment',
        'student',
    )
    search_fields = (
        'transaction_id',
        'remarks',
        'student__user__first_name',
        'student__user__last_name',
        'student__user__email',
        'batch_enrollment__batch__name',
    )
    readonly_fields = ('date', 'created_by', 'created_at', 'modified_at',
                       'metadata',)
    fieldsets = (
        (None, {
            'fields': ((
                'batch_enrollment',
                'student',
            ),)
        }),
        (None, {
            'fields': ((
                'amount',
                'method',
                'status',
                'transaction_id',
                'reference',
                'remarks',
                
            ),)
        }),
        (None, {
            'fields': ((
                'is_refunded',
                'refund_date',
            ),)
        }),
        ('Timestamps', {
            'fields': (
                ('date', 'created_by', 'created_at', 'modified_at'),
                ('metadata', ),
            ),
        }),
    )

    formfield_overrides = {
        models.TextField: {
            'widget': forms.Textarea(
                attrs={
                    'rows': 3,                     # Adjust height
                    'cols': 80,                    # Adjust width
                    'style': 'resize: vertical;',  # Allow vertical resize only
                    'placeholder': 'Enter payment remarks or notes here...',
                }
            )
        },
    }