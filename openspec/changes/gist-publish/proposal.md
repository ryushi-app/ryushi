## Why

Users hosting Ryushi on internal networks cannot easily share their digest feeds externally without exposing the entire application to the internet. Publishing feeds to GitHub Gists provides a secure way to make feeds publicly accessible while keeping Ryushi internal, leveraging GitHub's infrastructure for availability and CDN delivery.

## What Changes

- Add optional GitHub Gist publishing per category in config.yaml
- Create a GitHub Gist integration client using the GitHub API
- After successful digest generation, publish the Atom feed XML to a Gist
- Support authentication via environment variables (GITHUB_TOKEN)
- Each category can independently enable/disable Gist publishing
- Gist is updated (not recreated) on each digest run for stable URLs

## Capabilities

### New Capabilities
- `gist-publish`: Publishing Atom feeds to GitHub Gists with per-category configuration, authentication via environment variables, and automatic updates on digest generation

### Modified Capabilities
- `category-config`: Add `gist_enabled` and optional `gist_id` fields to per-category configuration
- `job-execution`: After storing feed entry, optionally publish to Gist if enabled for the category

## Impact

- **Config**: Extended `config.yaml` schema with `gist_enabled` (bool) and `gist_id` (string, optional) per category
- **Environment**: New `GITHUB_TOKEN` environment variable required when Gist publishing is enabled
- **Dependencies**: May require `httpx` for GitHub API calls (already a dependency)
- **Scheduler/Executor**: `JobExecutor` calls Gist publisher after successful feed storage
- **New Module**: `ryushi/integrations/github/` for Gist client implementation
- **Storage**: Gist IDs may be stored in config or managed separately for persistence across restarts
