"""Tests for scheduler models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ryushi.scheduler.models import (
    CategorySchedule,
    JobHistoryResponse,
    JobListResponse,
    JobRun,
    JobStatus,
    JobTriggerResponse,
    ScheduleConfig,
)


class TestJobRun:
    """Tests for JobRun model."""

    def test_create_job_run_with_defaults(self):
        """Test creating a JobRun with minimal fields."""
        run = JobRun(category_slug="technology")
        assert run.category_slug == "technology"
        assert run.id is not None
        assert run.started_at is not None
        assert run.finished_at is None
        assert run.status == "running"
        assert run.article_count is None
        assert run.error is None

    def test_create_job_run_complete(self):
        """Test creating a completed JobRun."""
        started = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        finished = datetime(2024, 1, 15, 10, 1, 30, tzinfo=UTC)
        run = JobRun(
            id="test-run-123",
            category_slug="software-engineering",
            started_at=started,
            finished_at=finished,
            status="success",
            article_count=25,
        )
        assert run.id == "test-run-123"
        assert run.status == "success"
        assert run.article_count == 25
        assert run.finished_at == finished

    def test_create_job_run_failed(self):
        """Test creating a failed JobRun."""
        run = JobRun(
            category_slug="tech",
            status="failed",
            error="Connection timeout",
        )
        assert run.status == "failed"
        assert run.error == "Connection timeout"

    def test_job_run_id_auto_generated(self):
        """Test that JobRun generates unique IDs."""
        run1 = JobRun(category_slug="tech")
        run2 = JobRun(category_slug="tech")
        assert run1.id != run2.id

    def test_job_run_requires_category_slug(self):
        """Test that category_slug is required."""
        with pytest.raises(ValidationError):
            JobRun()

    def test_job_run_status_validation(self):
        """Test that status must be valid literal."""
        with pytest.raises(ValidationError):
            JobRun(category_slug="tech", status="invalid")


class TestJobStatus:
    """Tests for JobStatus model."""

    def test_create_job_status_minimal(self):
        """Test creating JobStatus with minimal fields."""
        status = JobStatus(category_slug="technology")
        assert status.category_slug == "technology"
        assert status.last_run is None
        assert status.next_run is None
        assert status.status == "scheduled"

    def test_create_job_status_complete(self):
        """Test creating JobStatus with all fields."""
        last = datetime(2024, 1, 14, 6, 0, 0, tzinfo=UTC)
        next_run = datetime(2024, 1, 15, 6, 0, 0, tzinfo=UTC)
        status = JobStatus(
            category_slug="tech",
            last_run=last,
            next_run=next_run,
            status="running",
        )
        assert status.last_run == last
        assert status.next_run == next_run
        assert status.status == "running"


class TestCategorySchedule:
    """Tests for CategorySchedule model."""

    def test_create_category_schedule(self):
        """Test creating a CategorySchedule."""
        schedule = CategorySchedule(schedule="0 6 * * *")
        assert schedule.schedule == "0 6 * * *"

    def test_category_schedule_requires_schedule(self):
        """Test that schedule field is required."""
        with pytest.raises(ValidationError):
            CategorySchedule()


class TestScheduleConfig:
    """Tests for ScheduleConfig model."""

    def test_create_empty_config(self):
        """Test creating empty ScheduleConfig."""
        config = ScheduleConfig()
        assert config.categories == {}

    def test_create_config_with_categories(self):
        """Test creating ScheduleConfig with categories."""
        config = ScheduleConfig(
            categories={
                "technology": CategorySchedule(schedule="0 6 * * *"),
                "science": CategorySchedule(schedule="0 8 * * 1"),
            }
        )
        assert len(config.categories) == 2
        assert config.categories["technology"].schedule == "0 6 * * *"
        assert config.categories["science"].schedule == "0 8 * * 1"


class TestResponseModels:
    """Tests for API response models."""

    def test_job_trigger_response(self):
        """Test JobTriggerResponse model."""
        response = JobTriggerResponse(job_id="run-123")
        assert response.status == "started"
        assert response.job_id == "run-123"

    def test_job_list_response_empty(self):
        """Test empty JobListResponse."""
        response = JobListResponse()
        assert response.jobs == []

    def test_job_list_response_with_jobs(self):
        """Test JobListResponse with jobs."""
        jobs = [
            JobStatus(category_slug="tech"),
            JobStatus(category_slug="science"),
        ]
        response = JobListResponse(jobs=jobs)
        assert len(response.jobs) == 2

    def test_job_history_response_empty(self):
        """Test empty JobHistoryResponse."""
        response = JobHistoryResponse()
        assert response.runs == []

    def test_job_history_response_with_runs(self):
        """Test JobHistoryResponse with runs."""
        runs = [
            JobRun(category_slug="tech", status="success"),
            JobRun(category_slug="tech", status="failed"),
        ]
        response = JobHistoryResponse(runs=runs)
        assert len(response.runs) == 2
