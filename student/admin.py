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
        ('user', 'student_id', 'birth_registration_number', 'date_of_birth','school'),
        ('guardian_name', 'guardian_phone', 'guardian_email', 'guardian_relationship'),
        ('profile_picture', 'address', ),
        ('created_at', 'modified_at')
    ]
    list_filter = ('school',)
    readonly_fields = ('student_id', 'created_at', 'modified_at')
    search_fields = ('user__first_name__icontains', 'user__last_name__icontains', 'user__username__icontains', 'user__email__icontains', 'student_id', 'school__name__icontains')

    # raw_id_fields = ('user', 'school')


