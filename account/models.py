from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.db import models
from account.utils import phone_validator

class CustomUserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Mobile number is required")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra_fields)


class Role(models.Model):
    """Role model to define different roles in the system."""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('staff', 'Staff'),
        ('academy', 'Academy'),
    ]
    name = models.CharField(max_length=10, unique=True, choices=ROLE_CHOICES)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom user model that uses phone number as the unique identifier."""
    email = models.EmailField(_("email address"), unique=True, null=True, blank=True)
    roles = models.ManyToManyField(Role, related_name="users")
    phone = models.CharField(_("Mobile number"), max_length=15, unique=True, validators=[phone_validator])
    otp = models.CharField(max_length=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["id"]

    def is_admin(self):
        return self.roles.filter(name="admin").exists()

    def is_teacher(self):
        return self.roles.filter(name="teacher").exists()

    def is_teacher_staff(self):
        return self.roles.filter(name="staff").exists()

    def is_student(self):
        return self.roles.filter(name="student").exists()

    def is_academy_owner(self):
        return self.roles.filter(name="academy").exists()

    def __str__(self):
        return self.username
