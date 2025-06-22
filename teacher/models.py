from django.db import models
from account.models import User
from academy.models import Batch
from classmate.models import ClassMateModel


class Teacher(ClassMateModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'roles__name': 'teacher'})
    batches = models.ManyToManyField(Batch, related_name='teachers')

    def __str__(self):
        return self.user
