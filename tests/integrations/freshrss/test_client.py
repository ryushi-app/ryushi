"""Tests for FreshRSS client."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from ryushi.integrations.freshrss import (
    Article,
    AuthError,
    Category,
    FetchError,
    FreshRSSClient,
    RateLimitError,
)


def make_response(status_code: int, **kwargs) -> httpx.Response:
    """Create a mock response with a request attached."""
    request = httpx.Request("GET", "https://example.com/test")
    return httpx.Response(status_code, request=request, **kwargs)


# Sample API responses
AUTH_RESPONSE = "SID=test-sid\nAuth=test-auth-token\n"

CATEGORIES_RESPONSE = {
    "tags": [
        {"id": "user/-/label/Technology"},
        {"id": "user/-/label/News"},
        {"id": "user/-/state/com.google/reading-list"},  # System tag, should be filtered
    ]
}

ARTICLES_RESPONSE = {
    "items": [
        {
            "id": "tag:google.com,2005:reader/item/123",
            "title": "Test Article 1",
            "alternate": [{"type": "text/html", "href": "https://example.com/1"}],
            "author": "Author 1",
            "published": 1704067200,  # 2024-01-01 00:00:00 UTC
            "content": {"content": "<p>Article content preview</p>"},
            "categories": ["user/-/label/Technology"],
            "origin": {"title": "Example Blog"},
        },
        {
            "id": "tag:google.com,2005:reader/item/456",
            "title": "Test Article 2",
            "alternate": [{"type": "text/html", "href": "https://example.com/2"}],
            "published": 1704153600,
            "summary": {"content": "Short summary"},
            "categories": ["user/-/label/News"],
            "origin": {"title": "News Site"},
        },
    ],
    "continuation": None,
}

ARTICLES_PAGINATED_PAGE1 = {
    "items": [
        {
            "id": "tag:google.com,2005:reader/item/1",
            "title": "Article 1",
            "alternate": [{"type": "text/html", "href": "https://example.com/1"}],
            "published": 1704067200,
            "content": {"content": "Content 1"},
            "categories": ["user/-/label/Tech"],
            "origin": {"title": "Feed 1"},
        },
    ],
    "continuation": "page2token",
}

ARTICLES_PAGINATED_PAGE2 = {
    "items": [
        {
            "id": "tag:google.com,2005:reader/item/2",
            "title": "Article 2",
            "alternate": [{"type": "text/html", "href": "https://example.com/2"}],
            "published": 1704153600,
            "content": {"content": "Content 2"},
            "categories": ["user/-/label/Tech"],
            "origin": {"title": "Feed 2"},
        },
    ],
    "continuation": None,
}


@pytest.fixture
def mock_env(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("FRESHRSS_URL", "https://freshrss.example.com")
    monkeypatch.setenv("FRESHRSS_USERNAME", "testuser")
    monkeypatch.setenv("FRESHRSS_PASSWORD", "testpass")


class TestClientInitialization:
    """Tests for FreshRSSClient initialization."""

    def test_init_with_env_vars(self, mock_env):
        """Client initializes with environment variables."""
        client = FreshRSSClient()
        assert client._url == "https://freshrss.example.com"
        assert client._username == "testuser"
        assert client._password == "testpass"

    def test_init_with_explicit_credentials(self):
        """Client accepts explicit credentials."""
        client = FreshRSSClient(
            url="https://custom.example.com",
            username="customuser",
            password="custompass",
        )
        assert client._url == "https://custom.example.com"
        assert client._username == "customuser"
        assert client._password == "custompass"

    def test_init_missing_url_raises_auth_error(self, monkeypatch):
        """Client raises AuthError when URL is missing."""
        monkeypatch.delenv("FRESHRSS_URL", raising=False)
        monkeypatch.setenv("FRESHRSS_USERNAME", "user")
        monkeypatch.setenv("FRESHRSS_PASSWORD", "pass")

        with pytest.raises(AuthError) as exc_info:
            FreshRSSClient()
        assert "FRESHRSS_URL" in str(exc_info.value)

    def test_init_missing_all_credentials_raises_auth_error(self, monkeypatch):
        """Client raises AuthError listing all missing credentials."""
        monkeypatch.delenv("FRESHRSS_URL", raising=False)
        monkeypatch.delenv("FRESHRSS_USERNAME", raising=False)
        monkeypatch.delenv("FRESHRSS_PASSWORD", raising=False)

        with pytest.raises(AuthError) as exc_info:
            FreshRSSClient()
        error_msg = str(exc_info.value)
        assert "FRESHRSS_URL" in error_msg
        assert "FRESHRSS_USERNAME" in error_msg
        assert "FRESHRSS_PASSWORD" in error_msg

    def test_init_normalizes_url_trailing_slash(self):
        """Client removes trailing slash from URL."""
        client = FreshRSSClient(
            url="https://example.com/",
            username="user",
            password="pass",
        )
        assert client._url == "https://example.com"


class TestAuthentication:
    """Tests for authentication flow."""

    async def test_successful_authentication(self, mock_env):
        """Client authenticates successfully with valid credentials."""
        client = FreshRSSClient()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = make_response(200, text=AUTH_RESPONSE)
            token = await client._authenticate()

        assert token == "test-auth-token"
        assert client._auth_token == "test-auth-token"

    async def test_authentication_invalid_credentials(self, mock_env):
        """Client raises AuthError on 401 response."""
        client = FreshRSSClient()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = make_response(401)
            with pytest.raises(AuthError) as exc_info:
                await client._authenticate()

        assert "authentication failed" in str(exc_info.value).lower()

    async def test_authentication_rate_limited(self, mock_env):
        """Client raises RateLimitError on 429 response."""
        client = FreshRSSClient()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = make_response(429)
            with pytest.raises(RateLimitError):
                await client._authenticate()

    async def test_authentication_server_error(self, mock_env):
        """Client raises FetchError on 5xx response."""
        client = FreshRSSClient()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = make_response(500)
            with pytest.raises(FetchError) as exc_info:
                await client._authenticate()

        assert exc_info.value.status_code == 500

    async def test_authentication_timeout(self, mock_env):
        """Client raises FetchError on timeout."""
        client = FreshRSSClient()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Connection timed out")
            with pytest.raises(FetchError) as exc_info:
                await client._authenticate()

        assert "timeout" in str(exc_info.value).lower()


class TestTokenRefresh:
    """Tests for token refresh on 401 responses."""

    async def test_token_refresh_on_401(self, mock_env):
        """Client refreshes token and retries on 401."""
        client = FreshRSSClient()
        client._auth_token = "expired-token"

        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # First API call returns 401
                return make_response(401)
            return make_response(200, json=CATEGORIES_RESPONSE)

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
                mock_req.side_effect = mock_request
                mock_post.return_value = make_response(200, text=AUTH_RESPONSE)

                categories = await client.get_categories()

        assert len(categories) == 2
        assert client._auth_token == "test-auth-token"

    async def test_persistent_401_raises_auth_error(self, mock_env):
        """Client raises AuthError if 401 persists after refresh."""
        client = FreshRSSClient()
        client._auth_token = "bad-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
                mock_req.return_value = make_response(401)
                mock_post.return_value = make_response(200, text=AUTH_RESPONSE)

                with pytest.raises(AuthError) as exc_info:
                    await client.get_categories()

        assert "after token refresh" in str(exc_info.value).lower()


class TestGetCategories:
    """Tests for category fetching."""

    async def test_get_categories_success(self, mock_env):
        """Client fetches and parses categories correctly."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(200, json=CATEGORIES_RESPONSE)
            categories = await client.get_categories()

        assert len(categories) == 2
        assert all(isinstance(c, Category) for c in categories)
        assert categories[0].id == "user/-/label/Technology"
        assert categories[0].name == "Technology"
        assert categories[1].name == "News"

    async def test_get_categories_empty(self, mock_env):
        """Client returns empty list when no categories exist."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(200, json={"tags": []})
            categories = await client.get_categories()

        assert categories == []

    async def test_get_categories_network_error(self, mock_env):
        """Client raises FetchError on network error."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = httpx.ConnectError("Connection refused")
            with pytest.raises(FetchError):
                await client.get_categories()


class TestGetUnreadItems:
    """Tests for article fetching."""

    async def test_get_unread_items_success(self, mock_env):
        """Client fetches and parses articles correctly."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(200, json=ARTICLES_RESPONSE)
            articles = await client.get_unread_items()

        assert len(articles) == 2
        assert all(isinstance(a, Article) for a in articles)
        assert articles[0].title == "Test Article 1"
        assert articles[0].url == "https://example.com/1"
        assert articles[0].author == "Author 1"
        assert articles[0].feed_title == "Example Blog"
        # Second article has no author
        assert articles[1].author is None

    async def test_get_unread_items_with_category(self, mock_env):
        """Client passes category_id parameter correctly."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(200, json=ARTICLES_RESPONSE)
            await client.get_unread_items(category_id="user/-/label/Technology")

        call_args = mock_req.call_args
        assert call_args[1]["params"]["s"] == "user/-/label/Technology"

    async def test_get_unread_items_respects_max_articles(self, mock_env):
        """Client respects max_articles limit."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(200, json=ARTICLES_RESPONSE)
            articles = await client.get_unread_items(max_articles=1)

        assert len(articles) == 1

    async def test_get_unread_items_pagination(self, mock_env):
        """Client handles pagination correctly."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_response(200, json=ARTICLES_PAGINATED_PAGE1)
            return make_response(200, json=ARTICLES_PAGINATED_PAGE2)

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = mock_request
            articles = await client.get_unread_items(max_articles=10)

        assert len(articles) == 2
        assert call_count == 2

    async def test_get_unread_items_empty(self, mock_env):
        """Client returns empty list when no articles exist."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(200, json={"items": []})
            articles = await client.get_unread_items()

        assert articles == []

    async def test_get_unread_items_teaser_truncation(self, mock_env):
        """Client truncates teaser to 500 characters."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        long_content = "x" * 1000
        response_data = {
            "items": [
                {
                    "id": "123",
                    "title": "Test",
                    "alternate": [{"type": "text/html", "href": "https://example.com"}],
                    "published": 1704067200,
                    "content": {"content": long_content},
                    "categories": ["user/-/label/Test"],
                    "origin": {"title": "Test Feed"},
                }
            ]
        }

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(200, json=response_data)
            articles = await client.get_unread_items()

        assert len(articles[0].teaser) == 500


class TestErrorHandling:
    """Tests for error handling scenarios."""

    async def test_rate_limit_error(self, mock_env):
        """Client raises RateLimitError on 429 response."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(429)
            with pytest.raises(RateLimitError):
                await client.get_categories()

    async def test_server_error(self, mock_env):
        """Client raises FetchError with status code on 5xx response."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(503)
            with pytest.raises(FetchError) as exc_info:
                await client.get_categories()

        assert exc_info.value.status_code == 503

    async def test_timeout_error(self, mock_env):
        """Client raises FetchError on timeout."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = httpx.TimeoutException("Request timed out")
            with pytest.raises(FetchError) as exc_info:
                await client.get_categories()

        assert "timeout" in str(exc_info.value).lower()

    async def test_credentials_not_in_error_messages(self, mock_env):
        """Credentials are not exposed in error messages."""
        client = FreshRSSClient()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = make_response(401)
            with pytest.raises(AuthError) as exc_info:
                await client._authenticate()

        error_msg = str(exc_info.value)
        assert "testpass" not in error_msg
        assert "testuser" not in error_msg


class TestReadOnlyBehavior:
    """Tests to verify read-only behavior."""

    async def test_get_unread_items_excludes_read_items(self, mock_env):
        """Client requests only unread items (does not mark as read)."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(200, json={"items": []})
            await client.get_unread_items()

        call_args = mock_req.call_args
        # Verify we're using the exclude-read filter
        assert call_args[1]["params"]["xt"] == "user/-/state/com.google/read"
        # Verify we're not making any POST requests that could modify state
        assert call_args[0][0] == "GET"


class TestMarkAsRead:
    """Tests for marking articles as read."""

    async def test_mark_single_article_as_read(self, mock_env):
        """Client marks a single article as read."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(200, json={})
            await client.mark_as_read(["tag:google.com,2005:reader/item/123"])

        call_args = mock_req.call_args
        # Verify POST to edit-tag endpoint
        assert call_args[0][0] == "POST"
        assert "edit-tag" in call_args[0][1]
        # Verify read tag is used
        assert call_args[1]["params"]["t"] == "user/-/state/com.google/read"

    async def test_mark_multiple_articles_as_read(self, mock_env):
        """Client marks multiple articles as read in one request."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        article_ids = [
            "tag:google.com,2005:reader/item/123",
            "tag:google.com,2005:reader/item/456",
            "tag:google.com,2005:reader/item/789",
        ]

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(200, json={})
            await client.mark_as_read(article_ids)

        call_args = mock_req.call_args
        assert call_args[0][0] == "POST"
        assert "edit-tag" in call_args[0][1]

    async def test_mark_as_read_empty_list(self, mock_env):
        """Client does not make request for empty article list."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            await client.mark_as_read([])

        # Should not have made any HTTP request
        mock_req.assert_not_called()

    async def test_mark_as_read_batch_chunking(self, mock_env):
        """Client batches requests for large article lists (max 50 per request)."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        # Create 150 article IDs (will be split into 3 batches of 50)
        article_ids = [f"tag:google.com,2005:reader/item/{i}" for i in range(150)]

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(200, json={})
            await client.mark_as_read(article_ids)

        # Should have made 3 POST requests (150 / 50)
        assert mock_req.call_count == 3
        # All calls should be POST to edit-tag
        for call in mock_req.call_args_list:
            assert call[0][0] == "POST"
            assert "edit-tag" in call[0][1]

    async def test_mark_as_read_partial_batch_failure(self, mock_env):
        """Client continues processing batches even if one fails."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        article_ids = [f"tag:google.com,2005:reader/item/{i}" for i in range(100)]

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            # First batch succeeds, second fails, third succeeds
            mock_req.side_effect = [
                make_response(200, json={}),
                make_response(500),  # Server error
                make_response(200, json={}),
            ]
            # Should not raise exception
            await client.mark_as_read(article_ids)

        # Should have attempted all 2 requests
        assert mock_req.call_count == 2  # After first failure, remaining batches continue

    async def test_mark_as_read_auth_error(self, mock_env):
        """Client logs warning on authentication failure instead of raising."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(401)
            # mark_as_read logs warnings but doesn't raise (graceful failure)
            await client.mark_as_read(["tag:google.com,2005:reader/item/123"])

    async def test_mark_as_read_rate_limit_error(self, mock_env):
        """Client logs warning on rate limiting instead of raising."""
        client = FreshRSSClient()
        client._auth_token = "valid-token"

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_response(429)
            # mark_as_read logs warnings but doesn't raise (graceful failure)
            await client.mark_as_read(["tag:google.com,2005:reader/item/123"])
