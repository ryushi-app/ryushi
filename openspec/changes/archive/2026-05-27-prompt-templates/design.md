## Context

Ryushi currently supports custom prompts per category via the `prompt` field in `CategoryConfig`. The default prompt in `prompts.py` is a basic digest template with `{language}` substitution. Users wanting common patterns (news digests, recommendations) must write their own prompts, duplicating formatting rules and best practices.

The codebase already has:
- `DEFAULT_SYSTEM_PROMPT` in `ryushi/digest/prompts.py`
- `format_system_prompt()` for `{language}` substitution
- `CategoryConfig` model with optional `prompt` field

## Goals / Non-Goals

**Goals:**
- Provide 2 built-in templates: `digest` and `recommendation`
- Allow template selection via `template_type` config field
- Support template-specific parameters (e.g., `interests`, `item_type`)
- Maintain full backward compatibility with existing custom prompts

**Non-Goals:**
- User-defined template registration (future enhancement)
- Template versioning or A/B testing
- Per-template AI model recommendations

## Decisions

### Decision 1: Template Registry Pattern
Use a simple dictionary registry in `prompts.py` mapping template type names to template strings and metadata.

**Rationale:** Matches existing code style (see `MODEL_CONTEXT_WINDOWS` dict). Simple to understand, test, and extend.

**Alternative considered:** Template class hierarchy - rejected as over-engineered for 2 templates.

### Decision 2: Template Priority Resolution
Resolution order: `prompt` (custom) → `template_type` → default template.

**Rationale:** Preserves backward compatibility. Custom prompts always win, template_type is opt-in.

### Decision 3: Template Parameters as Top-Level Config Fields
Add `item_type` and `interests` directly to `CategoryConfig` rather than nested under a `template_params` object.

**Rationale:** Simpler YAML syntax for users. These fields are only meaningful for `recommendation` template but harmless if present otherwise.

**Alternative considered:** Nested `template_params: {item_type: ..., interests: [...]}` - rejected for added config complexity.

### Decision 4: Interests as List Field
Store `interests` as `list[str]` and join into bullet points during template rendering.

**Rationale:** Easier to manage in YAML. More structured than freeform text.

## Risks / Trade-offs

**[Risk] Template text becomes stale or inconsistent with AI model expectations**
→ Templates are code-defined with tests. Changes require deployment but are version-controlled.

**[Risk] Users provide invalid template_type**
→ Log warning and fall back to default template (fail-safe).

**[Risk] Recommendation template requires interests but none provided**
→ Use generic "based on the feed content" phrasing. Log info-level message.

**[Trade-off] Flat config fields vs nested template_params**
→ Accepted trade-off: simpler config syntax at cost of fields that are only relevant for specific template types.
