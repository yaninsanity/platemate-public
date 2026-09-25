"""
Database models for SMS service.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

User = get_user_model()


class SMSRecord(models.Model):
    """Record of SMS messages sent through the system."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    # User information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_records',
        help_text="User who triggered the SMS"
    )

    # Phone information
    phone_number = models.CharField(
        max_length=50,
        help_text="Original phone number provided"
    )
    formatted_phone = models.CharField(
        max_length=20,
        help_text="Formatted phone number used for sending"
    )

    # Message content
    message = models.TextField(help_text="SMS message content")

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if sending failed"
    )

    # Notification tracking
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the user has read/acknowledged this SMS notification"
    )

    # Textbelt response
    textbelt_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw response from Textbelt API"
    )

    # Retry information
    attempts = models.IntegerField(default=1)

    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the request"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text="User agent of the request"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when SMS was successfully sent"
    )

    class Meta:
        db_table = 'sms_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['phone_number', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"SMS to {self.phone_number} - {self.status}"

    def mark_as_sent(self):
        """Mark the SMS as successfully sent."""
        self.status = 'success'
        self.sent_at = timezone.localtime(timezone.now())
        self.save(update_fields=['status', 'sent_at'])

    def mark_as_failed(self, error_message):
        """Mark the SMS as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])

    def mark_as_read(self):
        """Mark the SMS as read by the user."""
        self.is_read = True
        self.save(update_fields=['is_read'])

    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread SMS for a user."""
        return cls.objects.filter(
            user=user,
            status='success',
            is_read=False
        ).count()


class OTPRecord(models.Model):
    """Record of OTP (One-Time Password) verifications."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('expired', 'Expired'),
        ('failed', 'Failed'),
        ('max_attempts', 'Max Attempts Exceeded'),
    ]

    # User information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_otp_records',
        help_text="User who requested the OTP"
    )

    # Phone information
    phone_number = models.CharField(
        max_length=50,
        help_text="Original phone number provided"
    )
    formatted_phone = models.CharField(
        max_length=20,
        help_text="Formatted phone number used for sending"
    )

    # OTP information
    otp_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique user ID for this OTP session (used for verification)"
    )
    purpose = models.CharField(
        max_length=50,
        default='verification',
        help_text="Purpose of OTP (e.g., login, registration, password_reset)"
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    attempts = models.IntegerField(
        default=0,
        help_text="Number of verification attempts"
    )

    # Textbelt responses
    generation_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Response from OTP generation"
    )
    verification_responses = models.JSONField(
        default=list,
        help_text="List of verification attempt responses"
    )

    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the request"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text="User agent of the request"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="OTP expiration time"
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when OTP was successfully verified"
    )
    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last verification attempt"
    )

    class Meta:
        db_table = 'sms_otp_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['otp_id']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['phone_number', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"OTP for {self.phone_number} - {self.status}"

    def save(self, *args, **kwargs):
        """Override save to set expiration time on creation."""
        if not self.pk and not self.expires_at:
            expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
            self.expires_at = timezone.localtime(timezone.now()) + timezone.timedelta(minutes=expiry_minutes)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if OTP has expired."""
        if not self.expires_at:
            return False
        return timezone.localtime(timezone.now()) > self.expires_at

    @property
    def can_attempt_verification(self):
        """Check if more verification attempts are allowed."""
        max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 3)
        return self.attempts < max_attempts and not self.is_expired

    def increment_attempts(self):
        """Increment verification attempts."""
        self.attempts += 1
        self.last_attempt_at = timezone.localtime(timezone.now())

        max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 3)
        if self.attempts >= max_attempts:
            self.status = 'max_attempts'

        self.save(update_fields=['attempts', 'last_attempt_at', 'status'])

    def mark_as_verified(self):
        """Mark OTP as successfully verified."""
        self.status = 'verified'
        self.verified_at = timezone.localtime(timezone.now())
        self.save(update_fields=['status', 'verified_at'])

    def mark_as_expired(self):
        """Mark OTP as expired."""
        self.status = 'expired'
        self.save(update_fields=['status'])


class SMSTemplate(models.Model):
    """Optional: Predefined SMS templates for common messages."""

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Template identifier"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of when to use this template"
    )
    template = models.TextField(
        help_text="Message template with {variable} placeholders"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sms_templates'
        ordering = ['name']

    def __str__(self):
        return self.name

