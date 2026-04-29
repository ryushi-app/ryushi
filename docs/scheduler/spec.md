# Scheduler

## Overview

Orchestrates digest generation jobs based on per-category cron schedules
defined in config.yaml.

## Requirements

### R1 — Schedule Configuration
- MUST read schedules from `config.yaml` per category
- MUST support standard cron expressions
- MUST start all jobs on application startup
- MUST allow manual trigger via `POST /jobs/{category_slug}/run`

### R2 — Job Execution
- MUST run Fetcher → Digest Engine → Feed Generator as a pipeline
- MUST log start, end, duration, and article count per job run
- MUST persist job run history to SQLite

### R3 — Error Isolation
- A failure in one category job MUST NOT affect other jobs
- MUST send error to logs with full traceback
- MUST update job status to `failed` in store

### R4 — Startup Behavior
- On startup MUST check if a job is overdue (last run > schedule interval)
- If overdue MUST run immediately, then resume normal schedule

## Scenarios

### Scenario 1 — Scheduled run
GIVEN category "Software Engineering" with schedule `0 6 * * *`  
WHEN clock reaches 06:00  
THEN job fetches articles, generates digest, updates feed  
AND logs `"Digest complete: 30 articles, category=Software Engineering"`

### Scenario 2 — Manual trigger
GIVEN the server is running  
WHEN `POST /jobs/software-engineering/run` is called  
THEN job runs immediately regardless of schedule  
AND returns `{"status": "started", "job_id": "..."}`

### Scenario 3 — Job failure
GIVEN AI backend is unreachable  
WHEN digest job runs  
THEN job status is set to `failed` in store  
AND next scheduled run proceeds normally

### Scenario 4 — Overdue job on startup
GIVEN last run was 2 days ago  
AND schedule is daily  
WHEN application starts  
THEN job runs immediately on startup

## Data Models

```python
class JobRun(BaseModel):
    id: str
    category_slug: str
    started_at: datetime
    finished_at: datetime | None
    status: Literal["running", "success", "failed"]
    article_count: int | None
    error: str | None

class JobStatus(BaseModel):
    category_slug: str
    last_run: datetime | None
    next_run: datetime
    status: str
```

## Dependencies
- apscheduler — cron scheduling
- fastapi — manual trigger endpoint