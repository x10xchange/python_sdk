"""
Custom exceptions for Extended Exchange SDK.

Follows the Hyperliquid/Pacifica error handling pattern.
"""

from typing import Any, Dict, Optional


class ExtendedError(Exception):
    """Base exception for Extended SDK."""

    pass


class ExtendedAPIError(ExtendedError):
    """
    API error with status code and message.

    Raised when the Extended API returns an error response.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        response: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.response = response
        super().__init__(f"[{status_code}] {message}")


class ExtendedAuthError(ExtendedError):
    """
    Authentication error.

    Raised when authentication fails (invalid API key, invalid signature, etc.).
    """

    pass


class ExtendedRateLimitError(ExtendedAPIError):
    """
    Rate limit exceeded (HTTP 429).

    Raised when the API rate limit is exceeded.
    Note: Following Hyperliquid/Pacifica pattern, we do NOT implement
    automatic retry. The caller is responsible for handling this.
    """

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(429, message)


class ExtendedValidationError(ExtendedError):
    """
    Validation error for request parameters.

    Raised when request parameters fail validation before being sent to the API.
    """

    pass


class ExtendedNotFoundError(ExtendedAPIError):
    """
    Resource not found error (HTTP 404).

    Raised when a requested resource (order, position, etc.) is not found.
    """

    def __init__(self, message: str = "Resource not found"):
        super().__init__(404, message)
