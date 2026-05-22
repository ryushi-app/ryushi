"""Job executor for digest generation pipeline.

This module provides the JobExecutor class that runs the
Fetcher → Digest Engine → Feed Store pipeline.
"""

import logging
import traceback
from datetime import UTC, datetime

from ryushi.digest import DigestConfig, DigestEngine
from ryushi.feeds import FeedStore, digest_to_entry
from ryushi.integrations.freshrss import FreshRSSClient
from ryushi.scheduler.models import JobRun
from ryushi.scheduler.store import JobStore

logger = logging.getLogger(__name__)


class JobExecutor:
    """Executes digest generation jobs.

    Orchestrates the pipeline: Fetch articles → Generate digest → Store feed entry.

    Attributes:
        job_store: JobStore for persisting job runs.
        feed_store: FeedStore for persisting feed entries.
        freshrss_client: Client for fetching articles.
        digest_engine: Engine for generating digests.
    """

    def __init__(
        self,
        job_store: JobStore,
        feed_store: FeedStore,
        freshrss_client: FreshRSSClient | None = None,
        digest_config: DigestConfig | None = None,
    ):
        """Initialize the JobExecutor.

        Args:
            job_store: JobStore for persisting job runs.
            feed_store: FeedStore for persisting feed entries.
            freshrss_client: Client for fetching articles (creates default if None).
            digest_config: Configuration for digest engine (uses defaults if None).
        """
        self.job_store = job_store
        self.feed_store = feed_store
        self.freshrss_client = freshrss_client or FreshRSSClient()
        self.digest_engine = DigestEngine(digest_config or DigestConfig())

    async def execute_job(
        self,
        category_slug: str,
        language: str | None = None,
        custom_prompt: str | None = None,
        favicon: str | None = None,
    ) -> JobRun:
        """Execute a digest generation job for a category.

        Pipeline:
        1. Create job run record with status 'running'
        2. Fetch unread articles from FreshRSS
        3. Generate digest using DigestEngine (if articles exist)
        4. Store feed entry (if digest generated)
        5. Mark articles as read in FreshRSS
        6. Complete job run with status 'success' or 'failed'

        Args:
            category_slug: The category slug to process.
            language: Optional language override for digest generation.
            custom_prompt: Optional custom prompt override for digest generation.
            favicon: Optional favicon URL for feed generation.

        Returns:
            The completed JobRun record.

        Raises:
            JobExecutionError: If a critical error occurs.
        """
        # Create job run record
        job_run = await self.job_store.create_run(category_slug)
        started_at = datetime.now(UTC)

        logger.info(
            "Starting job for category '%s' (job_id=%s)",
            category_slug,
            job_run.id,
        )

        try:
            # Step 1: Fetch articles
            article_count = await self._fetch_and_process(
                category_slug,
                language=language,
                custom_prompt=custom_prompt,
                favicon=favicon,
            )

            # Calculate duration
            finished_at = datetime.now(UTC)
            duration = (finished_at - started_at).total_seconds()

            # Complete job as success
            await self.job_store.complete_run(
                job_id=job_run.id,
                status="success",
                article_count=article_count,
            )

            logger.info(
                "Job complete: %d articles, category=%s, duration=%.2fs",
                article_count,
                category_slug,
                duration,
            )

            # Refresh job run data
            history = await self.job_store.get_history(category_slug, limit=1)
            return history[0] if history else job_run

        except Exception as e:
            # Log full traceback
            error_traceback = traceback.format_exc()
            logger.error(
                "Job failed for category '%s': %s\n%s",
                category_slug,
                str(e),
                error_traceback,
            )

            # Complete job as failed
            await self.job_store.complete_run(
                job_id=job_run.id,
                status="failed",
                error=str(e),
            )

            # Refresh job run data
            history = await self.job_store.get_history(category_slug, limit=1)
            return history[0] if history else job_run

    async def _fetch_and_process(
        self,
        category_slug: str,
        language: str | None = None,
        custom_prompt: str | None = None,
        favicon: str | None = None,
    ) -> int:
        """Fetch articles and process them into a digest.

        Args:
            category_slug: The category slug to process.
            language: Optional language override for digest generation.
            custom_prompt: Optional custom prompt override for digest generation.
            favicon: Optional favicon URL for feed generation.

        Returns:
            Number of articles processed.
        """
        # Get categories to find the category ID
        categories = await self.freshrss_client.get_categories()

        # Find category by slug (convert slug back to potential names)
        category = None
        category_name = category_slug.replace("-", " ").title()

        for cat in categories:
            # Match by name (case-insensitive) or by slug conversion
            cat_slug = cat.name.lower().replace(" ", "-")
            if cat_slug == category_slug or cat.name.lower() == category_name.lower():
                category = cat
                break

        if not category:
            logger.warning("Category '%s' not found in FreshRSS", category_slug)
            return 0

        # Fetch unread articles
        articles = await self.freshrss_client.get_unread_items(
            category_id=category.id,
            max_articles=50,  # Limit to prevent overwhelming the digest
        )

        if not articles:
            logger.info("No unread articles for category '%s'", category_slug)
            return 0

        article_count = len(articles)
        logger.info(
            "Fetched %d articles for category '%s'",
            article_count,
            category_slug,
        )

        # Generate digest with optional language and prompt overrides
        digest = await self.digest_engine.generate_digest(
            articles,
            category.name,
            language=language,
            custom_prompt=custom_prompt,
        )

        if digest is None:
            logger.warning("No digest generated for category '%s'", category_slug)
            return article_count

        # Convert to feed entry and store with favicon
        feed_entry = digest_to_entry(digest, favicon_url=favicon)
        await self.feed_store.add_entry(feed_entry)

        logger.info(
            "Stored feed entry for category '%s' (digest_id=%s)",
            category_slug,
            digest.id,
        )

        # Mark articles as read in FreshRSS
        article_ids = [article.id for article in articles]
        await self.freshrss_client.mark_as_read(article_ids)
        logger.debug(
            "Marked %d articles as read for category '%s'",
            len(article_ids),
            category_slug,
        )

        return article_count
