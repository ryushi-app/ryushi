"""Tests for feed generation."""

import xml.etree.ElementTree as ET
from datetime import UTC, datetime

import pytest

from ryushi.digest.models import Digest
from ryushi.feeds.generator import (
    FeedGenerator,
    digest_to_entry,
    generate_slug,
    render_markdown_to_html,
)
from ryushi.feeds.models import FeedEntry


class TestGenerateSlug:
    """Tests for the generate_slug function."""

    def test_simple_category_name(self):
        """Test slug generation for simple category name."""
        assert generate_slug("Technology") == "technology"

    def test_multi_word_category_name(self):
        """Test slug generation for multi-word category name."""
        assert generate_slug("Software Engineering") == "software-engineering"

    def test_category_with_special_characters(self):
        """Test slug generation with special characters."""
        assert generate_slug("AI & Machine Learning") == "ai-machine-learning"

    def test_category_with_numbers(self):
        """Test slug generation with numbers."""
        assert generate_slug("Web 3.0") == "web-3-0"

    def test_category_with_extra_spaces(self):
        """Test slug generation with extra spaces."""
        assert generate_slug("  Multiple   Spaces  ") == "multiple-spaces"

    def test_empty_category_name(self):
        """Test slug generation with empty string."""
        assert generate_slug("") == ""

    def test_category_with_unicode(self):
        """Test slug generation with unicode characters."""
        # Unicode is stripped, only alphanumeric remains
        result = generate_slug("Café & News")
        assert result == "caf-news"


class TestRenderMarkdownToHtml:
    """Tests for markdown to HTML rendering."""

    def test_simple_paragraph(self):
        """Test rendering a simple paragraph."""
        html = render_markdown_to_html("Hello world")
        assert "<p>Hello world</p>" in html

    def test_heading(self):
        """Test rendering headings."""
        html = render_markdown_to_html("# Title")
        assert "<h1>Title</h1>" in html

    def test_bold_text(self):
        """Test rendering bold text."""
        html = render_markdown_to_html("**bold**")
        assert "<strong>bold</strong>" in html

    def test_links(self):
        """Test rendering links."""
        html = render_markdown_to_html("[link](https://example.com)")
        assert 'href="https://example.com"' in html

    def test_list(self):
        """Test rendering unordered list."""
        html = render_markdown_to_html("- item 1\n- item 2")
        assert "<ul>" in html
        assert "<li>" in html


class TestDigestToEntry:
    """Tests for converting Digest to FeedEntry."""

    def test_converts_digest_to_entry(self):
        """Test basic conversion of Digest to FeedEntry."""
        digest = Digest(
            id="test-digest-id",
            category_name="Technology",
            generated_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            summary="# Summary\n\nThis is a test digest.",
            article_count=5,
            source_urls=["https://example.com/1", "https://example.com/2"],
            model_used="gpt-4o-mini",
        )

        entry = digest_to_entry(digest)

        assert entry.id == "test-digest-id"
        assert entry.category_slug == "technology"
        assert entry.title == "Technology Digest - 2024-01-15"
        assert entry.published == datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        assert "<h1>Summary</h1>" in entry.content_html
        assert entry.source_urls == ["https://example.com/1", "https://example.com/2"]

    def test_multi_word_category_slug(self):
        """Test category slug generation for multi-word names."""
        digest = Digest(
            category_name="Software Engineering",
            generated_at=datetime(2024, 1, 15, tzinfo=UTC),
            summary="Test",
            article_count=1,
            model_used="test",
        )

        entry = digest_to_entry(digest)
        assert entry.category_slug == "software-engineering"


class TestFeedGenerator:
    """Tests for the FeedGenerator class."""

    def test_generate_empty_feed(self):
        """Test generating a feed with no entries."""
        generator = FeedGenerator(base_url="https://example.com")
        xml = generator.generate_feed([], "Technology")

        # Parse and validate XML
        root = ET.fromstring(xml)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        assert root.find("atom:title", ns).text == "Technology - Ryushi Digest"
        assert root.find("atom:id", ns).text == "urn:ryushi:feed:technology"
        assert root.find("atom:author/atom:name", ns).text == "Ryushi"

    def test_generate_feed_with_entries(self):
        """Test generating a feed with entries."""
        entries = [
            FeedEntry(
                id="entry-1",
                category_slug="technology",
                title="Technology Digest - 2024-01-15",
                published=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
                content_html="<p>First digest</p>",
                source_urls=["https://example.com/1"],
            ),
            FeedEntry(
                id="entry-2",
                category_slug="technology",
                title="Technology Digest - 2024-01-14",
                published=datetime(2024, 1, 14, 10, 0, 0, tzinfo=UTC),
                content_html="<p>Second digest</p>",
                source_urls=[],
            ),
        ]

        generator = FeedGenerator(base_url="https://example.com")
        xml = generator.generate_feed(entries, "Technology")

        # Parse and validate XML
        root = ET.fromstring(xml)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        # Check feed metadata
        assert root.find("atom:title", ns).text == "Technology - Ryushi Digest"

        # Check entries exist
        entry_elements = root.findall("atom:entry", ns)
        assert len(entry_elements) == 2

        # Check first entry (should be newest due to sorting)
        first_entry = entry_elements[0]
        assert first_entry.find("atom:id", ns).text == "urn:ryushi:entry:entry-1"
        assert first_entry.find("atom:title", ns).text == "Technology Digest - 2024-01-15"

    def test_feed_has_self_link(self):
        """Test that feed has self link."""
        generator = FeedGenerator(base_url="https://example.com")
        xml = generator.generate_feed([], "Software Engineering")

        root = ET.fromstring(xml)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        links = root.findall("atom:link", ns)
        self_link = next((l for l in links if l.get("rel") == "self"), None)
        assert self_link is not None
        assert self_link.get("href") == "https://example.com/feeds/software-engineering/atom.xml"

    def test_entry_has_source_links(self):
        """Test that entries have source URLs as links.

        Note: feedgen 1.0.0 has a bug where the 'rel' attribute is not rendered
        for entry links. The links are still present and functional.
        """
        entries = [
            FeedEntry(
                id="entry-1",
                category_slug="tech",
                title="Test Digest",
                published=datetime(2024, 1, 15, tzinfo=UTC),
                content_html="<p>Content</p>",
                source_urls=["https://source1.com", "https://source2.com"],
            ),
        ]

        generator = FeedGenerator(base_url="https://example.com")
        xml = generator.generate_feed(entries, "Tech")

        root = ET.fromstring(xml)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        entry = root.find("atom:entry", ns)
        links = entry.findall("atom:link", ns)
        hrefs = [l.get("href") for l in links]

        # Source URLs should be present as links
        assert "https://source1.com" in hrefs
        assert "https://source2.com" in hrefs

    def test_custom_author_name(self):
        """Test setting custom author name."""
        generator = FeedGenerator(base_url="https://example.com", author_name="Custom Author")
        xml = generator.generate_feed([], "Tech")

        root = ET.fromstring(xml)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        assert root.find("atom:author/atom:name", ns).text == "Custom Author"

    def test_entries_sorted_newest_first(self):
        """Test that entries are sorted with newest first."""
        entries = [
            FeedEntry(
                id="older",
                category_slug="tech",
                title="Older",
                published=datetime(2024, 1, 10, tzinfo=UTC),
                content_html="<p>Old</p>",
            ),
            FeedEntry(
                id="newer",
                category_slug="tech",
                title="Newer",
                published=datetime(2024, 1, 15, tzinfo=UTC),
                content_html="<p>New</p>",
            ),
        ]

        generator = FeedGenerator()
        xml = generator.generate_feed(entries, "Tech")

        root = ET.fromstring(xml)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        entry_elements = root.findall("atom:entry", ns)
        assert entry_elements[0].find("atom:id", ns).text == "urn:ryushi:entry:newer"
        assert entry_elements[1].find("atom:id", ns).text == "urn:ryushi:entry:older"
