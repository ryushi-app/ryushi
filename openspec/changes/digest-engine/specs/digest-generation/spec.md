## ADDED Requirements

### Requirement: Generate digest from articles
The system SHALL accept a list of Article objects and generate a Digest containing an AI-generated summary with source attribution.

#### Scenario: Successful digest generation
- **WHEN** `generate_digest(articles, category_name)` is called with 30 articles
- **THEN** returns a Digest object with non-empty summary
- **THEN** summary references at least 5 article URLs from the input

#### Scenario: Empty article list
- **WHEN** `generate_digest([])` is called with empty list
- **THEN** returns None without calling AI backend

#### Scenario: Single article
- **WHEN** `generate_digest([article])` is called with one article
- **THEN** returns a Digest with summary mentioning that article

### Requirement: Prompt building with article data
The system SHALL build prompts that include article title, URL, and teaser for each article, along with category name and article count.

#### Scenario: Prompt contains article metadata
- **WHEN** prompt is built for articles with titles and teasers
- **THEN** each article's title, URL, and teaser appear in the prompt

#### Scenario: Prompt includes category context
- **WHEN** prompt is built for category "Software Engineering" with 30 articles
- **THEN** prompt includes "Software Engineering" and "30 articles"

### Requirement: Configurable system prompt
The system SHALL support configurable system prompt templates with placeholder substitution for language and other parameters.

#### Scenario: Default system prompt
- **WHEN** no custom prompt is configured
- **THEN** uses the default digest summarization prompt

#### Scenario: Custom system prompt
- **WHEN** custom system_prompt is provided in config
- **THEN** uses the custom prompt instead of default

### Requirement: Context window management
The system SHALL truncate article input to fit within 80% of the model's context window to prevent API errors.

#### Scenario: Articles fit within context
- **WHEN** total prompt fits within context limit
- **THEN** all articles are included in prompt

#### Scenario: Articles exceed context limit
- **WHEN** articles would exceed context window
- **THEN** truncates article list to fit
- **THEN** includes article count in prompt so AI knows content was truncated

### Requirement: LiteLLM integration
The system SHALL use LiteLLM for all AI calls, supporting any OpenAI-compatible endpoint via base_url configuration.

#### Scenario: Standard OpenAI endpoint
- **WHEN** no custom base_url is configured
- **THEN** uses default OpenAI endpoint via LiteLLM

#### Scenario: Custom AI endpoint
- **WHEN** base_url is configured to custom endpoint
- **THEN** routes requests to that endpoint

#### Scenario: API key from environment
- **WHEN** digest generation is invoked
- **THEN** reads API key from environment variable

### Requirement: Configurable model parameters
The system SHALL respect max_tokens and temperature settings from configuration.

#### Scenario: Custom max_tokens
- **WHEN** max_tokens is set to 1000 in config
- **THEN** limits AI response to 1000 tokens

#### Scenario: Custom temperature
- **WHEN** temperature is set to 0.3 in config
- **THEN** passes temperature=0.3 to AI backend

### Requirement: Digest data model
The system SHALL return a Digest object containing id, category_name, generated_at, summary, article_count, source_urls, and model_used.

#### Scenario: Digest contains required fields
- **WHEN** digest is successfully generated
- **THEN** Digest has valid UUID as id
- **THEN** Digest has category_name matching input
- **THEN** Digest has generated_at timestamp
- **THEN** Digest has summary as markdown string
- **THEN** Digest has article_count matching input
- **THEN** Digest has source_urls extracted from summary
- **THEN** Digest has model_used identifying the AI model
