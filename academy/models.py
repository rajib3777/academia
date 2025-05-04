from django.db import models
from account.models import User
from classmate.models import ClassMateModel
from django.core.exceptions import ValidationError
from account.utils import phone_validator


class Academy(ClassMateModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='academy_logos/', null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    address = models.TextField()
    # city = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15, validators=[phone_validator])
    email = models.EmailField(null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, limit_choices_to={'roles__name': 'academy'})


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


class Batch(ClassMateModel):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name='batches')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.course.name}"

    class Meta:
        verbose_name = 'Batch'
        verbose_name_plural = 'Batchs'
        ordering = ['start_date']

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError('End date cannot be before start date.')