## ADDED Requirements

### Requirement: Fetch all feed categories
The system SHALL retrieve all feed categories from FreshRSS and return them as a list of Category objects containing human-readable category names and their corresponding FreshRSS category IDs.

#### Scenario: Successful category listing
- **WHEN** `get_categories()` is called with valid authentication
- **THEN** returns a list of Category objects with `id` and `name` fields populated from FreshRSS

#### Scenario: Category listing with no categories
- **WHEN** FreshRSS instance has no categories
- **THEN** returns an empty list without error

#### Scenario: Category listing with network failure
- **WHEN** the FreshRSS server is unreachable
- **THEN** the system raises `FetchError` with HTTP status code and URL logged

### Requirement: Category ID to name mapping
The system SHALL map FreshRSS category identifiers (internal IDs) to human-readable names returned by the API, preserving the original category hierarchy structure if applicable.

#### Scenario: Category names are human-readable
- **WHEN** categories are fetched from FreshRSS
- **THEN** returned Category names are suitable for display to end users (e.g., "Technology", "News", "Entertainment")

#### Scenario: Duplicate category handling
- **WHEN** FreshRSS returns duplicate or similar category names
- **THEN** each category is returned with its unique ID for accurate feed identification
