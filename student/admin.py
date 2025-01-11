from django.contrib import admin
from student.models import Student, School
from classmate.admin import ClassMateAdmin


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Student)
class StudentAdmin(ClassMateAdmin):
    list_display = ('user', 'school', 'enrollment_date')
    list_filter = ('school',)
    search_fields = ('user__full_name', 'school__name')
    filter_horizontal = ('batches',)
    ordering = ('enrollment_date',)
