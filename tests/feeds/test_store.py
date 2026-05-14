"""Tests for feed storage."""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ryushi.feeds.models import FeedEntry
from ryushi.feeds.store import FeedStore


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_feeds.db"


@pytest.fixture
async def store(temp_db_path):
    """Create an initialized FeedStore."""
    store = FeedStore(db_path=temp_db_path)
    await store.initialize()
    return store


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
        source_urls=["https://example.com/1"],
    )


class TestFeedStoreInitialization:
    """Tests for FeedStore initialization."""

    async def test_initialize_creates_database(self, temp_db_path):
        """Test that initialize creates the database file."""
        store = FeedStore(db_path=temp_db_path)
        assert not temp_db_path.exists()

        await store.initialize()

        assert temp_db_path.exists()

    async def test_initialize_is_idempotent(self, temp_db_path):
        """Test that initialize can be called multiple times."""
        store = FeedStore(db_path=temp_db_path)
        await store.initialize()
        await store.initialize()  # Should not raise

    async def test_auto_initialize_on_first_operation(self, temp_db_path):
        """Test that store auto-initializes on first operation."""
        store = FeedStore(db_path=temp_db_path)
        assert not temp_db_path.exists()

        # Operation should trigger initialization
        entries = await store.get_entries("nonexistent")

        assert temp_db_path.exists()
        assert entries == []


class TestFeedStoreAddEntry:
    """Tests for adding entries."""

    async def test_add_single_entry(self, store):
        """Test adding a single entry."""
        entry = make_entry()
        await store.add_entry(entry)

        entries = await store.get_entries(entry.category_slug)
        assert len(entries) == 1
        assert entries[0].id == entry.id

    async def test_add_multiple_entries(self, store):
        """Test adding multiple entries to same category."""
        entries_to_add = [
            make_entry(entry_id=f"entry-{i}", published=datetime.now(UTC) - timedelta(hours=i))
            for i in range(5)
        ]

        for entry in entries_to_add:
            await store.add_entry(entry)

        retrieved = await store.get_entries("technology")
        assert len(retrieved) == 5

    async def test_entry_persists_all_fields(self, store):
        """Test that all entry fields are persisted correctly."""
        published = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        entry = FeedEntry(
            id="test-id-123",
            category_slug="software-engineering",
            title="SE Digest - 2024-01-15",
            published=published,
            content_html="<h1>Title</h1><p>Content</p>",
            source_urls=["https://a.com", "https://b.com"],
        )

        await store.add_entry(entry)
        retrieved = await store.get_entries("software-engineering")

        assert len(retrieved) == 1
        r = retrieved[0]
        assert r.id == "test-id-123"
        assert r.category_slug == "software-engineering"
        assert r.title == "SE Digest - 2024-01-15"
        assert r.published == published
        assert r.content_html == "<h1>Title</h1><p>Content</p>"
        assert r.source_urls == ["https://a.com", "https://b.com"]

    async def test_replace_entry_with_same_id(self, store):
        """Test that adding an entry with same ID replaces it."""
        entry1 = FeedEntry(
            id="same-id",
            category_slug="tech",
            title="Original",
            published=datetime.now(UTC),
            content_html="<p>Original</p>",
        )
        entry2 = FeedEntry(
            id="same-id",
            category_slug="tech",
            title="Updated",
            published=datetime.now(UTC),
            content_html="<p>Updated</p>",
        )

        await store.add_entry(entry1)
        await store.add_entry(entry2)

        entries = await store.get_entries("tech")
        assert len(entries) == 1
        assert entries[0].title == "Updated"


class TestFeedStoreRetention:
    """Tests for retention limit enforcement."""

    async def test_retention_limit_enforced(self, temp_db_path):
        """Test that retention limit removes oldest entries."""
        store = FeedStore(db_path=temp_db_path, retention_limit=5)
        await store.initialize()

        # Add 7 entries
        base_time = datetime.now(UTC)
        for i in range(7):
            entry = make_entry(
                entry_id=f"entry-{i}",
                published=base_time - timedelta(hours=i),
            )
            await store.add_entry(entry)

        entries = await store.get_entries("technology")
        assert len(entries) == 5

        # Should have the 5 newest entries (entry-0 through entry-4)
        entry_ids = [e.id for e in entries]
        assert "entry-0" in entry_ids
        assert "entry-4" in entry_ids
        assert "entry-5" not in entry_ids
        assert "entry-6" not in entry_ids

    async def test_retention_per_category(self, temp_db_path):
        """Test that retention is per-category."""
        store = FeedStore(db_path=temp_db_path, retention_limit=3)
        await store.initialize()

        # Add 4 entries to category A
        for i in range(4):
            entry = make_entry(category_slug="category-a", entry_id=f"a-{i}")
            await store.add_entry(entry)

        # Add 2 entries to category B
        for i in range(2):
            entry = make_entry(category_slug="category-b", entry_id=f"b-{i}")
            await store.add_entry(entry)

        # Category A should have 3 entries (retention limit)
        entries_a = await store.get_entries("category-a")
        assert len(entries_a) == 3

        # Category B should still have 2 entries (under limit)
        entries_b = await store.get_entries("category-b")
        assert len(entries_b) == 2

    async def test_default_retention_limit(self, store):
        """Test that default retention limit is 30."""
        assert store.retention_limit == 30


class TestFeedStoreGetEntries:
    """Tests for retrieving entries."""

    async def test_get_entries_empty_category(self, store):
        """Test getting entries from empty category."""
        entries = await store.get_entries("nonexistent")
        assert entries == []

    async def test_get_entries_ordered_newest_first(self, store):
        """Test that entries are returned newest first."""
        base_time = datetime.now(UTC)
        entries_to_add = [
            make_entry(entry_id="oldest", published=base_time - timedelta(days=2)),
            make_entry(entry_id="middle", published=base_time - timedelta(days=1)),
            make_entry(entry_id="newest", published=base_time),
        ]

        for entry in entries_to_add:
            await store.add_entry(entry)

        retrieved = await store.get_entries("technology")

        assert len(retrieved) == 3
        assert retrieved[0].id == "newest"
        assert retrieved[1].id == "middle"
        assert retrieved[2].id == "oldest"


class TestFeedStoreListCategories:
    """Tests for listing categories."""

    async def test_list_categories_empty(self, store):
        """Test listing categories when none exist."""
        categories = await store.list_categories()
        assert categories == []

    async def test_list_categories_single(self, store):
        """Test listing a single category."""
        entry = make_entry(category_slug="technology")
        await store.add_entry(entry)

        categories = await store.list_categories(base_url="https://example.com")

        assert len(categories) == 1
        cat = categories[0]
        assert cat.category == "Technology"
        assert cat.slug == "technology"
        assert cat.url == "https://example.com/feeds/technology/atom.xml"
        assert cat.item_count == 1
        assert cat.last_updated is not None

    async def test_list_categories_multiple(self, store):
        """Test listing multiple categories."""
        await store.add_entry(make_entry(category_slug="tech", entry_id="t1"))
        await store.add_entry(make_entry(category_slug="tech", entry_id="t2"))
        await store.add_entry(make_entry(category_slug="science", entry_id="s1"))

        categories = await store.list_categories()

        assert len(categories) == 2
        slugs = [c.slug for c in categories]
        assert "tech" in slugs
        assert "science" in slugs

        tech_cat = next(c for c in categories if c.slug == "tech")
        assert tech_cat.item_count == 2

        science_cat = next(c for c in categories if c.slug == "science")
        assert science_cat.item_count == 1

    async def test_list_categories_ordered_by_last_updated(self, store):
        """Test that categories are ordered by last_updated descending."""
        base_time = datetime.now(UTC)

        # Add older entry to category A
        await store.add_entry(
            make_entry(
                category_slug="older-category",
                entry_id="old",
                published=base_time - timedelta(days=1),
            )
        )

        # Add newer entry to category B
        await store.add_entry(
            make_entry(
                category_slug="newer-category",
                entry_id="new",
                published=base_time,
            )
        )

        categories = await store.list_categories()

        assert len(categories) == 2
        assert categories[0].slug == "newer-category"
        assert categories[1].slug == "older-category"


class TestFeedStoreHelpers:
    """Tests for helper methods."""

    async def test_get_entry_count_all(self, store):
        """Test counting all entries."""
        await store.add_entry(make_entry(category_slug="a", entry_id="1"))
        await store.add_entry(make_entry(category_slug="a", entry_id="2"))
        await store.add_entry(make_entry(category_slug="b", entry_id="3"))

        count = await store.get_entry_count()
        assert count == 3

    async def test_get_entry_count_by_category(self, store):
        """Test counting entries by category."""
        await store.add_entry(make_entry(category_slug="a", entry_id="1"))
        await store.add_entry(make_entry(category_slug="a", entry_id="2"))
        await store.add_entry(make_entry(category_slug="b", entry_id="3"))

        count_a = await store.get_entry_count("a")
        count_b = await store.get_entry_count("b")

        assert count_a == 2
        assert count_b == 1

    async def test_category_exists(self, store):
        """Test checking if category exists."""
        assert not await store.category_exists("tech")

        await store.add_entry(make_entry(category_slug="tech"))

        assert await store.category_exists("tech")
        assert not await store.category_exists("other")
