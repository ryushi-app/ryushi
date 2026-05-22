## Why

Currently, digest configuration is global: one language (English), one system prompt, and no category-specific customization. Users managing multi-language FreshRSS categories or wanting different digest styles per topic cannot configure this without code changes. Additionally, articles used in digests remain unread in FreshRSS, causing duplication in subsequent runs, and generated feeds lack favicons for visual identification.

## What Changes

- Add per-category configuration for language (German as default) and custom prompt templates
- Add per-category favicon configuration that appears in the generated Atom feed
- Mark articles as read in FreshRSS after they've been included in a digest
- Extend `config.yaml` structure to support these category-level settings

## Capabilities

### New Capabilities
- `category-config`: Per-category configuration for language, prompt, and favicon with sensible defaults

### Modified Capabilities
- `freshrss-articles`: Add ability to mark articles as read after digest generation
- `feed-generation`: Include favicon/icon in generated Atom feeds from category config

## Impact

- **Config**: Extended `config.yaml` schema with category-level `language`, `prompt`, and `favicon` fields
- **Scheduler**: `JobExecutor` must pass category config to digest engine and handle marking articles read
- **Digest Engine**: `DigestConfig` may need category-aware overrides or factory pattern
- **FreshRSS Client**: New method to mark article IDs as read via FreshRSS API
- **Feed Generator**: Atom feed output includes `<icon>` element when favicon is configured
- **Migration**: Existing configs remain valid; new fields are optional with defaults
