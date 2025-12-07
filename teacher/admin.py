from django.contrib import admin
from teacher.models import Teacher
from landingpage.admin import TeacherSubjectInline, TeacherEducationInline, TeacherAchievementInline


# Register your models here.
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 
        'academy', 
        'title', 
        'experience_years', 
        'is_featured', 
        'is_available',
        'is_active'
    ]
    list_filter = ['is_featured', 'is_available', 'is_active', 'created_at']
    search_fields = ['full_name', 'title', 'academy__name', 'bio']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (('academy', 'full_name', 'title', 'bio', 'profile_image'),)
        }),
        ('Professional Details', {
            'fields': (('experience_years', 'location'),)
        }),
        ('Contact Information', {
            'fields': (('email', 'phone', 'linkedin_url'),)
        }),
        ('Status', {
            'fields': (('is_featured', 'is_available', 'is_active'),)
        }),
        ('Timestamps', {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TeacherSubjectInline, TeacherEducationInline, TeacherAchievementInline]