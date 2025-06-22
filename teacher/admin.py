from django.contrib import admin
from .models import Teacher
from classmate.admin import ClassMateAdmin

@admin.register(Teacher)
class TeacherAdmin(ClassMateAdmin):
    list_display = ('user',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username')
    filter_horizontal = ('batches',)
    ordering = ('id',)

