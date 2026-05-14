"""Tests for job store."""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ryushi.scheduler.models import JobRun
from ryushi.scheduler.store import JobStore


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_jobs.db"


@pytest.fixture
async def store(temp_db_path):
    """Create an initialized JobStore."""
    store = JobStore(db_path=temp_db_path)
    await store.initialize()
    return store


class TestJobStoreInitialization:
    """Tests for JobStore initialization."""

    async def test_initialize_creates_database(self, temp_db_path):
        """Test that initialize creates the database file."""
        store = JobStore(db_path=temp_db_path)
        assert not temp_db_path.exists()

        await store.initialize()

        assert temp_db_path.exists()

    async def test_initialize_is_idempotent(self, temp_db_path):
        """Test that initialize can be called multiple times."""
        store = JobStore(db_path=temp_db_path)
        await store.initialize()
        await store.initialize()  # Should not raise

    async def test_auto_initialize_on_first_operation(self, temp_db_path):
        """Test that store auto-initializes on first operation."""
        store = JobStore(db_path=temp_db_path)
        assert not temp_db_path.exists()

        # Operation should trigger initialization
        history = await store.get_history("nonexistent")

        assert temp_db_path.exists()
        assert history == []


class TestJobStoreCreateRun:
    """Tests for creating job runs."""

    async def test_create_run(self, store):
        """Test creating a job run."""
        run = await store.create_run("technology")

        assert run.category_slug == "technology"
        assert run.status == "running"
        assert run.id is not None
        assert run.started_at is not None
        assert run.finished_at is None

    async def test_create_run_unique_ids(self, store):
        """Test that each run gets a unique ID."""
        run1 = await store.create_run("tech")
        run2 = await store.create_run("tech")

        assert run1.id != run2.id

    async def test_create_run_persisted(self, store):
        """Test that created run is persisted."""
        run = await store.create_run("technology")

        history = await store.get_history("technology")
        assert len(history) == 1
        assert history[0].id == run.id


class TestJobStoreCompleteRun:
    """Tests for completing job runs."""

    async def test_complete_run_success(self, store):
        """Test completing a run with success."""
        run = await store.create_run("technology")

        await store.complete_run(run.id, "success", article_count=25)

        history = await store.get_history("technology")
        assert len(history) == 1
        assert history[0].status == "success"
        assert history[0].article_count == 25
        assert history[0].finished_at is not None

    async def test_complete_run_failed(self, store):
        """Test completing a run with failure."""
        run = await store.create_run("technology")

        await store.complete_run(run.id, "failed", error="Connection timeout")

        history = await store.get_history("technology")
        assert len(history) == 1
        assert history[0].status == "failed"
        assert history[0].error == "Connection timeout"


class TestJobStoreRetention:
    """Tests for retention limit enforcement."""

    async def test_retention_limit_enforced(self, temp_db_path):
        """Test that retention limit removes oldest runs."""
        store = JobStore(db_path=temp_db_path, retention_limit=5)
        await store.initialize()

        # Create and complete 7 runs
        for i in range(7):
            run = await store.create_run("technology")
            await store.complete_run(run.id, "success", article_count=i)

        history = await store.get_history("technology", limit=100)
        assert len(history) == 5

    async def test_retention_per_category(self, temp_db_path):
        """Test that retention is per-category."""
        store = JobStore(db_path=temp_db_path, retention_limit=3)
        await store.initialize()

        # Add 4 runs to category A
        for _ in range(4):
            run = await store.create_run("category-a")
            await store.complete_run(run.id, "success")

        # Add 2 runs to category B
        for _ in range(2):
            run = await store.create_run("category-b")
            await store.complete_run(run.id, "success")

        # Category A should have 3 runs (retention limit)
        history_a = await store.get_history("category-a", limit=100)
        assert len(history_a) == 3

        # Category B should have 2 runs (under limit)
        history_b = await store.get_history("category-b", limit=100)
        assert len(history_b) == 2


class TestJobStoreGetLastRun:
    """Tests for getting last run."""

    async def test_get_last_run_none_when_empty(self, store):
        """Test get_last_run returns None for empty category."""
        result = await store.get_last_run("nonexistent")
        assert result is None

    async def test_get_last_run_ignores_running(self, store):
        """Test get_last_run ignores running jobs."""
        run = await store.create_run("technology")
        # Don't complete it

        result = await store.get_last_run("technology")
        assert result is None

    async def test_get_last_run_returns_completed(self, store):
        """Test get_last_run returns most recent completed."""
        run1 = await store.create_run("technology")
        await store.complete_run(run1.id, "success", article_count=10)

        run2 = await store.create_run("technology")
        await store.complete_run(run2.id, "failed", error="Error")

        result = await store.get_last_run("technology")
        assert result is not None
        assert result.id == run2.id
        assert result.status == "failed"


class TestJobStoreGetHistory:
    """Tests for getting job history."""

    async def test_get_history_empty(self, store):
        """Test get_history for empty category."""
        history = await store.get_history("nonexistent")
        assert history == []

    async def test_get_history_ordered_newest_first(self, store):
        """Test that history is ordered newest first."""
        # Create runs with small delay
        run1 = await store.create_run("technology")
        await store.complete_run(run1.id, "success")

        run2 = await store.create_run("technology")
        await store.complete_run(run2.id, "success")

        history = await store.get_history("technology")

        assert len(history) == 2
        assert history[0].id == run2.id
        assert history[1].id == run1.id

    async def test_get_history_with_limit(self, store):
        """Test get_history respects limit."""
        for _ in range(5):
            run = await store.create_run("technology")
            await store.complete_run(run.id, "success")

        history = await store.get_history("technology", limit=3)
        assert len(history) == 3


class TestJobStoreRunningStatus:
    """Tests for checking running status."""

    async def test_is_job_running_false_when_empty(self, store):
        """Test is_job_running returns False for empty category."""
        result = await store.is_job_running("nonexistent")
        assert result is False

    async def test_is_job_running_true_when_running(self, store):
        """Test is_job_running returns True when running."""
        await store.create_run("technology")

        result = await store.is_job_running("technology")
        assert result is True

    async def test_is_job_running_false_when_completed(self, store):
        """Test is_job_running returns False after completion."""
        run = await store.create_run("technology")
        await store.complete_run(run.id, "success")

        result = await store.is_job_running("technology")
        assert result is False

    async def test_get_running_job(self, store):
        """Test get_running_job returns the running job."""
        run = await store.create_run("technology")

        result = await store.get_running_job("technology")
        assert result is not None
        assert result.id == run.id
        assert result.status == "running"

    async def test_get_running_job_none_when_completed(self, store):
        """Test get_running_job returns None after completion."""
        run = await store.create_run("technology")
        await store.complete_run(run.id, "success")

        result = await store.get_running_job("technology")
        assert result is None
