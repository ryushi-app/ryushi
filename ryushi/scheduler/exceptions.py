"""Scheduler module exceptions.

This module defines exceptions for job scheduling, execution, and storage.
"""


class SchedulerError(Exception):
    """Base exception for scheduler-related errors.

    Attributes:
        message: Human-readable error description.
        category_slug: Category slug if relevant (optional).
    """

    def __init__(
        self,
        message: str,
        category_slug: str | None = None,
    ):
        """Initialize SchedulerError.

        Args:
            message: Human-readable error description.
            category_slug: Category slug if relevant.
        """
        super().__init__(message)
        self.message = message
        self.category_slug = category_slug

    def __str__(self) -> str:
        """Return string representation with context."""
        if self.category_slug:
            return f"{self.message} | category={self.category_slug}"
        return self.message


class JobNotFoundError(SchedulerError):
    """Raised when a requested job or category does not exist."""

    pass


class JobAlreadyRunningError(SchedulerError):
    """Raised when attempting to start a job that is already running."""

    pass


class JobExecutionError(SchedulerError):
    """Raised when job execution fails."""

    pass


class ConfigurationError(SchedulerError):
    """Raised when scheduler configuration is invalid."""

    pass
