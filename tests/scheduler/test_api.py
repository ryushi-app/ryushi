"""Tests for scheduler HTTP API."""

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from ryushi.feeds.store import FeedStore
from ryushi.scheduler.api import router, set_scheduler
from ryushi.scheduler.models import CategorySchedule, JobRun, ScheduleConfig
from ryushi.scheduler.scheduler import DigestScheduler
from ryushi.scheduler.store import JobStore


@pytest.fixture
def temp_db_paths():
    """Create temporary database file paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield {
            "jobs": Path(tmpdir) / "jobs.db",
            "feeds": Path(tmpdir) / "feeds.db",
        }


@pytest.fixture
async def job_store(temp_db_paths):
    """Create an initialized JobStore."""
    store = JobStore(db_path=temp_db_paths["jobs"])
    await store.initialize()
    return store


@pytest.fixture
async def feed_store(temp_db_paths):
    """Create an initialized FeedStore."""
    store = FeedStore(db_path=temp_db_paths["feeds"])
    await store.initialize()
    return store


@pytest.fixture
def sample_config():
    """Create a sample schedule configuration."""
    return ScheduleConfig(
        categories={
            "technology": CategorySchedule(schedule="0 6 * * *"),
            "science": CategorySchedule(schedule="0 8 * * 1"),
        }
    )


@pytest.fixture
def mock_executor():
    """Create a mock job executor."""
    executor = MagicMock()
    executor.execute_job = AsyncMock(return_value=None)
    executor._fetch_and_process = AsyncMock(return_value=5)
    return executor


@pytest.fixture
async def scheduler(sample_config, job_store, feed_store, mock_executor):
    """Create a scheduler."""
    sched = DigestScheduler(
        config=sample_config,
        job_store=job_store,
        feed_store=feed_store,
        executor=mock_executor,
    )
    await sched.start()
    yield sched
    await sched.stop()


@pytest.fixture
async def app(scheduler):
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(router)
    set_scheduler(scheduler)
    return app


@pytest.fixture
async def client(app):
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestListJobsEndpoint:
    """Tests for GET /jobs endpoint."""

    async def test_list_jobs(self, client):
        """Test listing all jobs."""
        response = await client.get("/jobs")

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert len(data["jobs"]) == 2

        slugs = [j["category_slug"] for j in data["jobs"]]
        assert "technology" in slugs
        assert "science" in slugs

    async def test_list_jobs_includes_status(self, client):
        """Test that job list includes status info."""
        response = await client.get("/jobs")

        data = response.json()
        job = data["jobs"][0]

        assert "category_slug" in job
        assert "status" in job
        assert "last_run" in job
        assert "next_run" in job


class TestJobStatusEndpoint:
    """Tests for GET /jobs/{category_slug}/status endpoint."""

    async def test_get_status(self, client):
        """Test getting job status."""
        response = await client.get("/jobs/technology/status")

        assert response.status_code == 200
        data = response.json()
        assert data["category_slug"] == "technology"
        assert data["status"] == "scheduled"

    async def test_get_status_unknown_category(self, client):
        """Test getting status for unknown category."""
        response = await client.get("/jobs/nonexistent/status")

        assert response.status_code == 404
        data = response.json()
        assert "nonexistent" in data["detail"]


class TestTriggerJobEndpoint:
    """Tests for POST /jobs/{category_slug}/run endpoint."""

    async def test_trigger_job(self, client):
        """Test triggering a job."""
        response = await client.post("/jobs/technology/run")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert "job_id" in data

    async def test_trigger_unknown_category(self, client):
        """Test triggering job for unknown category."""
        response = await client.post("/jobs/nonexistent/run")

        assert response.status_code == 404

    async def test_trigger_already_running(self, client, scheduler):
        """Test triggering job that's already running."""
        # First trigger starts the job
        response1 = await client.post("/jobs/technology/run")
        assert response1.status_code == 200

        # Second trigger should fail (job still running)
        response2 = await client.post("/jobs/technology/run")
        assert response2.status_code == 409
        assert "already running" in response2.json()["detail"]


class TestJobHistoryEndpoint:
    """Tests for GET /jobs/{category_slug}/history endpoint."""

    async def test_get_history_empty(self, client):
        """Test getting history for category with no runs."""
        response = await client.get("/jobs/technology/history")

        assert response.status_code == 200
        data = response.json()
        assert data["runs"] == []

    async def test_get_history_with_runs(self, client, job_store):
        """Test getting history with runs."""
        # Add some job runs
        run = await job_store.create_run("technology")
        await job_store.complete_run(run.id, "success", article_count=10)

        response = await client.get("/jobs/technology/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data["runs"]) == 1
        assert data["runs"][0]["status"] == "success"

    async def test_get_history_with_limit(self, client, job_store):
        """Test getting history with limit."""
        # Add several job runs
        for i in range(5):
            run = await job_store.create_run("technology")
            await job_store.complete_run(run.id, "success", article_count=i)

        response = await client.get("/jobs/technology/history?limit=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data["runs"]) == 3

    async def test_get_history_unknown_category(self, client):
        """Test getting history for unknown category."""
        response = await client.get("/jobs/nonexistent/history")

        assert response.status_code == 404
