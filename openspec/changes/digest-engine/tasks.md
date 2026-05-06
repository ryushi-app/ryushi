## 1. Project Setup

- [ ] 1.1 Create `ryushi/digest/` directory structure with `__init__.py`
- [ ] 1.2 Create `ryushi/digest/exceptions.py` with DigestError class
- [ ] 1.3 Add litellm and tenacity to project dependencies in pyproject.toml

## 2. Data Models

- [ ] 2.1 Create `ryushi/digest/models.py` with Digest Pydantic model (id, category_name, generated_at, summary, article_count, source_urls, model_used)
- [ ] 2.2 Create DigestConfig model for engine configuration (model, max_tokens, temperature, timeout, base_url)
- [ ] 2.3 Add validation tests for Digest and DigestConfig models

## 3. Prompt Building

- [ ] 3.1 Create `ryushi/digest/prompts.py` with default system prompt template
- [ ] 3.2 Implement `build_prompt(articles, category_name)` function
- [ ] 3.3 Include article title, URL, and teaser in prompt format
- [ ] 3.4 Add category name and article count to prompt context
- [ ] 3.5 Implement context window truncation logic (80% of model limit)
- [ ] 3.6 Add unit tests for prompt building

## 4. Core Engine Implementation

- [ ] 4.1 Create `ryushi/digest/engine.py` with DigestEngine class
- [ ] 4.2 Implement `__init__` method accepting DigestConfig
- [ ] 4.3 Implement `generate_digest(articles, category_name)` async method
- [ ] 4.4 Integrate LiteLLM for AI calls with configurable model parameters
- [ ] 4.5 Parse AI response and extract source URLs
- [ ] 4.6 Return Digest object with all required fields populated
- [ ] 4.7 Handle empty article list by returning None

## 5. Error Handling and Resilience

- [ ] 5.1 Implement retry decorator with tenacity for transient errors (429, 503, 5xx)
- [ ] 5.2 Configure exponential backoff (max 3 retries)
- [ ] 5.3 Implement 60-second timeout for AI calls
- [ ] 5.4 Handle authentication failures (401) without retry
- [ ] 5.5 Handle invalid request errors (400) without retry
- [ ] 5.6 Ensure credentials are never logged or exposed in errors

## 6. Logging and Observability

- [ ] 6.1 Add logging for all AI requests with status codes and latency
- [ ] 6.2 Log model used and token counts
- [ ] 6.3 Log retry attempts with count and delay
- [ ] 6.4 Log errors with context (excluding sensitive data)

## 7. API Exports

- [ ] 7.1 Update `ryushi/digest/__init__.py` to export DigestEngine, Digest, DigestConfig, DigestError
- [ ] 7.2 Make the public API clean and intuitive for consumers

## 8. Testing

- [ ] 8.1 Create unit tests for DigestEngine with mocked LiteLLM
- [ ] 8.2 Test successful digest generation
- [ ] 8.3 Test empty article list handling
- [ ] 8.4 Test context window truncation
- [ ] 8.5 Test retry logic on transient errors
- [ ] 8.6 Test timeout handling
- [ ] 8.7 Test custom prompt template
- [ ] 8.8 Test DigestError contains proper context

## 9. Documentation

- [ ] 9.1 Add docstrings to all public methods and classes
- [ ] 9.2 Document environment variables (API key configuration)
- [ ] 9.3 Document DigestConfig options and defaults

## 10. Quality and Verification

- [ ] 10.1 Run type checking (mypy) on the new module
- [ ] 10.2 Run linting (ruff) on the new module
- [ ] 10.3 Ensure all tests pass
- [ ] 10.4 Code review and merge to main branch
