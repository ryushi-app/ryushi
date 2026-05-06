"""Pydantic models for FreshRSS data.

This module defines the Article and Category models that represent
data fetched from FreshRSS servers.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class Category(BaseModel):
    """Represents a FreshRSS feed category.

    Attributes:
        id: Unique identifier for the category from FreshRSS.
        name: Human-readable category name suitable for display.
    """

    id: str
    name: str


class Article(BaseModel):
    """Represents an article fetched from FreshRSS.

    Attributes:
        id: Unique identifier for the article from FreshRSS.
        title: Article title.
        url: Original article URL.
        author: Article author (optional, may be None).
        published_at: Publication timestamp.
        teaser: First 500 characters of article content.
        category_id: ID of the category this article belongs to.
        feed_title: Title of the feed this article came from.
    """

    id: str
    title: str
    url: str
    author: str | None = None
    published_at: datetime
    teaser: str = Field(default="", max_length=500)
    category_id: str
    feed_title: str
