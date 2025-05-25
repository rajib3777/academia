from django.contrib import admin
from student.models import Student, School
from classmate.admin import ClassMateAdmin


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number', 'website', 'address')
    search_fields = ('name__icontains', 'website', 'address__icontains')
    ordering = ('name',)


@admin.register(Student)
class StudentAdmin(ClassMateAdmin):
    list_display = ('student_id', 'school', 'user', 'date_of_birth', 'guardian_name')
    ordering = ('user__first_name', 'school__name')
    fields = [
        ('user', 'birth_registration_number', 'date_of_birth','school'),
        ('guardian_name', 'guardian_phone', 'guardian_email', 'guardian_relationship'),
        ('address', )
    ]
    list_filter = ('school',)
    search_fields = ('user__full_name', 'school__name')
    
    # raw_id_fields = ('user', 'school')


