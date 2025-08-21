from django.db import models
from account.models import User
from classmate.models import ClassMateModel
from django.core.exceptions import ValidationError
from account.utils import phone_validator
from smart_selects.db_fields import ChainedForeignKey
from utils.models import Division, District, Upazila
from academy.choices_fields import YEAR_CHOICES

class Academy(ClassMateModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='academy_logos/', null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    contact_number = models.CharField(max_length=15, validators=[phone_validator])
    email = models.EmailField(null=True, blank=True)
    # user = models.ForeignKey(User, on_delete=models.PROTECT, limit_choices_to={'role__name': 'academy'}, related_name='academy')
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='academy')
    established_year = models.CharField(max_length=20, null=True, blank=True, default='2025', choices=YEAR_CHOICES)
    # Standard Bangladeshi Address Fields
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)
    district = ChainedForeignKey(
        District,
        chained_field="division",
        chained_model_field="division",
        show_all=False,
        auto_choose=True,
        sort=True,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    upazila = ChainedForeignKey(
        Upazila,
        chained_field="district",
        chained_model_field="district",
        show_all=False,
        auto_choose=True,
        sort=True,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    area_or_union = models.CharField(max_length=100, help_text="Union/Ward/Area")
    street_address = models.CharField(max_length=255, help_text="House/Road/Village")
    postal_code = models.CharField(max_length=10)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Academy'
        verbose_name_plural = 'Academies'
        ordering = ['name']


class Course(ClassMateModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    academy = models.ForeignKey(Academy, on_delete=models.PROTECT, null=True, related_name='courses')

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['academy', 'name'], name='unique_course_name_per_academy')
        ]


class Batch(ClassMateModel):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='batches')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    students = models.ManyToManyField(
        'student.Student',
        through='BatchEnrollment',
        related_name='enrolled_batches'
    )

    def __str__(self):
        return f"{self.name} - {self.course.name}"

    class Meta:
        verbose_name = 'Batch'
        verbose_name_plural = 'Batchs'
        ordering = ['start_date']
        unique_together = ('name', 'course')  # Ensures batch name is unique within a course

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError('End date cannot be before start date.')
        

class Grade(models.Model):
    GRADE_CHOICES = [
        ('A+', 'A+'),
        ('A', 'A'),
        ('A-', 'A-'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('F', 'F'),
    ]

    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, unique=True)

    def __str__(self):
        return self.grade
        

class BatchEnrollment(ClassMateModel):
    student = models.ForeignKey('student.Student', on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)

    enrollment_date = models.DateField(auto_now_add=True)
    completion_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    final_grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'batch')
        verbose_name = "Batch Enrollment"
        verbose_name_plural = "Batch Enrollments"

    def __str__(self):
        return f"{self.student} in {self.batch}"
