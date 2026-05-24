"""Tests for GitHub Gist publisher."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from ryushi.integrations.github import GistPublisher


@pytest.fixture
def gist_publisher():
    """Create a GistPublisher instance."""
    return GistPublisher()


class TestGistPublisherConfiguration:
    """Tests for GistPublisher configuration."""

    def test_is_configured_with_token(self, monkeypatch):
        """Test is_configured returns True when token is set."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test123")
        publisher = GistPublisher()
        assert publisher.is_configured is True

    def test_is_configured_without_token(self, monkeypatch):
        """Test is_configured returns False when token is missing."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        publisher = GistPublisher()
        assert publisher.is_configured is False


class TestGistPublisherPublish:
    """Tests for publish method."""

    async def test_publish_without_token(self, monkeypatch):
        """Test publish gracefully handles missing token."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        publisher = GistPublisher()

        # Should not raise, just log warning
        await publisher.publish("abc123", "test.xml", "<content/>")

    async def test_publish_successful(self, monkeypatch):
        """Test successful Gist publish."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test123")
        publisher = GistPublisher()

        with patch.object(httpx.AsyncClient, "patch", new_callable=AsyncMock) as mock_patch:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_patch.return_value = mock_response

            await publisher.publish("abc123", "test.xml", "<content/>")

            # Verify request was made
            assert mock_patch.called
            call_args = mock_patch.call_args
            assert "gists/abc123" in call_args[0][0]
            assert call_args[1]["json"]["files"]["test.xml"]["content"] == "<content/>"

    async def test_publish_gist_not_found(self, monkeypatch):
        """Test publish handles gist not found (404)."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test123")
        publisher = GistPublisher()

        with patch.object(httpx.AsyncClient, "patch", new_callable=AsyncMock) as mock_patch:
            mock_response = AsyncMock()
            mock_response.status_code = 404
            mock_patch.return_value = mock_response

            # Should not raise, logs warning
            await publisher.publish("notfound123", "test.xml", "<content/>")

    async def test_publish_auth_error(self, monkeypatch):
        """Test publish handles auth error (401)."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_invalid")
        publisher = GistPublisher()

        with patch.object(httpx.AsyncClient, "patch", new_callable=AsyncMock) as mock_patch:
            mock_response = AsyncMock()
            mock_response.status_code = 401
            mock_patch.return_value = mock_response

            # Should not raise, logs warning
            await publisher.publish("abc123", "test.xml", "<content/>")

    async def test_publish_rate_limit(self, monkeypatch):
        """Test publish handles rate limit (403)."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test123")
        publisher = GistPublisher()

        with patch.object(httpx.AsyncClient, "patch", new_callable=AsyncMock) as mock_patch:
            mock_response = AsyncMock()
            mock_response.status_code = 403
            mock_response.json = AsyncMock(return_value={"message": "API rate limit exceeded"})
            mock_patch.return_value = mock_response

            # Should not raise, logs warning
            await publisher.publish("abc123", "test.xml", "<content/>")

    async def test_publish_server_error(self, monkeypatch):
        """Test publish handles server error (500)."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test123")
        publisher = GistPublisher()

        with patch.object(httpx.AsyncClient, "patch", new_callable=AsyncMock) as mock_patch:
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_patch.return_value = mock_response

            # Should not raise, logs warning
            await publisher.publish("abc123", "test.xml", "<content/>")

    async def test_publish_timeout(self, monkeypatch):
        """Test publish handles timeout gracefully."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test123")
        publisher = GistPublisher(timeout=0.1)

        with patch.object(httpx.AsyncClient, "patch", new_callable=AsyncMock) as mock_patch:
            mock_patch.side_effect = httpx.TimeoutException("Request timed out")

            # Should not raise, logs warning
            await publisher.publish("abc123", "test.xml", "<content/>")

    async def test_publish_network_error(self, monkeypatch):
        """Test publish handles network error gracefully."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test123")
        publisher = GistPublisher()

        with patch.object(httpx.AsyncClient, "patch", new_callable=AsyncMock) as mock_patch:
            mock_patch.side_effect = httpx.RequestError("Connection refused")

            # Should not raise, logs warning
            await publisher.publish("abc123", "test.xml", "<content/>")
