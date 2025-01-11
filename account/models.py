from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, mobile_number, password=None, **extra_fields):
        if not mobile_number:
            raise ValueError("Mobile number is required")
        user = self.model(mobile_number=mobile_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(mobile_number, password, **extra_fields)


class Role(models.Model):
    """Role model to define different roles in the system."""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('staff', 'Staff'),
        ('academy', 'Academy'),
    ]
    name = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(null=True, blank=True)
    roles = models.ManyToManyField(Role, related_name="users")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'mobile_number'
    REQUIRED_FIELDS = ['full_name']

    objects = CustomUserManager()

    def is_teacher(self):
        return self.roles.filter(name="teacher").exists()

    def is_academy_owner(self):
        return self.roles.filter(name="academy").exists()

    def __str__(self):
        return self.full_name
