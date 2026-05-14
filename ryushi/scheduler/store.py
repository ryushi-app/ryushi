"""SQLite storage for job run history.

This module provides async SQLite persistence for JobRun records
with a rolling 100-run retention policy per category.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

import aiosqlite

from ryushi.scheduler.exceptions import SchedulerError
from ryushi.scheduler.models import JobRun

logger = logging.getLogger(__name__)

# Default retention limit: number of job runs to keep per category
DEFAULT_RETENTION_LIMIT = 100

# SQLite schema for job_runs table
SCHEMA = """
CREATE TABLE IF NOT EXISTS job_runs (
    id TEXT PRIMARY KEY,
    category_slug TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    article_count INTEGER,
    error TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_job_runs_category_started
ON job_runs(category_slug, started_at DESC);
"""


class JobStore:
    """Async SQLite storage for job run history.

    Provides CRUD operations for JobRun records with automatic
    retention management (100 runs per category by default).

    Attributes:
        db_path: Path to the SQLite database file.
        retention_limit: Maximum job runs to keep per category.
    """

    def __init__(
        self,
        db_path: str | Path = "jobs.db",
        retention_limit: int = DEFAULT_RETENTION_LIMIT,
    ):
        """Initialize the JobStore.

        Args:
            db_path: Path to the SQLite database file.
            retention_limit: Maximum runs per category (default: 100).
        """
        self.db_path = Path(db_path)
        self.retention_limit = retention_limit
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the database schema.

        Creates the job_runs table and indexes if they don't exist.
        This method is idempotent and safe to call multiple times.

        Raises:
            SchedulerError: If database initialization fails.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.executescript(SCHEMA)
                await db.commit()
            self._initialized = True
            logger.info("Job store initialized at %s", self.db_path)
        except Exception as e:
            raise SchedulerError(f"Failed to initialize job store: {e}") from e

    async def _ensure_initialized(self) -> None:
        """Ensure the database is initialized before operations."""
        if not self._initialized:
            await self.initialize()

    async def create_run(self, category_slug: str) -> JobRun:
        """Create a new job run record with status 'running'.

        Args:
            category_slug: The category slug for the job.

        Returns:
            The created JobRun with status 'running'.

        Raises:
            SchedulerError: If the operation fails.
        """
        await self._ensure_initialized()

        job_run = JobRun(
            id=str(uuid4()),
            category_slug=category_slug,
            started_at=datetime.now(UTC),
            status="running",
        )

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT INTO job_runs 
                    (id, category_slug, started_at, status, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        job_run.id,
                        job_run.category_slug,
                        job_run.started_at.isoformat(),
                        job_run.status,
                        datetime.now(UTC).isoformat(),
                    ),
                )
                await db.commit()
                logger.debug("Created job run %s for category %s", job_run.id, category_slug)
                return job_run

        except Exception as e:
            raise SchedulerError(
                f"Failed to create job run: {e}",
                category_slug=category_slug,
            ) from e

    async def complete_run(
        self,
        job_id: str,
        status: Literal["success", "failed"],
        article_count: int | None = None,
        error: str | None = None,
    ) -> None:
        """Complete a job run with final status.

        Also enforces retention limit by removing oldest runs.

        Args:
            job_id: ID of the job run to complete.
            status: Final status ('success' or 'failed').
            article_count: Number of articles processed (optional).
            error: Error message if failed (optional).

        Raises:
            SchedulerError: If the operation fails.
        """
        await self._ensure_initialized()

        finished_at = datetime.now(UTC)

        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Update the job run
                await db.execute(
                    """
                    UPDATE job_runs 
                    SET finished_at = ?, status = ?, article_count = ?, error = ?
                    WHERE id = ?
                    """,
                    (
                        finished_at.isoformat(),
                        status,
                        article_count,
                        error,
                        job_id,
                    ),
                )

                # Get the category_slug for retention enforcement
                cursor = await db.execute(
                    "SELECT category_slug FROM job_runs WHERE id = ?",
                    (job_id,),
                )
                row = await cursor.fetchone()
                if row:
                    category_slug = row[0]
                    # Enforce retention limit
                    await db.execute(
                        """
                        DELETE FROM job_runs 
                        WHERE category_slug = ? 
                        AND id NOT IN (
                            SELECT id FROM job_runs 
                            WHERE category_slug = ? 
                            ORDER BY started_at DESC 
                            LIMIT ?
                        )
                        """,
                        (category_slug, category_slug, self.retention_limit),
                    )

                await db.commit()
                logger.debug("Completed job run %s with status %s", job_id, status)

        except Exception as e:
            raise SchedulerError(f"Failed to complete job run: {e}") from e

    async def get_last_run(self, category_slug: str) -> JobRun | None:
        """Get the most recent completed job run for a category.

        Args:
            category_slug: The category slug to look up.

        Returns:
            The most recent JobRun with status 'success' or 'failed',
            or None if no completed runs exist.

        Raises:
            SchedulerError: If the operation fails.
        """
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """
                    SELECT id, category_slug, started_at, finished_at, 
                           status, article_count, error
                    FROM job_runs
                    WHERE category_slug = ? AND status IN ('success', 'failed')
                    ORDER BY started_at DESC
                    LIMIT 1
                    """,
                    (category_slug,),
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                return JobRun(
                    id=row["id"],
                    category_slug=row["category_slug"],
                    started_at=datetime.fromisoformat(row["started_at"]),
                    finished_at=datetime.fromisoformat(row["finished_at"])
                    if row["finished_at"]
                    else None,
                    status=row["status"],
                    article_count=row["article_count"],
                    error=row["error"],
                )

        except Exception as e:
            raise SchedulerError(
                f"Failed to get last run: {e}",
                category_slug=category_slug,
            ) from e

    async def get_history(
        self,
        category_slug: str,
        limit: int = 20,
    ) -> list[JobRun]:
        """Get job run history for a category.

        Args:
            category_slug: The category slug to look up.
            limit: Maximum number of runs to return (default: 20).

        Returns:
            List of JobRun objects ordered by started_at descending.

        Raises:
            SchedulerError: If the operation fails.
        """
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """
                    SELECT id, category_slug, started_at, finished_at,
                           status, article_count, error
                    FROM job_runs
                    WHERE category_slug = ?
                    ORDER BY started_at DESC
                    LIMIT ?
                    """,
                    (category_slug, limit),
                )
                rows = await cursor.fetchall()

                runs = []
                for row in rows:
                    runs.append(
                        JobRun(
                            id=row["id"],
                            category_slug=row["category_slug"],
                            started_at=datetime.fromisoformat(row["started_at"]),
                            finished_at=datetime.fromisoformat(row["finished_at"])
                            if row["finished_at"]
                            else None,
                            status=row["status"],
                            article_count=row["article_count"],
                            error=row["error"],
                        )
                    )

                return runs

        except Exception as e:
            raise SchedulerError(
                f"Failed to get history: {e}",
                category_slug=category_slug,
            ) from e

    async def is_job_running(self, category_slug: str) -> bool:
        """Check if a job is currently running for a category.

        Args:
            category_slug: The category slug to check.

        Returns:
            True if a job with status 'running' exists.
        """
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT COUNT(*) FROM job_runs
                    WHERE category_slug = ? AND status = 'running'
                    """,
                    (category_slug,),
                )
                row = await cursor.fetchone()
                return row[0] > 0 if row else False

        except Exception as e:
            raise SchedulerError(
                f"Failed to check running status: {e}",
                category_slug=category_slug,
            ) from e

    async def get_running_job(self, category_slug: str) -> JobRun | None:
        """Get the currently running job for a category if any.

        Args:
            category_slug: The category slug to check.

        Returns:
            The running JobRun or None.
        """
        await self._ensure_initialized()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """
                    SELECT id, category_slug, started_at, finished_at,
                           status, article_count, error
                    FROM job_runs
                    WHERE category_slug = ? AND status = 'running'
                    ORDER BY started_at DESC
                    LIMIT 1
                    """,
                    (category_slug,),
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                return JobRun(
                    id=row["id"],
                    category_slug=row["category_slug"],
                    started_at=datetime.fromisoformat(row["started_at"]),
                    finished_at=None,
                    status=row["status"],
                    article_count=row["article_count"],
                    error=row["error"],
                )

        except Exception as e:
            raise SchedulerError(
                f"Failed to get running job: {e}",
                category_slug=category_slug,
            ) from e
