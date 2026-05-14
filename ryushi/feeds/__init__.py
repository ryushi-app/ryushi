"""Feed generation and serving module for Ryushi.

This module provides Atom feed generation from Digest objects,
SQLite persistence for feed entries, and HTTP serving capabilities.

Main components:
    FeedGenerator: Generates Atom 1.0 feeds from FeedEntry objects.
    FeedStore: Async SQLite storage with retention management.
    FeedEntry: Model representing a single feed entry.
    FeedError: Base exception for feed-related errors.

Usage:
    from ryushi.feeds import FeedGenerator, FeedStore, FeedEntry

    # Create and store an entry
    store = FeedStore(db_path="feeds.db")
    await store.add_entry(entry)

    # Generate feed XML
    generator = FeedGenerator(base_url="https://example.com")
    entries = await store.get_entries("technology")
    xml = generator.generate_feed(entries, "Technology")
"""

from ryushi.feeds.exceptions import (
    FeedError,
    FeedGenerationError,
    FeedNotFoundError,
    FeedStorageError,
)
from ryushi.feeds.generator import (
    FeedGenerator,
    digest_to_entry,
    generate_slug,
    render_markdown_to_html,
)
from ryushi.feeds.models import FeedEntry, FeedIndex, FeedMeta
from ryushi.feeds.store import FeedStore

__all__ = [
    # Core classes
    "FeedGenerator",
    "FeedStore",
    # Models
    "FeedEntry",
    "FeedMeta",
    "FeedIndex",
    # Exceptions
    "FeedError",
    "FeedGenerationError",
    "FeedNotFoundError",
    "FeedStorageError",
    # Utilities
    "digest_to_entry",
    "generate_slug",
    "render_markdown_to_html",
]
