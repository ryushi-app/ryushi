"""Digest engine exceptions.

This module defines exceptions for digest generation failures.
"""


class DigestError(Exception):
    """Raised when digest generation fails.

    Attributes:
        message: Human-readable error description.
        status_code: HTTP status code if from AI backend (optional).
        model: Model that was being used (optional).
        retry_count: Number of retries attempted (optional).
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        model: str | None = None,
        retry_count: int | None = None,
    ):
        """Initialize DigestError.

        Args:
            message: Human-readable error description.
            status_code: HTTP status code if available.
            model: Model identifier if available.
            retry_count: Number of retries attempted if available.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.model = model
        self.retry_count = retry_count

    def __str__(self) -> str:
        """Return string representation with context."""
        parts = [self.message]
        if self.status_code:
            parts.append(f"status_code={self.status_code}")
        if self.model:
            parts.append(f"model={self.model}")
        if self.retry_count is not None:
            parts.append(f"retries={self.retry_count}")
        return " | ".join(parts)
