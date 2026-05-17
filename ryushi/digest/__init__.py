"""Digest generation engine for Ryushi.

This module provides AI-powered digest generation from article lists
using LiteLLM for model-agnostic AI calls.

Example:
    from ryushi.digest import DigestEngine, DigestConfig

    config = DigestConfig(model="gpt-4.1-mini", temperature=0.7)
    engine = DigestEngine(config)
    digest = await engine.generate_digest(articles, "Technology")

Environment Variables:
    RYUSHI_AI_MODEL: Model to use (default: gpt-4.1-mini)
    RYUSHI_AI_API_KEY: API key for OpenAI or compatible provider
    RYUSHI_AI_BASE_URL: Custom API endpoint URL (optional)
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
