# Feed Generator

## Overview

Converts Digest objects into valid Atom feeds served over HTTP,
subscribable by FreshRSS or any feed reader.

## Requirements

### R1 — Atom Feed Generation
- MUST generate valid Atom 1.0 feeds (RFC 4287)
- MUST create one feed per category
- MUST include: title, id, updated, author, entry per digest
- Each entry MUST include: title, id, published, updated, content, links to sources

### R2 — Feed Storage
- MUST persist feeds to SQLite via `store.py`
- MUST keep last 30 digests per category
- MUST update feed on each new digest

### R3 — HTTP Serving
- MUST serve feeds at `/feeds/{category_slug}/atom.xml`
- MUST return `Content-Type: application/atom+xml`
- MUST serve `/health` endpoint returning `{"status": "ok"}`
- MUST serve `/feeds` index listing all available feeds

### R4 — Feed Discovery
- `/feeds` MUST return JSON list of `{category, url, last_updated, item_count}`

## Scenarios

### Scenario 1 — Feed available in FreshRSS
GIVEN a digest was generated for "Software Engineering"  
WHEN FreshRSS polls `/feeds/software-engineering/atom.xml`  
THEN returns valid Atom XML with Content-Type `application/atom+xml`  
AND feed contains at least 1 entry

### Scenario 2 — New digest appended
GIVEN an existing feed with 5 entries  
WHEN a new digest is generated  
THEN feed contains 6 entries  
AND newest entry appears first

### Scenario 3 — Unknown category
GIVEN no digest exists for "Cooking"  
WHEN GET `/feeds/cooking/atom.xml` is requested  
THEN returns 404 with helpful error message

### Scenario 4 — Health check
WHEN GET `/health` is called  
THEN returns 200 with `{"status": "ok", "feeds": 3, "last_run": "..."}`

## Data Models

```python
class FeedEntry(BaseModel):
    id: str
    category_slug: str
    title: str
    published: datetime
    content_html: str           # markdown rendered to HTML
    source_urls: list[str]

class FeedIndex(BaseModel):
    feeds: list[FeedMeta]

class FeedMeta(BaseModel):
    category: str
    slug: str
    url: str
    last_updated: datetime
    item_count: int
```

## Dependencies
- feedgen — Atom feed generation
- fastapi — HTTP server
- uvicorn — ASGI server
- markdown-it-py — markdown to HTML
