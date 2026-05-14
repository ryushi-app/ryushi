## 1. Project Setup

- [x] 1.1 Create `ryushi/scheduler/` directory structure with `__init__.py`
- [x] 1.2 Create `ryushi/scheduler/exceptions.py` with SchedulerError classes
- [x] 1.3 Add croniter to project dependencies (for overdue detection)

## 2. Data Models

- [x] 2.1 Create `ryushi/scheduler/models.py` with JobRun Pydantic model
- [x] 2.2 Create JobStatus model for status endpoint
- [x] 2.3 Create ScheduleConfig model for config.yaml parsing
- [x] 2.4 Add validation tests for all scheduler models

## 3. Configuration

- [x] 3.1 Create `ryushi/scheduler/config.py` for loading config.yaml
- [x] 3.2 Implement category schedule parsing with validation
- [x] 3.3 Handle missing/invalid cron expressions gracefully
- [x] 3.4 Add unit tests for configuration loading

## 4. Job Store

- [x] 4.1 Create `ryushi/scheduler/store.py` with JobStore class
- [x] 4.2 Implement SQLite schema for job_runs table
- [x] 4.3 Implement `create_run(category_slug)` returning new JobRun with status "running"
- [x] 4.4 Implement `complete_run(job_id, status, article_count, error)` to finalize a run
- [x] 4.5 Implement `get_last_run(category_slug)` for overdue detection
- [x] 4.6 Implement `get_history(category_slug, limit)` for history endpoint
- [x] 4.7 Implement 100-run retention per category
- [x] 4.8 Add unit tests for job store

## 5. Job Executor

- [x] 5.1 Create `ryushi/scheduler/executor.py` with JobExecutor class
- [x] 5.2 Implement `execute_job(category_slug)` pipeline: fetch → digest → feed
- [x] 5.3 Add error handling with full traceback logging
- [x] 5.4 Integrate with JobStore for run persistence
- [x] 5.5 Handle "no articles" case gracefully
- [x] 5.6 Add unit tests for job executor (with mocked dependencies)

## 6. Scheduler

- [x] 6.1 Create `ryushi/scheduler/scheduler.py` with DigestScheduler class
- [x] 6.2 Implement APScheduler AsyncIOScheduler setup
- [x] 6.3 Implement `start()` to register all configured jobs
- [x] 6.4 Implement `stop()` for graceful shutdown
- [x] 6.5 Implement `trigger_job(category_slug)` for manual triggering
- [x] 6.6 Implement `get_job_status(category_slug)` returning JobStatus
- [x] 6.7 Implement `list_jobs()` returning all job statuses
- [x] 6.8 Implement overdue job detection on startup
- [x] 6.9 Add unit tests for scheduler

## 7. HTTP API

- [x] 7.1 Create `ryushi/scheduler/api.py` with FastAPI router
- [x] 7.2 Implement POST `/jobs/{category_slug}/run` endpoint
- [x] 7.3 Implement GET `/jobs/{category_slug}/status` endpoint
- [x] 7.4 Implement GET `/jobs` endpoint (list all)
- [x] 7.5 Implement GET `/jobs/{category_slug}/history` endpoint
- [x] 7.6 Handle 404 for unknown categories
- [x] 7.7 Handle 409 for job already running
- [x] 7.8 Add integration tests for HTTP endpoints

## 8. Integration

- [x] 8.1 Update `ryushi/scheduler/__init__.py` to export public API
- [x] 8.2 Create sample config.yaml with example schedules
- [x] 8.3 Integrate scheduler with main application startup

## 9. Documentation and Quality

- [x] 9.1 Add docstrings to all public methods and classes
- [x] 9.2 Run linting (ruff) on the new module
- [x] 9.3 Ensure all tests pass
