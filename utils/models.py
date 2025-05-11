from django.db import models
from django.utils.timezone import now
from datetime import timedelta

from utils.choices import SMS_TYPE_CHOICES, STATUS_CHOICES, OTHER, QUEUE
from utils.constants import BANGLADESH_DISTRICTS, BANGLADESH_DIVISIONS, BANGLADESH_UPAZILAS


class OTPVerification(models.Model):
    phone_number = models.CharField(max_length=14, unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = now() + timedelta(minutes=5)  # OTP valid for 5 minutes
        super().save(*args, **kwargs)

    def is_expired(self):
        if self.expires_at is None:
            return None
        return self.expires_at < now()


class SMSHistory(models.Model):
    phone_number = models.CharField(max_length=15, help_text="Recipient's phone number")
    message = models.TextField(help_text="The content of the SMS")
    sms_type = models.CharField(max_length=20, choices=SMS_TYPE_CHOICES, default=OTHER, help_text="Type of SMS")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=QUEUE, help_text="Delivery status of the SMS")
    sent_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the SMS was sent")
    response_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when the SMS was response")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the record was last updated")
    failed_reason = models.TextField(null=True, blank=True, help_text="Reason for failure if SMS sending failed")
    failed_status_code = models.CharField(max_length=10, null=True, blank=True, help_text="Status code returned when SMS failed")


    def __str__(self):
        return f"{self.sms_type} SMS to {self.phone_number} - {self.status}"

    class Meta:
        verbose_name = "SMS History"
        verbose_name_plural = "SMS Histories"
        ordering = ['-sent_at']


class Division(models.Model):
    name = models.CharField(max_length=100, unique=True, choices=BANGLADESH_DIVISIONS)

    def __str__(self):
        return self.name


class District(models.Model):
    division = models.ForeignKey(Division, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True, choices=BANGLADESH_DISTRICTS)

    def __str__(self):
        return self.name


class Upazila(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True, choices=BANGLADESH_UPAZILAS)

    def __str__(self):
        return self.name
