## MODIFIED Requirements

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
