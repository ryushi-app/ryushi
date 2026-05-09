# Environment variables:
# export FRESHRSS_URL="https://your-freshrss.example.com"
# export FRESHRSS_USERNAME="your_username"
# export FRESHRSS_PASSWORD="your_password"
# export OPENAI_API_KEY="sk-..."  # or another LiteLLM-supported provider
# export OPENAI_API_BASE="https://your-api-server.example.com/v1"  # optional: custom API endpoint
#
# Run smoke test (requires -m smoke to run, skipped by default):
# uv run pytest tests/smoke_test.py -v -s -m smoke
#
# Run as script:
# uv run python tests/smoke_test.py

import asyncio
import os

import pytest

from ryushi.digest import DigestConfig, DigestEngine
from ryushi.integrations.freshrss import FreshRSSClient


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_freshrss_digest_generation():
    """Smoke test: fetch articles from FreshRSS and generate a digest."""
    # Fetch articles from FreshRSS
    client = FreshRSSClient()
    categories = await client.get_categories()
    print(f"Found {len(categories)} categories")

    assert categories, "No categories found in FreshRSS"

    # Get articles from first category
    articles = await client.get_unread_items(category_id=categories[0].id, max_articles=10)
    print(f"Found {len(articles)} articles in '{categories[0].name}'")

    assert articles, f"No articles found in category '{categories[0].name}'"

    # Generate digest
    engine = DigestEngine(
        DigestConfig(
            model="gpt-4.1-mini",
            base_url=os.getenv("OPENAI_API_BASE"),
        )
    )
    digest = await engine.generate_digest(articles, categories[0].name)

    print(f"\n{'=' * 60}")
    print(digest.summary)
    print(f"{'=' * 60}")
    print(f"Sources: {digest.source_urls}")

    # Basic assertions
    assert digest.summary, "Digest summary should not be empty"
    assert digest.article_count == len(articles)
    assert digest.category_name == categories[0].name


# Allow running as a script
if __name__ == "__main__":
    asyncio.run(test_freshrss_digest_generation())
