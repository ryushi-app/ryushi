## 1. Category Configuration Extension

- [x] 1.1 Add `gist_enabled: bool = False` and `gist_id: str | None = None` fields to `CategoryConfig` in `ryushi/scheduler/models.py`
- [x] 1.2 Update `parse_config()` in `ryushi/scheduler/config.py` to parse gist_enabled and gist_id from YAML
- [x] 1.3 Add unit tests for CategoryConfig with Gist fields (valid configs, defaults, missing gist_id warning)

## 2. GitHub Gist Publisher Client

- [x] 2.1 Create `ryushi/integrations/github/` package with `__init__.py`
- [x] 2.2 Create `GistPublisher` class in `ryushi/integrations/github/client.py` with token from `GITHUB_TOKEN` env var
- [x] 2.3 Implement `is_configured` property to check if token is available
- [x] 2.4 Implement `publish(gist_id: str, filename: str, content: str)` method using GitHub REST API v3
- [x] 2.5 Add graceful error handling (log warnings, don't raise exceptions)
- [x] 2.6 Create `GistPublishError` exception class in `ryushi/integrations/github/exceptions.py`
- [x] 2.7 Add unit tests for GistPublisher (successful publish, missing token, API errors)

## 3. Job Execution Integration

- [x] 3.1 Update `JobExecutor.execute_job()` signature to accept `gist_enabled` and `gist_id` parameters
- [x] 3.2 Update `JobExecutor._fetch_and_process()` to accept and use Gist configuration
- [x] 3.3 After successful feed storage, generate Atom XML using FeedGenerator
- [x] 3.4 Call GistPublisher.publish() if gist_enabled is True and gist_id is provided
- [x] 3.5 Log appropriate messages for Gist publish success/failure
- [x] 3.6 Add unit tests for executor with Gist publishing (enabled, disabled, failure scenarios)

## 4. Scheduler Integration

- [x] 4.1 Update scheduler `_run_job()` to extract gist_enabled and gist_id from category config
- [x] 4.2 Pass Gist configuration to executor.execute_job()
- [x] 4.3 Add integration test for end-to-end Gist publishing flow

## 5. Configuration Documentation

- [x] 5.1 Update `config.yaml.example` with gist_enabled and gist_id fields and examples
- [x] 5.2 Add comments explaining Gist publishing configuration options
- [x] 5.3 Document GITHUB_TOKEN environment variable requirement
