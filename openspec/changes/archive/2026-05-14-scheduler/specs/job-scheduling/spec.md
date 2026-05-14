## ADDED Requirements

### Requirement: Read schedules from configuration
The system SHALL read per-category cron schedules from config.yaml.

#### Scenario: Valid configuration loaded
- **WHEN** application starts with config.yaml containing category schedules
- **THEN** scheduler creates a job for each configured category
- **THEN** each job uses the specified cron expression

#### Scenario: Missing schedule defaults to disabled
- **WHEN** a category exists in FreshRSS but has no schedule in config.yaml
- **THEN** no scheduled job is created for that category

### Requirement: Support standard cron expressions
The system SHALL accept standard 5-field cron expressions for schedules.

#### Scenario: Daily schedule at specific time
- **WHEN** schedule is "0 6 * * *"
- **THEN** job runs at 06:00 every day

#### Scenario: Weekly schedule
- **WHEN** schedule is "0 8 * * 1"
- **THEN** job runs at 08:00 every Monday

#### Scenario: Invalid cron expression
- **WHEN** schedule contains invalid cron syntax
- **THEN** application logs error and skips that category
- **THEN** other valid schedules still start

### Requirement: Start jobs on application startup
The system SHALL register and start all configured scheduled jobs when the application starts.

#### Scenario: Jobs registered on startup
- **WHEN** application starts
- **THEN** scheduler is running
- **THEN** all configured category jobs are scheduled

#### Scenario: Scheduler survives individual job failures
- **WHEN** one category job fails during execution
- **THEN** scheduler continues running
- **THEN** other scheduled jobs execute normally

### Requirement: Detect and run overdue jobs
The system SHALL check for overdue jobs on startup and run them immediately.

#### Scenario: Overdue job runs immediately
- **GIVEN** last successful run for "technology" was 2 days ago
- **AND** schedule is daily at 06:00
- **WHEN** application starts
- **THEN** job for "technology" runs immediately
- **THEN** normal schedule resumes after immediate run

#### Scenario: Recent job does not trigger
- **GIVEN** last successful run for "technology" was 2 hours ago
- **AND** schedule is daily at 06:00
- **WHEN** application starts
- **THEN** job waits for next scheduled time

#### Scenario: No previous run triggers immediate execution
- **GIVEN** no job history exists for "technology"
- **WHEN** application starts
- **THEN** job for "technology" runs immediately
