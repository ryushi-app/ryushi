## Context

Ryushi currently uses a global `DigestConfig` for all categories with English as the hardcoded default language and a single system prompt template. The config.yaml only defines schedule per category. Users with multi-language FreshRSS setups or different digest style preferences per topic cannot customize without code changes.

Additionally, articles used in digest generation remain unread in FreshRSS, causing them to appear in subsequent runs. Generated feeds also lack visual identification through favicons.

## Goals / Non-Goals

**Goals:**
- Per-category configuration for language, custom prompt, and favicon
- German as the new default language (user preference)
- Mark articles as read after successful digest generation
- Include favicon in generated Atom feeds
- Backward-compatible config: existing configs work without changes

**Non-Goals:**
- Per-article language detection or mixed-language digests
- Dynamic favicon fetching from source feeds
- Undo/unmark-as-read functionality
- Feed icon caching or optimization

## Decisions

### D1: Extend config.yaml with category-level settings
**Decision**: Add optional `language`, `prompt`, and `favicon` fields to each category in config.yaml.

```yaml
categories:
  technology:
    schedule: "0 6 * * *"
    language: "German"          # Optional, defaults to "German"
    prompt: |                   # Optional, uses default template
      Fasse die Artikel kurz zusammen...
    favicon: "/static/tech.png" # Optional, relative or absolute URL
```

**Rationale**: Keeps all configuration in one place. YAML supports multi-line strings for prompts naturally.

**Alternative considered**: Separate `prompts/` directory with prompt files per category - rejected as over-engineering for simple text templates.

### D2: CategoryConfig model
**Decision**: Create a `CategoryConfig` Pydantic model containing schedule, language, prompt, and favicon. The scheduler config loader returns these instead of raw dicts.

**Rationale**: Type safety, validation, and IDE support. Makes defaults explicit and documented.

### D3: Mark articles read via FreshRSS edit-tag API
**Decision**: After successful digest generation, call FreshRSS `edit-tag` API endpoint to mark article IDs as read using the `user/-/state/com.google/read` tag.

**Rationale**: Standard Google Reader API pattern that FreshRSS supports. Operates in batch (single request for multiple IDs).

**Alternative considered**: Store processed article IDs locally - rejected as it duplicates state and can drift from FreshRSS.

### D4: Favicon in Atom feed
**Decision**: Include `<icon>` element in Atom feed when category config specifies a favicon URL. The URL is used as-is (can be relative to feed or absolute).

**Rationale**: Atom 1.0 supports `<icon>` natively. Feed readers display it alongside the feed title.

### D5: Default language change
**Decision**: Change default language from "English" to "German" in `DigestConfig`.

**Rationale**: User request. Existing users with explicit `language` config are unaffected.

## Risks / Trade-offs

**[Config migration]** → Users with existing configs get German digests by default after upgrade. Mitigation: Document in changelog; users can add `language: English` explicitly.

**[Mark-as-read failure]** → If marking fails after digest generation, articles may be duplicated in next run. Mitigation: Log warning but don't fail the job; user can manually mark read in FreshRSS.

**[Prompt injection]** → Custom prompts could potentially be crafted maliciously. Mitigation: Config file is local; only admin can edit it. No user-facing prompt input.

**[Large batch mark-as-read]** → FreshRSS API may have limits on batch size. Mitigation: Chunk into batches of 50 IDs if needed based on testing.
