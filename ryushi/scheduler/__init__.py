"""Scheduler module for automated digest generation.

This module provides cron-based job scheduling for digest generation,
including job execution, persistence, and HTTP API endpoints.

Main components:
    DigestScheduler: Main scheduler class managing cron jobs.
    JobExecutor: Executes the fetch → digest → feed pipeline.
    JobStore: SQLite persistence for job run history.
    JobRun: Model representing a job execution record.

Usage:
    from ryushi.scheduler import DigestScheduler, JobStore

    # Create from config file
    scheduler = DigestScheduler.from_config_file("config.yaml")
    await scheduler.start()

    # Manual trigger
    job_run = await scheduler.trigger_job("technology")

    # Get status
    status = await scheduler.get_job_status("technology")
"""

from ryushi.scheduler.api import router as scheduler_router
from ryushi.scheduler.api import set_scheduler
from ryushi.scheduler.config import load_config
from ryushi.scheduler.exceptions import (
    ConfigurationError,
    JobAlreadyRunningError,
    JobExecutionError,
    JobNotFoundError,
    SchedulerError,
)
from ryushi.scheduler.executor import JobExecutor
from ryushi.scheduler.models import (
    CategorySchedule,
    JobHistoryResponse,
    JobListResponse,
    JobRun,
    JobStatus,
    JobTriggerResponse,
    ScheduleConfig,
)
from ryushi.scheduler.scheduler import DigestScheduler
from ryushi.scheduler.store import JobStore

__all__ = [
    # Core classes
    "DigestScheduler",
    "JobExecutor",
    "JobStore",
    # Models
    "JobRun",
    "JobStatus",
    "ScheduleConfig",
    "CategorySchedule",
    "JobTriggerResponse",
    "JobListResponse",
    "JobHistoryResponse",
    # Exceptions
    "SchedulerError",
    "JobNotFoundError",
    "JobAlreadyRunningError",
    "JobExecutionError",
    "ConfigurationError",
    # Configuration
    "load_config",
    # API
    "scheduler_router",
    "set_scheduler",
]
