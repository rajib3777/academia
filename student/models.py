from django.db import models
from account.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
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
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role__name': 'student'}, related_name='student')
    profile_picture = models.ImageField(upload_to='student_profiles/', null=True, blank=True, help_text="Upload a profile picture for the student")
    school = models.ForeignKey(School, on_delete=models.PROTECT)
    student_id = models.CharField(max_length=20, unique=True, help_text="Unique ID for the student", editable=False, null=True, blank=True)
    birth_registration_number = models.CharField(max_length=50, null=True, blank=True, help_text="Unique birth registration number for the student")
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
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['school_id']),
        ]


@receiver(pre_save, sender=Student)
def set_student_id_on_create(sender, instance, **kwargs):
    """
    Signal to auto-generate student_id only when creating a new Student.
    """
    from student.utils import generate_student_id

    if (not instance.pk and not instance.student_id) or (instance.pk and not instance.student_id):
        instance.student_id = generate_student_id()