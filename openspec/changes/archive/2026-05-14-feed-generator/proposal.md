## Why

The digest engine generates AI-powered summaries of articles, but there's no way to consume these digests externally. Users need to access their digests through standard RSS/Atom feeds so they can subscribe via FreshRSS or any other feed reader, completing the core Ryushi workflow.

## What Changes

- Add Atom 1.0 feed generation from Digest objects
- Persist feeds to SQLite with rolling 30-digest window per category
- Serve feeds over HTTP with proper Content-Type headers
- Provide feed discovery endpoint listing all available feeds
- Add health check endpoint for monitoring

## Capabilities

### New Capabilities
- `feed-generation`: Atom 1.0 feed generation from Digest objects with proper entry structure
- `feed-storage`: SQLite persistence of feed entries with retention policy
- `feed-serving`: HTTP endpoints for serving feeds, discovery, and health checks

### Modified Capabilities

## Impact

- New `ryushi/feeds/` module with generator, store, and server components
- New dependencies: feedgen, fastapi, uvicorn, markdown-it-py
- New database tables for feed entries
- HTTP server running on configurable port
