"""SQLite storage for feed entries.

This module provides async SQLite persistence for FeedEntry records
with a rolling 30-entry retention policy per category.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from ryushi.feeds.exceptions import FeedStorageError
from ryushi.feeds.models import FeedEntry, FeedMeta

logger = logging.getLogger(__name__)

# Default retention limit: number of entries to keep per category
DEFAULT_RETENTION_LIMIT = 30

# SQLite schema for feed_entries table
SCHEMA = """
CREATE TABLE IF NOT EXISTS feed_entries (
    id TEXT PRIMARY KEY,
    category_slug TEXT NOT NULL,
    title TEXT NOT NULL,
    published TEXT NOT NULL,
    content_html TEXT NOT NULL,
    source_urls TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feed_entries_category_published 
ON feed_entries(category_slug, published DESC);
"""


class FeedStore:
    """Async SQLite storage for feed entries.

    Provides CRUD operations for FeedEntry records with automatic
    retention management (30 entries per category by default).

    Attributes:
        db_path: Path to the SQLite database file.
        retention_limit: Maximum entries to keep per category.
    """

    def __init__(
        self,
        db_path: str | Path = "feeds.db",
        retention_limit: int = DEFAULT_RETENTION_LIMIT,
    ):
        """Initialize the FeedStore.

        Args:
            db_path: Path to the SQLite database file.
            retention_limit: Maximum entries per category (default: 30).
        """
        self.db_path = Path(db_path)
        self.retention_limit = retention_limit
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the database schema.

        Creates the feed_entries table and indexes if they don't exist.
        This method is idempotent and safe to call multiple times.

        Raises:
            FeedStorageError: If database initialization fails.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.executescript(SCHEMA)
                await db.commit()
            self._initialized = True
            logger.info("Feed store initialized at %s", self.db_path)
        except Exception as e:
            raise FeedStorageError(f"Failed to initialize database: {e}") from e

    async def _ensure_initialized(self) -> None:
        """Ensure the database is initialized before operations."""
        if not self._initialized:
            await self.initialize()

    async def add_entry(self, entry: FeedEntry) -> None:
        """Add a feed entry and enforce retention limit.

        Stores the entry and removes the oldest entries if the category
        exceeds the retention limit.

        Args:
            entry: The FeedEntry to store.

        Raises:
            FeedStorageError: If the operation fails.
        """
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Insert the new entry
                await db.execute(
                    """
                    INSERT OR REPLACE INTO feed_entries 
                    (id, category_slug, title, published, content_html, source_urls, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.id,
                        entry.category_slug,
                        entry.title,
                        entry.published.isoformat(),
                        entry.content_html,
                        json.dumps(entry.source_urls),
                        datetime.now(UTC).isoformat(),
                    ),
                )

                # Enforce retention limit: delete oldest entries beyond limit
                await db.execute(
                    """
                    DELETE FROM feed_entries 
                    WHERE category_slug = ? 
                    AND id NOT IN (
                        SELECT id FROM feed_entries 
                        WHERE category_slug = ? 
                        ORDER BY published DESC 
                        LIMIT ?
                    )
                    """,
                    (entry.category_slug, entry.category_slug, self.retention_limit),
                )

                await db.commit()
                logger.debug("Added entry %s to category %s", entry.id, entry.category_slug)

        except Exception as e:
            raise FeedStorageError(
                f"Failed to add entry: {e}",
                category_slug=entry.category_slug,
            ) from e

    async def get_entries(self, category_slug: str) -> list[FeedEntry]:
        """Get all entries for a category, newest first.

        Args:
            category_slug: The category slug to retrieve entries for.

        Returns:
            List of FeedEntry objects ordered by published date descending.

        Raises:
            FeedStorageError: If the operation fails.
        """
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """
                    SELECT id, category_slug, title, published, content_html, source_urls
                    FROM feed_entries
                    WHERE category_slug = ?
                    ORDER BY published DESC
                    """,
                    (category_slug,),
                )
                rows = await cursor.fetchall()

                entries = []
                for row in rows:
                    entries.append(
                        FeedEntry(
                            id=row["id"],
                            category_slug=row["category_slug"],
                            title=row["title"],
                            published=datetime.fromisoformat(row["published"]),
                            content_html=row["content_html"],
                            source_urls=json.loads(row["source_urls"]),
                        )
                    )

                return entries

        except Exception as e:
            raise FeedStorageError(
                f"Failed to get entries: {e}",
                category_slug=category_slug,
            ) from e

    async def list_categories(self, base_url: str = "") -> list[FeedMeta]:
        """List all categories with feed metadata.

        Args:
            base_url: Base URL for constructing feed URLs.

        Returns:
            List of FeedMeta objects for each category with entries.

        Raises:
            FeedStorageError: If the operation fails.
        """
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """
                    SELECT 
                        category_slug,
                        MAX(published) as last_updated,
                        COUNT(*) as item_count
                    FROM feed_entries
                    GROUP BY category_slug
                    ORDER BY last_updated DESC
                    """
                )
                rows = await cursor.fetchall()

                categories = []
                for row in rows:
                    slug = row["category_slug"]
                    # Convert slug back to title case for category name
                    category_name = slug.replace("-", " ").title()

                    categories.append(
                        FeedMeta(
                            category=category_name,
                            slug=slug,
                            url=f"{base_url}/feeds/{slug}/atom.xml",
                            last_updated=datetime.fromisoformat(row["last_updated"]),
                            item_count=row["item_count"],
                        )
                    )

                return categories

        except Exception as e:
            raise FeedStorageError(f"Failed to list categories: {e}") from e

    async def get_entry_count(self, category_slug: str | None = None) -> int:
        """Get the count of entries, optionally filtered by category.

        Args:
            category_slug: Optional category to filter by.

        Returns:
            Number of entries.

        Raises:
            FeedStorageError: If the operation fails.
        """
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                if category_slug:
                    cursor = await db.execute(
                        "SELECT COUNT(*) FROM feed_entries WHERE category_slug = ?",
                        (category_slug,),
                    )
                else:
                    cursor = await db.execute("SELECT COUNT(*) FROM feed_entries")

                result = await cursor.fetchone()
                return result[0] if result else 0

        except Exception as e:
            raise FeedStorageError(
                f"Failed to count entries: {e}",
                category_slug=category_slug,
            ) from e

    async def category_exists(self, category_slug: str) -> bool:
        """Check if a category has any entries.

        Args:
            category_slug: The category slug to check.

        Returns:
            True if the category has entries, False otherwise.
        """
        count = await self.get_entry_count(category_slug)
        return count > 0
