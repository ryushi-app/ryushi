"""Tests for prompt building functionality."""

from unittest.mock import MagicMock


from ryushi.digest.prompts import (
    DEFAULT_SYSTEM_PROMPT,
    build_prompt,
    estimate_tokens,
    format_system_prompt,
    get_context_window,
)


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


class TestGetContextWindow:
    """Tests for context window lookup."""

    def test_known_model(self):
        """Returns correct window for known models."""
        assert get_context_window("gpt-4o-mini") == 128000
        assert get_context_window("gpt-4") == 8192

    def test_model_with_version_suffix(self):
        """Returns correct window for versioned model names."""
        assert get_context_window("gpt-4o-mini-2024-07-18") == 128000
        assert get_context_window("gpt-4-turbo-preview") == 128000

    def test_unknown_model(self):
        """Returns default window for unknown models."""
        assert get_context_window("unknown-model") == 8192


class TestEstimateTokens:
    """Tests for token estimation."""

    def test_empty_string(self):
        """Empty string has 0 tokens."""
        assert estimate_tokens("") == 0

    def test_short_text(self):
        """Estimates tokens for short text."""
        # 4 chars per token estimate
        assert estimate_tokens("test") == 1
        assert estimate_tokens("testtest") == 2

    def test_longer_text(self):
        """Estimates tokens for longer text."""
        text = "x" * 400
        assert estimate_tokens(text) == 100


class TestFormatSystemPrompt:
    """Tests for system prompt formatting."""

    def test_default_language(self):
        """Formats with default English language."""
        result = format_system_prompt(DEFAULT_SYSTEM_PROMPT)
        assert "in English" in result

    def test_custom_language(self):
        """Formats with custom language."""
        result = format_system_prompt(DEFAULT_SYSTEM_PROMPT, language="German")
        assert "in German" in result

    def test_custom_template(self):
        """Formats custom template."""
        template = "Write summary in {language}."
        result = format_system_prompt(template, language="Spanish")
        assert result == "Write summary in Spanish."


class TestBuildPrompt:
    """Tests for prompt building."""

    def test_empty_articles(self):
        """Returns empty prompt for empty article list."""
        prompt, count = build_prompt([], "Technology")
        assert prompt == ""
        assert count == 0

    def test_single_article(self):
        """Builds prompt with single article."""
        article = make_mock_article(
            title="Test Title",
            url="https://example.com/test",
            author="Author Name",
            teaser="Article teaser content.",
        )
        prompt, count = build_prompt([article], "Tech News")

        assert count == 1
        assert "Category: Tech News" in prompt
        assert "Total articles: 1" in prompt
        assert "### Test Title" in prompt
        assert "URL: https://example.com/test" in prompt
        assert "Author: Author Name" in prompt
        assert "Teaser: Article teaser content." in prompt

    def test_multiple_articles(self):
        """Builds prompt with multiple articles."""
        articles = [
            make_mock_article(title="Article 1", url="https://example.com/1"),
            make_mock_article(title="Article 2", url="https://example.com/2"),
            make_mock_article(title="Article 3", url="https://example.com/3"),
        ]
        prompt, count = build_prompt(articles, "News")

        assert count == 3
        assert "Total articles: 3" in prompt
        assert "### Article 1" in prompt
        assert "### Article 2" in prompt
        assert "### Article 3" in prompt

    def test_article_without_author(self):
        """Handles article with no author."""
        article = make_mock_article(author=None)
        prompt, count = build_prompt([article], "Tech")

        assert count == 1
        assert "Author:" not in prompt

    def test_article_without_teaser(self):
        """Handles article with empty teaser."""
        article = make_mock_article(teaser="")
        prompt, count = build_prompt([article], "Tech")

        assert count == 1
        assert "Teaser:" not in prompt or "Teaser: \n" in prompt

    def test_truncation_on_context_limit(self):
        """Truncates articles when exceeding context window."""
        # Create many articles that would exceed a small context window
        articles = [
            make_mock_article(
                title=f"Article {i}",
                url=f"https://example.com/{i}",
                teaser="x" * 500,  # Long teaser
            )
            for i in range(100)
        ]

        # Use a model with small context window
        prompt, count = build_prompt(articles, "News", model="gpt-4", max_context_ratio=0.8)

        # Should have truncated
        assert count < 100
        assert count > 0
        # Should include truncation notice
        assert f"Showing {count} of 100 articles" in prompt

    def test_category_name_in_prompt(self):
        """Category name appears in prompt."""
        article = make_mock_article()
        prompt, _ = build_prompt([article], "Software Engineering")

        assert "Category: Software Engineering" in prompt

    def test_article_count_in_prompt(self):
        """Total article count appears in prompt."""
        articles = [make_mock_article() for _ in range(15)]
        prompt, _ = build_prompt(articles, "News")

        assert "Total articles: 15" in prompt
