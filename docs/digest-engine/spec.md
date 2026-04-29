# Digest Engine

## Overview

Takes a list of Articles, builds a structured prompt, sends it to an
OpenAI-compatible AI backend via LiteLLM, and returns a formatted digest.

## Requirements

### R1 — Prompt Building
- MUST include article title, URL, and teaser in the prompt
- MUST include category name and article count
- MUST use a configurable system prompt template
- MUST truncate input to fit within model context window

### R2 — AI Backend
- MUST use LiteLLM for all AI calls (enables model switching)
- MUST support any OpenAI-compatible endpoint via `base_url`
- MUST read `api_key` from environment
- MUST respect `max_tokens` and `temperature` from config

### R3 — Output Format
- MUST return a `Digest` object with title, summary, and article references
- MUST include source URLs for each mentioned article
- SHOULD structure output as: intro paragraph + bullet points per article

### R4 — Resilience
- MUST retry on transient AI errors (429, 503) with exponential backoff
- MUST fail gracefully: if AI call fails, log error and skip digest
- MUST enforce a timeout of 60 seconds per AI call

## Scenarios

### Scenario 1 — Successful digest
GIVEN 30 unread articles in category "Software Engineering"  
WHEN digest job runs  
THEN returns `Digest` with non-empty summary  
AND summary references at least 5 article URLs

### Scenario 2 — AI rate limit
GIVEN AI backend returns 429  
WHEN digest job runs  
THEN retries up to 3 times with backoff  
AND raises `DigestError` if all retries fail

### Scenario 3 — Empty article list
GIVEN category has 0 unread articles  
WHEN digest job runs  
THEN returns `None` without calling AI backend

### Scenario 4 — Custom prompt template
GIVEN custom `system_prompt` in config  
WHEN digest job runs  
THEN uses custom prompt instead of default

## Data Models

```python
class Digest(BaseModel):
    id: str                     # uuid
    category_name: str
    generated_at: datetime
    summary: str                # AI-generated markdown
    article_count: int
    source_urls: list[str]
    model_used: str

class DigestError(Exception):
    pass
```

##  Default System Prompt

```
You are a helpful assistant that summarizes RSS news digests.
Given a list of articles with titles and teasers, write a concise
digest in {language}. Structure: one intro paragraph summarizing
the main themes, then a bullet point per notable article with
a one-sentence summary and the source URL.
Keep the total length under 600 words.
```

## Dependencies
- litellm — AI backend abstraction
- pydantic — data validation
- tenacity — retry logic