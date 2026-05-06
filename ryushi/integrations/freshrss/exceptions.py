"""FreshRSS client exceptions.

This module defines typed exceptions for different failure scenarios
when interacting with FreshRSS servers.
"""


class FreshRSSError(Exception):
    """Base exception for all FreshRSS errors."""

    pass


class AuthError(FreshRSSError):
    """Raised when authentication with FreshRSS fails.

    This includes invalid credentials, missing environment variables,
    or persistent 401 responses after token refresh attempts.
    """

    pass


class FetchError(FreshRSSError):
    """Raised when fetching data from FreshRSS fails.

    This includes network timeouts, 5xx server errors, and other
    non-auth-related failures.
    """

    def __init__(self, message: str, status_code: int | None = None, url: str | None = None):
        """Initialize FetchError with optional status code and URL.

        Args:
            message: Human-readable error description.
            status_code: HTTP status code if available.
            url: Request URL (with credentials redacted).
        """
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class RateLimitError(FreshRSSError):
    """Raised when FreshRSS returns HTTP 429 Too Many Requests.

    Callers should implement backoff/retry logic when catching this error.
    """

    pass
