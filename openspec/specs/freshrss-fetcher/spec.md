# FreshRSS Fetcher

## Overview

Authenticates with FreshRSS via Google Reader API and fetches unread articles
grouped by category.

## Requirements

### R1 — Authentication
- MUST support token-based auth via Google Reader API `/accounts/ClientLogin`
- MUST read credentials from environment variables
- MUST refresh token on 401 responses

### R2 — Category Listing
- MUST return all feed categories from FreshRSS
- MUST map category IDs to human-readable names

### R3 — Unread Item Fetching
- MUST fetch unread items for a given category ID
- MUST respect a configurable `max_articles` limit
- MUST return: title, url, author, published_at, teaser (first 500 chars)
- SHOULD handle pagination for large feeds

### R4 — Error Handling
- MUST raise typed exceptions: `AuthError`, `FetchError`, `RateLimitError`
- MUST log failed requests with status code and URL

## Scenarios

### Scenario 1 — Successful fetch
GIVEN valid credentials in environment  
WHEN `get_unread_items(category_id="software-engineering", max=50)` is called  
THEN returns list of `Article` objects with title, url, published_at  
AND marks nothing as read (read-only operation)

### Scenario 2 — Invalid credentials
GIVEN invalid password in environment  
WHEN any API call is made  
THEN raises `AuthError` with message "FreshRSS authentication failed"

### Scenario 3 — Empty category
GIVEN valid credentials  
WHEN category has no unread items  
THEN returns empty list without error

### Scenario 4 — Max articles limit
GIVEN a category with 200 unread articles  
WHEN `max_articles=50` is configured  
THEN returns exactly 50 most recent articles

## Data Models

```python
class Article(BaseModel):
    id: str
    title: str
    url: str
    author: str | None
    published_at: datetime
    teaser: str | None          # first 500 chars of content
    category_id: str
    feed_title: str
```

## Dependencies
- httpx — async HTTP client
- pydantic — data validation
