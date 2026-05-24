"""GitHub API client for publishing Gists."""

import logging
import os

import httpx

from .exceptions import GistPublishError

logger = logging.getLogger(__name__)

# GitHub API base URL
GITHUB_API_BASE = "https://api.github.com"


class GistPublisher:
    """Client for publishing Atom feeds to GitHub Gists.

    Uses the GitHub REST API v3 to update Gist content.
    """

    def __init__(self, timeout: float = 30.0):
        """Initialize the Gist publisher.

        Reads GITHUB_TOKEN from environment variables for authentication.

        Args:
            timeout: Request timeout in seconds (default 30).
        """
        self._token = os.environ.get("GITHUB_TOKEN")
        self._timeout = timeout

    @property
    def is_configured(self) -> bool:
        """Check if GitHub token is available.

        Returns:
            True if GITHUB_TOKEN is set, False otherwise.
        """
        return self._token is not None

    async def publish(self, gist_id: str, filename: str, content: str) -> None:
        """Publish content to a GitHub Gist.

        Updates an existing Gist file with new content using PATCH /gists/{gist_id}.
        Gracefully handles errors - logs warnings instead of raising exceptions.

        Args:
            gist_id: GitHub Gist ID (e.g., "abc123def456").
            filename: Filename in the Gist (e.g., "technology.atom.xml").
            content: File content to publish.
        """
        if not self.is_configured:
            logger.warning(
                "GitHub token not configured (GITHUB_TOKEN env var missing), skipping Gist publish"
            )
            return

        try:
            await self._update_gist(gist_id, filename, content)
            logger.debug("Successfully published to Gist %s", gist_id)
        except GistPublishError as e:
            logger.warning("Failed to publish to Gist %s: %s", gist_id, e.message)
        except Exception as e:
            logger.warning("Unexpected error publishing to Gist %s: %s", gist_id, str(e))

    async def _update_gist(self, gist_id: str, filename: str, content: str) -> None:
        """Update a Gist file via GitHub API.

        Args:
            gist_id: GitHub Gist ID.
            filename: Filename in the Gist.
            content: File content.

        Raises:
            GistPublishError: If the update fails.
        """
        url = f"{GITHUB_API_BASE}/gists/{gist_id}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # GitHub Gist PATCH payload structure
        payload = {
            "files": {
                filename: {
                    "content": content,
                }
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.patch(url, json=payload, headers=headers)

                if response.status_code == 401:
                    raise GistPublishError(
                        "GitHub authentication failed (invalid or expired token)",
                        gist_id=gist_id,
                        status_code=401,
                    )
                elif response.status_code == 404:
                    raise GistPublishError(
                        f"Gist not found (ID: {gist_id})",
                        gist_id=gist_id,
                        status_code=404,
                    )
                elif response.status_code == 403:
                    # Could be rate limit or permission issue
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            raise GistPublishError(
                                f"GitHub API error: {error_data['message']}",
                                gist_id=gist_id,
                                status_code=403,
                            )
                    except Exception:
                        pass
                    raise GistPublishError(
                        "GitHub API forbidden (rate limited or insufficient permissions)",
                        gist_id=gist_id,
                        status_code=403,
                    )
                elif response.status_code >= 500:
                    raise GistPublishError(
                        f"GitHub API server error ({response.status_code})",
                        gist_id=gist_id,
                        status_code=response.status_code,
                    )
                elif response.status_code >= 400:
                    raise GistPublishError(
                        f"GitHub API error ({response.status_code}): {response.text[:200]}",
                        gist_id=gist_id,
                        status_code=response.status_code,
                    )

                if response.status_code not in (200, 201):
                    raise GistPublishError(
                        f"Unexpected response status {response.status_code}",
                        gist_id=gist_id,
                        status_code=response.status_code,
                    )

        except httpx.TimeoutException as e:
            raise GistPublishError(
                f"Request timeout: {str(e)}",
                gist_id=gist_id,
            ) from e
        except httpx.RequestError as e:
            raise GistPublishError(
                f"Network error: {str(e)}",
                gist_id=gist_id,
            ) from e
