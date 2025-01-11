from django.contrib import admin
from .models import Teacher
from classmate.admin import ClassMateAdmin

@admin.register(Teacher)
class TeacherAdmin(ClassMateAdmin):
    list_display = ('user',)
    search_fields = ('user__full_name',)
    filter_horizontal = ('batches',)
    ordering = ('user__full_name',)

