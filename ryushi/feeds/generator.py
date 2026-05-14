"""Feed generation from Digest objects.

This module provides functionality to generate Atom 1.0 feeds from
Digest objects, including slug generation and markdown rendering.
"""

import re
from datetime import UTC, datetime

from feedgen.feed import FeedGenerator as FeedGenLib  # type: ignore[import-untyped]
from markdown_it import MarkdownIt

from ryushi.digest.models import Digest
from ryushi.feeds.exceptions import FeedGenerationError
from ryushi.feeds.models import FeedEntry


def generate_slug(category_name: str) -> str:
    """Generate a URL-safe slug from a category name.

    Converts category names to lowercase, replaces spaces and special
    characters with hyphens, and removes any non-alphanumeric characters.

    Args:
        category_name: Human-readable category name.

    Returns:
        URL-safe slug (e.g., "Software Engineering" -> "software-engineering").

    Examples:
        >>> generate_slug("Technology")
        'technology'
        >>> generate_slug("Software Engineering")
        'software-engineering'
        >>> generate_slug("AI & Machine Learning")
        'ai-machine-learning'
    """
    # Convert to lowercase
    slug = category_name.lower()
    # Replace spaces and special characters with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)
    return slug


def render_markdown_to_html(markdown_text: str) -> str:
    """Render markdown text to HTML.

    Uses CommonMark-compliant markdown-it-py for rendering.

    Args:
        markdown_text: Markdown-formatted text.

    Returns:
        HTML-rendered content.
    """
    md = MarkdownIt()
    return str(md.render(markdown_text))


def digest_to_entry(digest: Digest) -> FeedEntry:
    """Convert a Digest object to a FeedEntry.

    Creates a FeedEntry with:
    - ID from the digest ID
    - Category slug from category_name
    - Title including category and date
    - HTML content from markdown summary
    - Source URLs preserved

    Args:
        digest: The Digest object to convert.

    Returns:
        FeedEntry ready for storage and feed generation.
    """
    category_slug = generate_slug(digest.category_name)
    date_str = digest.generated_at.strftime("%Y-%m-%d")
    title = f"{digest.category_name} Digest - {date_str}"
    content_html = render_markdown_to_html(digest.summary)

    return FeedEntry(
        id=digest.id,
        category_slug=category_slug,
        title=title,
        published=digest.generated_at,
        content_html=content_html,
        source_urls=digest.source_urls,
    )


class FeedGenerator:
    """Generates Atom 1.0 feeds from FeedEntry objects.

    Attributes:
        base_url: Base URL for feed links (e.g., "https://example.com").
        author_name: Author name for the feed (default: "Ryushi").
    """

    def __init__(self, base_url: str = "", author_name: str = "Ryushi"):
        """Initialize the FeedGenerator.

        Args:
            base_url: Base URL for feed links.
            author_name: Author name for the feed.
        """
        self.base_url = base_url.rstrip("/")
        self.author_name = author_name

    def generate_feed(
        self,
        entries: list[FeedEntry],
        category_name: str,
    ) -> str:
        """Generate an Atom 1.0 feed from a list of entries.

        Creates a valid Atom feed with:
        - Feed id as URN based on category slug
        - Feed title as "{category} - Ryushi Digest"
        - Feed updated as most recent entry timestamp
        - Each entry with proper id, title, published, content, and links

        Args:
            entries: List of FeedEntry objects to include.
            category_name: Human-readable category name.

        Returns:
            Atom 1.0 XML as a string.

        Raises:
            FeedGenerationError: If feed generation fails.
        """
        try:
            category_slug = generate_slug(category_name)
            fg = FeedGenLib()

            # Set feed metadata
            feed_id = f"urn:ryushi:feed:{category_slug}"
            fg.id(feed_id)
            fg.title(f"{category_name} - Ryushi Digest")
            fg.author({"name": self.author_name})

            # Set feed link
            feed_url = f"{self.base_url}/feeds/{category_slug}/atom.xml"
            fg.link(href=feed_url, rel="self")
            fg.link(href=self.base_url or "/", rel="alternate")

            # Set updated timestamp (most recent entry or now)
            if entries:
                latest = max(e.published for e in entries)
                fg.updated(latest)
            else:
                fg.updated(datetime.now(UTC))

            # Add entries (oldest first since feedgen prepends entries)
            # This results in newest entries appearing first in the output
            sorted_entries = sorted(entries, key=lambda e: e.published, reverse=False)
            for entry in sorted_entries:
                fe = fg.add_entry()
                entry_id = f"urn:ryushi:entry:{entry.id}"
                fe.id(entry_id)
                fe.title(entry.title)
                fe.published(entry.published)
                fe.updated(entry.published)
                fe.content(entry.content_html, type="html")

                # Add source URLs as links
                for url in entry.source_urls:
                    fe.link(href=url, rel="related")

            # Generate Atom XML
            xml_bytes: bytes = fg.atom_str(pretty=True)
            return xml_bytes.decode("utf-8")

        except Exception as e:
            raise FeedGenerationError(
                f"Failed to generate feed: {e}",
                category_slug=generate_slug(category_name),
            ) from e
