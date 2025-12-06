from django.contrib import admin
from landingpage.models import (
    AcademyGallery,
    AcademyFacility,
    AcademyProgram,
    AcademyReview
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

