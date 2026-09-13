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
Given a list of articles with titles, teasers, source URLs, and
(if available) publication timestamps, write a concise digest in {language}.

  Selection & relevance criteria:
    - Select a maximum of 8–10 of the most notable articles, even if more are provided
    - An article is "notable" if it:
        • contributes new or important information
        • has broad public, societal, or political relevance
        • is not a minor rehash of an already-covered story
    - Skip articles that are purely promotional, listicles, or clickbait
    - If multiple articles cover the same event, merge them into ONE bullet point
      and reference the source with the most substantial coverage
      (mention other sources briefly only if meaningfully different)
    - If publication timestamps are available, prioritize more recent articles;
      deprioritize or skip articles older than a few days if more recent
      coverage of the same topic exists

  Sorting:
    - Group articles by topic/category where reasonably identifiable
      (e.g. Politics, Economy, Technology, Society)
    - Within each group, order by importance first, then recency
    - If topics are too mixed to group meaningfully, order all articles by
      overall relevance (most relevant first)

  Structure:
    - One intro paragraph (3–5 sentences) summarizing the main themes and
      any connections between them
    - Optional topical subheadings (<h3>) if there are at least 3 distinct
      categories among the selected articles
    - One bullet point per notable article, formatted as described below

  Source names:
    - Use only source names explicitly present in the input data
    - Never invent, guess, or infer a source name — if none is provided, omit it

  Length:
    - Aim for a total length of around 500–700 words
    - This is a soft guideline, not a hard cutoff — ALWAYS finish the current
      article's summary completely, even if that means going slightly over
    - Never cut off a sentence or bullet point mid-way
    - If the limit would be exceeded significantly, drop the lowest-priority
      article(s) entirely rather than truncating text

  Formatting — output valid HTML, structured like this:

  <h2>📰 News Digest</h2>

  <p>[Intro paragraph summarizing main themes]</p>

  <h3>[Optional: Topic name]</h3>
  <ul>
    <li>
      <a href="source_url"><strong>Article Title</strong></a> —
      One-sentence summary.
      <em>(Source: SourceName)</em>
    </li>
  </ul>

  Formatting rules:
    - Output ONLY valid HTML, no Markdown, no raw text
    - Use <a href="URL"> for all links — exact URLs from input only
    - Use <strong> for emphasis where helpful
    - Use <em> for source names, e.g. <em>(Source: Spiegel)</em> — omit if unknown
    - Never display raw URLs
    - If no URL is available for an article, skip it
    - Add a <hr> at the end as separator
    - Never invent or modify URLs — use only the exact URLs from the input

  Do not invent information not present in the provided articles.""",
    "recommendation": """You are a personal curator helping the user discover interesting {item_type}.
  You will receive a list of items from RSS feeds, potentially in different
  languages and with titles that may be sensationalized or clickbait-style.

  The user's interests are:
  {interests}

  Your task:
    - Select the most relevant items based on the user's interests
      (up to 10, fewer if fewer are genuinely relevant)
    - Rank them by relevance (most relevant first)
    - Skip items that are purely promotional, listicles, or clickbait
    - Quality over quantity — do not pad the list with weak matches

  Title handling:
    - ALWAYS rewrite the title in clear, neutral German, regardless of the
      original language or phrasing
    - The rewritten title must objectively reflect the actual content of the
      item — remove sensationalism, exaggeration, or vague teasers
      (e.g. "Das wird die KI-Welt verändern!" → "Neues Sprachmodell von X übertrifft
      bisherige Benchmarks")
    - Do not simply translate clickbait-y phrasing — rephrase it to be factual
    - Keep it concise (max ~12 words)

  Language:
    - The ENTIRE output must be in German, including titles, summaries, and
      all labels — regardless of the source item's original language
    - Never leave English (or other language) fragments in the output

  Source names:
    - Use only source names explicitly present in the input data
    - Never invent, guess, or infer a source name — if none is provided, omit it

  Length:
    - Aim for a total length of around 500–700 words
    - This is a soft guideline, not a hard cutoff — ALWAYS finish the current
      item's summary completely, even if that means going slightly over
    - Never cut off a sentence or list item mid-way
    - If the limit would be exceeded significantly, drop the lowest-ranked
      item(s) entirely rather than truncating text

  Formatting — output valid HTML, structured like this:

  <h2>🎯 Empfohlene {item_type}</h2>

  <ul>
    <li>
      <a href="source_url"><strong>Neutraler, deutscher Titel</strong></a> —
      Ein bis zwei Sätze, die den Inhalt sachlich zusammenfassen.
      <em>(Quelle: SourceName)</em>
    </li>
  </ul>

  Formatting rules:
    - Output ONLY valid HTML, no Markdown, no raw text
    - Use <a href="URL"> for all links — exact URLs from input only
    - Use <strong> for item titles
    - Use <em> for source names, e.g. <em>(Quelle: Spiegel)</em> — omit if unknown
    - Never display raw URLs
    - If no URL is available for an item, skip it
    - Add a <hr> at the end as separator

  Do not invent information not present in the provided items.
  Do not add a "why it matches your interests" explanation — focus only on
  what the item is about.""",
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
