## 1. Category Configuration Extension

- [ ] 1.1 Add `gist_enabled: bool = False` and `gist_id: str | None = None` fields to `CategoryConfig` in `ryushi/scheduler/models.py`
- [ ] 1.2 Update `parse_config()` in `ryushi/scheduler/config.py` to parse gist_enabled and gist_id from YAML
- [ ] 1.3 Add unit tests for CategoryConfig with Gist fields (valid configs, defaults, missing gist_id warning)

## 2. GitHub Gist Publisher Client

- [ ] 2.1 Create `ryushi/integrations/github/` package with `__init__.py`
- [ ] 2.2 Create `GistPublisher` class in `ryushi/integrations/github/client.py` with token from `GITHUB_TOKEN` env var
- [ ] 2.3 Implement `is_configured` property to check if token is available
- [ ] 2.4 Implement `publish(gist_id: str, filename: str, content: str)` method using GitHub REST API v3
- [ ] 2.5 Add graceful error handling (log warnings, don't raise exceptions)
- [ ] 2.6 Create `GistPublishError` exception class in `ryushi/integrations/github/exceptions.py`
- [ ] 2.7 Add unit tests for GistPublisher (successful publish, missing token, API errors)

## 3. Job Execution Integration

- [ ] 3.1 Update `JobExecutor.execute_job()` signature to accept `gist_enabled` and `gist_id` parameters
- [ ] 3.2 Update `JobExecutor._fetch_and_process()` to accept and use Gist configuration
- [ ] 3.3 After successful feed storage, generate Atom XML using FeedGenerator
- [ ] 3.4 Call GistPublisher.publish() if gist_enabled is True and gist_id is provided
- [ ] 3.5 Log appropriate messages for Gist publish success/failure
- [ ] 3.6 Add unit tests for executor with Gist publishing (enabled, disabled, failure scenarios)

## 4. Scheduler Integration

- [ ] 4.1 Update scheduler `_run_job()` to extract gist_enabled and gist_id from category config
- [ ] 4.2 Pass Gist configuration to executor.execute_job()
- [ ] 4.3 Add integration test for end-to-end Gist publishing flow

## 5. Configuration Documentation

- [ ] 5.1 Update `config.yaml.example` with gist_enabled and gist_id fields and examples
- [ ] 5.2 Add comments explaining Gist publishing configuration options
- [ ] 5.3 Document GITHUB_TOKEN environment variable requirement
