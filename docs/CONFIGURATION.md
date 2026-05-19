# Ryushi Configuration Guide

Ryushi uses a **hybrid configuration approach** that follows the 12-factor app methodology:

- **Scheduler configuration** (categories & schedules) → `config.yaml`
- **External services & secrets** (FreshRSS, AI provider) → Environment variables (`.env`)

This separation allows flexible deployment across different environments without code changes.

## Quick Start

### 1. Set Up Environment Variables

Copy the example file and configure your settings:

```bash
cp .env.example .env
```

Then edit `.env` with your values:

```bash
# FreshRSS connection (required)
FRESHRSS_URL=http://freshrss.local
FRESHRSS_USERNAME=your_username
FRESHRSS_PASSWORD=your_password

# AI provider (required)
RYUSHI_AI_API_KEY=your-api-key

# AI provider settings (optional)
RYUSHI_AI_MODEL=gpt-4.1-mini              # default
RYUSHI_AI_BASE_URL=https://api.openai.com/v1  # optional
```

### 2. Configure Scheduler Categories

Copy the example and set up your digest schedules:

```bash
cp config.yaml.example config.yaml
```

Then edit `config.yaml` with your categories:

```yaml
categories:
  technology:
    schedule: "0 6 * * *"    # Daily at 6:00 AM

  software-engineering:
    schedule: "0 7 * * *"    # Daily at 7:00 AM

  science:
    schedule: "0 8 * * 1"    # Mondays at 8:00 AM
```

### 3. Start the Application

```bash
docker compose up -d
```

## Configuration Files

### `config.yaml` - Scheduler Configuration

**Purpose:** Define digest generation schedules per FreshRSS category

**Location:** Root directory (`config.yaml`)

**Format:**
```yaml
categories:
  {category-slug}:
    schedule: "{cron-expression}"
```

**Requirements:**
- Category slugs must match your FreshRSS category names (converted to lowercase with spaces replaced by hyphens)
- Schedules use standard 5-field cron expressions

**Example:**
```yaml
categories:
  technology:
    schedule: "0 6 * * *"        # Every day at 6:00 AM
  
  software-engineering:
    schedule: "0 7 * * 1-5"      # Weekdays at 7:00 AM
  
  news:
    schedule: "0 6,18 * * *"     # Every day at 6:00 AM and 6:00 PM
```

**Cron Expression Format:**
```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sunday=0)
│ │ │ │ │
* * * * *
```

**Cron Examples:**
- `0 6 * * *` - Every day at 6:00 AM
- `0 */6 * * *` - Every 6 hours
- `0 8 * * 1` - Every Monday at 8:00 AM
- `0 6,18 * * *` - Daily at 6:00 AM and 6:00 PM
- `*/30 * * * *` - Every 30 minutes
- `0 0 1 * *` - First day of each month at midnight

### `.env` - Environment Variables

**Purpose:** Configure external services, secrets, and runtime settings

**Location:** Root directory (`.env` or via docker-compose)

**Method:** Environment variables are the 12-factor app standard for configuration that varies per environment

#### Required Variables

**FreshRSS Configuration:**
```bash
FRESHRSS_URL=http://freshrss.local      # Base URL of your FreshRSS instance
FRESHRSS_USERNAME=your_username          # FreshRSS username
FRESHRSS_PASSWORD=your_password          # FreshRSS password
```

**AI Provider:**
```bash
RYUSHI_AI_API_KEY=your-api-key          # API key for your AI provider
```

#### Optional Variables

**AI Model Configuration:**
```bash
# Model to use (default: gpt-4.1-mini)
RYUSHI_AI_MODEL=gpt-4.1-mini

# API endpoint (default: OpenAI)
# Leave empty to use OpenAI, or set to custom provider
RYUSHI_AI_BASE_URL=https://api.mammouth.ai/v1

# Supported models:
# OpenAI: gpt-4.1-mini, gpt-4o, gpt-3.5-turbo
# Mammouth: mammouth-ai/claude-haiku-4-5
# Anthropic: claude-3-haiku, claude-3-sonnet
# Local LM: ollama/llama2, ollama/mistral
```

**Server Configuration:**
```bash
# External port (default: 8000)
RYUSHI_PORT=8000

# Base URL for feed links in browser (optional)
# Use if accessing from remote domain
RYUSHI_BASE_URL=https://ryushi.example.com
```

**Advanced Configuration:**
```bash
# Path to config.yaml (default: config.yaml)
RYUSHI_CONFIG=/data/config.yaml

# Database paths (default: jobs.db, feeds.db)
RYUSHI_JOBS_DB=/data/jobs.db
RYUSHI_FEEDS_DB=/data/feeds.db

# Server binding (default: 0.0.0.0)
RYUSHI_HOST=0.0.0.0
```

## Common Configurations

### Simple Setup (OpenAI)

**.env:**
```bash
FRESHRSS_URL=http://freshrss.local
FRESHRSS_USERNAME=myuser
FRESHRSS_PASSWORD=mypass
RYUSHI_AI_API_KEY=sk-proj-...
RYUSHI_AI_MODEL=gpt-4.1-mini
```

**config.yaml:**
```yaml
categories:
  technology:
    schedule: "0 6 * * *"
```

### Using Mammouth AI

**.env:**
```bash
FRESHRSS_URL=http://freshrss.local
FRESHRSS_USERNAME=myuser
FRESHRSS_PASSWORD=mypass
RYUSHI_AI_API_KEY=your-mammouth-key
RYUSHI_AI_MODEL=mammouth-ai/claude-haiku-4-5
RYUSHI_AI_BASE_URL=https://api.mammouth.ai/v1
```

### Using Local LM Studio

**.env:**
```bash
FRESHRSS_URL=http://freshrss.local
FRESHRSS_USERNAME=myuser
FRESHRSS_PASSWORD=mypass
RYUSHI_AI_API_KEY=anything
RYUSHI_AI_MODEL=local-model
RYUSHI_AI_BASE_URL=http://localhost:1234/v1
```

### Multiple Categories with Different Schedules

**config.yaml:**
```yaml
categories:
  technology:
    schedule: "0 6 * * *"        # Daily at 6 AM

  science:
    schedule: "0 8 * * 1"        # Mondays at 8 AM

  news:
    schedule: "0 */6 * * *"      # Every 6 hours

  books:
    schedule: "0 10 * * 0"       # Sundays at 10 AM
```

## Category Name to Slug Conversion

Your FreshRSS category names are automatically converted to slugs (lowercase with hyphens):

| FreshRSS Category | Config Slug | Cron Entry |
|-------------------|-------------|-----------|
| Technology | technology | `technology:` |
| Software Engineering | software-engineering | `software-engineering:` |
| AI & Machine Learning | ai-machine-learning | `ai-machine-learning:` |
| News (breaking) | news-breaking | `news-breaking:` |

## Docker Compose Configuration

When using docker-compose, environment variables can be set in two ways:

### Option 1: Using `.env` file

Create `.env` in the same directory as `docker-compose.yaml`:

```bash
FRESHRSS_URL=http://freshrss.local
FRESHRSS_USERNAME=myuser
FRESHRSS_PASSWORD=mypass
RYUSHI_AI_API_KEY=sk-proj-...
RYUSHI_AI_MODEL=gpt-4.1-mini
RYUSHI_PORT=8000
```

Docker compose automatically loads from `.env`.

### Option 2: Direct in docker-compose.yaml

```yaml
environment:
  - FRESHRSS_URL=http://freshrss.local
  - FRESHRSS_USERNAME=myuser
  - FRESHRSS_PASSWORD=mypass
  - RYUSHI_AI_API_KEY=sk-proj-...
  - RYUSHI_AI_MODEL=gpt-4.1-mini
  - RYUSHI_PORT=8000
```

## Environment Variable Priority

Environment variables take precedence when both YAML and env vars are available:

1. Environment variables (highest priority)
2. Hardcoded defaults in code
3. Config file values (if applicable)

Example: If you set `RYUSHI_AI_MODEL=gpt-4o` in `.env`, it will override any default.

## Validation & Errors

### Missing Required Variables

If required variables are not set, you'll see errors at startup:

```
AuthError: Missing required credentials: FRESHRSS_URL, FRESHRSS_USERNAME, FRESHRSS_PASSWORD
```

**Solution:** Set all required variables in `.env` or docker-compose

### Invalid Cron Expressions

```
Invalid cron expression '0 6' for category 'technology', skipping
```

**Solution:** Use 5-field cron format: `minute hour day month day-of-week`

### Category Not Found

```
Category 'invalid-slug' not found in FreshRSS
```

**Solution:** Ensure category slug matches your FreshRSS category (converted to lowercase with hyphens)

## Configuration Best Practices

1. **Use `.env` for secrets** - Never commit API keys to version control
2. **Use `config.yaml` for schedules** - These rarely change and are deployment-independent
3. **Environment-specific configs** - Use different `.env` files per environment (dev, staging, prod)
4. **Document your categories** - Add comments explaining what each category contains
5. **Start with daily schedules** - Once working, adjust frequency as needed

## Examples

See the following files for more examples:

- `config.yaml.example` - Scheduler category examples
- `.env.example` - All available environment variables
- `AI_PROVIDERS.md` - Configuration for different AI providers
- `DOCKER_COMPOSE.md` - Docker deployment configuration
