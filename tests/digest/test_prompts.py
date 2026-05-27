"""Tests for prompt building functionality."""

from unittest.mock import MagicMock


from ryushi.digest.prompts import (
    DEFAULT_SYSTEM_PROMPT,
    PROMPT_TEMPLATES,
    build_prompt,
    estimate_tokens,
    format_system_prompt,
    get_context_window,
    get_template,
    render_template,
    select_prompt,
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
        """Formats with default German language."""
        result = format_system_prompt(DEFAULT_SYSTEM_PROMPT)
        assert "in German" in result

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


class TestGetTemplate:
    """Tests for template registry lookup."""

    def test_digest_template_exists(self):
        """Digest template can be retrieved."""
        template = get_template("digest")
        assert template is not None
        assert isinstance(template, str)
        assert "digest" in template.lower()

    def test_recommendation_template_exists(self):
        """Recommendation template can be retrieved."""
        template = get_template("recommendation")
        assert template is not None
        assert isinstance(template, str)
        assert "curator" in template.lower() or "interest" in template.lower()

    def test_unknown_template(self):
        """Returns None for unknown template type."""
        template = get_template("unknown-type")
        assert template is None

    def test_template_registry_contains_expected_types(self):
        """Registry contains expected template types."""
        assert "digest" in PROMPT_TEMPLATES
        assert "recommendation" in PROMPT_TEMPLATES


class TestRenderTemplate:
    """Tests for template rendering with parameter substitution."""

    def test_language_substitution(self):
        """Substitutes {language} placeholder."""
        template = "Write in {language}."
        result = render_template(template, language="Spanish")
        assert result == "Write in Spanish."

    def test_language_default(self):
        """Uses German as default language."""
        template = "Write in {language}."
        result = render_template(template)
        assert result == "Write in German."

    def test_item_type_substitution(self):
        """Substitutes {item_type} placeholder."""
        template = "Recommend {item_type}."
        result = render_template(template, item_type="books")
        assert result == "Recommend books."

    def test_item_type_default(self):
        """Uses 'items' as default item_type."""
        template = "Recommend {item_type}."
        result = render_template(template)
        assert result == "Recommend items."

    def test_interests_substitution(self):
        """Substitutes {interests} with formatted list."""
        template = "User interests:\n{interests}"
        result = render_template(
            template,
            interests=["Fantasy", "Science Fiction", "Mystery"],
        )
        assert "- Fantasy" in result
        assert "- Science Fiction" in result
        assert "- Mystery" in result

    def test_interests_empty(self):
        """Uses default message for empty interests."""
        template = "Interests:\n{interests}"
        result = render_template(template, interests=[])
        assert "(No specific interests provided)" in result

    def test_interests_none(self):
        """Uses default message for None interests."""
        template = "Interests:\n{interests}"
        result = render_template(template, interests=None)
        assert "(No specific interests provided)" in result

    def test_digest_template_rendering(self):
        """Renders digest template with language substitution."""
        template = get_template("digest")
        result = render_template(template, language="English")
        assert "English" in result

    def test_digest_template_has_html_formatting(self):
        """Digest template uses HTML formatting."""
        template = get_template("digest")
        assert "<h2>" in template
        assert "<ul>" in template
        assert "<li>" in template
        assert "<a href=" in template
        assert "<strong>" in template
        assert "<hr>" in template

    def test_recommendation_template_rendering(self):
        """Renders recommendation template with all parameters."""
        template = get_template("recommendation")
        result = render_template(
            template,
            language="English",
            item_type="movies",
            interests=["Action", "Drama"],
        )
        assert "English" in result
        assert "- Action" in result
        assert "- Drama" in result

    def test_recommendation_template_has_html_formatting(self):
        """Recommendation template uses HTML formatting."""
        template = get_template("recommendation")
        assert "<h2>" in template
        assert "<ol>" in template
        assert "<li>" in template
        assert "<a href=" in template
        assert "<em>" in template
        assert "<hr>" in template

    def test_recommendation_template_uses_item_type(self):
        """Recommendation template includes {item_type} placeholder."""
        template = get_template("recommendation")
        assert "{item_type}" in template
        # Verify it's used in the heading
        assert "Recommended {item_type}" in template

    def test_recommendation_template_output_includes_item_type(self):
        """Rendered recommendation output includes the item_type."""
        template = get_template("recommendation")
        result = render_template(
            template,
            language="English",
            item_type="books",
            interests=["Fiction"],
        )
        assert "Recommended books" in result


class TestSelectPrompt:
    """Tests for prompt selection priority logic."""

    def test_custom_prompt_takes_priority(self):
        """Custom prompt takes priority over template_type."""
        custom = "This is custom."
        result = select_prompt(
            custom_prompt=custom,
            template_type="digest",
            language="German",
        )
        assert "This is custom." in result

    def test_template_type_when_no_custom(self):
        """Uses template_type when custom_prompt is None."""
        result = select_prompt(
            custom_prompt=None,
            template_type="digest",
            language="English",
        )
        # Digest template should be included
        assert "digest" in result.lower() or "summarize" in result.lower()

    def test_default_when_no_custom_or_template(self):
        """Falls back to default when neither custom nor template_type provided."""
        result = select_prompt(
            custom_prompt=None,
            template_type=None,
            language="German",
        )
        # Should return a prompt
        assert len(result) > 0

    def test_invalid_template_type_fallback(self):
        """Falls back to default for invalid template_type."""
        result = select_prompt(
            custom_prompt=None,
            template_type="invalid-type",
            language="English",
        )
        # Should still return a prompt (fallback to default)
        assert len(result) > 0

    def test_template_parameters_forwarded(self):
        """Forwards item_type and interests to template rendering."""
        result = select_prompt(
            custom_prompt=None,
            template_type="recommendation",
            language="English",
            item_type="books",
            interests=["Fantasy", "Mystery"],
        )
        # Should contain the interests
        assert "- Fantasy" in result
        assert "- Mystery" in result

    def test_language_parameter_applied(self):
        """Language parameter is applied to selected prompt."""
        result = select_prompt(
            custom_prompt=None,
            template_type="digest",
            language="Spanish",
        )
        # Should contain the language
        assert "Spanish" in result
