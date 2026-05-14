"""Pydantic models for feed generation and storage.

This module defines the FeedEntry, FeedMeta, and FeedIndex models used
by the feed generator and storage.
"""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class FeedEntry(BaseModel):
    """Represents a single entry in an Atom feed.

    Attributes:
        id: Unique identifier (UUID string).
        category_slug: URL-safe slug for the category.
        title: Entry title (e.g., "Technology Digest - 2024-01-15").
        published: Timestamp when the digest was generated.
        content_html: HTML-rendered digest summary.
        source_urls: URLs referenced in the digest.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    category_slug: str
    title: str
    published: datetime = Field(default_factory=lambda: datetime.now(UTC))
    content_html: str
    source_urls: list[str] = Field(default_factory=list)


class FeedMeta(BaseModel):
    """Metadata about a feed category for the discovery endpoint.

    Attributes:
        category: Human-readable category name.
        slug: URL-safe category slug.
        url: Full URL to the feed.
        last_updated: Timestamp of the most recent entry.
        item_count: Number of entries in the feed.
    """

    category: str
    slug: str
    url: str
    last_updated: datetime | None = None
    item_count: int = 0


class FeedIndex(BaseModel):
    """Response model for the feed discovery endpoint.

    Attributes:
        feeds: List of all available feeds with metadata.
    """

    feeds: list[FeedMeta] = Field(default_factory=list)
