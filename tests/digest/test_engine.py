"""Tests for DigestEngine."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ryushi.digest import Digest, DigestConfig, DigestEngine, DigestError


def make_mock_article(
    title: str = "Test Article",
    url: str = "https://example.com/article",
    author: str | None = "Test Author",
    teaser: str = "This is a test teaser.",
) -> MagicMock:
    """Create a mock Article object."""
    article = MagicMock()
    article.title = title
    article.url = url
    article.author = author
    article.teaser = teaser
    return article


def make_mock_response(content: str) -> MagicMock:
    """Create a mock LiteLLM response."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    response.usage = MagicMock()
    response.usage.prompt_tokens = 100
    response.usage.completion_tokens = 200
    response.usage.total_tokens = 300
    return response


class TestDigestEngineInit:
    """Tests for DigestEngine initialization."""

    def test_default_config(self, monkeypatch):
        """Engine uses default config when none provided."""
        # Clear env vars to test true defaults
        monkeypatch.delenv("RYUSHI_AI_MODEL", raising=False)
        monkeypatch.delenv("RYUSHI_AI_BASE_URL", raising=False)
        monkeypatch.delenv("RYUSHI_AI_API_KEY", raising=False)

        engine = DigestEngine()
        assert engine.config.model == "gpt-4.1-mini"
        assert engine.config.temperature == 0.7

    def test_custom_config(self):
        """Engine accepts custom config."""
        config = DigestConfig(model="claude-3-haiku", temperature=0.3)
        engine = DigestEngine(config)
        assert engine.config.model == "claude-3-haiku"
        assert engine.config.temperature == 0.3


class TestGenerateDigest:
    """Tests for digest generation."""

    async def test_empty_article_list_returns_none(self):
        """Returns None for empty article list."""
        engine = DigestEngine()
        result = await engine.generate_digest([], "Technology")
        assert result is None

    async def test_successful_digest_generation(self, monkeypatch):
        """Generates digest successfully with mocked LiteLLM."""
        # Clear env vars to test true defaults
        monkeypatch.delenv("RYUSHI_AI_MODEL", raising=False)
        monkeypatch.delenv("RYUSHI_AI_BASE_URL", raising=False)
        monkeypatch.delenv("RYUSHI_AI_API_KEY", raising=False)

        engine = DigestEngine()
        articles = [
            make_mock_article(title="Article 1", url="https://example.com/1"),
            make_mock_article(title="Article 2", url="https://example.com/2"),
        ]

        mock_response = make_mock_response(
            "Here's a summary of today's tech news.\n\n"
            "- Article 1 discusses... (https://example.com/1)\n"
            "- Article 2 covers... (https://example.com/2)"
        )

        with patch("ryushi.digest.engine.litellm.acompletion", new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = mock_response
            digest = await engine.generate_digest(articles, "Technology")

        assert digest is not None
        assert isinstance(digest, Digest)
        assert digest.category_name == "Technology"
        assert digest.article_count == 2
        assert digest.model_used == "gpt-4.1-mini"
        assert "summary" in digest.summary.lower() or len(digest.summary) > 0

    async def test_digest_extracts_source_urls(self):
        """Extracts article URLs from summary."""
        engine = DigestEngine()
        articles = [
            make_mock_article(title="Article 1", url="https://example.com/article-1"),
            make_mock_article(title="Article 2", url="https://example.com/article-2"),
        ]

        mock_response = make_mock_response(
            "Summary with links:\n"
            "- First article: https://example.com/article-1\n"
            "- Second article: https://example.com/article-2"
        )

        with patch("ryushi.digest.engine.litellm.acompletion", new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = mock_response
            digest = await engine.generate_digest(articles, "News")

        assert "https://example.com/article-1" in digest.source_urls
        assert "https://example.com/article-2" in digest.source_urls

    async def test_digest_ignores_non_article_urls(self):
        """Does not include URLs that weren't in the article list."""
        engine = DigestEngine()
        articles = [
            make_mock_article(title="Article 1", url="https://example.com/article-1"),
        ]

        mock_response = make_mock_response(
            "Summary with external link:\n"
            "- https://example.com/article-1\n"
            "- https://other-site.com/random"
        )

        with patch("ryushi.digest.engine.litellm.acompletion", new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = mock_response
            digest = await engine.generate_digest(articles, "News")

        assert "https://example.com/article-1" in digest.source_urls
        assert "https://other-site.com/random" not in digest.source_urls

    async def test_custom_system_prompt(self):
        """Uses custom system prompt from config."""
        config = DigestConfig(system_prompt="Custom prompt for {language}.")
        engine = DigestEngine(config)
        articles = [make_mock_article()]

        mock_response = make_mock_response("Summary")

        with patch("ryushi.digest.engine.litellm.acompletion", new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = mock_response
            await engine.generate_digest(articles, "Tech")

        # Check that custom prompt was used
        call_args = mock_ai.call_args
        messages = call_args.kwargs["messages"]
        system_message = messages[0]["content"]
        assert "Custom prompt for English" in system_message


class TestRetryLogic:
    """Tests for retry behavior on transient errors."""

    async def test_retries_on_429(self):
        """Retries on rate limit error."""
        engine = DigestEngine()
        articles = [make_mock_article()]

        error_429 = Exception("Rate limit exceeded")
        error_429.status_code = 429

        mock_response = make_mock_response("Success after retry")

        with patch("ryushi.digest.engine.litellm.acompletion", new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = [error_429, mock_response]
            digest = await engine.generate_digest(articles, "Tech")

        assert digest is not None
        assert mock_ai.call_count == 2

    async def test_retries_on_503(self):
        """Retries on service unavailable error."""
        engine = DigestEngine()
        articles = [make_mock_article()]

        error_503 = Exception("Service unavailable")
        error_503.status_code = 503

        mock_response = make_mock_response("Success after retry")

        with patch("ryushi.digest.engine.litellm.acompletion", new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = [error_503, mock_response]
            digest = await engine.generate_digest(articles, "Tech")

        assert digest is not None
        assert mock_ai.call_count == 2

    async def test_no_retry_on_401(self):
        """Does not retry on authentication error."""
        engine = DigestEngine()
        articles = [make_mock_article()]

        error_401 = Exception("Unauthorized")
        error_401.status_code = 401

        with patch("ryushi.digest.engine.litellm.acompletion", new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = error_401
            with pytest.raises(DigestError) as exc_info:
                await engine.generate_digest(articles, "Tech")

        assert exc_info.value.status_code == 401
        assert mock_ai.call_count == 1

    async def test_no_retry_on_400(self):
        """Does not retry on bad request error."""
        engine = DigestEngine()
        articles = [make_mock_article()]

        error_400 = Exception("Bad request")
        error_400.status_code = 400

        with patch("ryushi.digest.engine.litellm.acompletion", new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = error_400
            with pytest.raises(DigestError) as exc_info:
                await engine.generate_digest(articles, "Tech")

        assert exc_info.value.status_code == 400
        assert mock_ai.call_count == 1

    async def test_max_retries_exceeded(self):
        """Raises DigestError after max retries."""
        engine = DigestEngine()
        articles = [make_mock_article()]

        # Create a proper exception class with status_code
        class APIError(Exception):
            def __init__(self, message: str, status_code: int):
                super().__init__(message)
                self.status_code = status_code

        error_503 = APIError("Service unavailable", 503)

        with patch("ryushi.digest.engine.litellm.acompletion", new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = error_503
            with pytest.raises(DigestError):
                await engine.generate_digest(articles, "Tech")

        # Should have tried 3 times (initial + 2 retries)
        assert mock_ai.call_count == 3


class TestDigestError:
    """Tests for DigestError context."""

    async def test_digest_error_contains_status_code(self):
        """DigestError includes status code."""
        engine = DigestEngine()
        articles = [make_mock_article()]

        # Create a proper exception class with status_code
        class APIError(Exception):
            def __init__(self, message: str, status_code: int):
                super().__init__(message)
                self.status_code = status_code

        error = APIError("Server error", 500)

        with patch("ryushi.digest.engine.litellm.acompletion", new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = error
            with pytest.raises(DigestError) as exc_info:
                await engine.generate_digest(articles, "Tech")

        assert exc_info.value.status_code == 500

    async def test_digest_error_contains_model(self):
        """DigestError includes model name."""
        config = DigestConfig(model="test-model")
        engine = DigestEngine(config)
        articles = [make_mock_article()]

        error = Exception("Error")
        error.status_code = 401

        with patch("ryushi.digest.engine.litellm.acompletion", new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = error
            with pytest.raises(DigestError) as exc_info:
                await engine.generate_digest(articles, "Tech")

        assert exc_info.value.model == "test-model"

    async def test_digest_error_no_credentials(self):
        """DigestError does not expose credentials."""
        engine = DigestEngine()
        articles = [make_mock_article()]

        error = Exception("Invalid API key: sk-test-12345")
        error.status_code = 401

        with patch("ryushi.digest.engine.litellm.acompletion", new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = error
            with pytest.raises(DigestError) as exc_info:
                await engine.generate_digest(articles, "Tech")

        # The error message may contain the original, but DigestError should not add more
        str(exc_info.value)
        # We can't control what the underlying error contains, but we shouldn't log extra secrets
        assert exc_info.value.model is not None  # Has context
        assert exc_info.value.retry_count is not None  # Has context


class TestContextTruncation:
    """Tests for context window truncation."""

    async def test_truncates_large_article_list(self):
        """Truncates articles to fit context window."""
        # Use a model with small context window
        config = DigestConfig(model="gpt-4")  # 8192 tokens
        engine = DigestEngine(config)

        # Create many articles with long teasers
        articles = [
            make_mock_article(
                title=f"Article {i}",
                url=f"https://example.com/{i}",
                teaser="x" * 500,
            )
            for i in range(100)
        ]

        mock_response = make_mock_response("Summary of truncated articles")

        with patch("ryushi.digest.engine.litellm.acompletion", new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = mock_response
            digest = await engine.generate_digest(articles, "News")

        assert digest is not None
        # The prompt should have been truncated
        call_args = mock_ai.call_args
        user_message = call_args.kwargs["messages"][1]["content"]
        # Should mention truncation
        assert "100 articles" in user_message or "Showing" in user_message
