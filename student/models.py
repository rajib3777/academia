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
    user = models.OneToOneField(User, on_delete=models.PROTECT, limit_choices_to={'role': 'student'})
    school = models.OneToOneField(School, on_delete=models.PROTECT)
    enrollment_date = models.DateField(auto_now_add=True)
    date_of_birth = models.DateField(null=True, blank=True)
    guardian_name = models.CharField(max_length=255, null=True, blank=True)  
    guardian_contact = models.CharField(max_length=20, null=True, blank=True)
    guardian_email = models.EmailField(null=True, blank=True)
    guardian_relationship = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    batches = models.ManyToManyField(Batch, related_name='students')

    def __str__(self):
        return self.user.full_name
