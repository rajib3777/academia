from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.db import models
from account.utils import phone_validator
from account.choices import ROLE_CHOICES

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
    name = models.CharField(max_length=10, unique=True, choices=ROLE_CHOICES)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom user model that uses phone number as the unique identifier."""
    email = models.EmailField(_("email address"), unique=True, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
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
        return self.role and self.role.name == "admin"

    def is_student(self):
        return self.role and self.role.name == "student"

    def is_academy_owner(self):
        return self.role and self.role.name == "academy"

    def __str__(self):
        return self.username
