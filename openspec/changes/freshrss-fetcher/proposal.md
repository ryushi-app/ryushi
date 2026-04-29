## Why

Ryushi needs a way to fetch and aggregate unread articles from FreshRSS servers. This integration enables users to browse their RSS feeds directly within the application, supporting the core feature of content discovery and reading.

## What Changes

- Add FreshRSS authentication module supporting Google Reader API token-based auth
- Implement category listing and discovery from FreshRSS
- Build unread article fetching with filtering and pagination support
- Add typed exception handling for auth, fetch, and rate limit errors
- Define Article data model matching FreshRSS feed structure

## Capabilities

### New Capabilities
- `freshrss-auth`: Token-based authentication with FreshRSS via Google Reader API, including credential management and token refresh on 401 responses
- `freshrss-categories`: Fetch and map FreshRSS feed categories to human-readable names
- `freshrss-articles`: Fetch unread articles by category with title, URL, author, publication date, and content teaser (first 500 chars)

### Modified Capabilities
<!-- No existing capabilities require requirement changes -->

## Impact

- New module: `src/integrations/freshrss/` for FreshRSS integration logic
- Dependencies: httpx (async HTTP), pydantic (data validation)
- Environment variables required: FreshRSS credentials (URL, username, password)
- API surface: Async functions for auth, category listing, and article fetching
