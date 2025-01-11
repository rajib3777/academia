from django.db import models
from account.models import User
from classmate.models import ClassMateModel


class Academy(ClassMateModel):
    name = models.CharField(max_length=255)
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    email = models.EmailField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'academy'})


    def __str__(self):
        return self.name


class Course(ClassMateModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    academy = models.ForeignKey(Academy, on_delete=models.SET_NULL, null=True, related_name='courses')

    def __str__(self):
        return self.name


class Batch(ClassMateModel):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='batches')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.course.name}"
