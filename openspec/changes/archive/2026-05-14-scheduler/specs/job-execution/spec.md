## ADDED Requirements

### Requirement: Execute digest pipeline
The system SHALL run Fetcher → Digest Engine → Feed Generator as a sequential pipeline for each job.

#### Scenario: Successful pipeline execution
- **WHEN** job runs for category "software-engineering"
- **THEN** fetches unread articles from FreshRSS for that category
- **THEN** generates digest using DigestEngine
- **THEN** stores feed entry using FeedStore
- **THEN** job completes with status "success"

#### Scenario: No articles to process
- **WHEN** job runs and category has no unread articles
- **THEN** job completes with status "success"
- **THEN** article_count is 0
- **THEN** no digest or feed entry is created

### Requirement: Log job execution details
The system SHALL log start, end, duration, and article count for each job run.

#### Scenario: Job logging on success
- **WHEN** job completes successfully
- **THEN** log includes job start time
- **THEN** log includes job end time
- **THEN** log includes duration in seconds
- **THEN** log includes article count processed
- **THEN** log includes category name

#### Scenario: Job logging on failure
- **WHEN** job fails with an error
- **THEN** log includes full error traceback
- **THEN** log includes category name
- **THEN** log level is ERROR

### Requirement: Persist job run history
The system SHALL persist job run records to SQLite for each execution.

#### Scenario: Successful run persisted
- **WHEN** job completes successfully
- **THEN** JobRun record exists in database
- **THEN** record has status "success"
- **THEN** record has started_at and finished_at timestamps
- **THEN** record has article_count

#### Scenario: Failed run persisted
- **WHEN** job fails with an error
- **THEN** JobRun record exists in database
- **THEN** record has status "failed"
- **THEN** record has error message

#### Scenario: Running job persisted
- **WHEN** job starts execution
- **THEN** JobRun record exists with status "running"
- **THEN** finished_at is null

### Requirement: Isolate job failures
The system SHALL ensure a failure in one category job does not affect other jobs.

#### Scenario: Failure isolation between categories
- **GIVEN** jobs scheduled for "technology" and "science"
- **WHEN** "technology" job fails due to API error
- **THEN** "science" job runs at its scheduled time
- **THEN** scheduler continues operating normally

#### Scenario: Failure does not prevent next run
- **GIVEN** job for "technology" failed in last run
- **WHEN** next scheduled time arrives
- **THEN** job for "technology" runs again

### Requirement: Maintain job history retention
The system SHALL keep only the last 100 job runs per category.

#### Scenario: Old runs pruned
- **GIVEN** category has 100 job runs in history
- **WHEN** new job run completes
- **THEN** oldest run is removed
- **THEN** category has exactly 100 runs
