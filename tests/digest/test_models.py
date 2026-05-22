"""Tests for digest Pydantic models."""

from datetime import UTC, datetime, timezone

import pytest
from pydantic import ValidationError

from ryushi.digest.models import Digest, DigestConfig


class TestDigestConfig:
    """Tests for DigestConfig model."""

    def test_default_values(self, monkeypatch):
        """DigestConfig has sensible defaults."""
        # Clear env vars to test true defaults
        monkeypatch.delenv("RYUSHI_AI_MODEL", raising=False)
        monkeypatch.delenv("RYUSHI_AI_BASE_URL", raising=False)
        monkeypatch.delenv("RYUSHI_AI_API_KEY", raising=False)

        config = DigestConfig()
        assert config.model == "gpt-4.1-mini"
        assert config.max_tokens == 1500
        assert config.temperature == 0.7
        assert config.timeout == 60.0
        assert config.base_url is None
        assert config.api_key is None
        assert config.system_prompt is None
        assert config.language == "German"

    def test_custom_values(self):
        """DigestConfig accepts custom values."""
        config = DigestConfig(
            model="claude-3-haiku",
            max_tokens=2000,
            temperature=0.3,
            timeout=120.0,
            base_url="https://custom.api.example.com",
            system_prompt="Custom prompt",
            language="German",
        )
        assert config.model == "claude-3-haiku"
        assert config.max_tokens == 2000
        assert config.temperature == 0.3
        assert config.timeout == 120.0
        assert config.base_url == "https://custom.api.example.com"
        assert config.system_prompt == "Custom prompt"
        assert config.language == "German"

    def test_temperature_validation_min(self):
        """DigestConfig rejects temperature below 0."""
        with pytest.raises(ValidationError):
            DigestConfig(temperature=-0.1)

    def test_temperature_validation_max(self):
        """DigestConfig rejects temperature above 2."""
        with pytest.raises(ValidationError):
            DigestConfig(temperature=2.1)

    def test_temperature_boundary_values(self):
        """DigestConfig accepts temperature at boundaries."""
        config_min = DigestConfig(temperature=0.0)
        config_max = DigestConfig(temperature=2.0)
        assert config_min.temperature == 0.0
        assert config_max.temperature == 2.0


class TestDigest:
    """Tests for Digest model."""

    def test_digest_with_required_fields(self):
        """Digest requires category_name, summary, article_count, model_used."""
        digest = Digest(
            category_name="Technology",
            summary="This is a test summary.",
            article_count=10,
            model_used="gpt-4.1-mini",
        )
        assert digest.category_name == "Technology"
        assert digest.summary == "This is a test summary."
        assert digest.article_count == 10
        assert digest.model_used == "gpt-4.1-mini"

    def test_digest_auto_generates_id(self):
        """Digest auto-generates UUID if not provided."""
        digest = Digest(
            category_name="News",
            summary="Summary",
            article_count=5,
            model_used="gpt-4o",
        )
        assert digest.id is not None
        assert len(digest.id) == 36  # UUID format

    def test_digest_auto_generates_timestamp(self):
        """Digest auto-generates generated_at timestamp."""
        before = datetime.now(UTC)
        digest = Digest(
            category_name="News",
            summary="Summary",
            article_count=5,
            model_used="gpt-4o",
        )
        after = datetime.now(UTC)
        assert before <= digest.generated_at <= after

    def test_digest_with_source_urls(self):
        """Digest accepts source_urls list."""
        urls = ["https://example.com/1", "https://example.com/2"]
        digest = Digest(
            category_name="News",
            summary="Summary",
            article_count=2,
            model_used="gpt-4o",
            source_urls=urls,
        )
        assert digest.source_urls == urls

    def test_digest_source_urls_default_empty(self):
        """Digest source_urls defaults to empty list."""
        digest = Digest(
            category_name="News",
            summary="Summary",
            article_count=5,
            model_used="gpt-4o",
        )
        assert digest.source_urls == []

    def test_digest_article_count_validation(self):
        """Digest rejects negative article_count."""
        with pytest.raises(ValidationError):
            Digest(
                category_name="News",
                summary="Summary",
                article_count=-1,
                model_used="gpt-4o",
            )

    def test_digest_article_count_zero_allowed(self):
        """Digest accepts article_count of 0."""
        digest = Digest(
            category_name="News",
            summary="No articles available",
            article_count=0,
            model_used="gpt-4o",
        )
        assert digest.article_count == 0

    def test_digest_missing_required_fields(self):
        """Digest raises error when required fields missing."""
        with pytest.raises(ValidationError):
            Digest(category_name="News")

    def test_digest_serialization(self):
        """Digest can be serialized to dict."""
        digest = Digest(
            id="test-uuid",
            category_name="Tech",
            generated_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            summary="Test summary",
            article_count=10,
            source_urls=["https://example.com"],
            model_used="gpt-4.1-mini",
        )
        data = digest.model_dump()
        assert data["id"] == "test-uuid"
        assert data["category_name"] == "Tech"
        assert data["summary"] == "Test summary"
        assert data["article_count"] == 10
        assert data["source_urls"] == ["https://example.com"]
        assert data["model_used"] == "gpt-4.1-mini"
