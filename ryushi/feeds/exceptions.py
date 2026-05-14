"""Feed module exceptions.

This module defines exceptions for feed generation, storage, and serving.
"""


class FeedError(Exception):
    """Base exception for feed-related errors.

    Attributes:
        message: Human-readable error description.
        category_slug: Category slug if relevant (optional).
    """

    def __init__(
        self,
        message: str,
        category_slug: str | None = None,
    ):
        """Initialize FeedError.

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


class FeedNotFoundError(FeedError):
    """Raised when a requested feed category does not exist."""

    pass


class FeedStorageError(FeedError):
    """Raised when feed storage operations fail."""

    pass


class FeedGenerationError(FeedError):
    """Raised when feed XML generation fails."""

    pass
