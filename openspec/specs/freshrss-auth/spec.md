## ADDED Requirements

### Requirement: Google Reader API authentication
The system SHALL support token-based authentication with FreshRSS via the Google Reader API `/accounts/ClientLogin` endpoint. Credentials SHALL be read from environment variables (`FRESHRSS_URL`, `FRESHRSS_USERNAME`, `FRESHRSS_PASSWORD`).

#### Scenario: Successful authentication
- **WHEN** valid credentials are available in environment variables
- **THEN** the client authenticates with FreshRSS and obtains an auth token

#### Scenario: Invalid credentials
- **WHEN** invalid password is provided in environment
- **THEN** the system raises `AuthError` with message "FreshRSS authentication failed"

#### Scenario: Missing environment variable
- **WHEN** environment variables are not set
- **THEN** the system raises `AuthError` with descriptive message about missing credentials

### Requirement: Automatic token refresh on 401 responses
The system SHALL automatically refresh the authentication token when a 401 Unauthorized response is received, then retry the failed request once.

#### Scenario: Token refresh on 401
- **WHEN** an API call returns 401 Unauthorized
- **THEN** the system re-authenticates, obtains a new token, and retries the original request

#### Scenario: Persistent 401 after refresh
- **WHEN** token refresh fails or second attempt returns 401
- **THEN** the system raises `AuthError` with message indicating authentication failure

### Requirement: Credential management
The system SHALL store FreshRSS credentials (URL, username, password) securely in memory during the client's lifetime. Credentials SHALL NOT be logged or exposed in error messages.

#### Scenario: Credentials stored on client initialization
- **WHEN** FreshRSSClient is initialized with valid environment variables
- **THEN** credentials are stored internally for use in subsequent API calls

#### Scenario: Credentials not exposed in errors
- **WHEN** an authentication error occurs
- **THEN** error messages do not contain password or sensitive credential data
