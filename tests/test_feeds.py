"""Tests for feed functionality."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ryushi.feeds.models import FeedEntry, FeedIndex, FeedMeta


class TestFeedEntry:
    """Tests for FeedEntry model."""

    def test_create_feed_entry_with_defaults(self):
        """Test creating a FeedEntry with minimal required fields."""
        entry = FeedEntry(
            category_slug="technology",
            title="Technology Digest - 2024-01-15",
            content_html="<p>Summary of articles</p>",
        )
        assert entry.category_slug == "technology"
        assert entry.title == "Technology Digest - 2024-01-15"
        assert entry.content_html == "<p>Summary of articles</p>"
        assert entry.id is not None
        assert entry.published is not None
        assert entry.source_urls == []

    def test_create_feed_entry_with_all_fields(self):
        """Test creating a FeedEntry with all fields specified."""
        published = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        entry = FeedEntry(
            id="test-id-123",
            category_slug="software-engineering",
            title="Software Engineering Digest",
            published=published,
            content_html="<h1>Digest</h1><p>Content here</p>",
            source_urls=["https://example.com/1", "https://example.com/2"],
        )
        assert entry.id == "test-id-123"
        assert entry.category_slug == "software-engineering"
        assert entry.published == published
        assert len(entry.source_urls) == 2

    def test_feed_entry_id_auto_generated(self):
        """Test that FeedEntry generates unique IDs."""
        entry1 = FeedEntry(
            category_slug="tech",
            title="Title 1",
            content_html="<p>Content</p>",
        )
        entry2 = FeedEntry(
            category_slug="tech",
            title="Title 2",
            content_html="<p>Content</p>",
        )
        assert entry1.id != entry2.id

    def test_feed_entry_requires_category_slug(self):
        """Test that category_slug is required."""
        with pytest.raises(ValidationError):
            FeedEntry(
                title="Test",
                content_html="<p>Content</p>",
            )

    def test_feed_entry_requires_title(self):
        """Test that title is required."""
        with pytest.raises(ValidationError):
            FeedEntry(
                category_slug="tech",
                content_html="<p>Content</p>",
            )

    def test_feed_entry_requires_content_html(self):
        """Test that content_html is required."""
        with pytest.raises(ValidationError):
            FeedEntry(
                category_slug="tech",
                title="Test",
            )


class TestFeedMeta:
    """Tests for FeedMeta model."""

    def test_create_feed_meta_minimal(self):
        """Test creating FeedMeta with minimal fields."""
        meta = FeedMeta(
            category="Technology",
            slug="technology",
            url="/feeds/technology/atom.xml",
        )
        assert meta.category == "Technology"
        assert meta.slug == "technology"
        assert meta.url == "/feeds/technology/atom.xml"
        assert meta.last_updated is None
        assert meta.item_count == 0

    def test_create_feed_meta_complete(self):
        """Test creating FeedMeta with all fields."""
        last_updated = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        meta = FeedMeta(
            category="Software Engineering",
            slug="software-engineering",
            url="/feeds/software-engineering/atom.xml",
            last_updated=last_updated,
            item_count=25,
        )
        assert meta.category == "Software Engineering"
        assert meta.last_updated == last_updated
        assert meta.item_count == 25

    def test_feed_meta_requires_category(self):
        """Test that category is required."""
        with pytest.raises(ValidationError):
            FeedMeta(
                slug="tech",
                url="/feeds/tech/atom.xml",
            )

    def test_feed_meta_requires_slug(self):
        """Test that slug is required."""
        with pytest.raises(ValidationError):
            FeedMeta(
                category="Tech",
                url="/feeds/tech/atom.xml",
            )

    def test_feed_meta_requires_url(self):
        """Test that url is required."""
        with pytest.raises(ValidationError):
            FeedMeta(
                category="Tech",
                slug="tech",
            )


class TestFeedIndex:
    """Tests for FeedIndex model."""

    def test_create_empty_feed_index(self):
        """Test creating an empty FeedIndex."""
        index = FeedIndex()
        assert index.feeds == []

    def test_create_feed_index_with_feeds(self):
        """Test creating FeedIndex with multiple feeds."""
        meta1 = FeedMeta(
            category="Technology",
            slug="technology",
            url="/feeds/technology/atom.xml",
            item_count=10,
        )
        meta2 = FeedMeta(
            category="Science",
            slug="science",
            url="/feeds/science/atom.xml",
            item_count=5,
        )
        index = FeedIndex(feeds=[meta1, meta2])
        assert len(index.feeds) == 2
        assert index.feeds[0].category == "Technology"
        assert index.feeds[1].category == "Science"

    def test_feed_index_serialization(self):
        """Test that FeedIndex serializes to JSON correctly."""
        meta = FeedMeta(
            category="Tech",
            slug="tech",
            url="/feeds/tech/atom.xml",
            item_count=3,
        )
        index = FeedIndex(feeds=[meta])
        data = index.model_dump()
        assert "feeds" in data
        assert len(data["feeds"]) == 1
        assert data["feeds"][0]["category"] == "Tech"
