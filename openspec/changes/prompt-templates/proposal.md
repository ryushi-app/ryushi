## Why

Currently, users must provide a full custom prompt to configure digest generation, which is complex and error-prone. Providing default prompt templates for common use cases (news digest, recommendations) would make configuration simpler and ensure consistent, well-formatted output across feeds.

## What Changes

- Add a new `template_type` field to category configuration with predefined types: `digest` (news summarization) and `recommendation` (personalized item selection)
- Include built-in prompt templates with proper formatting rules (HTML output, URL handling, word limits)
- Allow template-specific parameters: `recommendation` templates accept `item_type` and `interests` fields
- Templates use `{language}` placeholder like existing custom prompts
- Maintain backward compatibility: custom `prompt` field still overrides any template

## Capabilities

### New Capabilities
- `prompt-templates`: Registry of built-in prompt templates with parameter substitution, template type validation, and formatted output generation

### Modified Capabilities
- `category-config`: Add `template_type`, `item_type`, and `interests` fields to CategoryConfig model

## Impact

- **Models**: Extend `CategoryConfig` with new optional fields
- **Prompts**: Add template registry and selection logic in `ryushi/digest/prompts.py`
- **Config**: Update config parsing to handle new fields in `ryushi/scheduler/config.py`
- **Tests**: Add tests for template selection and parameter substitution
