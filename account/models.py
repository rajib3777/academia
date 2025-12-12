from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.db import models
from datetime import timedelta
from django.utils import timezone
from account.utils import phone_validator
from account.choices import ROLE_CHOICES, STUDENT, ACADEMY, ADMIN, RECOVERY_OTP_STATUS_CHOICES, NOT_USED, USED, BLOCKED

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
    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True)
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
        return self.role and self.role.name == ADMIN

    def is_student(self):
        return self.role and self.role.name == STUDENT

    def is_academy(self):
        return self.role and self.role.name == ACADEMY

    def __str__(self):
        return self.username


class Permission(models.Model):
    """Defines a single permission action."""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Menu(models.Model):
    """Represents a menu or submenu in the frontend."""
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='submenus', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, help_text="Order for menu/submenu display")
    remarks = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['name', 'order']

    def __str__(self):
        if self.remarks:
            return f"{self.name} ({self.remarks})"
        else:
            return f"{self.name}"

class RoleMenuPermission(models.Model):
    """Maps a role to menu and its allowed permissions."""
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    permissions = models.ManyToManyField(Permission, blank=True)
    remarks = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('role', 'menu')

    def __str__(self):
        return f"{self.role.name} - {self.menu.name}"
  

class RecoveryOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recovery_otps")
    code = models.IntegerField()  # stores 6-digit numeric OTP
    phone = models.CharField(max_length=15, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=RECOVERY_OTP_STATUS_CHOICES, default=NOT_USED)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_recovery_otps")

    def is_valid(self):
        return (self.status == NOT_USED) and (timezone.now() < self.expires_at)

    def mark_used(self):
        self.status = USED
        self.save()
    
    def mark_not_used(self):
        self.status = NOT_USED
        self.save()
    
    def mark_blocked(self):
        self.status = BLOCKED
        self.save()

    def __str__(self):
        status = "Used" if self.status == USED else "Valid"
        return f"OTP {self.code} ({status}) for {self.user.username}"

