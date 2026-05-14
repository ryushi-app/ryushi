## ADDED Requirements

### Requirement: Serve feed at category endpoint
The system SHALL serve Atom feeds at `/feeds/{category_slug}/atom.xml`.

#### Scenario: Valid feed request
- **WHEN** GET `/feeds/software-engineering/atom.xml` is requested
- **THEN** returns 200 OK
- **THEN** Content-Type is `application/atom+xml`
- **THEN** body is valid Atom XML with entries for that category

#### Scenario: Unknown category returns 404
- **WHEN** GET `/feeds/nonexistent-category/atom.xml` is requested
- **THEN** returns 404 Not Found
- **THEN** body contains helpful error message

### Requirement: Serve feed discovery endpoint
The system SHALL serve a feed index at `/feeds` listing all available feeds.

#### Scenario: List all feeds
- **WHEN** GET `/feeds` is requested
- **THEN** returns 200 OK
- **THEN** Content-Type is `application/json`
- **THEN** body contains array of feed metadata objects
- **THEN** each object has category, slug, url, last_updated, item_count

#### Scenario: No feeds available
- **WHEN** GET `/feeds` is requested and no digests exist
- **THEN** returns 200 OK
- **THEN** body contains empty array

### Requirement: Serve health check endpoint
The system SHALL serve a health check at `/health` for monitoring.

#### Scenario: Healthy server
- **WHEN** GET `/health` is requested
- **THEN** returns 200 OK
- **THEN** body is JSON with status "ok"
- **THEN** body includes feeds count
- **THEN** body includes last_run timestamp if available

#### Scenario: Health check minimal dependency
- **WHEN** GET `/health` is requested
- **THEN** response completes within 1 second
- **THEN** does not require external services to be available

### Requirement: FreshRSS compatibility
The system SHALL produce feeds that FreshRSS can successfully subscribe to and poll.

#### Scenario: FreshRSS subscription
- **WHEN** FreshRSS adds feed URL `/feeds/software-engineering/atom.xml`
- **THEN** FreshRSS successfully parses the feed
- **THEN** FreshRSS displays entries with correct titles and content

#### Scenario: FreshRSS polling
- **WHEN** FreshRSS polls an existing feed after new digest is added
- **THEN** FreshRSS detects and displays the new entry
