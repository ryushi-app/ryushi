"""Prompt templates and building for digest generation.

This module provides default system prompts and utility functions
for building AI prompts from article lists.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ryushi.integrations.freshrss.models import Article

logger = logging.getLogger(__name__)

# Default system prompt template
DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant that summarizes RSS news digests.
Given a list of articles with titles and teasers, write a concise
digest in {language}. Structure: one intro paragraph summarizing
the main themes, then a bullet point per notable article with
a one-sentence summary and the source URL.
Keep the total length under 600 words."""

# Built-in prompt templates registry
PROMPT_TEMPLATES = {
    "digest": """You are a helpful assistant that summarizes RSS news digests.
Given a list of articles with titles and teasers, write a concise
digest in {language}.

Structure:
  - One intro paragraph summarizing the main themes
  - A bullet point per notable article formatted EXACTLY like this:
    • [Article Title](source_url) — One-sentence summary.
  - The article title must ALWAYS be wrapped as a Markdown hyperlink using the source URL provided in the input data.
  - Skip articles that are purely promotional or clickbait.

Formatting — output valid HTML, structured like this:

<h2>📰 News Digest</h2>

<p>[Intro paragraph summarizing main themes]</p>

<ul>
  <li>
    <a href="source_url"><strong>Article Title</strong></a> —
      One-sentence summary.
  </li>
</ul>

Formatting rules:
  - Output ONLY valid HTML, no Markdown, no raw text
  - Use <a href="URL"> for all links — exact URLs from input only
  - Use <strong> for emphasis where helpful
  - Use <em> for source names, e.g. <em>(Source: Spiegel)</em>
  - Never display raw URLs
  - If no URL is available for an article, skip it
  - Add a <hr> at the end as separator
  - Never invent or modify URLs — use only the exact URLs from the input

Keep the total length under 600 words.
Do not invent information not present in the provided articles.""",
    "recommendation": """You are a personal curator helping the user discover interesting {item_type}.
You will receive a list of items from RSS feeds.

The user's interests are:
{interests}

Your task:
  - Select the 10 most relevant items based on the user's interests
  - Rank them by relevance (most relevant first)
  - Skip items that are purely promotional, listicles, or clickbait
  - If fewer than 10 items are genuinely relevant, recommend less — quality over quantity

Formatting — output valid HTML, structured like this:

<h2>🎯 Recommended {item_type}</h2>

<ol>
  <li>
    <a href="source_url"><strong>Item Title</strong></a>
    <p><em>Why it matches:</em> One sentence explaining relevance to interests.</p>
    <p><em>What it is:</em> One sentence description of the item.</p>
  </li>
</ol>

Formatting rules:
  - Output ONLY valid HTML, no Markdown, no raw text
  - Use <a href="URL"> for all links — exact URLs from input only
  - Use <strong> for item titles
  - Use <em> for section labels ("Why it matches:" and "What it is:")
  - Never display raw URLs
  - If no URL is available for an item, skip it
  - Use ordered list (<ol>) with numbered items
  - Add a <hr> at the end as separator

Respond in {language}.
Do not invent information not present in the provided items.""",
}

# Approximate tokens per character (conservative estimate for English)
CHARS_PER_TOKEN = 4

# Default context window sizes for common models
MODEL_CONTEXT_WINDOWS = {
    "gpt-4.1": 1047576,
    "gpt-4.1-mini": 1047576,
    "gpt-4.1-nano": 1047576,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16385,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    "claude-sonnet-4": 200000,
    "claude-opus-4": 200000,
}

# Default context window for unknown models
DEFAULT_CONTEXT_WINDOW = 8192


def get_template(template_type: str) -> str | None:
    """Retrieve a template from the registry.

    Args:
        template_type: Template type identifier (e.g., "digest", "recommendation").

    Returns:
        Template string if found, None otherwise.
    """
    return PROMPT_TEMPLATES.get(template_type)


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


def select_prompt(
    custom_prompt: str | None = None,
    template_type: str | None = None,
    language: str = "German",
    item_type: str | None = None,
    interests: list[str] | None = None,
) -> str:
    """Select and render a prompt based on priority.

    Priority order: custom_prompt > template_type > default template

    Args:
        custom_prompt: Custom prompt template (takes precedence).
        template_type: Built-in template type identifier.
        language: Language for output (default: German).
        item_type: Type of items for recommendation template.
        interests: List of user interests for recommendation template.

    Returns:
        Rendered system prompt.
    """
    # Priority 1: Custom prompt (if provided, use it directly)
    if custom_prompt:
        return render_template(custom_prompt, language, item_type, interests)

    # Priority 2: Template type (if specified, look it up)
    if template_type:
        template = get_template(template_type)
        if template:
            return render_template(template, language, item_type, interests)
        else:
            # Unknown template type - log warning and fall back to default
            logger.warning(
                "Unknown template type '%s', falling back to default digest template",
                template_type,
            )

    # Priority 3: Default template (digest)
    default_template = get_template("digest")
    if default_template:
        return render_template(default_template, language, item_type, interests)

    # Fallback (should not happen if templates are properly initialized)
    return render_template(DEFAULT_SYSTEM_PROMPT, language, item_type, interests)


def render_template(
    template: str,
    language: str = "German",
    item_type: str | None = None,
    interests: list[str] | None = None,
) -> str:
    """Render a template with parameter substitution.

    Substitutes {language}, {item_type}, and {interests} placeholders.
    Provides sensible defaults for missing optional parameters.

    Args:
        template: Template string with {variable} placeholders.
        language: Language for output (default: German).
        item_type: Type of items (e.g., "books", "movies"). Optional.
        interests: List of user interests. Optional.

    Returns:
        Rendered template with all placeholders substituted.
    """
    # Format interests as a bullet list if provided
    interests_text = ""
    if interests:
        interests_text = "\n".join(f"  - {interest}" for interest in interests)
    else:
        interests_text = "  (No specific interests provided)"

    return template.format(
        language=language,
        item_type=item_type or "items",
        interests=interests_text,
    )


def format_system_prompt(template: str, language: str = "German") -> str:
    """Format a system prompt template with variables.

    Args:
        template: System prompt template with {variable} placeholders.
        language: Language for digest output (default: German).

    Returns:
        Formatted system prompt.
    """
    return template.format(language=language)


def build_prompt(
    articles: list["Article"],
    category_name: str,
    model: str = "gpt-4.1-mini",
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
