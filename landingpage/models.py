from django.db import models
from academy.choices_fields import SUBJECT_TYPE_CHOICES, YEAR_CHOICES
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


class TeacherSubject(models.Model):
    """
    Subjects taught by a teacher
    """
    teacher = models.ForeignKey(
        'teacher.Teacher',
        on_delete=models.CASCADE,
        related_name='subjects'
    )
    subject = models.CharField(
        max_length=100,
        choices=SUBJECT_TYPE_CHOICES,
        help_text="Subject taught"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is the teacher's primary subject"
    )
    
    class Meta:
        verbose_name = 'Teacher Subject'
        verbose_name_plural = 'Teacher Subjects'
        unique_together = ('teacher', 'subject')
        ordering = ['-is_primary', 'subject']
    
    def __str__(self):
        return f"{self.teacher.full_name} - {self.get_subject_display()}"


class TeacherEducation(models.Model):
    """
    Teacher's educational qualifications
    """
    teacher = models.ForeignKey(
        'teacher.Teacher',
        on_delete=models.CASCADE,
        related_name='educations'
    )
    degree = models.CharField(
        max_length=255,
        help_text="Degree name (e.g., Ph.D. in Physics, M.Sc. in Chemistry)"
    )
    institution = models.CharField(
        max_length=255,
        help_text="Institution name (e.g., Stanford University)"
    )
    year = models.CharField(
        max_length=4,
        null=True,
        blank=True,
        choices=YEAR_CHOICES,
        help_text="Graduation year (e.g., 2025)"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    
    class Meta:
        verbose_name = 'Teacher Education'
        verbose_name_plural = 'Teacher Educations'
        ordering = ['order', '-year']
    
    def __str__(self):
        return f"{self.teacher.full_name} - {self.degree}"


class TeacherAchievement(models.Model):
    """
    Teacher's achievements and awards
    """
    teacher = models.ForeignKey(
        'teacher.Teacher',
        on_delete=models.CASCADE,
        related_name='achievements'
    )
    title = models.CharField(
        max_length=255,
        help_text="Achievement title (e.g., Science Educator of the Year 2022)"
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Achievement description"
    )
    year = models.CharField(
        max_length=4,
        null=True,
        blank=True,
        choices=YEAR_CHOICES,
        help_text="Year received"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    
    class Meta:
        verbose_name = 'Teacher Achievement'
        verbose_name_plural = 'Teacher Achievements'
        ordering = ['order', '-year']
    
    def __str__(self):
        return f"{self.teacher.full_name} - {self.title}"


class TeacherReview(models.Model):
    """
    Student reviews for teachers
    """
    teacher = models.ForeignKey(
        'teacher.Teacher',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    student = models.ForeignKey(
        'student.Student',
        on_delete=models.CASCADE,
        related_name='teacher_reviews',
        null=True,
        blank=True
    )
    student_name = models.CharField(
        max_length=255,
        help_text="Student name for display"
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )
    review_text = models.TextField(
        help_text="Review content"
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Whether review is approved by admin"
    )
    reviewed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Review submission date"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this review is active/visible"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Review creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Review update timestamp"
    )
    
    class Meta:
        verbose_name = 'Teacher Review'
        verbose_name_plural = 'Teacher Reviews'
        ordering = ['-reviewed_at']
        unique_together = ('teacher', 'student')
    
    def __str__(self):
        return f"{self.student_name} - {self.teacher.full_name} ({self.rating}★)"
