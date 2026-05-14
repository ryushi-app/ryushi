"""FastAPI HTTP server for serving Atom feeds.

This module provides HTTP endpoints for:
- Serving Atom feeds per category
- Feed discovery listing all available feeds
- Health check for monitoring
"""

import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response

from ryushi.feeds.generator import FeedGenerator
from ryushi.feeds.models import FeedIndex
from ryushi.feeds.store import FeedStore

logger = logging.getLogger(__name__)

# Content types
CONTENT_TYPE_ATOM = "application/atom+xml"
CONTENT_TYPE_JSON = "application/json"


def create_app(
    db_path: str | Path = "feeds.db",
    base_url: str = "",
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        db_path: Path to the SQLite database file.
        base_url: Base URL for feed links (e.g., "https://example.com").

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="Ryushi Feed Server",
        description="Serves AI-generated digest feeds in Atom format",
        version="0.1.0",
    )

    # Store instances in app state
    app.state.store = FeedStore(db_path=db_path)
    app.state.generator = FeedGenerator(base_url=base_url)
    app.state.base_url = base_url
    app.state.start_time = datetime.now(UTC)

    async def get_store() -> FeedStore:
        """Dependency to get the FeedStore instance."""
        store: FeedStore = app.state.store
        return store

    async def get_generator() -> FeedGenerator:
        """Dependency to get the FeedGenerator instance."""
        generator: FeedGenerator = app.state.generator
        return generator

    @app.get("/health", response_class=Response)
    async def health_check(
        store: Annotated[FeedStore, Depends(get_store)],
    ) -> Response:
        """Health check endpoint for monitoring.

        Returns JSON with:
        - status: "ok"
        - feeds_count: number of feed categories
        - entries_count: total number of entries
        - uptime_seconds: server uptime
        """
        try:
            categories = await store.list_categories()
            entry_count = await store.get_entry_count()

            uptime = datetime.now(UTC) - app.state.start_time

            health_data = {
                "status": "ok",
                "feeds_count": len(categories),
                "entries_count": entry_count,
                "uptime_seconds": int(uptime.total_seconds()),
            }

            import json

            return Response(
                content=json.dumps(health_data),
                media_type=CONTENT_TYPE_JSON,
            )
        except Exception as e:
            logger.error("Health check failed: %s", e)
            return Response(
                content='{"status": "error"}',
                media_type=CONTENT_TYPE_JSON,
                status_code=500,
            )

    @app.get("/feeds", response_class=Response)
    async def list_feeds(
        request: Request,
        store: Annotated[FeedStore, Depends(get_store)],
    ) -> Response:
        """Feed discovery endpoint listing all available feeds.

        Returns JSON array of feed metadata objects with:
        - category: Human-readable category name
        - slug: URL-safe category slug
        - url: Full URL to the Atom feed
        - last_updated: Timestamp of most recent entry
        - item_count: Number of entries in the feed
        """
        base_url = app.state.base_url or str(request.base_url).rstrip("/")
        categories = await store.list_categories(base_url=base_url)

        feed_index = FeedIndex(feeds=categories)

        return Response(
            content=feed_index.model_dump_json(),
            media_type=CONTENT_TYPE_JSON,
        )

    @app.get("/feeds/{category_slug}/atom.xml", response_class=Response)
    async def get_feed(
        category_slug: str,
        store: Annotated[FeedStore, Depends(get_store)],
        generator: Annotated[FeedGenerator, Depends(get_generator)],
    ) -> Response:
        """Serve Atom feed for a specific category.

        Args:
            category_slug: URL-safe category identifier.

        Returns:
            Atom XML feed with Content-Type: application/atom+xml

        Raises:
            HTTPException: 404 if category not found.
        """
        # Check if category exists
        if not await store.category_exists(category_slug):
            raise HTTPException(
                status_code=404,
                detail=f"Feed not found: '{category_slug}'. Use GET /feeds to see available feeds.",
            )

        entries = await store.get_entries(category_slug)

        # Convert slug back to category name for display
        category_name = category_slug.replace("-", " ").title()

        xml = generator.generate_feed(entries, category_name)

        return Response(
            content=xml,
            media_type=CONTENT_TYPE_ATOM,
        )

    return app


# Default app instance for uvicorn
# Reads configuration from environment variables set by CLI
app = create_app(
    db_path=os.environ.get("RYUSHI_FEEDS_DB", "feeds.db"),
    base_url=os.environ.get("RYUSHI_FEEDS_BASE_URL", ""),
)
