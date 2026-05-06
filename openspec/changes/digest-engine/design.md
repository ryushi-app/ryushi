## Context

The digest engine transforms raw articles from FreshRSS into AI-generated summaries. It sits between the FreshRSS fetcher (which provides Article objects) and the output layer (which serves digests via RSS/API). The engine must handle variable article counts, respect model context limits, and gracefully handle AI backend failures.

## Goals / Non-Goals

**Goals:**
- Provide a clean async API for generating digests from article lists
- Support any OpenAI-compatible backend via LiteLLM
- Handle transient failures with automatic retries
- Allow customizable prompts and model parameters
- Return structured Digest objects with source attribution

**Non-Goals:**
- Caching digests (handled by storage layer)
- Scheduling digest generation (handled by scheduler)
- User-facing output formatting (handled by feed generator)
- Supporting non-LLM summarization methods

## Decisions

**1. LiteLLM as the AI abstraction layer**
- Use LiteLLM for all AI calls to enable model switching without code changes
- Rationale: Supports 100+ models, handles auth/retries, aligns with existing dependency
- Alternative considered: Direct OpenAI SDK (rejected - locks us to OpenAI)

**2. Tenacity for retry logic**
- Use tenacity library for exponential backoff on transient errors (429, 503, 5xx)
- Rationale: Battle-tested, composable, works well with async
- Alternative considered: Manual retry loops (rejected - error-prone, verbose)

**3. Pydantic for Digest model**
- Define Digest as a Pydantic BaseModel for validation and serialization
- Rationale: Consistent with Article model, built-in JSON serialization
- Alternative considered: Dataclass (rejected - no built-in validation)

**4. Prompt template with Jinja2-style placeholders**
- Use simple string formatting for prompt templates with {variable} placeholders
- Rationale: Simple, no new dependencies, sufficient for current needs
- Alternative considered: Full Jinja2 (rejected - overkill for this use case)

**5. Module structure: `ryushi/digest/`**
- `engine.py`: DigestEngine class with generate() method
- `models.py`: Digest and DigestConfig Pydantic models
- `prompts.py`: Default prompt templates and builder
- `exceptions.py`: DigestError and related exceptions
- Rationale: Clean separation of concerns, easy to test

**6. Context window management**
- Truncate article list if total prompt exceeds 80% of model context
- Include article count in prompt so AI knows if content was truncated
- Rationale: Prevents API errors, ensures consistent output quality

## Risks / Trade-offs

**[Risk] Model output format inconsistency**
→ Mitigation: Use structured prompts with clear format instructions; validate output contains expected sections

**[Risk] High latency for large article sets**
→ Mitigation: Enforce 60s timeout; truncate articles to fit context window; document expected latency

**[Risk] API costs for frequent digest generation**
→ Mitigation: Configurable model selection; default to efficient models; caller controls generation frequency

**[Trade-off] String formatting vs Jinja2 for templates**
→ Chosen simple formatting for fewer dependencies; limits template complexity but sufficient for digest prompts

## Migration Plan

1. Add litellm and tenacity to project dependencies
2. Implement Digest model and exceptions
3. Implement DigestEngine with prompt building
4. Add retry logic with tenacity decorators
5. Write unit tests with mocked LiteLLM responses
6. Integration test with real AI backend (staging)

## Open Questions

- Should we support streaming responses for real-time digest preview?
- What is the optimal default temperature for digest generation?
- Should truncated article lists prioritize recent articles or distribute across feeds?
