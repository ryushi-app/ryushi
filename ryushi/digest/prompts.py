"""Prompt templates and building for digest generation.

This module provides default system prompts and utility functions
for building AI prompts from article lists.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ryushi.integrations.freshrss.models import Article

# Default system prompt template
DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant that summarizes RSS news digests.
Given a list of articles with titles and teasers, write a concise
digest in {language}. Structure: one intro paragraph summarizing
the main themes, then a bullet point per notable article with
a one-sentence summary and the source URL.
Keep the total length under 600 words."""

# Approximate tokens per character (conservative estimate for English)
CHARS_PER_TOKEN = 4

# Default context window sizes for common models
MODEL_CONTEXT_WINDOWS = {
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16385,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
}

# Default context window for unknown models
DEFAULT_CONTEXT_WINDOW = 8192


def get_context_window(model: str) -> int:
    """Get the context window size for a model.

    Args:
        model: Model identifier.

    Returns:
        Context window size in tokens.
    """
    # Check for exact match
    if model in MODEL_CONTEXT_WINDOWS:
        return MODEL_CONTEXT_WINDOWS[model]

    # Check for partial match (e.g., "gpt-4o-mini-2024-07-18")
    for known_model, window in MODEL_CONTEXT_WINDOWS.items():
        if model.startswith(known_model):
            return window

    return DEFAULT_CONTEXT_WINDOW


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.

    Uses a conservative character-based estimate.

    Args:
        text: Text to estimate tokens for.

    Returns:
        Estimated token count.
    """
    return len(text) // CHARS_PER_TOKEN


def format_system_prompt(template: str, language: str = "English") -> str:
    """Format a system prompt template with variables.

    Args:
        template: System prompt template with {variable} placeholders.
        language: Language for digest output.

    Returns:
        Formatted system prompt.
    """
    return template.format(language=language)


def build_prompt(
    articles: list["Article"],
    category_name: str,
    model: str = "gpt-4o-mini",
    max_context_ratio: float = 0.8,
) -> tuple[str, int]:
    """Build a user prompt from articles for digest generation.

    Includes article title, URL, and teaser for each article.
    Truncates article list if needed to fit within context window.

    Args:
        articles: List of Article objects to summarize.
        category_name: Name of the category being digested.
        model: Model identifier for context window lookup.
        max_context_ratio: Maximum ratio of context window to use (0.0-1.0).

    Returns:
        Tuple of (prompt_text, articles_included).
    """
    if not articles:
        return "", 0

    context_window = get_context_window(model)
    max_tokens = int(context_window * max_context_ratio)

    # Build header
    header = f"Category: {category_name}\nTotal articles: {len(articles)}\n\n"
    header += "Articles:\n\n"

    # Build article entries and track which fit
    prompt_parts = [header]
    current_tokens = estimate_tokens(header)
    articles_included = 0

    for article in articles:
        entry = _format_article_entry(article)
        entry_tokens = estimate_tokens(entry)

        if current_tokens + entry_tokens > max_tokens:
            # Add truncation notice if we couldn't fit all
            if articles_included < len(articles):
                notice = f"\n[Note: Showing {articles_included} of {len(articles)} articles due to length limits]\n"
                prompt_parts.append(notice)
            break

        prompt_parts.append(entry)
        current_tokens += entry_tokens
        articles_included += 1

    return "".join(prompt_parts), articles_included


def _format_article_entry(article: "Article") -> str:
    """Format a single article for inclusion in prompt.

    Args:
        article: Article to format.

    Returns:
        Formatted article entry string.
    """
    parts = [f"### {article.title}\n"]
    parts.append(f"URL: {article.url}\n")

    if article.author:
        parts.append(f"Author: {article.author}\n")

    if article.teaser:
        parts.append(f"Teaser: {article.teaser}\n")

    parts.append("\n")
    return "".join(parts)
