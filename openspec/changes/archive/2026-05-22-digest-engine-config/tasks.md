## 1. Category Configuration Model

- [x] 1.1 Create `CategoryConfig` Pydantic model in `ryushi/scheduler/config.py` with fields: schedule (str, required), language (str, default "German"), prompt (str | None), favicon (str | None)
- [x] 1.2 Update `load_config()` to parse category dicts into `CategoryConfig` objects
- [x] 1.3 Add unit tests for `CategoryConfig` validation (valid configs, missing schedule, defaults)

## 2. Default Language Change

- [x] 2.1 Change `DigestConfig.language` default from "English" to "German" in `ryushi/digest/models.py`
- [x] 2.2 Update any existing tests that assume English default

## 3. Mark Articles as Read

- [x] 3.1 Add `mark_as_read(article_ids: list[str])` method to `FreshRSSClient` in `ryushi/integrations/freshrss/client.py`
- [x] 3.2 Implement batch chunking (max 50 IDs per request) in `mark_as_read()`
- [x] 3.3 Add graceful error handling in `mark_as_read()` - log warnings, don't raise exceptions
- [x] 3.4 Add unit tests for `mark_as_read()` (single, batch, empty, error handling)

## 4. Digest Engine Category Config Integration

- [x] 4.1 Update `JobExecutor` to pass category language and prompt to `DigestEngine`
- [x] 4.2 Modify `DigestEngine.generate()` or config to accept per-call language/prompt overrides
- [x] 4.3 Update `JobExecutor` to call `mark_as_read()` after successful digest generation with article IDs

## 5. Feed Generation with Favicon

- [x] 5.1 Add optional `favicon` parameter to `FeedGenerator.generate_feed()` method
- [x] 5.2 Include `<icon>` element in Atom feed XML when favicon is provided
- [x] 5.3 Update `JobExecutor` to pass category favicon to feed generation
- [x] 5.4 Add unit tests for feed generation with and without favicon

## 6. Config Example and Documentation

- [x] 6.1 Update `config.yaml.example` with new category fields (language, prompt, favicon) and examples
- [x] 6.2 Add inline comments explaining the new configuration options
