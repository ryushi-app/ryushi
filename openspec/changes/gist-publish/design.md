## Context

Ryushi generates AI-powered RSS digest feeds from FreshRSS articles. Currently, feeds are served locally via FastAPI. Users hosting Ryushi on internal networks cannot share feeds externally without exposing the application. GitHub Gists provide a simple, free hosting solution for text files with stable URLs, API access, and version history.

The existing architecture has a clear pipeline: Scheduler → Executor → DigestEngine → FeedStore → FeedServer. Gist publishing fits naturally after the FeedStore step, publishing the same Atom XML that would be served locally.

## Goals / Non-Goals

**Goals:**
- Enable per-category opt-in Gist publishing via config.yaml
- Authenticate with GitHub via environment variable (GITHUB_TOKEN)
- Update existing Gists rather than creating new ones (stable URLs)
- Handle Gist publishing failures gracefully without failing the digest job
- Provide clear logging of Gist publish status

**Non-Goals:**
- Managing multiple GitHub accounts or tokens
- Creating new Gists automatically (user must provide gist_id or create manually first)
- Publishing to other platforms (GitLab snippets, Pastebin, etc.)
- Encrypting or access-controlling Gist content (Gists are either public or secret)
- Webhook notifications when Gist is updated

## Decisions

### D1: User provides Gist ID in config
**Decision**: Require users to create a Gist manually and provide the `gist_id` in config.yaml rather than auto-creating Gists.

**Rationale**: 
- Gives users control over Gist visibility (public vs secret)
- Avoids needing write permissions to create gists
- Simpler implementation with fewer edge cases
- User can choose descriptive Gist names/descriptions

**Alternative considered**: Auto-create Gists on first run - rejected because it requires broader API permissions and users lose control over Gist settings.

### D2: Use GitHub API v3 REST for Gist updates
**Decision**: Use GitHub REST API v3 with PATCH /gists/{gist_id} to update Gist content.

**Rationale**:
- Simple HTTP/JSON API, no additional dependencies needed
- httpx already available in the project
- PATCH allows updating single files without affecting Gist metadata

**Alternative considered**: Use PyGithub library - rejected as over-engineering for a single API endpoint.

### D3: Store Gist configuration per-category in config.yaml
**Decision**: Add `gist_enabled: bool` and `gist_id: str` fields to CategoryConfig.

```yaml
categories:
  technology:
    schedule: "0 6 * * *"
    gist_enabled: true
    gist_id: "abc123def456"
```

**Rationale**: Keeps all category configuration in one place, consistent with existing language/prompt/favicon pattern.

### D4: Publish after local feed generation succeeds
**Decision**: Call Gist publisher in JobExecutor after FeedStore.add_entry() succeeds but before marking job complete.

**Rationale**:
- Ensures local feed is always stored first (primary source of truth)
- Gist failure doesn't prevent local feed storage
- Job still succeeds even if Gist publish fails (with warning logged)

### D5: Graceful failure handling
**Decision**: Log warnings on Gist publish failures but don't fail the digest job or raise exceptions.

**Rationale**:
- Gist is a secondary distribution channel, not critical path
- Network issues with GitHub shouldn't break digest generation
- Users can manually check Gist if needed

### D6: File naming in Gist
**Decision**: Use `{category_slug}.atom.xml` as the filename in the Gist.

**Rationale**:
- Clear, descriptive naming
- Consistent with local feed URL pattern
- Raw URL is directly usable as feed URL in readers

## Risks / Trade-offs

**[Rate Limiting]** → GitHub API has rate limits (60/hour unauthenticated, 5000/hour authenticated). Mitigation: Authentication is required via GITHUB_TOKEN, providing ample headroom for typical usage.

**[Token Security]** → GITHUB_TOKEN in environment could be leaked. Mitigation: Document minimum required scope (gist), recommend fine-grained tokens.

**[Gist Size Limits]** → Gists have a 10MB limit per file. Mitigation: Atom feeds are typically small (<100KB). Log warning if approaching limit.

**[Secret Gists Not Truly Private]** → Secret Gists are accessible to anyone with the URL. Mitigation: Document this limitation clearly; users who need private feeds should use other solutions.

**[Configuration Complexity]** → Users must manually create Gist and copy ID. Mitigation: Provide clear documentation with step-by-step instructions.
