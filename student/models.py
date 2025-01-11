from django.db import models
from account.models import User
from academy.models import Batch
from classmate.models import ClassMateModel


class School(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField()

    def __str__(self):
        return self.name

class Student(ClassMateModel):
    user = models.OneToOneField(User, on_delete=models.PROTECT, limit_choices_to={'role': 'student'})
    school = models.OneToOneField(School, on_delete=models.PROTECT)
    enrollment_date = models.DateField(auto_now_add=True)
    batches = models.ManyToManyField(Batch, related_name='students')

    def __str__(self):
        return self.user.full_name
