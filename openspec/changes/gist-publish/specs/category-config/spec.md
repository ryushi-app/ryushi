## ADDED Requirements

### Requirement: Per-category Gist publishing configuration
The system SHALL support `gist_enabled` and `gist_id` fields in category configuration to enable publishing feeds to GitHub Gists.

#### Scenario: Category with Gist publishing enabled
- **WHEN** category config includes `gist_enabled: true` and `gist_id: "abc123"`
- **THEN** the generated Atom feed is published to the specified Gist after digest generation

#### Scenario: Category with Gist publishing disabled
- **WHEN** category config omits `gist_enabled` or sets it to false
- **THEN** no Gist publishing occurs for that category

#### Scenario: Gist enabled without gist_id
- **WHEN** category config includes `gist_enabled: true` but omits `gist_id`
- **THEN** a warning is logged indicating missing gist_id
- **THEN** Gist publishing is skipped for that category

### Requirement: CategoryConfig model extension
The system SHALL extend the `CategoryConfig` Pydantic model to include gist_enabled (bool, default False) and gist_id (str | None, default None).

#### Scenario: Valid category config with Gist fields
- **WHEN** config YAML contains gist_enabled and gist_id for a category
- **THEN** CategoryConfig model is populated with both values

#### Scenario: Valid category config without Gist fields
- **WHEN** config YAML omits gist_enabled and gist_id for a category
- **THEN** CategoryConfig model is created with defaults (gist_enabled=False, gist_id=None)

### Requirement: Backward-compatible config loading
The system SHALL accept existing config.yaml files without Gist fields, applying default values.

#### Scenario: Legacy config format
- **WHEN** config YAML uses the existing format without Gist fields
- **THEN** config loads successfully with gist_enabled=False for all categories
