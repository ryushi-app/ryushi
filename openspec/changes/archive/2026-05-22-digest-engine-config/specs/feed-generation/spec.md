## MODIFIED Requirements

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
