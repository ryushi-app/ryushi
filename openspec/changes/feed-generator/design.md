## Context

Ryushi fetches articles from FreshRSS, generates AI-powered digests per category, but currently has no way to expose these digests back to users. The `ryushi/feeds.py` and `ryushi/store.py` files exist but are empty stubs. The digest engine already produces `Digest` objects with all necessary metadata (category_name, summary, source_urls, generated_at).

The goal is to complete the feedback loop: digests become subscribable Atom feeds that users can add back to FreshRSS or any other feed reader.

## Goals / Non-Goals

**Goals:**
- Generate valid Atom 1.0 feeds from Digest objects
- Persist feed entries to SQLite with 30-entry rolling window per category
- Serve feeds over HTTP with proper headers and discovery
- Provide health/monitoring endpoint

**Non-Goals:**
- RSS 2.0 format support (Atom only for now)
- Authentication/authorization on feed endpoints
- Feed customization (themes, templates)
- Real-time push notifications (polling only)

## Decisions

### 1. Module Structure: New `ryushi/feeds/` Package

**Decision**: Create a new `ryushi/feeds/` package with separate modules for generation, storage, and serving.

**Rationale**: Mirrors the `ryushi/digest/` package structure. Separates concerns clearly:
- `generator.py`: Atom XML generation from Digest objects
- `store.py`: SQLite persistence for feed entries
- `server.py`: FastAPI HTTP server
- `models.py`: FeedEntry, FeedMeta, FeedIndex Pydantic models

**Alternatives considered**:
- Single `feeds.py` file: Would become unwieldy with HTTP server code
- Extend existing `store.py`: Different concern, should stay separate

### 2. Feed Generation: feedgen Library

**Decision**: Use the `feedgen` library for Atom feed generation.

**Rationale**: Well-maintained, handles RFC 4287 compliance, provides clean API for adding entries. Avoids manual XML construction and escaping bugs.

**Alternatives considered**:
- lxml with manual construction: More error-prone, requires RFC knowledge
- Jinja2 templates: Less type-safe, escaping concerns

### 3. Storage: SQLite via aiosqlite

**Decision**: Store FeedEntry records in SQLite using aiosqlite for async access.

**Rationale**: Consistent with the existing project approach. SQLite is sufficient for expected volume (30 entries × number of categories). aiosqlite allows non-blocking database operations alongside async HTTP serving.

**Alternatives considered**:
- File-based storage (one XML per category): Harder to query, no transactional guarantees
- PostgreSQL: Overkill for this use case, adds deployment complexity

### 4. HTTP Server: FastAPI with uvicorn

**Decision**: Use FastAPI for the HTTP server, run via uvicorn.

**Rationale**: FastAPI provides automatic OpenAPI docs, good async support, and easy routing. Uvicorn is the standard ASGI server. Both are well-tested in production.

**Alternatives considered**:
- Flask: Sync-first, would need workarounds for async DB access
- aiohttp: Lower-level, more boilerplate for routing

### 5. Category Slug Generation

**Decision**: Generate URL-safe slugs from category names using simple lowercasing and hyphenation (e.g., "Software Engineering" → "software-engineering").

**Rationale**: Predictable, reversible mapping. Users can guess URLs from category names.

**Alternatives considered**:
- UUIDs in URLs: Not user-friendly
- Database-stored slugs: Extra complexity for little benefit

### 6. Markdown Rendering: markdown-it-py

**Decision**: Use markdown-it-py to render digest summaries to HTML for feed content.

**Rationale**: CommonMark compliant, fast, pure Python. The digest summary is markdown; Atom entries need HTML content.

**Alternatives considered**:
- mistune: Slightly faster but less CommonMark compliant
- markdown: Older API, more complex extension system

## Risks / Trade-offs

**[Risk] Feed XML generation on every request** → Cache generated XML in memory with TTL or regenerate only on new digest arrival. Start with regeneration on write (simpler).

**[Risk] Database growth with many categories** → 30-entry limit per category keeps this bounded. Add index on (category_slug, published DESC).

**[Risk] Server needs to run alongside scheduler** → Design as separate process; can share SQLite database file. Document deployment pattern.

**[Trade-off] Sync vs async store operations** → Using aiosqlite adds complexity but necessary for FastAPI async handlers. Worth it for non-blocking I/O.
