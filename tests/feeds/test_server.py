"""Tests for feed HTTP server."""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from ryushi.feeds.models import FeedEntry
from ryushi.feeds.server import create_app
from ryushi.feeds.store import FeedStore


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_feeds.db"


@pytest.fixture
async def app(temp_db_path):
    """Create test FastAPI app."""
    app = create_app(db_path=temp_db_path, base_url="https://example.com")
    await app.state.store.initialize()
    return app


@pytest.fixture
async def client(app):
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://example.com") as client:
        yield client


@pytest.fixture
async def store(app) -> FeedStore:
    """Get the store from the app."""
    return app.state.store


def make_entry(
    category_slug: str = "technology",
    published: datetime | None = None,
    entry_id: str | None = None,
) -> FeedEntry:
    """Helper to create a FeedEntry for testing."""
    return FeedEntry(
        id=entry_id or f"entry-{datetime.now(UTC).timestamp()}",
        category_slug=category_slug,
        title=f"{category_slug.title()} Digest",
        published=published or datetime.now(UTC),
        content_html="<p>Test content</p>",
        source_urls=["https://example.com/source"],
    )


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    async def test_health_returns_ok(self, client):
        """Test health endpoint returns status ok."""
        response = await client.get("/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert data["status"] == "ok"

    async def test_health_includes_counts(self, client, store):
        """Test health endpoint includes feed and entry counts."""
        # Add some entries
        await store.add_entry(make_entry(category_slug="tech", entry_id="1"))
        await store.add_entry(make_entry(category_slug="tech", entry_id="2"))
        await store.add_entry(make_entry(category_slug="science", entry_id="3"))

        response = await client.get("/health")
        data = response.json()

        assert data["feeds_count"] == 2  # tech and science
        assert data["entries_count"] == 3

    async def test_health_includes_uptime(self, client):
        """Test health endpoint includes uptime."""
        response = await client.get("/health")
        data = response.json()

        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0


class TestFeedsDiscoveryEndpoint:
    """Tests for /feeds endpoint."""

    async def test_feeds_empty(self, client):
        """Test feeds endpoint with no feeds."""
        response = await client.get("/feeds")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert data["feeds"] == []

    async def test_feeds_lists_categories(self, client, store):
        """Test feeds endpoint lists all categories."""
        await store.add_entry(make_entry(category_slug="technology", entry_id="1"))
        await store.add_entry(make_entry(category_slug="science", entry_id="2"))

        response = await client.get("/feeds")
        data = response.json()

        assert len(data["feeds"]) == 2
        slugs = [f["slug"] for f in data["feeds"]]
        assert "technology" in slugs
        assert "science" in slugs

    async def test_feeds_includes_metadata(self, client, store):
        """Test feeds endpoint includes full metadata."""
        published = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        await store.add_entry(
            FeedEntry(
                id="test-entry",
                category_slug="technology",
                title="Tech Digest",
                published=published,
                content_html="<p>Content</p>",
            )
        )

        response = await client.get("/feeds")
        data = response.json()

        assert len(data["feeds"]) == 1
        feed = data["feeds"][0]
        assert feed["category"] == "Technology"
        assert feed["slug"] == "technology"
        assert feed["url"] == "https://example.com/feeds/technology/atom.xml"
        assert feed["item_count"] == 1
        assert "last_updated" in feed


class TestAtomFeedEndpoint:
    """Tests for /feeds/{category_slug}/atom.xml endpoint."""

    async def test_feed_returns_atom_xml(self, client, store):
        """Test feed endpoint returns valid Atom XML."""
        await store.add_entry(make_entry(category_slug="technology", entry_id="1"))

        response = await client.get("/feeds/technology/atom.xml")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/atom+xml"
        assert "<?xml version" in response.text
        assert "<feed" in response.text
        assert "Technology - Ryushi Digest" in response.text

    async def test_feed_includes_entries(self, client, store):
        """Test feed includes stored entries."""
        await store.add_entry(
            FeedEntry(
                id="entry-123",
                category_slug="technology",
                title="Tech Digest - 2024-01-15",
                published=datetime(2024, 1, 15, tzinfo=UTC),
                content_html="<p>Test content</p>",
                source_urls=["https://source.com"],
            )
        )

        response = await client.get("/feeds/technology/atom.xml")

        assert "urn:ryushi:entry:entry-123" in response.text
        assert "Tech Digest - 2024-01-15" in response.text

    async def test_feed_404_unknown_category(self, client):
        """Test feed returns 404 for unknown category."""
        response = await client.get("/feeds/nonexistent/atom.xml")

        assert response.status_code == 404
        data = response.json()
        assert "nonexistent" in data["detail"]
        assert "/feeds" in data["detail"]  # Helpful hint

    async def test_feed_with_multi_word_slug(self, client, store):
        """Test feed works with multi-word category slugs."""
        await store.add_entry(make_entry(category_slug="software-engineering", entry_id="1"))

        response = await client.get("/feeds/software-engineering/atom.xml")

        assert response.status_code == 200
        assert "Software Engineering - Ryushi Digest" in response.text


class TestContentTypes:
    """Tests for correct Content-Type headers."""

    async def test_health_json_content_type(self, client):
        """Test health endpoint has JSON content type."""
        response = await client.get("/health")
        assert response.headers["content-type"] == "application/json"

    async def test_feeds_json_content_type(self, client):
        """Test feeds discovery has JSON content type."""
        response = await client.get("/feeds")
        assert response.headers["content-type"] == "application/json"

    async def test_atom_feed_content_type(self, client, store):
        """Test atom feed has correct content type."""
        await store.add_entry(make_entry())

        response = await client.get("/feeds/technology/atom.xml")
        assert response.headers["content-type"] == "application/atom+xml"
