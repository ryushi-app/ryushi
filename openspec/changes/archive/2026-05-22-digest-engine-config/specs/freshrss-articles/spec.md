## ADDED Requirements

### Requirement: Mark articles as read
The system SHALL provide a method to mark a list of article IDs as read in FreshRSS using the Google Reader API `edit-tag` endpoint with the `user/-/state/com.google/read` tag.

#### Scenario: Mark single article as read
- **WHEN** `mark_as_read(article_ids=["123"])` is called with valid authentication
- **THEN** article with ID "123" is marked as read in FreshRSS

#### Scenario: Mark multiple articles as read
- **WHEN** `mark_as_read(article_ids=["123", "456", "789"])` is called
- **THEN** all three articles are marked as read in a single API call

#### Scenario: Empty article list
- **WHEN** `mark_as_read(article_ids=[])` is called with an empty list
- **THEN** no API call is made and method returns successfully

#### Scenario: Large batch of articles
- **WHEN** `mark_as_read()` is called with more than 50 article IDs
- **THEN** the request is batched into chunks of 50 IDs maximum

### Requirement: Mark-as-read error handling
The system SHALL handle errors gracefully when marking articles as read, logging warnings but not raising exceptions that would fail the digest job.

#### Scenario: Mark-as-read API failure
- **WHEN** the FreshRSS `edit-tag` API returns an error (4xx or 5xx)
- **THEN** a warning is logged with the error details
- **THEN** the method does not raise an exception

#### Scenario: Network timeout during mark-as-read
- **WHEN** the mark-as-read request times out
- **THEN** a warning is logged with timeout details
- **THEN** the method does not raise an exception

#### Scenario: Authentication expired during mark-as-read
- **WHEN** the auth token has expired during the mark-as-read call
- **THEN** the system attempts to re-authenticate and retry once
- **THEN** if retry fails, a warning is logged without raising exception

### Requirement: Article model includes ID for marking
The system SHALL ensure the Article model's `id` field contains the FreshRSS article ID suitable for use with the `edit-tag` API.

#### Scenario: Article ID format
- **WHEN** an article is fetched from FreshRSS
- **THEN** the `id` field contains the string ID as returned by FreshRSS API
- **THEN** this ID is valid for use with `mark_as_read()`
