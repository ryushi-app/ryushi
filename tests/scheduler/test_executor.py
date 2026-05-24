"""Tests for job executor."""

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ryushi.digest.models import Digest
from ryushi.integrations.freshrss.models import Article, Category
from ryushi.scheduler.executor import JobExecutor
from ryushi.scheduler.store import JobStore
from ryushi.feeds.store import FeedStore


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
def mock_freshrss_client():
    """Create a mock FreshRSS client."""
    client = MagicMock()
    client.get_categories = AsyncMock(return_value=[])
    client.get_unread_items = AsyncMock(return_value=[])
    client.mark_as_read = AsyncMock(return_value=None)
    return client


@pytest.fixture
def mock_digest_engine():
    """Create a mock digest engine."""
    engine = MagicMock()
    engine.generate_digest = AsyncMock(return_value=None)
    return engine


def make_category(name: str = "Technology", cat_id: str = "cat-1") -> Category:
    """Helper to create a Category."""
    return Category(id=cat_id, name=name)


def make_article(title: str = "Test Article") -> Article:
    """Helper to create an Article."""
    return Article(
        id="article-1",
        title=title,
        url="https://example.com/article",
        published_at=datetime.now(UTC),
        teaser="Test teaser",
        category_id="cat-1",
        feed_title="Test Feed",
    )


def make_digest(category_name: str = "Technology") -> Digest:
    """Helper to create a Digest."""
    return Digest(
        id="digest-1",
        category_name=category_name,
        generated_at=datetime.now(UTC),
        summary="# Summary\n\nTest digest content.",
        article_count=5,
        source_urls=["https://example.com/1"],
        model_used="gpt-4.1-mini",
    )


class TestJobExecutorSuccess:
    """Tests for successful job execution."""

    async def test_execute_job_with_articles(self, job_store, feed_store, mock_freshrss_client):
        """Test successful job execution with articles."""
        # Setup mocks
        mock_freshrss_client.get_categories = AsyncMock(return_value=[make_category("Technology")])
        mock_freshrss_client.get_unread_items = AsyncMock(
            return_value=[make_article(), make_article()]
        )

        with patch("ryushi.scheduler.executor.DigestEngine") as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine.generate_digest = AsyncMock(return_value=make_digest())
            mock_engine_class.return_value = mock_engine

            executor = JobExecutor(
                job_store=job_store,
                feed_store=feed_store,
                freshrss_client=mock_freshrss_client,
            )

            result = await executor.execute_job("technology")

            assert result.status == "success"
            assert result.article_count == 2
            assert result.error is None

    async def test_execute_job_no_articles(self, job_store, feed_store, mock_freshrss_client):
        """Test job execution with no articles."""
        mock_freshrss_client.get_categories = AsyncMock(return_value=[make_category("Technology")])
        mock_freshrss_client.get_unread_items = AsyncMock(return_value=[])

        executor = JobExecutor(
            job_store=job_store,
            feed_store=feed_store,
            freshrss_client=mock_freshrss_client,
        )

        result = await executor.execute_job("technology")

        assert result.status == "success"
        assert result.article_count == 0

    async def test_execute_job_category_not_found(
        self, job_store, feed_store, mock_freshrss_client
    ):
        """Test job execution when category not found."""
        mock_freshrss_client.get_categories = AsyncMock(return_value=[])

        executor = JobExecutor(
            job_store=job_store,
            feed_store=feed_store,
            freshrss_client=mock_freshrss_client,
        )

        result = await executor.execute_job("nonexistent")

        assert result.status == "success"
        assert result.article_count == 0


class TestJobExecutorFailure:
    """Tests for job execution failures."""

    async def test_execute_job_freshrss_error(self, job_store, feed_store, mock_freshrss_client):
        """Test job execution handles FreshRSS errors."""
        mock_freshrss_client.get_categories = AsyncMock(side_effect=Exception("Connection refused"))

        executor = JobExecutor(
            job_store=job_store,
            feed_store=feed_store,
            freshrss_client=mock_freshrss_client,
        )

        result = await executor.execute_job("technology")

        assert result.status == "failed"
        assert "Connection refused" in result.error

    async def test_execute_job_digest_error(self, job_store, feed_store, mock_freshrss_client):
        """Test job execution handles digest generation errors."""
        mock_freshrss_client.get_categories = AsyncMock(return_value=[make_category("Technology")])
        mock_freshrss_client.get_unread_items = AsyncMock(return_value=[make_article()])

        with patch("ryushi.scheduler.executor.DigestEngine") as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine.generate_digest = AsyncMock(side_effect=Exception("API error"))
            mock_engine_class.return_value = mock_engine

            executor = JobExecutor(
                job_store=job_store,
                feed_store=feed_store,
                freshrss_client=mock_freshrss_client,
            )

            result = await executor.execute_job("technology")

            assert result.status == "failed"
            assert "API error" in result.error


class TestJobExecutorPersistence:
    """Tests for job run persistence."""

    async def test_job_run_persisted(self, job_store, feed_store, mock_freshrss_client):
        """Test that job run is persisted to store."""
        mock_freshrss_client.get_categories = AsyncMock(return_value=[])

        executor = JobExecutor(
            job_store=job_store,
            feed_store=feed_store,
            freshrss_client=mock_freshrss_client,
        )

        await executor.execute_job("technology")

        history = await job_store.get_history("technology")
        assert len(history) == 1
        assert history[0].category_slug == "technology"

    async def test_feed_entry_persisted(self, job_store, feed_store, mock_freshrss_client):
        """Test that feed entry is persisted on success."""
        mock_freshrss_client.get_categories = AsyncMock(return_value=[make_category("Technology")])
        mock_freshrss_client.get_unread_items = AsyncMock(return_value=[make_article()])

        with patch("ryushi.scheduler.executor.DigestEngine") as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine.generate_digest = AsyncMock(return_value=make_digest())
            mock_engine_class.return_value = mock_engine

            executor = JobExecutor(
                job_store=job_store,
                feed_store=feed_store,
                freshrss_client=mock_freshrss_client,
            )

            await executor.execute_job("technology")

            entries = await feed_store.get_entries("technology")
            assert len(entries) == 1


class TestJobExecutorCategoryMatching:
    """Tests for category slug to name matching."""

    async def test_matches_by_slug(self, job_store, feed_store, mock_freshrss_client):
        """Test matching category by slug conversion."""
        mock_freshrss_client.get_categories = AsyncMock(
            return_value=[make_category("Software Engineering")]
        )
        mock_freshrss_client.get_unread_items = AsyncMock(return_value=[])

        executor = JobExecutor(
            job_store=job_store,
            feed_store=feed_store,
            freshrss_client=mock_freshrss_client,
        )

        await executor.execute_job("software-engineering")

        # Should have called get_unread_items (category was found)
        mock_freshrss_client.get_unread_items.assert_called_once()


class TestJobExecutorGistPublishing:
    """Tests for Gist publishing functionality."""

    async def test_gist_publishing_enabled(self, job_store, feed_store, mock_freshrss_client):
        """Test job execution with Gist publishing enabled."""
        mock_freshrss_client.get_categories = AsyncMock(return_value=[make_category("Technology")])
        mock_freshrss_client.get_unread_items = AsyncMock(return_value=[make_article()])

        with patch("ryushi.scheduler.executor.DigestEngine") as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine.generate_digest = AsyncMock(return_value=make_digest())
            mock_engine_class.return_value = mock_engine

            with patch("ryushi.scheduler.executor.GistPublisher") as mock_gist_class:
                mock_gist = MagicMock()
                mock_gist.publish = AsyncMock(return_value=None)
                mock_gist_class.return_value = mock_gist

                executor = JobExecutor(
                    job_store=job_store,
                    feed_store=feed_store,
                    freshrss_client=mock_freshrss_client,
                )

                result = await executor.execute_job(
                    "technology",
                    gist_enabled=True,
                    gist_id="test-gist-id",
                )

                assert result.status == "success"
                # Verify GistPublisher.publish was called
                mock_gist.publish.assert_called_once()
                call_args = mock_gist.publish.call_args
                assert call_args[0][0] == "test-gist-id"  # gist_id
                assert call_args[0][1] == "technology.atom.xml"  # filename
                assert "<?xml" in call_args[0][2]  # content contains XML

    async def test_gist_publishing_disabled(self, job_store, feed_store, mock_freshrss_client):
        """Test job execution with Gist publishing disabled."""
        mock_freshrss_client.get_categories = AsyncMock(return_value=[make_category("Technology")])
        mock_freshrss_client.get_unread_items = AsyncMock(return_value=[make_article()])

        with patch("ryushi.scheduler.executor.DigestEngine") as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine.generate_digest = AsyncMock(return_value=make_digest())
            mock_engine_class.return_value = mock_engine

            with patch("ryushi.scheduler.executor.GistPublisher") as mock_gist_class:
                mock_gist = MagicMock()
                mock_gist.publish = AsyncMock(return_value=None)
                mock_gist_class.return_value = mock_gist

                executor = JobExecutor(
                    job_store=job_store,
                    feed_store=feed_store,
                    freshrss_client=mock_freshrss_client,
                )

                result = await executor.execute_job("technology", gist_enabled=False)

                assert result.status == "success"
                # Verify GistPublisher.publish was NOT called
                mock_gist.publish.assert_not_called()

    async def test_gist_publishing_without_gist_id(
        self, job_store, feed_store, mock_freshrss_client
    ):
        """Test job execution with Gist enabled but no gist_id."""
        mock_freshrss_client.get_categories = AsyncMock(return_value=[make_category("Technology")])
        mock_freshrss_client.get_unread_items = AsyncMock(return_value=[make_article()])

        with patch("ryushi.scheduler.executor.DigestEngine") as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine.generate_digest = AsyncMock(return_value=make_digest())
            mock_engine_class.return_value = mock_engine

            with patch("ryushi.scheduler.executor.GistPublisher") as mock_gist_class:
                mock_gist = MagicMock()
                mock_gist.publish = AsyncMock(return_value=None)
                mock_gist_class.return_value = mock_gist

                executor = JobExecutor(
                    job_store=job_store,
                    feed_store=feed_store,
                    freshrss_client=mock_freshrss_client,
                )

                result = await executor.execute_job("technology", gist_enabled=True, gist_id=None)

                assert result.status == "success"
                # Verify GistPublisher.publish was NOT called (no gist_id)
                mock_gist.publish.assert_not_called()

    async def test_gist_publishing_failure_doesnt_fail_job(
        self, job_store, feed_store, mock_freshrss_client
    ):
        """Test that Gist publishing failure doesn't fail the job."""
        mock_freshrss_client.get_categories = AsyncMock(return_value=[make_category("Technology")])
        mock_freshrss_client.get_unread_items = AsyncMock(return_value=[make_article()])

        with patch("ryushi.scheduler.executor.DigestEngine") as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine.generate_digest = AsyncMock(return_value=make_digest())
            mock_engine_class.return_value = mock_engine

            with patch("ryushi.scheduler.executor.GistPublisher") as mock_gist_class:
                mock_gist = MagicMock()
                # Simulate Gist publishing failure
                mock_gist.publish = AsyncMock(side_effect=Exception("Gist API error"))
                mock_gist_class.return_value = mock_gist

                executor = JobExecutor(
                    job_store=job_store,
                    feed_store=feed_store,
                    freshrss_client=mock_freshrss_client,
                )

                result = await executor.execute_job(
                    "technology",
                    gist_enabled=True,
                    gist_id="test-gist-id",
                )

                # Job should still succeed even if Gist publishing fails
                assert result.status == "success"
                assert result.article_count == 1
