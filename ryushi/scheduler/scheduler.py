"""Digest scheduler using APScheduler.

This module provides the DigestScheduler class that manages cron-based
job scheduling for digest generation.
"""

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from croniter import croniter

from ryushi.feeds.store import FeedStore
from ryushi.scheduler.config import load_config
from ryushi.scheduler.exceptions import JobAlreadyRunningError, JobNotFoundError
from ryushi.scheduler.executor import JobExecutor
from ryushi.scheduler.models import JobRun, JobStatus, ScheduleConfig
from ryushi.scheduler.store import JobStore

logger = logging.getLogger(__name__)


class DigestScheduler:
    """Manages scheduled digest generation jobs.

    Uses APScheduler to run cron-based jobs for each configured category.

    Attributes:
        config: Schedule configuration.
        job_store: Store for job run persistence.
        feed_store: Store for feed entry persistence.
        executor: Job executor for running pipelines.
    """

    def __init__(
        self,
        config: ScheduleConfig,
        job_store: JobStore,
        feed_store: FeedStore,
        executor: JobExecutor | None = None,
    ):
        """Initialize the DigestScheduler.

        Args:
            config: Schedule configuration with category cron expressions.
            job_store: Store for job run persistence.
            feed_store: Store for feed entry persistence.
            executor: Job executor (creates default if None).
        """
        self.config = config
        self.job_store = job_store
        self.feed_store = feed_store
        self.executor = executor or JobExecutor(
            job_store=job_store,
            feed_store=feed_store,
        )
        self._scheduler = AsyncIOScheduler()
        self._running = False

    @classmethod
    def from_config_file(
        cls,
        config_path: str | Path,
        jobs_db_path: str | Path = "jobs.db",
        feeds_db_path: str | Path = "feeds.db",
    ) -> "DigestScheduler":
        """Create a DigestScheduler from a config file.

        Args:
            config_path: Path to config.yaml.
            jobs_db_path: Path to jobs SQLite database.
            feeds_db_path: Path to feeds SQLite database.

        Returns:
            Configured DigestScheduler instance.
        """
        config = load_config(config_path)
        job_store = JobStore(db_path=jobs_db_path)
        feed_store = FeedStore(db_path=feeds_db_path)

        return cls(
            config=config,
            job_store=job_store,
            feed_store=feed_store,
        )

    async def start(self) -> None:
        """Start the scheduler and register all configured jobs.

        Also checks for overdue jobs and runs them immediately.
        """
        if self._running:
            logger.warning("Scheduler is already running")
            return

        # Initialize stores
        await self.job_store.initialize()
        await self.feed_store.initialize()

        # Register jobs for each category
        for category_slug, category_config in self.config.categories.items():
            self._register_job(category_slug, category_config.schedule)

        # Start the scheduler
        self._scheduler.start()
        self._running = True

        logger.info(
            "Scheduler started with %d jobs",
            len(self.config.categories),
        )

        # Check for overdue jobs
        await self._check_overdue_jobs()

    async def stop(self) -> None:
        """Stop the scheduler gracefully."""
        if not self._running:
            return

        self._scheduler.shutdown(wait=True)
        self._running = False
        logger.info("Scheduler stopped")

    def _register_job(self, category_slug: str, cron_expression: str) -> None:
        """Register a job with the scheduler.

        Args:
            category_slug: Category identifier.
            cron_expression: Cron expression for scheduling.
        """
        # Parse cron expression into APScheduler trigger
        parts = cron_expression.split()
        if len(parts) != 5:
            logger.error(
                "Invalid cron expression for '%s': %s",
                category_slug,
                cron_expression,
            )
            return

        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )

        self._scheduler.add_job(
            self._run_job,
            trigger=trigger,
            args=[category_slug],
            id=f"digest-{category_slug}",
            name=f"Digest: {category_slug}",
            replace_existing=True,
            max_instances=1,
        )

        logger.info(
            "Registered job for '%s' with schedule: %s",
            category_slug,
            cron_expression,
        )

    async def _run_job(self, category_slug: str) -> None:
        """Run a job for a category.

        Args:
            category_slug: Category to run job for.
        """
        try:
            # Get category config for language, prompt, favicon, and Gist settings
            category_config = self.config.categories.get(category_slug)
            language = category_config.language if category_config else None
            custom_prompt = category_config.prompt if category_config else None
            favicon = category_config.favicon if category_config else None
            gist_enabled = category_config.gist_enabled if category_config else False
            gist_id = category_config.gist_id if category_config else None

            await self.executor.execute_job(
                category_slug,
                language=language,
                custom_prompt=custom_prompt,
                favicon=favicon,
                gist_enabled=gist_enabled,
                gist_id=gist_id,
            )
        except Exception as e:
            logger.error("Error running job for '%s': %s", category_slug, e)

    async def _check_overdue_jobs(self) -> None:
        """Check for overdue jobs and run them immediately."""
        now = datetime.now(UTC)

        for category_slug, category_config in self.config.categories.items():
            try:
                last_run = await self.job_store.get_last_run(category_slug)

                if last_run is None:
                    # Never run before, run immediately
                    logger.info(
                        "No previous run for '%s', running immediately",
                        category_slug,
                    )
                    asyncio.create_task(self._run_job(category_slug))
                    continue

                # Calculate expected last run time based on cron
                cron = croniter(category_config.schedule, now)
                # Get the previous scheduled time
                prev_scheduled = cron.get_prev(datetime)

                if last_run.finished_at and last_run.finished_at < prev_scheduled:
                    # Overdue - should have run but didn't
                    logger.info(
                        "Overdue job for '%s' (last: %s, expected: %s), running immediately",
                        category_slug,
                        last_run.finished_at,
                        prev_scheduled,
                    )
                    asyncio.create_task(self._run_job(category_slug))

            except Exception as e:
                logger.error(
                    "Error checking overdue status for '%s': %s",
                    category_slug,
                    e,
                )

    async def trigger_job(self, category_slug: str) -> JobRun:
        """Manually trigger a job for a category.

        Args:
            category_slug: Category to trigger job for.

        Returns:
            The started JobRun.

        Raises:
            JobNotFoundError: If category is not configured.
            JobAlreadyRunningError: If job is already running.
        """
        if category_slug not in self.config.categories:
            raise JobNotFoundError(
                f"Category '{category_slug}' is not configured",
                category_slug=category_slug,
            )

        if await self.job_store.is_job_running(category_slug):
            raise JobAlreadyRunningError(
                f"Job already running for '{category_slug}'",
                category_slug=category_slug,
            )

        # Start job in background
        job_run = await self.job_store.create_run(category_slug)

        async def run_and_complete():
            try:
                # Get category config for Gist settings
                category_config = self.config.categories.get(category_slug)
                gist_enabled = category_config.gist_enabled if category_config else False
                gist_id = category_config.gist_id if category_config else None

                article_count = await self.executor._fetch_and_process(
                    category_slug,
                    gist_enabled=gist_enabled,
                    gist_id=gist_id,
                )
                await self.job_store.complete_run(
                    job_id=job_run.id,
                    status="success",
                    article_count=article_count,
                )
            except Exception as e:
                await self.job_store.complete_run(
                    job_id=job_run.id,
                    status="failed",
                    error=str(e),
                )

        asyncio.create_task(run_and_complete())

        return job_run

    async def get_job_status(self, category_slug: str) -> JobStatus:
        """Get status for a scheduled job.

        Args:
            category_slug: Category to get status for.

        Returns:
            JobStatus with last_run, next_run, and current status.

        Raises:
            JobNotFoundError: If category is not configured.
        """
        if category_slug not in self.config.categories:
            raise JobNotFoundError(
                f"Category '{category_slug}' is not configured",
                category_slug=category_slug,
            )

        last_run = await self.job_store.get_last_run(category_slug)

        # Get next scheduled run time
        next_run = None
        job = self._scheduler.get_job(f"digest-{category_slug}")
        if job and job.next_run_time:
            next_run = job.next_run_time

        # Determine current status
        if await self.job_store.is_job_running(category_slug):
            status = "running"
        elif last_run and last_run.status == "failed":
            status = "last_failed"
        else:
            status = "scheduled"

        return JobStatus(
            category_slug=category_slug,
            last_run=last_run.finished_at if last_run else None,
            next_run=next_run,
            status=status,
        )

    async def list_jobs(self) -> list[JobStatus]:
        """List all scheduled jobs with their status.

        Returns:
            List of JobStatus for all configured categories.
        """
        statuses = []
        for category_slug in self.config.categories:
            try:
                status = await self.get_job_status(category_slug)
                statuses.append(status)
            except Exception as e:
                logger.error("Error getting status for '%s': %s", category_slug, e)

        return statuses

    def get_category_slugs(self) -> list[str]:
        """Get list of configured category slugs.

        Returns:
            List of category slugs.
        """
        return list(self.config.categories.keys())
