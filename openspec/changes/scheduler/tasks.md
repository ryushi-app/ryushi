## 1. Project Setup

- [ ] 1.1 Create `ryushi/scheduler/` directory structure with `__init__.py`
- [ ] 1.2 Create `ryushi/scheduler/exceptions.py` with SchedulerError classes
- [ ] 1.3 Add croniter to project dependencies (for overdue detection)

## 2. Data Models

- [ ] 2.1 Create `ryushi/scheduler/models.py` with JobRun Pydantic model
- [ ] 2.2 Create JobStatus model for status endpoint
- [ ] 2.3 Create ScheduleConfig model for config.yaml parsing
- [ ] 2.4 Add validation tests for all scheduler models

## 3. Configuration

- [ ] 3.1 Create `ryushi/scheduler/config.py` for loading config.yaml
- [ ] 3.2 Implement category schedule parsing with validation
- [ ] 3.3 Handle missing/invalid cron expressions gracefully
- [ ] 3.4 Add unit tests for configuration loading

## 4. Job Store

- [ ] 4.1 Create `ryushi/scheduler/store.py` with JobStore class
- [ ] 4.2 Implement SQLite schema for job_runs table
- [ ] 4.3 Implement `create_run(category_slug)` returning new JobRun with status "running"
- [ ] 4.4 Implement `complete_run(job_id, status, article_count, error)` to finalize a run
- [ ] 4.5 Implement `get_last_run(category_slug)` for overdue detection
- [ ] 4.6 Implement `get_history(category_slug, limit)` for history endpoint
- [ ] 4.7 Implement 100-run retention per category
- [ ] 4.8 Add unit tests for job store

## 5. Job Executor

- [ ] 5.1 Create `ryushi/scheduler/executor.py` with JobExecutor class
- [ ] 5.2 Implement `execute_job(category_slug)` pipeline: fetch → digest → feed
- [ ] 5.3 Add error handling with full traceback logging
- [ ] 5.4 Integrate with JobStore for run persistence
- [ ] 5.5 Handle "no articles" case gracefully
- [ ] 5.6 Add unit tests for job executor (with mocked dependencies)

## 6. Scheduler

- [ ] 6.1 Create `ryushi/scheduler/scheduler.py` with DigestScheduler class
- [ ] 6.2 Implement APScheduler AsyncIOScheduler setup
- [ ] 6.3 Implement `start()` to register all configured jobs
- [ ] 6.4 Implement `stop()` for graceful shutdown
- [ ] 6.5 Implement `trigger_job(category_slug)` for manual triggering
- [ ] 6.6 Implement `get_job_status(category_slug)` returning JobStatus
- [ ] 6.7 Implement `list_jobs()` returning all job statuses
- [ ] 6.8 Implement overdue job detection on startup
- [ ] 6.9 Add unit tests for scheduler

## 7. HTTP API

- [ ] 7.1 Create `ryushi/scheduler/api.py` with FastAPI router
- [ ] 7.2 Implement POST `/jobs/{category_slug}/run` endpoint
- [ ] 7.3 Implement GET `/jobs/{category_slug}/status` endpoint
- [ ] 7.4 Implement GET `/jobs` endpoint (list all)
- [ ] 7.5 Implement GET `/jobs/{category_slug}/history` endpoint
- [ ] 7.6 Handle 404 for unknown categories
- [ ] 7.7 Handle 409 for job already running
- [ ] 7.8 Add integration tests for HTTP endpoints

## 8. Integration

- [ ] 8.1 Update `ryushi/scheduler/__init__.py` to export public API
- [ ] 8.2 Create sample config.yaml with example schedules
- [ ] 8.3 Integrate scheduler with main application startup

## 9. Documentation and Quality

- [ ] 9.1 Add docstrings to all public methods and classes
- [ ] 9.2 Run type checking (mypy) on the new module
- [ ] 9.3 Run linting (ruff) on the new module
- [ ] 9.4 Ensure all tests pass
