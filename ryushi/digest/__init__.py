"""Digest generation engine for Ryushi.

This module provides AI-powered digest generation from article lists
using LiteLLM for model-agnostic AI calls.

Example:
    from ryushi.digest import DigestEngine, DigestConfig

    config = DigestConfig(model="gpt-4o-mini", temperature=0.7)
    engine = DigestEngine(config)
    digest = await engine.generate_digest(articles, "Technology")

Environment Variables:
    OPENAI_API_KEY: API key for OpenAI (or provider-specific key)
    Set via LiteLLM's standard environment variable handling.
"""

from .engine import DigestEngine
from .exceptions import DigestError
from .models import Digest, DigestConfig

__all__ = [
    "DigestEngine",
    "Digest",
    "DigestConfig",
    "DigestError",
]
