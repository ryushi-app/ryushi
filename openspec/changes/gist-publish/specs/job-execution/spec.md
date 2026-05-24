## ADDED Requirements

### Requirement: Publish to Gist after feed storage
The system SHALL publish the generated Atom feed to a GitHub Gist after successfully storing the feed entry, if Gist publishing is enabled for the category.

#### Scenario: Gist publishing enabled and successful
- **WHEN** digest generation succeeds
- **WHEN** feed entry is stored successfully
- **WHEN** category has gist_enabled=true and valid gist_id
- **THEN** the Atom feed XML is published to the specified Gist
- **THEN** the job completes with success status

#### Scenario: Gist publishing enabled but fails
- **WHEN** digest generation succeeds
- **WHEN** feed entry is stored successfully
- **WHEN** Gist publishing fails (network error, invalid token, etc.)
- **THEN** a warning is logged about Gist publish failure
- **THEN** the job still completes with success status
- **THEN** the local feed entry remains stored

#### Scenario: Gist publishing disabled
- **WHEN** digest generation succeeds
- **WHEN** category has gist_enabled=false or missing
- **THEN** no Gist publishing is attempted
- **THEN** the job completes normally

### Requirement: Generate Atom XML for Gist publishing
The system SHALL generate the Atom XML feed content using the FeedGenerator before publishing to Gist.

#### Scenario: Generate XML for single category
- **WHEN** publishing to Gist is triggered
- **THEN** the system generates Atom XML using FeedGenerator with the category's entries
- **THEN** the XML includes all feed metadata (title, icon, entries)

### Requirement: Pass Gist configuration to executor
The JobExecutor SHALL receive gist_enabled and gist_id from the scheduler along with other category configuration.

#### Scenario: Scheduler passes Gist config
- **WHEN** the scheduler triggers a job for a category
- **THEN** gist_enabled and gist_id are passed to execute_job()
- **THEN** the executor uses these values to determine if Gist publishing should occur
