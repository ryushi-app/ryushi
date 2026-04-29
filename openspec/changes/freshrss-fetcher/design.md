## Context

The FreshRSS integration is a new feature to connect Ryushi with FreshRSS servers. FreshRSS exposes a Google Reader API-compatible interface for authentication and feed management. The integration needs to handle authentication state management, category discovery, and efficient article fetching with pagination support.

## Goals / Non-Goals

**Goals:**
- Provide reliable authentication with automatic token refresh on 401 responses
- Expose a clean async API for fetching categories and unread articles
- Return rich Article objects with title, URL, author, publication date, and content teaser
- Support configurable limits on articles per category to manage data volume
- Handle errors gracefully with typed exceptions for different failure modes

**Non-Goals:**
- Marking articles as read (read-only integration)
- Building a UI layer (this is backend integration only)
- Supporting feed subscriptions or category management
- Caching responses (assume stateless fetches)

## Decisions

**1. Async-first implementation with httpx**
- Use httpx for async HTTP requests to support concurrent category/article fetching
- Rationale: Non-blocking I/O aligns with Ryushi's async architecture and enables efficient bulk fetching of multiple categories
- Alternative considered: Synchronous requests with requests library (rejected - less efficient, harder to parallelize)

**2. Pydantic models for data validation**
- Define Article and Category as Pydantic BaseModel subclasses
- Rationale: Built-in validation, serialization, and IDE support; aligns with existing Ryushi patterns
- Alternative considered: Dataclasses (rejected - no built-in validation)

**3. Stateful authentication with credential storage**
- Store FreshRSS URL, username, password in environment variables
- Implement token refresh logic with 401 handling
- Rationale: Credentials are server-specific and rarely change; environment variables are secure and follow Django convention
- Alternative considered: Per-request authentication (rejected - inefficient, requires credentials with each call)

**4. Pagination via `offset` and `limit` parameters**
- FreshRSS API supports `offset` and `limit` for article endpoints
- Implement client-side pagination logic; return only requested articles up to `max_articles` limit
- Rationale: Allows flexibility for different use cases (small vs. large feeds)
- Alternative considered: Return all articles (rejected - unbounded memory usage, slow for large feeds)

**5. Module structure: `src/integrations/freshrss/`**
- `client.py`: Core FreshRSSClient class with auth and fetch methods
- `models.py`: Pydantic Article and Category models
- `exceptions.py`: AuthError, FetchError, RateLimitError classes
- `__init__.py`: Public API exports
- Rationale: Clean separation of concerns, easy to test and extend
- Alternative considered: Single file (rejected - reduced maintainability at scale)

## Risks / Trade-offs

**[Risk] Token expiration during long-running operations**
→ Mitigation: Implement token refresh before each API call; handle 401 responses transparently by re-authenticating and retrying

**[Risk] Large feeds causing performance issues**
→ Mitigation: Enforce `max_articles` limit; implement pagination to avoid loading entire feeds into memory

**[Risk] Rate limiting from FreshRSS server**
→ Mitigation: Raise RateLimitError on 429 responses; let caller implement backoff strategy

**[Trade-off] Environment variables for credentials vs. config file**
→ Chosen environment variables for better security in containerized environments; less flexible for multiple FreshRSS instances

## Migration Plan

1. Create `src/integrations/freshrss/` module structure
2. Implement core authentication and API client
3. Add category and article fetching logic
4. Write unit tests and integration tests
5. Deploy as internal API (no user-facing changes initially)
6. Integrate into feed service after validation

## Open Questions

- Should we cache authentication tokens in memory or on disk?
- How should we handle FreshRSS instances with self-signed certificates?
- What timeout values should we use for HTTP requests?
