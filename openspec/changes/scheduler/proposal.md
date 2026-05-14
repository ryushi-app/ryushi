## Why

Ryushi can fetch articles, generate digests, and serve feeds, but these operations must be triggered manually. Users need automatic, scheduled digest generation per category based on configurable cron schedules, completing the autonomous operation loop.

## What Changes

- Add cron-based job scheduling using APScheduler
- Create job execution pipeline (Fetcher → Digest Engine → Feed Generator)
- Persist job run history to SQLite for monitoring
- Add manual trigger endpoint for on-demand job execution
- Implement overdue job detection on startup
- Add error isolation so failures in one category don't affect others

## Capabilities

### New Capabilities
- `job-scheduling`: Cron-based scheduling of digest generation jobs per category, reading schedules from config.yaml
- `job-execution`: Pipeline execution connecting Fetcher, Digest Engine, and Feed Generator with logging and persistence
- `job-api`: HTTP endpoints for manual triggering and job status retrieval

### Modified Capabilities

## Impact

- New `ryushi/scheduler/` module with scheduler, executor, store, and API components
- New SQLite table for job run history
- New configuration schema in config.yaml for per-category schedules
- Integration with existing FreshRSSClient, DigestEngine, and FeedStore
- New HTTP endpoints under `/jobs/`
