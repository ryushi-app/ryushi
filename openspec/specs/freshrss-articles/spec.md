## Purpose

Fetch unread articles from FreshRSS with proper authentication, error handling, and pagination support.

## Requirements

### Requirement: Fetch unread articles by category
The system SHALL fetch unread articles for a given category ID and return them as a list of Article objects. The operation SHALL be read-only and SHALL NOT mark any articles as read.

#### Scenario: Successful unread articles fetch
- **WHEN** `get_unread_items(category_id="software-engineering")` is called with valid authentication
- **THEN** returns a list of Article objects with all required fields populated

#### Scenario: Empty category
- **WHEN** a category has no unread items
- **THEN** returns an empty list without error

#### Scenario: Invalid category ID
- **WHEN** a non-existent category ID is provided
- **WHEN** FreshRSS returns a 404 or empty result
- **THEN** returns an empty list (no error raised)

### Requirement: Article data model
The system SHALL return articles as objects containing: title, URL, author (optional), published date, category ID, feed title, and a teaser (first 500 characters of content).

#### Scenario: Article with complete metadata
- **WHEN** an article is fetched from FreshRSS
- **THEN** it contains title, url, published_at, category_id, feed_title, and teaser fields

#### Scenario: Article with missing optional fields
- **WHEN** an article has no author or incomplete content
- **THEN** author is null and teaser contains available content up to 500 characters

#### Scenario: Teaser length enforcement
- **WHEN** article content exceeds 500 characters
- **THEN** teaser field contains exactly the first 500 characters

### Requirement: Configurable max articles limit
The system SHALL respect a configurable `max_articles` parameter that limits the number of articles returned. When a category has more articles than the limit, the system SHALL return the most recent articles up to that limit.

#### Scenario: Fetch with max articles limit
- **WHEN** a category has 200 unread articles and `max_articles=50` is configured
- **THEN** returns exactly 50 most recent articles

#### Scenario: Fetch fewer articles than limit
- **WHEN** a category has 30 unread articles and `max_articles=50` is configured
- **THEN** returns all 30 articles

#### Scenario: Default max articles limit
- **WHEN** `get_unread_items()` is called without specifying `max_articles`
- **THEN** uses a sensible default (e.g., 100 articles) or applies no limit

### Requirement: Pagination support
The system SHOULD handle pagination for large feeds using offset and limit parameters to avoid loading entire feed sets into memory.

#### Scenario: Articles paginated internally
- **WHEN** fetching articles from a large category
- **THEN** the client handles pagination transparently (caller sees a single unified list)

#### Scenario: Pagination with max articles limit
- **WHEN** `max_articles=50` and pagination returns results in multiple batches
- **THEN** pagination stops once 50 total articles are collected

### Requirement: Error handling and logging
The system SHALL raise typed exceptions (`AuthError`, `FetchError`, `RateLimitError`) for different failure scenarios. Failed requests SHALL be logged with HTTP status code, request URL, and error details.

#### Scenario: Rate limit error (429)
- **WHEN** FreshRSS returns HTTP 429 Too Many Requests
- **THEN** raises `RateLimitError` and logs the attempt with timestamp

#### Scenario: Server error (5xx)
- **WHEN** FreshRSS returns HTTP 500 or similar server error
- **THEN** raises `FetchError` with status code and URL logged

#### Scenario: Network timeout
- **WHEN** the request times out after configured duration
- **THEN** raises `FetchError` with timeout message and URL logged

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
