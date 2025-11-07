from django.db import models
from account.models import User
from classmate.models import ClassMateModel
from django.core.exceptions import ValidationError
from account.utils import phone_validator
from smart_selects.db_fields import ChainedForeignKey
from academy import utils as academy_utils
from django.db.models.signals import pre_save
from django.dispatch import receiver
from utils.models import Division, District, Upazila
from academy.choices_fields import YEAR_CHOICES, COURSE_TYPE_CHOICES, COURSE_TYPE_BANGLA, SLOT_CATEGORY_CHOICES, JAN_JUN

class Academy(ClassMateModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='academy_logos/', null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    contact_number = models.CharField(max_length=15, validators=[phone_validator])
    academy_id = models.CharField(max_length=20, unique=True, help_text="Unique ID for the Academy", editable=False, null=True, blank=True)
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
    course_id = models.CharField(max_length=20, unique=True, help_text="Unique ID for the Course", editable=False, null=True, blank=True)
    course_type = models.CharField(
        max_length=50,
        choices=COURSE_TYPE_CHOICES,
        default=COURSE_TYPE_BANGLA,
        help_text="Subject"
    )

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
    batch_id = models.CharField(max_length=20, unique=True, help_text="Unique ID for the Batch", editable=False, null=True, blank=True)
    students = models.ManyToManyField(
        'student.Student',
        through='BatchEnrollment',
        related_name='enrolled_batches'
    )
    slot_category = models.CharField(
        max_length=20,
        choices=SLOT_CATEGORY_CHOICES,
        default=JAN_JUN,
        help_text='Batch duration slot/category'
    )

    def __str__(self):
        return f"{self.name} - {self.course.name}"

    class Meta:
        verbose_name = 'Batch'
        verbose_name_plural = 'Batches'
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

    # New field for discount fee
    discount_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.0,
        help_text='Discount fee for this student. If null, uses the course default fee.'
    )

    class Meta:
        unique_together = ('student', 'batch')
        verbose_name = "Student Enrollment"
        verbose_name_plural = "Student Enrollments"

    def __str__(self):
        return f"{self.student.user.get_full_name()} in {self.batch}"
    
    @property
    def effective_fee(self):
        """Calculates the effective fee."""
        if self.discount_fee is not None:
            return self.batch.course.fee - self.discount_fee
        return self.batch.course.fee


@receiver(pre_save, sender=Academy)
def set_academy_id_on_create(sender, instance, **kwargs):
    """
    Signal to auto-generate academy_id only when creating a new Academy.
    """
    if (not instance.pk and not instance.academy_id) or (instance.pk and not instance.academy_id):
        instance.academy_id = academy_utils.generate_academy_id()


@receiver(pre_save, sender=Course)
def set_course_id_on_create(sender, instance, **kwargs):
    """
    Signal to auto-generate course_id only when creating a new Course.
    """
    if (not instance.pk and not instance.course_id) or (instance.pk and not instance.course_id):
        instance.course_id = academy_utils.generate_course_id()


@receiver(pre_save, sender=Batch)
def set_batch_id_on_create(sender, instance, **kwargs):
    """
    Signal to auto-generate batch_id only when creating a new Batch.
    """
    if (not instance.pk and not instance.batch_id) or (instance.pk and not instance.batch_id):
        instance.batch_id = academy_utils.generate_batch_id()

