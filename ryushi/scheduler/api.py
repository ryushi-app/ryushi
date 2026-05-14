"""FastAPI router for scheduler HTTP endpoints.

This module provides HTTP endpoints for:
- Manual job triggering
- Job status retrieval
- Job history retrieval
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ryushi.scheduler.exceptions import JobAlreadyRunningError, JobNotFoundError
from ryushi.scheduler.models import (
    JobHistoryResponse,
    JobListResponse,
    JobStatus,
    JobTriggerResponse,
)
from ryushi.scheduler.scheduler import DigestScheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])

# Global scheduler instance - set by the application
_scheduler: DigestScheduler | None = None


def set_scheduler(scheduler: DigestScheduler) -> None:
    """Set the global scheduler instance.

    Args:
        scheduler: The DigestScheduler instance to use.
    """
    global _scheduler
    _scheduler = scheduler


def get_scheduler() -> DigestScheduler:
    """Get the global scheduler instance.

    Returns:
        The DigestScheduler instance.

    Raises:
        HTTPException: If scheduler is not initialized.
    """
    if _scheduler is None:
        raise HTTPException(
            status_code=503,
            detail="Scheduler not initialized",
        )
    return _scheduler


@router.get("", response_model=JobListResponse)
async def list_jobs(
    scheduler: Annotated[DigestScheduler, Depends(get_scheduler)],
) -> JobListResponse:
    """List all scheduled jobs.

    Returns a list of all configured jobs with their current status,
    last run time, and next scheduled run time.
    """
    jobs = await scheduler.list_jobs()
    return JobListResponse(jobs=jobs)


@router.get("/{category_slug}/status", response_model=JobStatus)
async def get_job_status(
    category_slug: str,
    scheduler: Annotated[DigestScheduler, Depends(get_scheduler)],
) -> JobStatus:
    """Get status for a specific job.

    Args:
        category_slug: The category identifier.

    Returns:
        Job status including last_run, next_run, and current status.

    Raises:
        HTTPException: 404 if category not found.
    """
    try:
        return await scheduler.get_job_status(category_slug)
    except JobNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: '{category_slug}'. Use GET /jobs to see available jobs.",
        ) from e


@router.post("/{category_slug}/run", response_model=JobTriggerResponse)
async def trigger_job(
    category_slug: str,
    scheduler: Annotated[DigestScheduler, Depends(get_scheduler)],
) -> JobTriggerResponse:
    """Manually trigger a job.

    Starts a job immediately regardless of its schedule.

    Args:
        category_slug: The category identifier.

    Returns:
        Response with status "started" and the job ID.

    Raises:
        HTTPException: 404 if category not found, 409 if job already running.
    """
    try:
        job_run = await scheduler.trigger_job(category_slug)
        return JobTriggerResponse(status="started", job_id=job_run.id)
    except JobNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: '{category_slug}'. Use GET /jobs to see available jobs.",
        ) from e
    except JobAlreadyRunningError as e:
        raise HTTPException(
            status_code=409,
            detail=f"Job already running for '{category_slug}'. Wait for it to complete.",
        ) from e


@router.get("/{category_slug}/history", response_model=JobHistoryResponse)
async def get_job_history(
    category_slug: str,
    scheduler: Annotated[DigestScheduler, Depends(get_scheduler)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JobHistoryResponse:
    """Get job run history for a category.

    Args:
        category_slug: The category identifier.
        limit: Maximum number of runs to return (1-100, default 20).

    Returns:
        List of job run records ordered by start time descending.

    Raises:
        HTTPException: 404 if category not configured.
    """
    # Check if category is configured
    if category_slug not in scheduler.get_category_slugs():
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: '{category_slug}'. Use GET /jobs to see available jobs.",
        )

    history = await scheduler.job_store.get_history(category_slug, limit=limit)
    return JobHistoryResponse(runs=history)
