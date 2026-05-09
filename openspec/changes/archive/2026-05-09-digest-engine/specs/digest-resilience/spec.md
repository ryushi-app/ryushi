## ADDED Requirements

### Requirement: Retry on transient errors
The system SHALL retry AI calls on transient errors (429 Too Many Requests, 503 Service Unavailable, 5xx server errors) with exponential backoff.

#### Scenario: Rate limit with successful retry
- **WHEN** AI backend returns 429 on first attempt
- **THEN** waits with exponential backoff
- **THEN** retries the request
- **THEN** returns digest on successful retry

#### Scenario: Server error with successful retry
- **WHEN** AI backend returns 503 on first attempt
- **THEN** waits with exponential backoff
- **THEN** retries the request
- **THEN** returns digest on successful retry

#### Scenario: Max retries exceeded
- **WHEN** AI backend returns transient errors for all 3 retry attempts
- **THEN** raises DigestError after final retry

### Requirement: Graceful failure handling
The system SHALL fail gracefully when AI calls fail permanently, logging the error and raising DigestError without crashing.

#### Scenario: Authentication failure
- **WHEN** AI backend returns 401 Unauthorized
- **THEN** logs error with context (no credentials in log)
- **THEN** raises DigestError immediately without retry

#### Scenario: Invalid request
- **WHEN** AI backend returns 400 Bad Request
- **THEN** logs error with request details
- **THEN** raises DigestError immediately without retry

### Requirement: Request timeout
The system SHALL enforce a timeout of 60 seconds per AI call to prevent hung requests.

#### Scenario: Request completes within timeout
- **WHEN** AI backend responds in 5 seconds
- **THEN** returns digest normally

#### Scenario: Request exceeds timeout
- **WHEN** AI backend does not respond within 60 seconds
- **THEN** cancels the request
- **THEN** raises DigestError with timeout message

### Requirement: Error context preservation
The system SHALL preserve error context in DigestError, including status codes, error messages, and request metadata (excluding sensitive data).

#### Scenario: DigestError contains context
- **WHEN** AI call fails with 503 error
- **THEN** DigestError includes status_code=503
- **THEN** DigestError includes descriptive message
- **THEN** DigestError does NOT include API key or credentials

### Requirement: Logging for observability
The system SHALL log all AI requests with status codes, latency, and model used for observability and debugging.

#### Scenario: Successful request logged
- **WHEN** AI call succeeds
- **THEN** logs request with status=200, latency, and model name

#### Scenario: Failed request logged
- **WHEN** AI call fails
- **THEN** logs error with status code, error type, and retry count
