## ADDED Requirements

### Requirement: Manual job trigger endpoint
The system SHALL allow manual triggering of jobs via POST /jobs/{category_slug}/run.

#### Scenario: Trigger job successfully
- **WHEN** POST /jobs/software-engineering/run is called
- **THEN** returns 200 OK
- **THEN** response body contains {"status": "started", "job_id": "..."}
- **THEN** job runs immediately regardless of schedule

#### Scenario: Trigger unknown category
- **WHEN** POST /jobs/nonexistent-category/run is called
- **THEN** returns 404 Not Found
- **THEN** response body contains helpful error message

#### Scenario: Trigger while job running
- **WHEN** POST /jobs/technology/run is called
- **AND** job for "technology" is already running
- **THEN** returns 409 Conflict
- **THEN** response body indicates job already in progress

### Requirement: Job status endpoint
The system SHALL provide job status via GET /jobs/{category_slug}/status.

#### Scenario: Get status for active category
- **WHEN** GET /jobs/software-engineering/status is called
- **THEN** returns 200 OK
- **THEN** response contains category_slug
- **THEN** response contains last_run timestamp (or null)
- **THEN** response contains next_run timestamp
- **THEN** response contains current status

#### Scenario: Get status for unknown category
- **WHEN** GET /jobs/nonexistent/status is called
- **THEN** returns 404 Not Found

### Requirement: List all jobs endpoint
The system SHALL provide a list of all scheduled jobs via GET /jobs.

#### Scenario: List all scheduled jobs
- **WHEN** GET /jobs is called
- **THEN** returns 200 OK
- **THEN** response contains array of job status objects
- **THEN** each object has category_slug, last_run, next_run, status

#### Scenario: No jobs configured
- **WHEN** GET /jobs is called
- **AND** no categories are configured with schedules
- **THEN** returns 200 OK
- **THEN** response contains empty array

### Requirement: Job history endpoint
The system SHALL provide job run history via GET /jobs/{category_slug}/history.

#### Scenario: Get history for category
- **WHEN** GET /jobs/software-engineering/history is called
- **THEN** returns 200 OK
- **THEN** response contains array of JobRun objects
- **THEN** runs are ordered by started_at descending (newest first)

#### Scenario: Get history with limit
- **WHEN** GET /jobs/software-engineering/history?limit=10 is called
- **THEN** returns at most 10 job runs

#### Scenario: Get history for category with no runs
- **WHEN** GET /jobs/new-category/history is called
- **AND** category has no job history
- **THEN** returns 200 OK
- **THEN** response contains empty array
