from django.contrib import admin
from academy.models import Academy, Course, Batch
from classmate.admin import ClassMateAdmin

@admin.register(Academy)
class AcademyAdmin(ClassMateAdmin):
    list_display = ('name', 'contact_number', 'email', 'user')
    list_filter = ('user',)
    search_fields = ('name', 'contact_number', 'email')
    ordering = ('name',)


@admin.register(Course)
class CourseAdmin(ClassMateAdmin):
    list_display = ('name', 'fee', 'start_date', 'end_date', 'academy')
    list_filter = ('academy',)
    search_fields = ('name', 'academy__name')
    ordering = ('start_date',)


@admin.register(Batch)
class BatchAdmin(ClassMateAdmin):
    list_display = ('name', 'course', 'start_date', 'end_date')
    list_filter = ('course',)
    search_fields = ('name', 'course__name')
    ordering = ('start_date',)