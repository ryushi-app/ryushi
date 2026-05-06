## ADDED Requirements

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
