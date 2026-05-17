"""Digest generation engine.

This module provides the DigestEngine class for generating AI-powered
digests from article lists using LiteLLM.
"""

import logging
import re
import time
from typing import TYPE_CHECKING

import litellm
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import DigestError
from .models import Digest, DigestConfig
from .prompts import DEFAULT_SYSTEM_PROMPT, build_prompt, format_system_prompt

if TYPE_CHECKING:
    from ryushi.integrations.freshrss.models import Article

logger = logging.getLogger(__name__)


def _is_retryable_error(exception: BaseException) -> bool:
    """Check if an exception should trigger a retry.

    Retries on:
    - 429 Too Many Requests (rate limit)
    - 503 Service Unavailable
    - 5xx Server errors

    Does NOT retry on:
    - 400 Bad Request
    - 401 Unauthorized
    - 403 Forbidden
    - Other client errors

    Args:
        exception: The exception to check.

    Returns:
        True if the request should be retried.
    """
    if hasattr(exception, "status_code"):
        status = exception.status_code
        # Retry on rate limit and server errors
        if status == 429 or status >= 500:
            return True
        # Don't retry on client errors
        return False

    # Retry on timeout errors
    if "timeout" in str(exception).lower():
        return True

    return False


class DigestEngine:
    """Engine for generating AI-powered digests from articles.

    Uses LiteLLM for model-agnostic AI calls and supports configurable
    prompts, models, and parameters.

    Example:
        config = DigestConfig(model="gpt-4o-mini", temperature=0.7)
        engine = DigestEngine(config)
        digest = await engine.generate_digest(articles, "Technology")
    """

    def __init__(self, config: DigestConfig | None = None):
        """Initialize the digest engine.

        Args:
            config: Engine configuration. Uses defaults if not provided.
        """
        self.config = config or DigestConfig()
        self._retry_count = 0

    async def generate_digest(
        self,
        articles: list["Article"],
        category_name: str,
    ) -> Digest | None:
        """Generate a digest from a list of articles.

        This is a read-only operation that summarizes articles using AI.

        Args:
            articles: List of Article objects to summarize.
            category_name: Name of the category being digested.

        Returns:
            Digest object with AI-generated summary, or None if no articles.

        Raises:
            DigestError: If AI call fails after retries.
        """
        if not articles:
            logger.debug("No articles provided, returning None")
            return None

        # Build the prompt
        user_prompt, articles_included = build_prompt(
            articles,
            category_name,
            model=self.config.model,
        )

        if articles_included == 0:
            logger.warning("No articles fit in context window")
            return None

        # Format system prompt
        system_prompt = format_system_prompt(
            self.config.system_prompt or DEFAULT_SYSTEM_PROMPT,
            language=self.config.language,
        )

        # Make the AI call
        self._retry_count = 0
        start_time = time.time()

        try:
            summary = await self._call_ai(system_prompt, user_prompt)
        except DigestError:
            # Already wrapped, re-raise
            latency = time.time() - start_time
            logger.error(
                "AI call failed: model=%s, latency=%.2fs, retries=%d",
                self.config.model,
                latency,
                self._retry_count,
            )
            raise
        except Exception as e:
            # Wrap in DigestError after retries exhausted
            latency = time.time() - start_time
            status_code = getattr(e, "status_code", None)
            logger.error(
                "AI call failed: model=%s, latency=%.2fs, retries=%d, error=%s",
                self.config.model,
                latency,
                self._retry_count,
                str(e),
            )
            raise DigestError(
                f"AI request failed after {self._retry_count} attempts: {e}",
                status_code=status_code,
                model=self.config.model,
                retry_count=self._retry_count,
            ) from e

        latency = time.time() - start_time
        logger.info(
            "AI call succeeded: model=%s, latency=%.2fs, articles=%d",
            self.config.model,
            latency,
            articles_included,
        )

        # Extract URLs from the summary
        source_urls = self._extract_urls(summary, articles)

        return Digest(
            category_name=category_name,
            summary=summary,
            article_count=len(articles),
            source_urls=source_urls,
            model_used=self.config.model,
        )

    @retry(
        retry=retry_if_exception(_is_retryable_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _call_ai(self, system_prompt: str, user_prompt: str) -> str:
        """Make an AI call with retry logic.

        Args:
            system_prompt: System prompt for the AI.
            user_prompt: User prompt with article content.

        Returns:
            AI-generated summary text.

        Raises:
            DigestError: If the call fails.
        """
        self._retry_count += 1
        if self._retry_count > 1:
            logger.info(
                "Retrying AI call: attempt=%d, model=%s",
                self._retry_count,
                self.config.model,
            )

        try:
            # Build kwargs for litellm
            kwargs: dict = {
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "timeout": self.config.timeout,
            }

            if self.config.base_url:
                kwargs["api_base"] = self.config.base_url

            if self.config.api_key:
                kwargs["api_key"] = self.config.api_key

            response = await litellm.acompletion(**kwargs)

            # Extract content from response
            content = response.choices[0].message.content

            # Log token usage if available
            if hasattr(response, "usage") and response.usage:
                logger.debug(
                    "Token usage: prompt=%d, completion=%d, total=%d",
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    response.usage.total_tokens,
                )

            return str(content) if content else ""

        except Exception as e:
            status_code = getattr(e, "status_code", None)

            # Don't retry on auth errors
            if status_code in (400, 401, 403):
                logger.error(
                    "Non-retryable error: status=%s, model=%s",
                    status_code,
                    self.config.model,
                )
                raise DigestError(
                    f"AI request failed: {e}",
                    status_code=status_code,
                    model=self.config.model,
                    retry_count=self._retry_count,
                ) from e

            # Re-raise for retry logic to handle
            if _is_retryable_error(e):
                raise

            # Wrap other errors
            raise DigestError(
                f"AI request failed: {e}",
                status_code=status_code,
                model=self.config.model,
                retry_count=self._retry_count,
            ) from e

    def _extract_urls(self, summary: str, articles: list["Article"]) -> list[str]:
        """Extract article URLs that appear in the summary.

        Args:
            summary: AI-generated summary text.
            articles: Original article list.

        Returns:
            List of URLs from articles that are referenced in summary.
        """
        # Create a set of all article URLs
        article_urls = {article.url for article in articles}

        # Find all URLs in the summary
        url_pattern = r"https?://[^\s\)\]\"'<>]+"
        found_urls = re.findall(url_pattern, summary)

        # Filter to only include article URLs
        return [url for url in found_urls if url in article_urls]
