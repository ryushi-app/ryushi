"""Pydantic models for scheduler module.

This module defines the JobRun, JobStatus, and ScheduleConfig models
used by the scheduler, executor, and API.
"""

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class JobRun(BaseModel):
    """Represents a single job execution record.

    Attributes:
        id: Unique identifier (UUID string).
        category_slug: URL-safe slug for the category.
        started_at: Timestamp when the job started.
        finished_at: Timestamp when the job finished (None if running).
        status: Current status of the job run.
        article_count: Number of articles processed (None if not finished).
        error: Error message if the job failed (None otherwise).
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    category_slug: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    status: Literal["running", "success", "failed"] = "running"
    article_count: int | None = None
    error: str | None = None


class JobStatus(BaseModel):
    """Status information for a scheduled job.

    Attributes:
        category_slug: URL-safe slug for the category.
        last_run: Timestamp of the last completed run (None if never run).
        next_run: Timestamp of the next scheduled run.
        status: Current status (scheduled, running, etc.).
    """

    category_slug: str
    last_run: datetime | None = None
    next_run: datetime | None = None
    status: str = "scheduled"


class CategorySchedule(BaseModel):
    """Schedule configuration for a single category.

    Attributes:
        schedule: Cron expression (e.g., "0 6 * * *").
    """

    schedule: str


class ScheduleConfig(BaseModel):
    """Configuration for all category schedules.

    Attributes:
        categories: Mapping of category slug to schedule configuration.
    """

    categories: dict[str, CategorySchedule] = Field(default_factory=dict)


class JobTriggerResponse(BaseModel):
    """Response model for manual job trigger endpoint.

    Attributes:
        status: Status of the trigger ("started").
        job_id: ID of the started job run.
    """

    status: str = "started"
    job_id: str


class JobListResponse(BaseModel):
    """Response model for job list endpoint.

    Attributes:
        jobs: List of job statuses.
    """

    jobs: list[JobStatus] = Field(default_factory=list)


class JobHistoryResponse(BaseModel):
    """Response model for job history endpoint.

    Attributes:
        runs: List of job run records.
    """

    runs: list[JobRun] = Field(default_factory=list)
