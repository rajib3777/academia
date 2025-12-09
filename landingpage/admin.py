from django.contrib import admin
from landingpage.models import (
    AcademyGallery,
    AcademyFacility,
    AcademyProgram,
    AcademyReview,
    TeacherSubject,
    TeacherEducation,
    TeacherAchievement,
    TeacherReview,
    ContactUs
)


class AcademyGalleryInline(admin.TabularInline):
    model = AcademyGallery
    extra = 1
    fields = ['image', 'title', 'order', 'is_active']


class AcademyFacilityInline(admin.TabularInline):
    model = AcademyFacility
    extra = 1
    fields = ['name', 'is_active']


class AcademyProgramInline(admin.TabularInline):
    model = AcademyProgram
    extra = 1
    fields = ['name', 'is_active']


class AcademyReviewInline(admin.TabularInline):
    model = AcademyReview
    extra = 1
    fields = ['student', 'rating', 'review_text', 'is_verified', 'is_approved', 'is_active', 'created_at']
    readonly_fields = ('created_at',)


@admin.register(AcademyGallery)
class AcademyGalleryAdmin(admin.ModelAdmin):
    list_display = ['academy', 'title', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'academy']
    search_fields = ['academy__name', 'title']
    ordering = ['academy', 'order']


@admin.register(AcademyFacility)
class AcademyFacilityAdmin(admin.ModelAdmin):
    list_display = ['academy', 'name', 'is_active']
    list_filter = ['is_active', 'academy']
    search_fields = ['academy__name', 'name']
    autocomplete_fields = ['academy']


@admin.register(AcademyProgram)
class AcademyProgramAdmin(admin.ModelAdmin):
    list_display = ['academy', 'name', 'is_active']
    list_filter = ['is_active', 'academy']
    search_fields = ['academy__name', 'name']
    autocomplete_fields = ['academy']


@admin.register(AcademyReview)
class AcademyReviewAdmin(admin.ModelAdmin):
    list_display = ['academy', 'student', 'rating', 'is_verified', 'is_approved', 'is_active', 'created_at']
    list_filter = ['is_verified', 'is_approved', 'is_active', 'rating', 'academy']
    search_fields = ['academy__name', 'student__name', 'review_text']
    actions = ['approve_reviews', 'verify_reviews']
    readonly_fields = ('created_at',)
    autocomplete_fields = ['academy', 'student']    
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"
    
    def verify_reviews(self, request, queryset):
        queryset.update(is_verified=True)
    verify_reviews.short_description = "Verify selected reviews"


class TeacherSubjectInline(admin.TabularInline):
    model = TeacherSubject
    extra = 1
    fields = ['subject', 'is_primary']


class TeacherEducationInline(admin.TabularInline):
    model = TeacherEducation
    extra = 1
    fields = ['degree', 'institution', 'year', 'order']


class TeacherAchievementInline(admin.TabularInline):
    model = TeacherAchievement
    extra = 1
    fields = ['title', 'description', 'year', 'order']


@admin.register(TeacherSubject)
class TeacherSubjectAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'subject', 'is_primary']
    list_filter = ['teacher', 'subject', 'is_primary']
    search_fields = ['teacher__full_name', 'subject__name']
    autocomplete_fields = ['teacher']


@admin.register(TeacherEducation)
class TeacherEducationAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'degree', 'institution', 'year', 'order']
    list_filter = ['teacher', 'degree', 'institution', 'year', 'order']
    search_fields = ['teacher__full_name', 'degree', 'institution']
    autocomplete_fields = ['teacher']


@admin.register(TeacherAchievement)
class TeacherAchievementAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'title', 'description', 'year', 'order']
    list_filter = ['teacher', 'title', 'description', 'year', 'order']
    search_fields = ['teacher__full_name', 'title', 'description']
    autocomplete_fields = ['teacher']


@admin.register(TeacherReview)
class TeacherReviewAdmin(admin.ModelAdmin):
    list_display = [
        'teacher',
        'student_name',
        'rating',
        'is_approved',
        'is_active',
        'reviewed_at'
    ]
    list_filter = ['is_approved', 'is_active', 'rating', 'reviewed_at']
    search_fields = ['teacher__full_name', 'student_name', 'review_text']
    readonly_fields = ['reviewed_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Review Information', {
            'fields': ('teacher', 'student', 'student_name', 'rating', 'review_text')
        }),
        ('Status', {
            'fields': ('is_approved', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('reviewed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone', 'subject', 'status', 'created_at']
    list_filter = ['created_at', 'status']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'subject']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Contact Information', {
            'fields': (('first_name', 'last_name', 'email', 'phone', 'subject', 'status'), ('message'))
        }),
        ('Timestamps', {
            'fields': (('created_at', 'updated_at')),
            'classes': ('collapse',)
        }),
    )