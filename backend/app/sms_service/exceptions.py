"""
Custom exceptions for SMS service.
"""


class SMSServiceError(Exception):
    """Base exception for SMS service"""
    pass


class InvalidPhoneNumberError(SMSServiceError):
    """Raised when phone number format is invalid"""
    pass


class SMSSendError(SMSServiceError):
    """Raised when SMS sending fails"""
    pass


class OTPGenerationError(SMSServiceError):
    """Raised when OTP generation fails"""
    pass


class OTPVerificationError(SMSServiceError):
    """Raised when OTP verification fails"""
    pass


class OTPExpiredError(OTPVerificationError):
    """Raised when OTP has expired"""
    pass


class OTPMaxAttemptsError(OTPVerificationError):
    """Raised when maximum OTP verification attempts exceeded"""
    pass


class TextbeltAPIError(SMSServiceError):
    """Raised when Textbelt API returns an error"""
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response

