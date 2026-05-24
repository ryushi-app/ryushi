"""Exceptions for GitHub integration."""


class GistPublishError(Exception):
    """Raised when publishing to a GitHub Gist fails."""

    def __init__(self, message: str, gist_id: str | None = None, status_code: int | None = None):
        """Initialize the error.

        Args:
            message: Error message.
            gist_id: GitHub Gist ID if available.
            status_code: HTTP status code if available.
        """
        self.message = message
        self.gist_id = gist_id
        self.status_code = status_code
        super().__init__(message)
