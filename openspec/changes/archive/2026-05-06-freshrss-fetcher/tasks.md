## 1. Project Setup

- [x] 1.1 Create `src/integrations/freshrss/` directory structure with `__init__.py`
- [x] 1.2 Create `src/integrations/freshrss/exceptions.py` with AuthError, FetchError, RateLimitError classes
- [x] 1.3 Ensure httpx and pydantic dependencies are available in project

## 2. Data Models

- [x] 2.1 Create `src/integrations/freshrss/models.py` with Pydantic `Article` model (id, title, url, author, published_at, teaser, category_id, feed_title)
- [x] 2.2 Create `Category` model in models.py (id, name)
- [x] 2.3 Add validation tests for Article and Category models

## 3. Core Client Implementation

- [x] 3.1 Create `src/integrations/freshrss/client.py` with `FreshRSSClient` class
- [x] 3.2 Implement `__init__` method that reads credentials from environment variables (FRESHRSS_URL, FRESHRSS_USERNAME, FRESHRSS_PASSWORD)
- [x] 3.3 Implement `_authenticate()` method using Google Reader API `/accounts/ClientLogin`
- [x] 3.4 Implement token refresh logic with 401 response handling

## 4. Category Fetching

- [x] 4.1 Implement `get_categories()` async method to fetch all feed categories
- [x] 4.2 Map FreshRSS category IDs to human-readable names
- [x] 4.3 Add error handling for network failures and missing categories

## 5. Article Fetching

- [x] 5.1 Implement `get_unread_items(category_id, max_articles)` async method
- [x] 5.2 Implement pagination logic using offset and limit parameters
- [x] 5.3 Extract article data: title, URL, author, published_at, teaser (first 500 chars)
- [x] 5.4 Return articles as Article model instances
- [x] 5.5 Enforce max_articles limit by returning only most recent articles

## 6. Error Handling and Logging

- [x] 6.1 Add logging for all API requests with status codes and URLs
- [x] 6.2 Handle 401 Unauthorized with automatic token refresh and retry
- [x] 6.3 Handle 429 Rate Limit errors (raise RateLimitError)
- [x] 6.4 Handle 5xx server errors (raise FetchError with details)
- [x] 6.5 Handle network timeouts gracefully (raise FetchError)
- [x] 6.6 Ensure credentials are never logged or exposed in error messages

## 7. API Exports

- [x] 7.1 Update `src/integrations/freshrss/__init__.py` to export FreshRSSClient, Article, Category, and exception classes
- [x] 7.2 Make the public API clean and intuitive for consumers

## 8. Testing

- [x] 8.1 Create unit tests for authentication (successful auth, invalid credentials, token refresh)
- [x] 8.2 Create unit tests for category fetching (successful fetch, empty categories, network errors)
- [x] 8.3 Create unit tests for article fetching (successful fetch, max_articles limit, pagination, empty results)
- [x] 8.4 Create unit tests for all exception types and error handling paths
- [x] 8.5 Create integration tests with FreshRSS test instance (if available)
- [x] 8.6 Test that articles are never marked as read (verify read-only behavior)

## 9. Documentation

- [x] 9.1 Add docstrings to all public methods and classes
- [x] 9.2 Add usage examples in module README or main documentation
- [x] 9.3 Document environment variables required (FRESHRSS_URL, FRESHRSS_USERNAME, FRESHRSS_PASSWORD)
- [x] 9.4 Document timeout values and configuration options

## 10. Quality and Deployment

- [x] 10.1 Run type checking (mypy or similar) on the new module
- [x] 10.2 Run linting (black, flake8, or project standard) on the new module
- [x] 10.3 Ensure all tests pass
- [x] 10.4 Code review and merge to main branch
