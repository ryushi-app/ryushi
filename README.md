# Ryushi 🎯

**AI-powered RSS digest service** - Automatically generate concise summaries of your RSS feeds using any AI provider.

[![Tests](https://img.shields.io/badge/tests-243%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.13+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](Dockerfile)

## What is Ryushi?

Ryushi is an intelligent RSS feed aggregator that uses AI to summarize articles from your FreshRSS feeds. Instead of manually reading dozens of articles, Ryushi automatically generates concise digests on a schedule you define. Perfect for staying informed without information overload.

### Key Features

- 🤖 **AI-Powered Summarization** - Uses any LiteLLM-supported AI provider (OpenAI, Mammouth, Claude, local LMs, etc.)
- 📅 **Flexible Scheduling** - Define digest generation schedules with cron expressions
- 🌍 **Multi-Provider Support** - OpenAI, Mammouth AI, Anthropic, Azure, local LMs, and more
- 🔗 **REST API** - Manual job triggering, status monitoring, and job history
- 📡 **Atom Feeds** - Generated digests are served as standard Atom XML feeds
- 🐳 **Docker Ready** - Fully containerized with docker-compose support
- 📊 **12-Factor App** - Configuration via environment variables
- 🧪 **Well-Tested** - 243 comprehensive tests
- 📚 **Thoroughly Documented** - Complete API docs and setup guides

## Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- Or: Python 3.13+, SQLite3
- FreshRSS instance (for feed management)
- AI provider account (OpenAI, Mammouth, etc.)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ryushi-app/ryushi.git
   cd ryushi
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   ```bash
   FRESHRSS_URL=https://your-freshrss.example.com
   FRESHRSS_USERNAME=your_username
   FRESHRSS_PASSWORD=your_password
   RYUSHI_AI_API_KEY=sk-...  # or your Mammouth/Claude key
   RYUSHI_AI_MODEL=gpt-4.1-mini  # or your preferred model
   ```

3. **Configure digest schedules**
   ```bash
   cp config.yaml.example config.yaml
   ```
   
   Edit `config.yaml` to define your digest categories and schedules:
   ```yaml
   categories:
     technology:
       schedule: "0 6 * * *"      # Daily at 6:00 AM
     
     science:
       schedule: "0 8 * * 1"      # Mondays at 8:00 AM
   ```

4. **Start with Docker**
   ```bash
   docker-compose up -d
   ```

5. **Access the application**
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # List available feeds
   curl http://localhost:8000/feeds
   
   # List scheduled jobs
   curl http://localhost:8000/jobs
   ```

## 📊 API Endpoints

### Health Check
```bash
GET /health
```
Health status with scheduler information.

### Jobs API
```bash
GET /jobs                          # List all scheduled jobs
GET /jobs/{slug}/status            # Get job status
POST /jobs/{slug}/run              # Manually trigger a job
GET /jobs/{slug}/history?limit=20  # Get job run history
```

### Feeds API
```bash
GET /feeds                         # List all available feeds
GET /feeds/{slug}/atom.xml         # Get Atom feed for a category
```

See [API_ENDPOINTS.md](API_ENDPOINTS.md) for complete documentation with examples.

## 🔧 Configuration

### Environment Variables

**Required:**
- `FRESHRSS_URL` - Your FreshRSS instance URL
- `FRESHRSS_USERNAME` - FreshRSS username
- `FRESHRSS_PASSWORD` - FreshRSS password
- `RYUSHI_AI_API_KEY` - API key for your AI provider

**Optional:**
- `RYUSHI_AI_MODEL` - AI model (default: `gpt-4.1-mini`)
- `RYUSHI_AI_BASE_URL` - Custom API endpoint (for Mammouth, Azure, local LMs)
- `RYUSHI_PORT` - Server port (default: 8000)
- `RYUSHI_BASE_URL` - External URL for feed links

See [CONFIGURATION.md](CONFIGURATION.md) for detailed setup instructions.

### AI Provider Configuration

Ryushi supports any LiteLLM-compatible AI provider:

#### OpenAI (Default)
```bash
RYUSHI_AI_API_KEY=sk-...
RYUSHI_AI_MODEL=gpt-4.1-mini
```

#### Mammouth AI
```bash
RYUSHI_AI_API_KEY=your-mammouth-key
RYUSHI_AI_MODEL=mammouth-ai/claude-haiku-4-5
RYUSHI_AI_BASE_URL=https://api.mammouth.ai/v1
```

#### Anthropic Claude
```bash
RYUSHI_AI_API_KEY=sk-ant-...
RYUSHI_AI_MODEL=claude-3-haiku
```

#### Local LM Studio
```bash
RYUSHI_AI_API_KEY=anything
RYUSHI_AI_MODEL=local-model
RYUSHI_AI_BASE_URL=http://localhost:1234/v1
```

See [AI_PROVIDERS.md](AI_PROVIDERS.md) for more provider configurations.

## 📚 Documentation

- **[CONFIGURATION.md](CONFIGURATION.md)** - Complete setup and configuration guide
- **[API_ENDPOINTS.md](API_ENDPOINTS.md)** - REST API documentation with examples
- **[AI_PROVIDERS.md](AI_PROVIDERS.md)** - AI provider setup instructions
- **[docker-compose.yaml](docker-compose.yaml)** - Docker deployment configuration

## 🎯 Use Cases

- **Daily News Digests** - Get AI-summarized news from your feeds every morning
- **Research Aggregation** - Summarize articles from multiple research feeds
- **Content Curation** - Create curated digests of industry-specific news
- **Knowledge Base** - Build a searchable archive of digested articles
- **Email Newsletters** - Feed digests into your email system

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Ryushi Application                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌────────────────┐                   │
│  │  Scheduler   │──────│  Job Executor  │                   │
│  │  (APScheduler)      │  (APScheduler) │                   │
│  └──────────────┘      └────────────────┘                   │
│         │                       │                             │
│         v                       v                             │
│  ┌─────────────────────────────────────┐                     │
│  │    FreshRSS Integration             │                     │
│  │    (Fetch articles by category)     │                     │
│  └─────────────────────────────────────┘                     │
│         │                       │                             │
│         v                       v                             │
│  ┌──────────────────────────────────────┐                    │
│  │    Digest Engine (LiteLLM)           │                    │
│  │    (Summarize articles with AI)      │                    │
│  └──────────────────────────────────────┘                    │
│         │                       │                             │
│         v                       v                             │
│  ┌──────────────┐      ┌───────────────┐                     │
│  │ Feed Store   │      │ Job Store     │                     │
│  │ (SQLite)     │      │ (SQLite)      │                     │
│  └──────────────┘      └───────────────┘                     │
│         │                                                      │
│         v                                                      │
│  ┌──────────────────────────────────────┐                    │
│  │    Feed Server / REST API            │                    │
│  │    (FastAPI)                         │                    │
│  └──────────────────────────────────────┘                    │
│         │                                                      │
│         ├─ GET /feeds (List feeds)                            │
│         ├─ GET /feeds/{slug}/atom.xml (Atom feed)            │
│         ├─ GET /jobs (List jobs)                             │
│         ├─ POST /jobs/{slug}/run (Trigger job)              │
│         └─ GET /health (Health check)                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 🔒 Security

- **No built-in authentication** - Run behind a reverse proxy (nginx, Caddy) for external access
- **Secrets via environment** - Keep API keys in environment variables, not in code
- **HTTPS recommended** - Use a reverse proxy to handle HTTPS
- **Network isolation** - Can run in private networks only accessible to trusted services

## 📦 Deployment

### Docker (Recommended)

```bash
docker-compose up -d
```

See [docker-compose.yaml](docker-compose.yaml) for configuration options.

### Manual Installation

```bash
# Install dependencies
uv sync --frozen

# Run the application
uv run ryushi
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=ryushi

# Run specific test file
uv run pytest tests/digest/test_engine.py
```

**Test Coverage:** 243 tests covering all major components

## 🔍 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

Returns:
```json
{
  "status": "ok",
  "scheduler": {
    "running": true,
    "jobs_count": 3
  }
}
```

### Job Status
```bash
curl http://localhost:8000/jobs/technology/status
```

### View Logs
```bash
docker logs ryushi
```

## 🚀 Performance

- **Scheduler:** Single-threaded, jobs run sequentially
- **Database:** SQLite (suitable for small to medium deployments)
- **Memory:** Minimal (~100MB with scheduler)
- **CPU:** Low (only active during digest generation)

## 📝 Known Limitations

- **Single-threaded scheduling** - Jobs run sequentially, not in parallel
- **SQLite backend** - Suitable for small to medium deployments (~millions of entries)
- **No built-in authentication** - Add authentication via reverse proxy
- **No rate limiting** - Implement via reverse proxy if needed

## 🤝 Contributing

Contributions are welcome! Please feel free to:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install dev dependencies
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Format code
uv run ruff format .
```

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FreshRSS](https://freshrss.org/) - RSS feed aggregation
- [LiteLLM](https://docs.litellm.ai/) - Unified AI API interface
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [APScheduler](https://apscheduler.readthedocs.io/) - Advanced job scheduling

## 📞 Support

For questions, issues, and feature requests, please use [GitHub Issues](https://github.com/ryushi-app/ryushi/issues).

---

**Made with ❤️ to help you stay informed without information overload.**

[⬆ back to top](#ryushi-)
