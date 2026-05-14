## Context

Ryushi currently has three independent components: FreshRSSClient for fetching articles, DigestEngine for AI-powered summarization, and FeedStore/FeedGenerator for persisting and serving Atom feeds. These components work but require manual invocation. The scheduler will orchestrate these into an automated pipeline that runs on configurable cron schedules per category.

The existing codebase uses:
- APScheduler (already in dependencies) for cron scheduling
- FastAPI for HTTP endpoints
- SQLite via aiosqlite for persistence
- Pydantic for configuration

## Goals / Non-Goals

**Goals:**
- Automate digest generation with per-category cron schedules
- Provide job history and status tracking
- Enable manual job triggering via API
- Ensure job failures are isolated and don't cascade
- Detect and run overdue jobs on startup

**Non-Goals:**
- Distributed scheduling (single-instance only for now)
- Job queuing or retry policies (immediate execution only)
- Real-time job progress streaming
- Job cancellation mid-execution

## Decisions

### 1. Module Structure: New `ryushi/scheduler/` Package

**Decision**: Create a new `ryushi/scheduler/` package with separate modules for scheduling, execution, storage, and API.

**Rationale**: Mirrors the `ryushi/feeds/` and `ryushi/digest/` package structure. Separates concerns:
- `scheduler.py`: APScheduler wrapper for cron job management
- `executor.py`: Job execution pipeline (fetch → digest → feed)
- `store.py`: SQLite persistence for job run history
- `api.py`: FastAPI router for manual triggers and status
- `models.py`: JobRun, JobStatus, ScheduleConfig Pydantic models

**Alternatives considered**:
- Single `scheduler.py` file: Would become unwieldy with persistence and API code
- Integrate into existing `main.py`: Violates separation of concerns

### 2. Configuration: YAML-Based Per-Category Schedules

**Decision**: Read schedules from `config.yaml` with structure:
```yaml
categories:
  software-engineering:
    schedule: "0 6 * * *"
  technology:
    schedule: "0 8 * * *"
```

**Rationale**: YAML is already used in the project (pyyaml dependency exists). Per-category schedules allow different frequencies for different content types. Standard cron syntax is well-understood.

**Alternatives considered**:
- Environment variables: Not practical for multiple categories
- Database-stored schedules: Adds complexity, config file is simpler for this use case

### 3. Scheduler: APScheduler with AsyncIOScheduler

**Decision**: Use APScheduler's AsyncIOScheduler with CronTrigger for each category.

**Rationale**: APScheduler is already a dependency, well-tested, supports cron expressions natively. AsyncIOScheduler integrates with asyncio event loop used by FastAPI.

**Alternatives considered**:
- Celery Beat: Overkill, requires Redis/RabbitMQ
- Custom cron implementation: Reinventing the wheel

### 4. Job Execution: Sequential Pipeline with Error Boundaries

**Decision**: Execute jobs as: Fetch Articles → Generate Digest → Store Feed Entry, with try/except around entire pipeline.

**Rationale**: Simple, deterministic flow. Error boundary ensures one job's failure doesn't affect others. Each step's result feeds the next.

**Alternatives considered**:
- Parallel execution of categories: APScheduler handles this naturally
- Step-level error handling with partial commits: Adds complexity, all-or-nothing is simpler

### 5. Job History: SQLite Table with Recent Retention

**Decision**: Store job runs in `job_runs` SQLite table with 100-run retention per category.

**Rationale**: Consistent with FeedStore approach. SQLite is already used. 100 runs (~3 months of daily jobs) is enough for debugging without unbounded growth.

**Alternatives considered**:
- Log-only (no persistence): Loses history on restart
- Unlimited retention: Requires periodic cleanup

### 6. Overdue Detection: Compare Last Run to Schedule

**Decision**: On startup, for each category, compare last successful run time to schedule. If overdue by more than one interval, run immediately.

**Rationale**: Ensures no missed digests after downtime. Uses croniter to calculate expected run times.

**Alternatives considered**:
- Always run on startup: Wasteful if just restarted
- Never catch up: Users miss content after downtime

## Risks / Trade-offs

**[Risk] Long-running jobs block scheduler thread** → APScheduler's `max_instances=1` per job prevents overlap. Jobs run in executor, not scheduler thread. Add timeout to prevent indefinite hangs.

**[Risk] Config file changes require restart** → Acceptable for initial implementation. Future: add config reload endpoint or file watcher.

**[Risk] SQLite contention between scheduler and feed server** → Both use separate connections with WAL mode. Low write frequency makes this unlikely to be an issue.

**[Trade-off] Single instance only** → Simplifies implementation significantly. Distributed scheduling can be added later if needed.

**[Trade-off] No job cancellation** → Jobs are typically short (< 1 minute). Cancellation adds significant complexity for little benefit.
