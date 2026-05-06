"""Pydantic models for digest generation.

This module defines the Digest and DigestConfig models used by the
digest engine.
"""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class DigestConfig(BaseModel):
    """Configuration for the digest engine.

    Attributes:
        model: LiteLLM model identifier (e.g., "gpt-4o-mini", "claude-3-haiku").
        max_tokens: Maximum tokens for AI response.
        temperature: Sampling temperature (0.0-2.0).
        timeout: Request timeout in seconds.
        base_url: Custom API endpoint URL (optional).
        system_prompt: Custom system prompt template (optional).
        language: Language for digest output.
    """

    model: str = "gpt-4o-mini"
    max_tokens: int = 1500
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    timeout: float = 60.0
    base_url: str | None = None
    system_prompt: str | None = None
    language: str = "English"


class Digest(BaseModel):
    """Represents an AI-generated digest of articles.

    Attributes:
        id: Unique identifier (UUID).
        category_name: Name of the category being digested.
        generated_at: Timestamp when digest was created.
        summary: AI-generated markdown summary.
        article_count: Number of articles in the input.
        source_urls: URLs referenced in the summary.
        model_used: Model identifier used for generation.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    category_name: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    summary: str
    article_count: int = Field(ge=0)
    source_urls: list[str] = Field(default_factory=list)
    model_used: str
