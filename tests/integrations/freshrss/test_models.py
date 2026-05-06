"""Tests for FreshRSS Pydantic models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from ryushi.integrations.freshrss.models import Article, Category


class TestCategory:
    """Tests for the Category model."""

    def test_category_with_valid_data(self):
        """Category accepts valid id and name."""
        category = Category(id="user/-/label/Tech", name="Technology")
        assert category.id == "user/-/label/Tech"
        assert category.name == "Technology"

    def test_category_missing_id_raises_error(self):
        """Category requires id field."""
        with pytest.raises(ValidationError):
            Category(name="Technology")

    def test_category_missing_name_raises_error(self):
        """Category requires name field."""
        with pytest.raises(ValidationError):
            Category(id="user/-/label/Tech")

    def test_category_serialization(self):
        """Category can be serialized to dict."""
        category = Category(id="user/-/label/News", name="News")
        data = category.model_dump()
        assert data == {"id": "user/-/label/News", "name": "News"}


class TestArticle:
    """Tests for the Article model."""

    def test_article_with_complete_data(self):
        """Article accepts all fields including optional author."""
        article = Article(
            id="tag:google.com,2005:reader/item/123abc",
            title="Test Article",
            url="https://example.com/article",
            author="John Doe",
            published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            teaser="This is the article content preview...",
            category_id="user/-/label/Tech",
            feed_title="Example Blog",
        )
        assert article.id == "tag:google.com,2005:reader/item/123abc"
        assert article.title == "Test Article"
        assert article.url == "https://example.com/article"
        assert article.author == "John Doe"
        assert article.published_at == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert article.teaser == "This is the article content preview..."
        assert article.category_id == "user/-/label/Tech"
        assert article.feed_title == "Example Blog"

    def test_article_without_author(self):
        """Article author field is optional and defaults to None."""
        article = Article(
            id="123",
            title="Test",
            url="https://example.com",
            published_at=datetime.now(timezone.utc),
            teaser="Content",
            category_id="cat1",
            feed_title="Feed",
        )
        assert article.author is None

    def test_article_empty_teaser_default(self):
        """Article teaser defaults to empty string."""
        article = Article(
            id="123",
            title="Test",
            url="https://example.com",
            published_at=datetime.now(timezone.utc),
            category_id="cat1",
            feed_title="Feed",
        )
        assert article.teaser == ""

    def test_article_teaser_max_length(self):
        """Article teaser is truncated to 500 characters by validation."""
        long_content = "x" * 600
        with pytest.raises(ValidationError) as exc_info:
            Article(
                id="123",
                title="Test",
                url="https://example.com",
                published_at=datetime.now(timezone.utc),
                teaser=long_content,
                category_id="cat1",
                feed_title="Feed",
            )
        assert "max_length" in str(exc_info.value).lower() or "500" in str(exc_info.value)

    def test_article_teaser_exactly_500_chars(self):
        """Article teaser accepts exactly 500 characters."""
        content_500 = "x" * 500
        article = Article(
            id="123",
            title="Test",
            url="https://example.com",
            published_at=datetime.now(timezone.utc),
            teaser=content_500,
            category_id="cat1",
            feed_title="Feed",
        )
        assert len(article.teaser) == 500

    def test_article_missing_required_fields(self):
        """Article raises error when required fields are missing."""
        with pytest.raises(ValidationError):
            Article(title="Test")

    def test_article_serialization(self):
        """Article can be serialized to dict."""
        published = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        article = Article(
            id="123",
            title="Test",
            url="https://example.com",
            author="Author",
            published_at=published,
            teaser="Preview",
            category_id="cat1",
            feed_title="Feed",
        )
        data = article.model_dump()
        assert data["id"] == "123"
        assert data["title"] == "Test"
        assert data["author"] == "Author"
        assert data["published_at"] == published
