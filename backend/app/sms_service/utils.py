"""
Utility functions for SMS service.
"""

import re
import logging
from typing import Optional

from .exceptions import InvalidPhoneNumberError

logger = logging.getLogger(__name__)


def format_north_american_phone(phone_number: str) -> str:
    """
    Format phone number to North American format (+1XXXXXXXXXX).

    Args:
        phone_number: Input phone number in various formats

    Returns:
        Formatted phone number (+1XXXXXXXXXX)

    Raises:
        InvalidPhoneNumberError: If phone number format is invalid

    Examples:
        "+1 (555) 123-4567" -> "+15551234567"
        "555-123-4567" -> "+15551234567"
        "(555) 123 4567" -> "+15551234567"
        "15551234567" -> "+15551234567"
    """
    if not phone_number:
        raise InvalidPhoneNumberError("Phone number cannot be empty")

    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone_number.strip())

    # Extract digits only
    digits = re.sub(r'[^\d]', '', cleaned)

    # Handle different cases
    if len(digits) == 10:
        # Missing country code, add +1
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith('1'):
        # Has country code 1
        return f"+{digits}"
    elif cleaned.startswith('+1') and len(digits) == 11:
        # Already properly formatted
        return f"+{digits}"
    else:
        # Invalid format
        raise InvalidPhoneNumberError(
            f"Invalid phone number format: {phone_number}. "
            "Expected 10 or 11 digits for North American numbers."
        )


def should_retry_error(error_msg: str, status_code: Optional[int]) -> bool:
    """
    Determine if an error should trigger a retry.

    Args:
        error_msg: Error message from the API
        status_code: HTTP status code

    Returns:
        True if should retry, False otherwise
    """
    # Network/server errors that should be retried
    if status_code is None or status_code >= 500:
        return True

    if status_code in [408, 429, 502, 503, 504]:  # Timeout, rate limit, gateway errors
        return True

    # Textbelt specific errors that might be temporary
    retry_errors = [
        'rate limit',
        'temporary',
        'server error',
        'timeout',
        'network',
        'connection',
    ]

    if error_msg:
        error_lower = error_msg.lower()
        for retry_error in retry_errors:
            if retry_error in error_lower:
                return True

    return False


def mask_phone_number(phone_number: str) -> str:
    """
    Mask phone number for logging/display purposes.

    Args:
        phone_number: Phone number to mask

    Returns:
        Masked phone number (e.g., +1555***4567)
    """
    if not phone_number or len(phone_number) < 8:
        return phone_number

    # Keep first 5 and last 4 characters
    # return f"{phone_number[:5]}***{phone_number[-4:]}"
    return phone_number


def get_client_ip(request) -> Optional[str]:
    """
    Get client IP address from Django request.

    Args:
        request: Django request object

    Returns:
        Client IP address or None
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

