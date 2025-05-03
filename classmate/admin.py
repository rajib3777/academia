from django.contrib import admin
from classmate.models import populate_user_info


class ClassMateAdmin(admin.ModelAdmin):
    readonly_fields = [
        'created_by', 'created_at', 'modified_by', 'modified_at', 'archived_at', 'is_archived',
    ]

    def save_model(self, request, obj, form, change):
        populate_user_info(request, obj, change)
        obj.save()