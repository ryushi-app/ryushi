## 1. Model Updates

- [x] 1.1 Add `template_type`, `item_type`, and `interests` fields to `CategoryConfig` in `ryushi/scheduler/models.py`
- [x] 1.2 Update config parsing in `ryushi/scheduler/config.py` to read new fields from YAML

## 2. Template Registry

- [x] 2.1 Define `PROMPT_TEMPLATES` dictionary in `ryushi/digest/prompts.py` with `digest` and `recommendation` templates
- [x] 2.2 Create `get_template(template_type: str)` function to retrieve templates from registry
- [x] 2.3 Create `render_template()` function with `{language}`, `{item_type}`, `{interests}` substitution

## 3. Template Selection Logic

- [x] 3.1 Create `select_prompt()` function implementing priority: custom prompt > template_type > default
- [x] 3.2 Add warning logging for invalid/unknown template types
- [x] 3.3 Update digest generation to use `select_prompt()` instead of direct `format_system_prompt()`

## 4. Tests

- [x] 4.1 Add unit tests for template registry lookup (`get_template`)
- [x] 4.2 Add unit tests for template rendering with parameter substitution
- [x] 4.3 Add unit tests for prompt selection priority logic
- [x] 4.4 Add unit tests for CategoryConfig with new fields
- [x] 4.5 Add integration test verifying backward compatibility with existing configs

## 5. Documentation

- [x] 5.1 Update docs/prompt-templates.md with final template content and config examples
