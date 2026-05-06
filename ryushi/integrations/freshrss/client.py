"""FreshRSS API client.

This module provides an async client for interacting with FreshRSS servers
via the Google Reader API.
"""

import html
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from .exceptions import AuthError, FetchError, RateLimitError
from .models import Article, Category

logger = logging.getLogger(__name__)

# Default timeout for HTTP requests (seconds)
DEFAULT_TIMEOUT = 30.0

# Default limit for articles per request
DEFAULT_PAGE_SIZE = 50

# Default maximum articles to return
DEFAULT_MAX_ARTICLES = 100

# Maximum teaser length
MAX_TEASER_LENGTH = 500


class FreshRSSClient:
    """Async client for FreshRSS API.

    Uses the Google Reader API for authentication and data fetching.
    Credentials are read from environment variables:
    - FRESHRSS_URL: Base URL of the FreshRSS instance
    - FRESHRSS_USERNAME: Username for authentication
    - FRESHRSS_PASSWORD: Password for authentication

    Example:
        client = FreshRSSClient()
        categories = await client.get_categories()
        articles = await client.get_unread_items(category_id="user/-/label/Tech")
    """

    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize FreshRSS client.

        Args:
            url: FreshRSS base URL. Defaults to FRESHRSS_URL env var.
            username: Username. Defaults to FRESHRSS_USERNAME env var.
            password: Password. Defaults to FRESHRSS_PASSWORD env var.
            timeout: HTTP request timeout in seconds.

        Raises:
            AuthError: If required credentials are missing.
        """
        self._url = url or os.environ.get("FRESHRSS_URL")
        self._username = username or os.environ.get("FRESHRSS_USERNAME")
        self._password = password or os.environ.get("FRESHRSS_PASSWORD")
        self._timeout = timeout
        self._auth_token: str | None = None

        # Validate required credentials
        missing = []
        if not self._url:
            missing.append("FRESHRSS_URL")
        if not self._username:
            missing.append("FRESHRSS_USERNAME")
        if not self._password:
            missing.append("FRESHRSS_PASSWORD")

        if missing:
            raise AuthError(f"Missing required credentials: {', '.join(missing)}")

        # Normalize URL (remove trailing slash)
        # At this point we know _url is not None (we raised above if it was)
        assert self._url is not None
        self._url = self._url.rstrip("/")

    async def _authenticate(self) -> str:
        """Authenticate with FreshRSS and obtain auth token.

        Uses the Google Reader API ClientLogin endpoint.

        Returns:
            Authentication token string.

        Raises:
            AuthError: If authentication fails.
        """
        login_url = f"{self._url}/api/greader.php/accounts/ClientLogin"
        logger.debug("Authenticating with FreshRSS at %s", self._url)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(
                    login_url,
                    data={
                        "Email": self._username,
                        "Passwd": self._password,
                    },
                )

                logger.debug(
                    "Auth response: status=%d, url=%s",
                    response.status_code,
                    login_url,
                )

                if response.status_code == 401:
                    raise AuthError("FreshRSS authentication failed")

                if response.status_code == 429:
                    raise RateLimitError("Rate limited during authentication")

                if response.status_code >= 500:
                    raise FetchError(
                        f"Server error during authentication: {response.status_code}",
                        status_code=response.status_code,
                        url=login_url,
                    )

                response.raise_for_status()

                # Parse response to extract Auth token
                # Response format: SID=...\nAuth=TOKEN\n
                for line in response.text.split("\n"):
                    if line.startswith("Auth="):
                        token = line[5:].strip()
                        self._auth_token = token
                        logger.debug("Successfully authenticated with FreshRSS")
                        return token

                raise AuthError("FreshRSS authentication failed: no auth token in response")

            except httpx.TimeoutException as e:
                raise FetchError(
                    f"Timeout during authentication: {e}",
                    url=login_url,
                ) from e
            except httpx.RequestError as e:
                raise FetchError(
                    f"Network error during authentication: {e}",
                    url=login_url,
                ) from e

    async def _ensure_authenticated(self) -> str:
        """Ensure client has a valid auth token.

        Returns:
            Current auth token.

        Raises:
            AuthError: If authentication fails.
        """
        if self._auth_token is None:
            await self._authenticate()
        return self._auth_token  # type: ignore

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        retry_on_401: bool = True,
    ) -> httpx.Response:
        """Make an authenticated request to FreshRSS API.

        Handles 401 responses by refreshing the token and retrying once.

        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path (without base URL).
            params: Query parameters.
            retry_on_401: Whether to retry on 401 (default True).

        Returns:
            HTTP response object.

        Raises:
            AuthError: If authentication fails after retry.
            FetchError: For server errors or network issues.
            RateLimitError: If rate limited (429).
        """
        token = await self._ensure_authenticated()
        url = f"{self._url}{endpoint}"

        headers = {"Authorization": f"GoogleLogin auth={token}"}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                logger.debug("Request: %s %s", method, url)
                response = await client.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                )

                logger.debug(
                    "Response: status=%d, url=%s",
                    response.status_code,
                    url,
                )

                # Handle 401 - refresh token and retry
                if response.status_code == 401 and retry_on_401:
                    logger.debug("Got 401, refreshing token and retrying")
                    self._auth_token = None
                    return await self._request(method, endpoint, params, retry_on_401=False)

                # Handle 401 after retry
                if response.status_code == 401:
                    raise AuthError("FreshRSS authentication failed after token refresh")

                # Handle rate limiting
                if response.status_code == 429:
                    logger.warning("Rate limited by FreshRSS: %s", url)
                    raise RateLimitError("Rate limited by FreshRSS")

                # Handle server errors
                if response.status_code >= 500:
                    logger.error(
                        "Server error from FreshRSS: status=%d, url=%s",
                        response.status_code,
                        url,
                    )
                    raise FetchError(
                        f"FreshRSS server error: {response.status_code}",
                        status_code=response.status_code,
                        url=url,
                    )

                response.raise_for_status()
                return response

            except httpx.TimeoutException as e:
                logger.error("Timeout fetching %s: %s", url, e)
                raise FetchError(f"Request timeout: {e}", url=url) from e
            except httpx.RequestError as e:
                logger.error("Network error fetching %s: %s", url, e)
                raise FetchError(f"Network error: {e}", url=url) from e

    async def get_categories(self) -> list[Category]:
        """Fetch all feed categories from FreshRSS.

        Returns:
            List of Category objects with id and name fields.

        Raises:
            AuthError: If authentication fails.
            FetchError: For network or server errors.
            RateLimitError: If rate limited.
        """
        response = await self._request(
            "GET",
            "/api/greader.php/reader/api/0/tag/list",
            params={"output": "json"},
        )

        data = response.json()
        categories = []

        for tag in data.get("tags", []):
            tag_id = tag.get("id", "")
            # Only include user labels (categories), not system tags
            if "/label/" in tag_id:
                # Extract human-readable name from tag ID
                # Format: user/-/label/CategoryName
                name = tag_id.split("/label/")[-1]
                categories.append(Category(id=tag_id, name=name))

        logger.debug("Fetched %d categories from FreshRSS", len(categories))
        return categories

    async def get_unread_items(
        self,
        category_id: str | None = None,
        max_articles: int = DEFAULT_MAX_ARTICLES,
    ) -> list[Article]:
        """Fetch unread articles from FreshRSS.

        This is a read-only operation and does NOT mark articles as read.

        Args:
            category_id: Optional category ID to filter by. If None, fetches
                all unread articles.
            max_articles: Maximum number of articles to return. Defaults to 100.

        Returns:
            List of Article objects, most recent first.

        Raises:
            AuthError: If authentication fails.
            FetchError: For network or server errors.
            RateLimitError: If rate limited.
        """
        articles: list[Article] = []
        continuation: str | None = None

        while len(articles) < max_articles:
            remaining = max_articles - len(articles)
            page_size = min(DEFAULT_PAGE_SIZE, remaining)

            params: dict[str, Any] = {
                "output": "json",
                "n": page_size,
                "xt": "user/-/state/com.google/read",  # Exclude read items
            }

            if category_id:
                params["s"] = category_id

            if continuation:
                params["c"] = continuation

            response = await self._request(
                "GET",
                "/api/greader.php/reader/api/0/stream/contents",
                params=params,
            )

            data = response.json()

            for item in data.get("items", []):
                article = self._parse_article(item, category_id)
                if article:
                    articles.append(article)
                    if len(articles) >= max_articles:
                        break

            # Check for more pages
            continuation = data.get("continuation")
            if not continuation or len(data.get("items", [])) == 0:
                break

        logger.debug(
            "Fetched %d unread articles (category=%s)",
            len(articles),
            category_id or "all",
        )
        return articles

    def _parse_article(
        self, item: dict[str, Any], default_category_id: str | None
    ) -> Article | None:
        """Parse a FreshRSS item into an Article model.

        Args:
            item: Raw item data from FreshRSS API.
            default_category_id: Default category ID if not found in item.

        Returns:
            Article instance or None if parsing fails.
        """
        try:
            # Extract article ID
            article_id = item.get("id", "")

            # Extract title
            title = item.get("title", "Untitled")

            # Extract URL from alternate links
            url = ""
            for alt in item.get("alternate", []):
                if alt.get("type") == "text/html":
                    url = alt.get("href", "")
                    break
            if not url:
                url = item.get("canonical", [{}])[0].get("href", "")

            # Extract author
            author = item.get("author")

            # Extract published timestamp
            published_timestamp = item.get("published", item.get("crawlTimeMsec", 0))
            if isinstance(published_timestamp, str):
                published_timestamp = int(published_timestamp) // 1000
            published_at = datetime.fromtimestamp(published_timestamp, tz=timezone.utc)

            # Extract content and create teaser
            content = ""
            if "content" in item:
                content = item["content"].get("content", "")
            elif "summary" in item:
                content = item["summary"].get("content", "")

            teaser = self._create_teaser(content)

            # Extract category ID from categories
            category_id = default_category_id or ""
            for cat in item.get("categories", []):
                if "/label/" in cat:
                    category_id = cat
                    break

            # Extract feed title
            feed_title = item.get("origin", {}).get("title", "Unknown Feed")

            return Article(
                id=article_id,
                title=title,
                url=url,
                author=author,
                published_at=published_at,
                teaser=teaser,
                category_id=category_id,
                feed_title=feed_title,
            )

        except Exception as e:
            logger.warning("Failed to parse article: %s", e)
            return None

    def _create_teaser(self, content: str) -> str:
        """Create a teaser from HTML content.

        Strips HTML tags and limits to MAX_TEASER_LENGTH characters.

        Args:
            content: Raw HTML content.

        Returns:
            Plain text teaser string.
        """
        # Decode HTML entities
        text = html.unescape(content)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Truncate to max length
        if len(text) > MAX_TEASER_LENGTH:
            text = text[:MAX_TEASER_LENGTH]

        return text
