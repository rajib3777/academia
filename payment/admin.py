from django.contrib import admin
from payment.models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Payment model.
    """
    list_display = (
        'payer',
        'target',
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
        'payer_content_type',
        'target_content_type',
    )
    search_fields = (
        'transaction_id',
        'remarks',
    )
    readonly_fields = ('date', 'created_by', 'created_at', 'modified_at', 
                       'metadata', 'payer_content_type', 'target_content_type',
                       'payer_object_id', 'target_object_id'
        )
    fieldsets = (
        (None, {
            'fields': ((
                'payer_content_type',
                'payer_object_id',
                'target_content_type',
                'target_object_id',
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