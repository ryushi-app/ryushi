## 1. Project Setup

- [x] 1.1 Create `ryushi/feeds/` directory structure with `__init__.py`
- [x] 1.2 Create `ryushi/feeds/exceptions.py` with FeedError class
- [x] 1.3 Add feedgen, fastapi, uvicorn, aiosqlite, markdown-it-py to project dependencies

## 2. Data Models

- [x] 2.1 Create `ryushi/feeds/models.py` with FeedEntry Pydantic model
- [x] 2.2 Create FeedMeta and FeedIndex models for discovery endpoint
- [x] 2.3 Add validation tests for all feed models

## 3. Feed Generation

- [x] 3.1 Create `ryushi/feeds/generator.py` with FeedGenerator class
- [x] 3.2 Implement `generate_slug(category_name)` function for URL-safe slugs
- [x] 3.3 Implement `digest_to_entry(digest)` to convert Digest to FeedEntry
- [x] 3.4 Implement markdown-to-HTML rendering for digest summaries
- [x] 3.5 Implement `generate_feed(entries, category_name)` returning Atom XML
- [x] 3.6 Ensure generated feed is valid Atom 1.0 with required elements
- [x] 3.7 Add unit tests for feed generation

## 4. Feed Storage

- [x] 4.1 Create `ryushi/feeds/store.py` with FeedStore class
- [x] 4.2 Implement SQLite schema for feed_entries table
- [x] 4.3 Implement `add_entry(entry)` with 30-entry retention per category
- [x] 4.4 Implement `get_entries(category_slug)` returning entries newest-first
- [x] 4.5 Implement `list_categories()` returning FeedMeta for all categories
- [x] 4.6 Add database initialization and migration handling
- [x] 4.7 Add unit tests for feed storage with retention logic

## 5. HTTP Server

- [x] 5.1 Create `ryushi/feeds/server.py` with FastAPI app
- [x] 5.2 Implement GET `/feeds/{category_slug}/atom.xml` endpoint
- [x] 5.3 Implement GET `/feeds` discovery endpoint returning JSON
- [x] 5.4 Implement GET `/health` endpoint with status, feeds count, last_run
- [x] 5.5 Handle 404 for unknown categories with helpful message
- [x] 5.6 Set correct Content-Type headers (application/atom+xml, application/json)
- [x] 5.7 Add integration tests for HTTP endpoints

## 6. API Exports

- [x] 6.1 Update `ryushi/feeds/__init__.py` to export FeedGenerator, FeedStore, FeedEntry, FeedError
- [x] 6.2 Create entry point for running the feed server (uvicorn)

## 7. Documentation

- [x] 7.1 Add docstrings to all public methods and classes
- [x] 7.2 Document configuration options (database path, server port)
- [x] 7.3 Document deployment pattern (running alongside scheduler)

## 8. Quality and Verification

- [x] 8.1 Run type checking (mypy) on the new module
- [x] 8.2 Run linting (ruff) on the new module
- [x] 8.3 Ensure all tests pass
- [x] 8.4 Verify feed is parseable by a feed reader
