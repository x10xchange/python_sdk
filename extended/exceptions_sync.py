"""
Simple sync exceptions for Extended Exchange SDK.

Minimal exception classes to avoid dependencies.
"""


class ExtendedError(Exception):
    """Base exception for Extended SDK."""
    pass


class ExtendedAPIError(ExtendedError):
    """API-related errors."""
    def __init__(self, status_code: int, message: str, data=None):
        self.status_code = status_code
        self.message = message
        self.data = data
        super().__init__(message)


class ExtendedAuthError(ExtendedError):
    """Authentication-related errors."""
    pass


class ExtendedRateLimitError(ExtendedError):
    """Rate limiting errors."""
    pass


class ExtendedValidationError(ExtendedError):
    """Validation errors."""
    pass


class ExtendedNotFoundError(ExtendedError):
    """Not found errors."""
    pass