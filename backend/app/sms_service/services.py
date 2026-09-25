"""
Core SMS and OTP services using Textbelt API.
"""

import logging
import time
import requests
from typing import Optional, Dict, Any, Tuple
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

from .models import SMSRecord, OTPRecord
from .exceptions import (
    SMSServiceError, SMSSendError, OTPGenerationError,
    OTPVerificationError, OTPExpiredError, OTPMaxAttemptsError,
    TextbeltAPIError, InvalidPhoneNumberError
)
from .utils import format_north_american_phone, should_retry_error, mask_phone_number

User = get_user_model()
logger = logging.getLogger(__name__)


class SMSService:
    """Service for sending SMS messages."""

    def __init__(self):
        self.api_key = getattr(settings, 'TEXTBELT_API_KEY', None)
        if not self.api_key:
            raise SMSServiceError("TEXTBELT_API_KEY not configured in settings")

        self.max_retries = getattr(settings, 'SMS_MAX_RETRIES', 3)
        self.retry_delay = getattr(settings, 'SMS_RETRY_DELAY', 1.0)
        self.base_url = "https://textbelt.com"

    def send_sms(
        self,
        phone_number: str,
        message: str,
        user: Optional[User] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SMSRecord:
        """
        Send an SMS message and record it in the database.

        Args:
            phone_number: Recipient phone number
            message: SMS message content
            user: Optional user who triggered the SMS
            ip_address: Optional IP address of the request
            user_agent: Optional user agent of the request

        Returns:
            SMSRecord instance

        Raises:
            InvalidPhoneNumberError: If phone number format is invalid
            SMSSendError: If SMS sending fails after all retries
        """
        # Format phone number
        try:
            formatted_phone = format_north_american_phone(phone_number)
        except InvalidPhoneNumberError as e:
            logger.error(f"Invalid phone number: {phone_number}")
            # Still create a failed record
            record = SMSRecord.objects.create(
                user=user,
                phone_number=phone_number,
                formatted_phone="",
                message=message,
                status='failed',
                error_message=str(e),
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise

        # Create SMS record
        record = SMSRecord.objects.create(
            user=user,
            phone_number=phone_number,
            formatted_phone=formatted_phone,
            message=message,
            status='pending',
            ip_address=ip_address,
            user_agent=user_agent
        )

        logger.info(f"Sending SMS to {mask_phone_number(formatted_phone)} (Record ID: {record.id})")

        # Attempt to send SMS with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._send_sms_request(formatted_phone, message)
                result = self._parse_response(response)

                # Update record with response
                record.textbelt_response = result
                record.attempts = attempt + 1
                record.save(update_fields=['textbelt_response', 'attempts'])

                if result.get('success'):
                    record.mark_as_sent()
                    logger.info(f"SMS sent successfully to {mask_phone_number(formatted_phone)} "
                               f"after {attempt + 1} attempts")
                    return record

                # Handle failure
                error_msg = result.get('error', 'Unknown error')
                last_error = error_msg

                if attempt < self.max_retries and should_retry_error(error_msg, response.status_code):
                    logger.warning(f"SMS attempt {attempt + 1} failed, retrying: {error_msg}")
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    record.mark_as_failed(error_msg)
                    raise SMSSendError(f"SMS sending failed: {error_msg}")

            except requests.RequestException as e:
                last_error = str(e)
                logger.exception(f"Request exception on attempt {attempt + 1}")

                if attempt < self.max_retries and should_retry_error(last_error, None):
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    record.mark_as_failed(last_error)
                    record.attempts = attempt + 1
                    record.save(update_fields=['attempts'])
                    raise SMSSendError(f"SMS sending failed: {last_error}")

        # Should not reach here, but just in case
        record.mark_as_failed(last_error or "Maximum retries exceeded")
        record.attempts = self.max_retries + 1
        record.save(update_fields=['attempts'])
        raise SMSSendError(f"SMS sending failed after {self.max_retries + 1} attempts")

    def _send_sms_request(self, phone: str, message: str) -> requests.Response:
        """Make HTTP request to Textbelt SMS API."""
        url = f"{self.base_url}/text"
        payload = {
            "phone": phone,
            "message": message,
            "key": self.api_key,
        }
        return requests.post(url, data=payload, timeout=10)

    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse API response."""
        try:
            return response.json()
        except ValueError:
            return {
                'success': False,
                'error': f'Invalid JSON response: {response.text}',
                'status_code': response.status_code
            }


    def notify_couple_partner(self, user, message):
        # Get the couple
        couple = user.couple
        if not couple:
            raise ValueError("The user is not part of a couple.")

        # Find the other user in the couple
        partner = next((member for member in couple.members.all() if member != user), None)
        if not partner:
            raise ValueError("The other user in the couple could not be found.")

        # Check if the partner has a phone number
        if not partner.phone:
            raise ValueError(f"The partner ({partner.username}) does not have a phone number.")

        # Send the SMS
        return self.send_sms(phone_number=partner.phone, message=message, user=user)


class OTPService:
    """Service for OTP generation and verification."""

    def __init__(self):
        self.api_key = getattr(settings, 'TEXTBELT_API_KEY', None)
        if not self.api_key:
            raise SMSServiceError("TEXTBELT_API_KEY not configured in settings")

        self.base_url = "https://textbelt.com"
        self.expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
        self.max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 3)

    @transaction.atomic
    def send_otp(
        self,
        phone_number: str,
        purpose: str = 'verification',
        user: Optional[User] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        message_template: Optional[str] = None,
        otp_length: int = 6
    ) -> OTPRecord:
        """
        Generate and send an OTP to the specified phone number.

        Args:
            phone_number: Recipient phone number
            purpose: Purpose of OTP (login, registration, password_reset, etc.)
            user: Optional user who requested the OTP
            ip_address: Optional IP address of the request
            user_agent: Optional user agent of the request
            message_template: Optional custom message template (use $OTP for the code)
            otp_length: Length of OTP code (default 6)

        Returns:
            OTPRecord instance

        Raises:
            InvalidPhoneNumberError: If phone number format is invalid
            OTPGenerationError: If OTP generation fails
        """
        # Format phone number
        formatted_phone = format_north_american_phone(phone_number)

        # Check for existing pending OTPs for this phone/user
        self._invalidate_previous_otps(phone_number, user)

        # Generate a unique userid for this OTP session
        # Using formatted phone + timestamp to ensure uniqueness
        import uuid
        userid = f"{formatted_phone}_{uuid.uuid4().hex[:8]}"

        logger.info(f"Generating OTP for {mask_phone_number(formatted_phone)} "
                   f"(Purpose: {purpose})")

        # Prepare request
        url = f"{self.base_url}/otp/generate"
        payload = {
            "phone": formatted_phone,
            "userid": userid,
            "key": self.api_key,
            "lifetime": self.expiry_minutes * 60,  # Convert to seconds
            "length": otp_length
        }

        # Add custom message if provided
        if message_template:
            payload["message"] = message_template

        try:
            response = requests.post(url, data=payload, timeout=10)
            result = response.json() if response.status_code == 200 else {
                'success': False,
                'error': f'HTTP {response.status_code}: {response.text}'
            }
        except requests.RequestException as e:
            logger.exception("Failed to generate OTP")
            raise OTPGenerationError(f"Failed to generate OTP: {str(e)}")

        # Create OTP record - store userid in otp_id field
        record = OTPRecord.objects.create(
            user=user,
            phone_number=phone_number,
            formatted_phone=formatted_phone,
            purpose=purpose,
            otp_id=userid,  # Store the userid we generated
            generation_response=result,
            ip_address=ip_address,
            user_agent=user_agent,
            status='pending' if result.get('success') else 'failed'
        )

        if not result.get('success'):
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"OTP generation failed: {error_msg}")
            raise OTPGenerationError(f"Failed to generate OTP: {error_msg}")

        # Log success (don't log the actual OTP for security)
        logger.info(f"OTP generated successfully for {mask_phone_number(formatted_phone)} "
                   f"(UserID: {userid}, TextID: {result.get('textId')})")
        return record

    def verify_otp(
        self,
        phone_number: str,
        otp_code: str,
        purpose: Optional[str] = None,
        user: Optional[User] = None
    ) -> Tuple[bool, str]:
        """
        Verify an OTP code.

        Args:
            phone_number: Phone number that received the OTP
            otp_code: The OTP code to verify
            purpose: Optional purpose to match (for additional security)
            user: Optional user to match (for additional security)

        Returns:
            Tuple of (success: bool, message: str)

        Raises:
            OTPVerificationError: If verification fails
            OTPExpiredError: If OTP has expired
            OTPMaxAttemptsError: If max attempts exceeded
        """
        # Format phone number
        formatted_phone = format_north_american_phone(phone_number)

        # Find the most recent pending OTP for this phone
        otp_record = OTPRecord.objects.filter(
            formatted_phone=formatted_phone,
            status='pending'
        ).order_by('-created_at').first()

        if not otp_record:
            logger.warning(f"No pending OTP found for {mask_phone_number(formatted_phone)}")
            raise OTPVerificationError("No pending OTP found for this phone number")

        # Additional security checks
        if purpose and otp_record.purpose != purpose:
            raise OTPVerificationError("OTP purpose mismatch")

        if user and otp_record.user != user:
            raise OTPVerificationError("OTP user mismatch")

        # Check if OTP is expired
        if otp_record.is_expired:
            otp_record.mark_as_expired()
            raise OTPExpiredError("OTP has expired")

        # Check max attempts
        if not otp_record.can_attempt_verification:
            raise OTPMaxAttemptsError("Maximum verification attempts exceeded")

        # Increment attempts
        otp_record.increment_attempts()

        logger.info(f"Verifying OTP for {mask_phone_number(formatted_phone)} "
                   f"(Attempt {otp_record.attempts}/{self.max_attempts})")

        # Make verification request - using GET as per documentation
        url = f"{self.base_url}/otp/verify"
        params = {
            "otp": otp_code,
            "userid": otp_record.otp_id,  # This is the userid we stored
            "key": self.api_key,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json() if response.status_code == 200 else {
                'success': False,
                'error': f'HTTP {response.status_code}: {response.text}'
            }
        except requests.RequestException as e:
            logger.exception("Failed to verify OTP")
            raise OTPVerificationError(f"Failed to verify OTP: {str(e)}")

        # Update verification responses
        responses = otp_record.verification_responses
        responses.append({
            'timestamp': timezone.localtime(timezone.now()).isoformat(),
            'result': result,
            'attempt': otp_record.attempts
        })
        otp_record.verification_responses = responses
        otp_record.save(update_fields=['verification_responses'])

        # Check if the request was successful first
        if not result.get('success'):
            error_msg = result.get('error', 'API request failed')
            logger.error(f"OTP verification API error: {error_msg}")
            raise OTPVerificationError(f"Verification failed: {error_msg}")

        # Now check if the OTP is valid
        if result.get('isValidOtp'):
            otp_record.mark_as_verified()
            logger.info(f"OTP verified successfully for {mask_phone_number(formatted_phone)}")
            return True, "OTP verified successfully"
        else:
            logger.warning(f"Invalid OTP code for {mask_phone_number(formatted_phone)}")

            # Check if we've hit max attempts after this failure
            if otp_record.attempts >= self.max_attempts:
                otp_record.status = 'max_attempts'
                otp_record.save(update_fields=['status'])
                raise OTPMaxAttemptsError("Maximum verification attempts exceeded")

            return False, "Invalid OTP code"

    def _invalidate_previous_otps(self, phone_number: str, user: Optional[User] = None):
        """Invalidate any pending OTPs for the given phone/user."""
        formatted_phone = format_north_american_phone(phone_number)

        # Find pending OTPs
        query = OTPRecord.objects.filter(
            formatted_phone=formatted_phone,
            status='pending'
        )

        if user:
            query = query.filter(user=user)

        # Mark them as expired
        count = query.update(status='expired')
        if count > 0:
            logger.info(f"Invalidated {count} pending OTPs for {mask_phone_number(formatted_phone)}")


# Convenience functions for simple usage
_sms_service = None
_otp_service = None


def get_sms_service() -> SMSService:
    """Get or create SMS service singleton."""
    global _sms_service
    if _sms_service is None:
        _sms_service = SMSService()
    return _sms_service


def get_otp_service() -> OTPService:
    """Get or create OTP service singleton."""
    global _otp_service
    if _otp_service is None:
        _otp_service = OTPService()
    return _otp_service


def send_sms(phone_number: str, message: str, user: Optional[User] = None) -> bool:
    """
    Convenience function to send SMS.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        service = get_sms_service()
        record = service.send_sms(phone_number, message, user)
        return record.status == 'success'
    except Exception as e:
        logger.error(f"Failed to send SMS: {str(e)}")
        return False


def send_otp(phone_number: str, purpose: str = 'verification',
             user: Optional[User] = None) -> bool:
    """
    Convenience function to send OTP.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        service = get_otp_service()
        record = service.send_otp(phone_number, purpose, user)
        return record.status == 'pending'
    except Exception as e:
        logger.error(f"Failed to send OTP: {str(e)}")
        return False


def verify_otp(phone_number: str, otp_code: str,
               purpose: Optional[str] = None,
               user: Optional[User] = None) -> bool:
    """
    Convenience function to verify OTP.

    Returns:
        bool: True if verified successfully, False otherwise
    """
    try:
        service = get_otp_service()
        success, message = service.verify_otp(phone_number, otp_code, purpose, user)
        return success
    except Exception as e:
        logger.error(f"Failed to verify OTP: {str(e)}")
        return False

