from django.db import models
from account.models import User
from academy.models import Academy
from classmate.models import ClassMateModel
from django.core.validators import MinValueValidator, MaxValueValidator
from academy.choices_fields import SUBJECT_TYPE_CHOICES


class Teacher(ClassMateModel):
    """
    Teacher model - One teacher per academy
    """
    academy = models.ForeignKey(
        Academy, 
        on_delete=models.CASCADE, 
        related_name='teacher',
        help_text="One teacher per academy"
    )
    profile_image = models.ImageField(
        upload_to='teacher_profiles/', 
        null=True, 
        blank=True,
        help_text="Teacher profile image"
    )
    full_name = models.CharField(
        max_length=255,
        help_text="Teacher's full name (e.g., Dr. Sadia Ekter)"
    )
    title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Professional title (e.g., Mathematics Lead, Science Director)"
    )
    bio = models.TextField(
        null=True,
        blank=True,
        help_text="Teacher's biography/about section"
    )
    experience_years = models.PositiveIntegerField(
        default=0,
        help_text="Years of teaching experience"
    )

    location = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Location (e.g., San Francisco, USA)"
    )
    linkedin_url = models.URLField(
        null=True,
        blank=True,
        help_text="LinkedIn profile URL"
    )
    email = models.EmailField(
        null=True,
        blank=True,
        help_text="Contact email"
    )
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Contact phone number"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether this teacher is featured on landing page"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Whether teacher is currently available for booking"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this teacher is active/visible"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Teacher creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Teacher update timestamp"
    )
    
    class Meta:
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return self.full_name
    
    @property
    def total_students(self):
        """Get total students from academy"""
        return self.academy.total_students
    
    @property
    def total_courses(self):
        """Get total courses from academy"""
        return self.academy.courses.count()
    
    @property
    def average_rating(self):
        """Get average rating from reviews"""
        from django.db.models import Avg
        avg = self.academy.reviews.filter(
            is_approved=True,
            is_active=True
        ).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0
    
    @property
    def total_reviews(self):
        """Get total number of approved reviews"""
        return self.academy.reviews.filter(
            is_approved=True,
            is_active=True
        ).count()


