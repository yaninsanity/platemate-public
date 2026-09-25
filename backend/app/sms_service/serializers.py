"""
Serializers for SMS service API endpoints.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import SMSRecord, OTPRecord, SMSTemplate
from .utils import mask_phone_number

User = get_user_model()


# ────────────────────────────────────────────────────────────────
# Model Serializers
# ────────────────────────────────────────────────────────────────

class SMSRecordSerializer(serializers.ModelSerializer):
    """Serializer for SMS records."""

    masked_phone = serializers.SerializerMethodField()
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = SMSRecord
        fields = [
            'id',
            'masked_phone',
            'user_username',
            'message',
            'status',
            'is_read',
            'attempts',
            'error_message',
            'created_at',
            'sent_at',
        ]
        read_only_fields = [
            'id',
            'masked_phone',
            'user_username',
            'status',
            'attempts',
            'error_message',
            'created_at',
            'sent_at',
        ]

    def get_masked_phone(self, obj):
        """Return masked phone number for security."""
        return mask_phone_number(obj.formatted_phone or obj.phone_number)


class OTPRecordSerializer(serializers.ModelSerializer):
    """Serializer for OTP records."""

    masked_phone = serializers.SerializerMethodField()
    user_username = serializers.CharField(source='user.username', read_only=True)
    is_expired = serializers.SerializerMethodField()
    can_attempt = serializers.SerializerMethodField()

    class Meta:
        model = OTPRecord
        fields = [
            'id',
            'masked_phone',
            'user_username',
            'purpose',
            'status',
            'attempts',
            'is_expired',
            'can_attempt',
            'created_at',
            'expires_at',
            'verified_at',
            'last_attempt_at',
        ]
        read_only_fields = [
            'id',
            'masked_phone',
            'user_username',
            'status',
            'attempts',
            'is_expired',
            'can_attempt',
            'created_at',
            'expires_at',
            'verified_at',
            'last_attempt_at',
        ]

    def get_masked_phone(self, obj):
        """Return masked phone number for security."""
        return mask_phone_number(obj.formatted_phone or obj.phone_number)

    def get_is_expired(self, obj):
        """Check if OTP has expired."""
        return obj.is_expired

    def get_can_attempt(self, obj):
        """Check if more verification attempts are allowed."""
        return obj.can_attempt_verification


class SMSTemplateSerializer(serializers.ModelSerializer):
    """Serializer for SMS templates."""

    class Meta:
        model = SMSTemplate
        fields = [
            'id',
            'name',
            'description',
            'template',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ────────────────────────────────────────────────────────────────
# Request/Response Serializers
# ────────────────────────────────────────────────────────────────

class SendSMSRequestSerializer(serializers.Serializer):
    """Serializer for sending SMS requests."""

    phone_number = serializers.CharField(
        max_length=50,
        help_text="Phone number in any format (e.g., 555-123-4567, +1-555-123-4567)"
    )
    message = serializers.CharField(
        max_length=1000,
        help_text="SMS message content"
    )
    user_id = serializers.IntegerField(
        required=False,
        help_text="Optional user ID to associate with this SMS"
    )

    def validate_user_id(self, value):
        """Validate that user exists."""
        if value is not None:
            try:
                User.objects.get(id=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("User does not exist.")
        return value


class SendSMSResponseSerializer(serializers.Serializer):
    """Serializer for SMS sending response."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    sms_record = SMSRecordSerializer(read_only=True)


class SendOTPRequestSerializer(serializers.Serializer):
    """Serializer for sending OTP requests."""

    phone_number = serializers.CharField(
        max_length=50,
        help_text="Phone number in any format"
    )
    purpose = serializers.ChoiceField(
        choices=[
            ('verification', 'Phone Verification'),
            ('login', 'Login'),
            ('password_reset', 'Password Reset'),
            ('test', 'Test'),
        ],
        default='verification',
        help_text="Purpose of the OTP"
    )
    user_id = serializers.IntegerField(
        required=False,
        help_text="Optional user ID to associate with this OTP"
    )
    message_template = serializers.CharField(
        required=False,
        max_length=500,
        help_text="Optional custom message template. Use $OTP for the code."
    )

    def validate_user_id(self, value):
        """Validate that user exists."""
        if value is not None:
            try:
                User.objects.get(id=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("User does not exist.")
        return value


class SendOTPResponseSerializer(serializers.Serializer):
    """Serializer for OTP sending response."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    otp_record = OTPRecordSerializer(read_only=True)


class VerifyOTPRequestSerializer(serializers.Serializer):
    """Serializer for OTP verification requests."""

    phone_number = serializers.CharField(
        max_length=50,
        help_text="Phone number that received the OTP"
    )
    otp_code = serializers.CharField(
        max_length=10,
        min_length=4,
        help_text="The OTP code to verify"
    )
    purpose = serializers.ChoiceField(
        choices=[
            ('verification', 'Phone Verification'),
            ('login', 'Login'),
            ('password_reset', 'Password Reset'),
            ('test', 'Test'),
        ],
        required=False,
        help_text="Purpose to match (for additional security)"
    )
    user_id = serializers.IntegerField(
        required=False,
        help_text="User ID to match (for additional security)"
    )

    def validate_user_id(self, value):
        """Validate that user exists."""
        if value is not None:
            try:
                User.objects.get(id=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("User does not exist.")
        return value


class VerifyOTPResponseSerializer(serializers.Serializer):
    """Serializer for OTP verification response."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    verified = serializers.BooleanField()


class BulkSMSRequestSerializer(serializers.Serializer):
    """Serializer for bulk SMS sending requests."""

    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="List of user IDs to send SMS to"
    )
    message = serializers.CharField(
        max_length=1000,
        help_text="SMS message content"
    )

    def validate_user_ids(self, value):
        """Validate that all users exist and have phone numbers."""
        users = User.objects.filter(id__in=value)

        if len(users) != len(value):
            existing_ids = set(users.values_list('id', flat=True))
            missing_ids = set(value) - existing_ids
            raise serializers.ValidationError(
                f"Users with IDs {list(missing_ids)} do not exist."
            )

        # Check for phone numbers
        users_without_phone = []
        for user in users:
            if not hasattr(user, 'phone') or not user.phone:
                users_without_phone.append(user.username)

        if users_without_phone:
            raise serializers.ValidationError(
                f"Users without phone numbers: {', '.join(users_without_phone)}"
            )

        return value


class BulkSMSResponseSerializer(serializers.Serializer):
    """Serializer for bulk SMS sending response."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    total_sent = serializers.IntegerField()
    total_failed = serializers.IntegerField()
    details = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of individual send results"
    )


# ────────────────────────────────────────────────────────────────
# User Interface Serializers
# ────────────────────────────────────────────────────────────────

class UserSMSHistoryRequestSerializer(serializers.Serializer):
    """Serializer for user SMS history request parameters."""

    status = serializers.ChoiceField(
        choices=['success', 'failed', 'pending'],
        required=False,
        help_text="Filter by SMS status"
    )
    is_read = serializers.BooleanField(
        required=False,
        help_text="Filter by read status"
    )
    search = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Search in message content"
    )


class UserSMSHistoryResponseSerializer(serializers.Serializer):
    """Serializer for user SMS history response."""

    success = serializers.BooleanField()
    data = serializers.DictField()

    def to_representation(self, instance):
        """Custom representation for SMS history response."""
        return {
            'success': True,
            'data': {
                'sms_list': SMSRecordSerializer(instance['sms_list'], many=True).data,
                'summary': {
                    'total_sms': instance['total_count'],
                    'unread_count': instance['unread_count'],
                }
            }
        }


class UnreadCountResponseSerializer(serializers.Serializer):
    """Serializer for unread SMS count response."""

    success = serializers.BooleanField(default=True)
    unread_count = serializers.IntegerField()


class MarkSMSReadResponseSerializer(serializers.Serializer):
    """Serializer for mark SMS read response."""

    success = serializers.BooleanField()
    message = serializers.CharField()


class MarkAllSMSReadResponseSerializer(serializers.Serializer):
    """Serializer for mark all SMS read response."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    count = serializers.IntegerField()

