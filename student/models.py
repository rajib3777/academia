from django.db import models
from account.models import User
from academy.models import Batch
from classmate.models import ClassMateModel


class School(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField()
    email = models.EmailField(null=True, blank=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    logo = models.ImageField(upload_to='school_logos/', null=True, blank=True)

    def __str__(self):
        return self.name

class Student(ClassMateModel):
    user = models.OneToOneField(User, on_delete=models.PROTECT, limit_choices_to={'roles__name': 'student'})
    school = models.ForeignKey(School, on_delete=models.PROTECT)
    student_id = models.CharField(max_length=20, unique=True, help_text="Unique ID for the student")
    date_of_birth = models.DateField(null=True, blank=True)
    guardian_name = models.CharField(max_length=255, null=True, blank=True)  
    guardian_phone = models.CharField(max_length=20, null=True, blank=True)
    guardian_email = models.EmailField(null=True, blank=True)
    guardian_relationship = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
        ordering = ['id']
