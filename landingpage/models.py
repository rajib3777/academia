from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class AcademyGallery(models.Model):
    """Gallery images for academy"""
    academy = models.ForeignKey(
        'academy.Academy', 
        on_delete=models.CASCADE, 
        related_name='gallery_images'
    )
    image = models.ImageField(
        upload_to='academy_gallery/', 
        help_text="Gallery image for the academy"
    )
    title = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="Title/caption for the image"
    )
    description = models.TextField(
        null=True, 
        blank=True,
        help_text="Description of the image"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order of images"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this image is active/visible"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Gallery image creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Gallery image update timestamp"
    )
    class Meta:
        verbose_name = 'Academy Gallery Image'
        verbose_name_plural = 'Academy Gallery Images'
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['academy', 'is_active']),
            models.Index(fields=['order']),
        ]
    def __str__(self):
        return f"{self.academy.name} - {self.title or 'Gallery Image'}"


class AcademyFacility(models.Model):
    """Facilities offered by academy"""
    academy = models.ForeignKey(
        'academy.Academy', 
        on_delete=models.CASCADE, 
        related_name='facilities'
    )
    name = models.CharField(
        max_length=100,
        help_text="Name of the facility (e.g., Modern Classrooms, Science Labs)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this facility is active/visible"
    )
    class Meta:
        verbose_name = 'Academy Facility'
        verbose_name_plural = 'Academy Facilities'
        ordering = ['name']
        unique_together = ('academy', 'name')
    
    def __str__(self):
        return f"{self.academy.name} - {self.name}"


class AcademyProgram(models.Model):
    """Programs/categories offered by academy"""
    academy = models.ForeignKey(
        'academy.Academy', 
        on_delete=models.CASCADE, 
        related_name='programs'
    )
    name = models.CharField(
        max_length=100,
        help_text="Program name (e.g., STEM Programs, Primary Education)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this program is active/visible"
    )
    class Meta:
        verbose_name = 'Academy Program'
        verbose_name_plural = 'Academy Programs'
        ordering = ['name']
        unique_together = ('academy', 'name')
    def __str__(self):
        return f"{self.academy.name} - {self.name}"

class AcademyReview(models.Model):
    """Student/parent reviews for academy"""
    academy = models.ForeignKey(
        'academy.Academy', 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    student = models.ForeignKey(
        'student.Student',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Student who wrote the review"
    )

    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        help_text="Rating out of 5.0",
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(5.0)
        ]
    )
    review_text = models.TextField(
        help_text="Review content"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Review creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Review update timestamp"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether this review is verified"
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Whether this review is approved for display"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this review is active/visible"
    )
    class Meta:
        verbose_name = 'Academy Review'
        verbose_name_plural = 'Academy Reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['academy', 'is_approved', 'is_active']),
            models.Index(fields=['rating']),
        ]
    def __str__(self):
        return f"{self.academy.name} - {self.student} ({self.rating}★)"
