## Why

Ryushi needs to transform raw article feeds into readable AI-generated digests. The digest engine is the core component that takes articles from FreshRSS, builds structured prompts, and generates summaries using LiteLLM. This enables users to quickly scan their feeds instead of reading dozens of individual articles.

## What Changes

- Add digest generation module using LiteLLM for AI calls
- Implement prompt building with configurable system prompt templates
- Add Digest data model with title, summary, article references, and metadata
- Implement retry logic with exponential backoff for transient AI errors
- Support configurable model parameters (max_tokens, temperature, timeout)

## Capabilities

### New Capabilities
- `digest-generation`: Core digest creation from articles using AI, including prompt building, LiteLLM integration, and output parsing
- `digest-resilience`: Error handling, retry logic, and graceful failure for AI backend issues

### Modified Capabilities
<!-- No existing capabilities require requirement changes -->

## Impact

- New module: `ryushi/digest/` for digest generation logic
- Dependencies: litellm (AI abstraction), tenacity (retry logic)
- Environment variables: AI backend API key configuration
- Integration point: Consumes Article models from FreshRSS integration
