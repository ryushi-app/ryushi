## Purpose

Serve AI-generated digest feeds in Atom 1.0 format with proper metadata, icons, and entry structure.
## Requirements
### Requirement: Generate valid Atom 1.0 feed
The system SHALL generate Atom 1.0 feeds that conform to RFC 4287. When a favicon URL is provided, the feed SHALL include an `<icon>` element with that URL.

#### Scenario: Feed passes Atom validation
- **WHEN** feed XML is generated for a category with digests
- **THEN** the XML is valid Atom 1.0 per RFC 4287
- **THEN** the feed element contains id, title, updated, and author elements

#### Scenario: Feed contains required metadata
- **WHEN** feed is generated for category "Software Engineering"
- **THEN** feed title is "Software Engineering - Ryushi Digest"
- **THEN** feed id is a unique URN based on category slug
- **THEN** feed updated reflects the most recent entry timestamp
- **THEN** feed author name is "Ryushi"

#### Scenario: Feed with favicon
- **WHEN** feed is generated with favicon URL "/static/tech.png"
- **THEN** feed XML includes `<icon>/static/tech.png</icon>` element
- **THEN** icon element appears after feed-level metadata (id, title, updated)

#### Scenario: Feed without favicon
- **WHEN** feed is generated without a favicon URL (None or empty)
- **THEN** feed XML does not include an `<icon>` element

#### Scenario: Feed with absolute favicon URL
- **WHEN** feed is generated with favicon URL "https://example.com/icon.png"
- **THEN** feed XML includes `<icon>https://example.com/icon.png</icon>` element

### Requirement: Create feed entry from Digest
The system SHALL convert each Digest object into an Atom entry with proper structure.

#### Scenario: Entry contains digest content
- **WHEN** a Digest with summary and source_urls is converted to entry
- **THEN** entry title includes category name and date
- **THEN** entry id is the Digest id as URN
- **THEN** entry published matches Digest generated_at
- **THEN** entry content contains summary rendered as HTML
- **THEN** entry includes link elements for each source URL

#### Scenario: Markdown summary rendered to HTML
- **WHEN** Digest summary contains markdown formatting
- **THEN** entry content is valid HTML with markdown converted

### Requirement: Generate category slug from name
The system SHALL convert category names to URL-safe slugs for feed URLs.

#### Scenario: Simple category name
- **WHEN** category name is "Technology"
- **THEN** slug is "technology"

#### Scenario: Multi-word category name
- **WHEN** category name is "Software Engineering"
- **THEN** slug is "software-engineering"

#### Scenario: Category with special characters
- **WHEN** category name contains special characters
- **THEN** slug contains only lowercase letters, numbers, and hyphens

### Requirement: Include feed icon
The system SHALL include an Atom `<icon>` element in the feed when a favicon URL is provided in the category configuration.

#### Scenario: Feed with favicon URL
- **WHEN** feed is generated with a favicon URL in configuration
- **THEN** the generated Atom feed includes an `<icon>` element with that URL

#### Scenario: Feed without favicon
- **WHEN** feed is generated without a favicon URL
- **THEN** the generated Atom feed does not include an `<icon>` element

#### Scenario: Absolute favicon URL
- **WHEN** favicon URL is absolute (e.g., "https://example.com/icon.png")
- **THEN** the Atom feed includes the absolute URL as-is in the icon element

