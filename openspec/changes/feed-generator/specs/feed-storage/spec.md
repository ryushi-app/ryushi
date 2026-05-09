## ADDED Requirements

### Requirement: Persist feed entries to SQLite
The system SHALL store FeedEntry records in SQLite for each digest generated.

#### Scenario: New digest creates feed entry
- **WHEN** a Digest is converted and stored
- **THEN** a FeedEntry record exists in the database
- **THEN** FeedEntry contains id, category_slug, title, published, content_html, source_urls

#### Scenario: Entry persists across restarts
- **WHEN** server is restarted
- **THEN** previously stored feed entries are available

### Requirement: Maintain rolling window per category
The system SHALL keep only the last 30 feed entries per category, removing older entries.

#### Scenario: Under retention limit
- **WHEN** category has fewer than 30 entries
- **THEN** all entries are retained

#### Scenario: At retention limit
- **WHEN** a new entry is added to a category with 30 entries
- **THEN** the oldest entry is removed
- **THEN** the category has exactly 30 entries

#### Scenario: Multiple categories independent
- **WHEN** category A has 30 entries and category B has 5 entries
- **THEN** adding to category A removes oldest from A only
- **THEN** category B entries are unaffected

### Requirement: Retrieve entries for feed generation
The system SHALL provide efficient retrieval of entries by category for feed generation.

#### Scenario: Retrieve all entries for category
- **WHEN** feed is requested for "software-engineering"
- **THEN** returns all stored entries for that category
- **THEN** entries are ordered by published date descending (newest first)

#### Scenario: Retrieve entries for empty category
- **WHEN** feed is requested for category with no entries
- **THEN** returns empty list

### Requirement: List all categories with feeds
The system SHALL provide a listing of all categories that have stored feed entries.

#### Scenario: Multiple categories exist
- **WHEN** entries exist for 3 different categories
- **THEN** returns metadata for all 3 categories
- **THEN** each includes category name, slug, last_updated, and item_count

#### Scenario: No categories exist
- **WHEN** no feed entries have been stored
- **THEN** returns empty list
