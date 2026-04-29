## 1. Project Setup

- [ ] 1.1 Create `src/integrations/freshrss/` directory structure with `__init__.py`
- [ ] 1.2 Create `src/integrations/freshrss/exceptions.py` with AuthError, FetchError, RateLimitError classes
- [ ] 1.3 Ensure httpx and pydantic dependencies are available in project

## 2. Data Models

- [ ] 2.1 Create `src/integrations/freshrss/models.py` with Pydantic `Article` model (id, title, url, author, published_at, teaser, category_id, feed_title)
- [ ] 2.2 Create `Category` model in models.py (id, name)
- [ ] 2.3 Add validation tests for Article and Category models

## 3. Core Client Implementation

- [ ] 3.1 Create `src/integrations/freshrss/client.py` with `FreshRSSClient` class
- [ ] 3.2 Implement `__init__` method that reads credentials from environment variables (FRESHRSS_URL, FRESHRSS_USERNAME, FRESHRSS_PASSWORD)
- [ ] 3.3 Implement `_authenticate()` method using Google Reader API `/accounts/ClientLogin`
- [ ] 3.4 Implement token refresh logic with 401 response handling

## 4. Category Fetching

- [ ] 4.1 Implement `get_categories()` async method to fetch all feed categories
- [ ] 4.2 Map FreshRSS category IDs to human-readable names
- [ ] 4.3 Add error handling for network failures and missing categories

## 5. Article Fetching

- [ ] 5.1 Implement `get_unread_items(category_id, max_articles)` async method
- [ ] 5.2 Implement pagination logic using offset and limit parameters
- [ ] 5.3 Extract article data: title, URL, author, published_at, teaser (first 500 chars)
- [ ] 5.4 Return articles as Article model instances
- [ ] 5.5 Enforce max_articles limit by returning only most recent articles

## 6. Error Handling and Logging

- [ ] 6.1 Add logging for all API requests with status codes and URLs
- [ ] 6.2 Handle 401 Unauthorized with automatic token refresh and retry
- [ ] 6.3 Handle 429 Rate Limit errors (raise RateLimitError)
- [ ] 6.4 Handle 5xx server errors (raise FetchError with details)
- [ ] 6.5 Handle network timeouts gracefully (raise FetchError)
- [ ] 6.6 Ensure credentials are never logged or exposed in error messages

## 7. API Exports

- [ ] 7.1 Update `src/integrations/freshrss/__init__.py` to export FreshRSSClient, Article, Category, and exception classes
- [ ] 7.2 Make the public API clean and intuitive for consumers

## 8. Testing

- [ ] 8.1 Create unit tests for authentication (successful auth, invalid credentials, token refresh)
- [ ] 8.2 Create unit tests for category fetching (successful fetch, empty categories, network errors)
- [ ] 8.3 Create unit tests for article fetching (successful fetch, max_articles limit, pagination, empty results)
- [ ] 8.4 Create unit tests for all exception types and error handling paths
- [ ] 8.5 Create integration tests with FreshRSS test instance (if available)
- [ ] 8.6 Test that articles are never marked as read (verify read-only behavior)

## 9. Documentation

- [ ] 9.1 Add docstrings to all public methods and classes
- [ ] 9.2 Add usage examples in module README or main documentation
- [ ] 9.3 Document environment variables required (FRESHRSS_URL, FRESHRSS_USERNAME, FRESHRSS_PASSWORD)
- [ ] 9.4 Document timeout values and configuration options

## 10. Quality and Deployment

- [ ] 10.1 Run type checking (mypy or similar) on the new module
- [ ] 10.2 Run linting (black, flake8, or project standard) on the new module
- [ ] 10.3 Ensure all tests pass
- [ ] 10.4 Code review and merge to main branch
