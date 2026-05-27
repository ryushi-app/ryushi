# category-config Specification

## Purpose
TBD - created by archiving change digest-engine-config. Update Purpose after archive.
## Requirements
### Requirement: Per-category language configuration
The system SHALL support a `language` field in category configuration that specifies the output language for that category's digests. If not specified, the system SHALL default to "German".

#### Scenario: Category with explicit language
- **WHEN** category config includes `language: "English"`
- **THEN** digests for that category are generated in English

#### Scenario: Category without language specified
- **WHEN** category config omits the `language` field
- **THEN** digests for that category are generated in German (default)

#### Scenario: Multiple categories with different languages
- **WHEN** one category specifies `language: "German"` and another specifies `language: "English"`
- **THEN** each category's digest uses its configured language

### Requirement: Per-category prompt configuration
The system SHALL support a `prompt` field in category configuration that provides a custom system prompt template for that category's digest generation. If not specified, the system SHALL use the default prompt template with the category's language substituted.

#### Scenario: Category with custom prompt
- **WHEN** category config includes a `prompt` field with custom text
- **THEN** digest generation uses the custom prompt as the system prompt

#### Scenario: Category without custom prompt
- **WHEN** category config omits the `prompt` field
- **THEN** digest generation uses the default system prompt template

#### Scenario: Custom prompt with language placeholder
- **WHEN** custom prompt contains `{language}` placeholder
- **THEN** the placeholder is replaced with the category's configured language

### Requirement: Per-category favicon configuration
The system SHALL support a `favicon` field in category configuration that specifies a URL for the category's feed icon. The URL SHALL be used as-is in the generated feed.

#### Scenario: Category with favicon URL
- **WHEN** category config includes `favicon: "/static/tech.png"`
- **THEN** the generated Atom feed includes this URL as the feed icon

#### Scenario: Category without favicon
- **WHEN** category config omits the `favicon` field
- **THEN** the generated Atom feed does not include an icon element

#### Scenario: Absolute favicon URL
- **WHEN** category config includes `favicon: "https://example.com/icon.png"`
- **THEN** the generated Atom feed includes the absolute URL as-is

### Requirement: CategoryConfig model
The system SHALL provide a `CategoryConfig` Pydantic model containing: schedule (required), language (optional, default "German"), prompt (optional), favicon (optional), template_type (optional), item_type (optional), and interests (optional list of strings).

#### Scenario: Valid category config with all fields
- **WHEN** config YAML contains schedule, language, prompt, favicon, template_type, item_type, and interests for a category
- **THEN** CategoryConfig model is populated with all values

#### Scenario: Valid category config with only schedule
- **WHEN** config YAML contains only schedule for a category
- **THEN** CategoryConfig model is created with defaults (language="German", prompt=None, favicon=None, template_type=None, item_type=None, interests=None)

#### Scenario: Invalid category config without schedule
- **WHEN** config YAML omits the schedule field for a category
- **THEN** config validation raises an error

#### Scenario: Category config with template_type
- **WHEN** config YAML includes `template_type: "recommendation"`
- **THEN** CategoryConfig.template_type is set to "recommendation"

#### Scenario: Category config with interests list
- **WHEN** config YAML includes `interests: ["Fantasy novels", "Science fiction"]`
- **THEN** CategoryConfig.interests is a list containing those strings

#### Scenario: Category config with item_type
- **WHEN** config YAML includes `item_type: "books"`
- **THEN** CategoryConfig.item_type is set to "books"

### Requirement: Backward-compatible config loading
The system SHALL accept existing config.yaml files that only contain schedule fields per category without requiring changes.

#### Scenario: Legacy config format
- **WHEN** config YAML uses the existing format with only schedule per category
- **THEN** config loads successfully with default values for new fields

#### Scenario: Mixed config format
- **WHEN** some categories have new fields and others only have schedule
- **THEN** config loads successfully with defaults applied to categories without new fields

#### Scenario: Config with template fields but no template_type
- **WHEN** config YAML includes item_type and interests but no template_type
- **THEN** config loads successfully with all fields populated (template selection uses default)

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

