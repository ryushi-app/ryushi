# prompt-templates Specification

## Purpose
TBD - created by archiving change prompt-templates. Update Purpose after archive.
## Requirements
### Requirement: Template registry
The system SHALL maintain a registry of built-in prompt templates identified by string type names. Initially, the registry SHALL contain templates for types `digest` and `recommendation`.

#### Scenario: Registry contains digest template
- **WHEN** template registry is accessed with type `digest`
- **THEN** returns the news digest prompt template with HTML formatting rules

#### Scenario: Registry contains recommendation template  
- **WHEN** template registry is accessed with type `recommendation`
- **THEN** returns the personalized recommendation prompt template

#### Scenario: Unknown template type
- **WHEN** template registry is accessed with an unknown type
- **THEN** returns None to indicate template not found

### Requirement: Digest template content
The system SHALL provide a `digest` template that instructs the AI to summarize RSS feeds with: an intro paragraph, bullet points per article with hyperlinked titles, HTML output format, and strict URL preservation rules.

#### Scenario: Digest template structure
- **WHEN** digest template is retrieved
- **THEN** template includes instructions for intro paragraph and bullet list structure

#### Scenario: Digest template HTML formatting
- **WHEN** digest template is retrieved
- **THEN** template specifies HTML output with `<h2>`, `<ul>`, `<li>`, `<a>` elements

#### Scenario: Digest template URL rules
- **WHEN** digest template is retrieved
- **THEN** template explicitly prohibits inventing or modifying URLs

#### Scenario: Digest template word limit
- **WHEN** digest template is retrieved
- **THEN** template specifies a maximum word limit (600 words)

### Requirement: Recommendation template content
The system SHALL provide a `recommendation` template that instructs the AI to select and rank items based on user interests, with each item including title with URL, relevance explanation, and description.

#### Scenario: Recommendation template structure
- **WHEN** recommendation template is retrieved
- **THEN** template includes instructions to select top 10 most relevant items

#### Scenario: Recommendation template ranking
- **WHEN** recommendation template is retrieved
- **THEN** template instructs to rank items by relevance (most relevant first)

#### Scenario: Recommendation template item format
- **WHEN** recommendation template is retrieved
- **THEN** template specifies title with URL, why it matches interests, and what it's about

#### Scenario: Recommendation template quality filter
- **WHEN** recommendation template is retrieved
- **THEN** template instructs to skip promotional or clickbait items

### Requirement: Template parameter substitution
The system SHALL substitute `{language}`, `{item_type}`, and `{interests}` placeholders in templates with provided values.

#### Scenario: Language placeholder substitution
- **WHEN** template is rendered with language="English"
- **THEN** all `{language}` placeholders are replaced with "English"

#### Scenario: Item type substitution
- **WHEN** recommendation template is rendered with item_type="books"
- **THEN** `{item_type}` placeholder is replaced with "books"

#### Scenario: Interests list substitution
- **WHEN** recommendation template is rendered with interests=["Fantasy", "Sci-Fi"]
- **THEN** `{interests}` placeholder is replaced with formatted bullet list of interests

#### Scenario: Missing optional parameters
- **WHEN** template is rendered without optional parameters (item_type, interests)
- **THEN** placeholders are replaced with sensible defaults or generic text

### Requirement: Template selection function
The system SHALL provide a function to select and render the appropriate prompt based on category configuration, following the priority: custom `prompt` > `template_type` > default.

#### Scenario: Custom prompt takes priority
- **WHEN** category config has both `prompt` and `template_type` set
- **THEN** the custom `prompt` is used

#### Scenario: Template type selection
- **WHEN** category config has `template_type` but no `prompt`
- **THEN** the template matching `template_type` is used

#### Scenario: Default fallback
- **WHEN** category config has neither `prompt` nor `template_type`
- **THEN** the default digest template is used

#### Scenario: Invalid template type fallback
- **WHEN** category config has an unrecognized `template_type`
- **THEN** logs a warning and uses the default template

