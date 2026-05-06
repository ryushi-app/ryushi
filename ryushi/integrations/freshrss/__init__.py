"""FreshRSS integration for Ryushi.

This module provides a client for interacting with FreshRSS servers
via the Google Reader API.

Example:
    from ryushi.integrations.freshrss import FreshRSSClient, Article, Category

    client = FreshRSSClient()
    categories = await client.get_categories()
    articles = await client.get_unread_items(category_id="user/-/label/Tech")

Environment Variables:
    FRESHRSS_URL: Base URL of the FreshRSS instance
    FRESHRSS_USERNAME: Username for authentication
    FRESHRSS_PASSWORD: Password for authentication
"""

from .client import FreshRSSClient
from .exceptions import AuthError, FetchError, FreshRSSError, RateLimitError
from .models import Article, Category

__all__ = [
    "FreshRSSClient",
    "Article",
    "Category",
    "FreshRSSError",
    "AuthError",
    "FetchError",
    "RateLimitError",
]
