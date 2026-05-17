# AI Provider Configuration Guide

Ryushi uses [LiteLLM](https://docs.litellm.ai/) to support multiple AI providers. This guide shows how to configure Ryushi to work with different AI services.

## Supported Providers

Ryushi can work with any LiteLLM-supported provider, including:

- **OpenAI** (GPT-4, GPT-4o, GPT-3.5-turbo)
- **Mammouth AI** (Claude models)
- **Anthropic** (Claude)
- **Azure OpenAI**
- **Local LLMs** (Ollama, LM Studio, etc.)
- And [many more](https://docs.litellm.ai/docs/providers/)

## Configuration

Ryushi uses environment variables to configure the AI provider:

| Variable | Required | Description |
|----------|----------|-------------|
| `RYUSHI_AI_API_KEY` | Yes | API key for your provider |
| `RYUSHI_AI_MODEL` | No | Model identifier (default: `gpt-4.1-mini`) |
| `RYUSHI_AI_BASE_URL` | No | Custom API endpoint URL |

## Examples

### OpenAI (Default)

```bash
# .env file
RYUSHI_AI_API_KEY=sk-proj-...
RYUSHI_AI_MODEL=gpt-4.1-mini
# RYUSHI_AI_BASE_URL is optional (uses https://api.openai.com/v1 by default)
```

Or with docker-compose:

```yaml
environment:
  - RYUSHI_AI_API_KEY=sk-proj-...
  - RYUSHI_AI_MODEL=gpt-4.1-mini
```

### Mammouth AI

Mammouth AI provides access to Claude and other models through their API.

```bash
# .env file
RYUSHI_AI_API_KEY=your-mammouth-api-key
RYUSHI_AI_MODEL=mammouth-ai/claude-haiku-4-5
RYUSHI_AI_BASE_URL=https://api.mammouth.ai/v1
```

Or with docker-compose:

```yaml
environment:
  - RYUSHI_AI_API_KEY=${MAMMOUTH_API_KEY}
  - RYUSHI_AI_MODEL=mammouth-ai/claude-haiku-4-5
  - RYUSHI_AI_BASE_URL=https://api.mammouth.ai/v1
```

### Anthropic (Claude)

```bash
# .env file
RYUSHI_AI_API_KEY=sk-ant-...
RYUSHI_AI_MODEL=claude-3-haiku
# RYUSHI_AI_BASE_URL is optional for Anthropic
```

### Azure OpenAI

```bash
# .env file
RYUSHI_AI_API_KEY=your-azure-api-key
RYUSHI_AI_MODEL=gpt-4
RYUSHI_AI_BASE_URL=https://<your-resource>.openai.azure.com/
```

### Local LLMs (Ollama or LM Studio)

For local LLMs, you can use any OpenAI-compatible endpoint.

**Ollama:**

```bash
# Start Ollama with OpenAI compatibility
ollama serve

# .env file
RYUSHI_AI_API_KEY=anything
RYUSHI_AI_MODEL=ollama/llama2
RYUSHI_AI_BASE_URL=http://localhost:11434/v1
```

**LM Studio:**

```bash
# LM Studio runs on localhost by default

# .env file
RYUSHI_AI_API_KEY=anything
RYUSHI_AI_MODEL=local-model
RYUSHI_AI_BASE_URL=http://localhost:1234/v1
```

## Model Identifiers

The `RYUSHI_AI_MODEL` format depends on the provider:

- **OpenAI**: `gpt-4.1-mini`, `gpt-4o`, `gpt-3.5-turbo`
- **Mammouth**: `mammouth-ai/model-name` (e.g., `mammouth-ai/claude-haiku-4-5`)
- **Anthropic**: `claude-3-haiku`, `claude-3-sonnet`, `claude-3-opus`
- **Azure OpenAI**: Same as OpenAI (e.g., `gpt-4`)
- **Ollama**: `ollama/model-name` (e.g., `ollama/llama2`)
- **Other**: Check [LiteLLM documentation](https://docs.litellm.ai/docs/providers/)

## Docker Compose Example with Mammouth

Here's a complete `docker-compose.yaml` example using Mammouth AI:

```yaml
services:
  ryushi:
    image: ghcr.io/ryushi-app/ryushi:latest
    container_name: ryushi
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      # FreshRSS settings
      - FRESHRSS_URL=http://freshrss.local
      - FRESHRSS_USERNAME=your_username
      - FRESHRSS_PASSWORD=your_password
      
      # Mammouth AI settings
      - RYUSHI_AI_API_KEY=your-mammouth-api-key
      - RYUSHI_AI_MODEL=mammouth-ai/claude-haiku-4-5
      - RYUSHI_AI_BASE_URL=https://api.mammouth.ai/v1
    volumes:
      - ryushi-data:/data
      - ./config.yaml:/data/config.yaml:ro
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

volumes:
  ryushi-data:
    name: ryushi-data
```

## Debugging

To debug AI provider configuration issues:

1. **Check environment variables:**
   ```bash
   docker exec ryushi env | grep RYUSHI_AI
   ```

2. **Check logs:**
   ```bash
   docker logs ryushi
   ```

3. **Test the API key:**
   ```bash
   curl https://api.mammouth.ai/v1/models \
     -H "Authorization: Bearer your-api-key"
   ```

4. **Verify LiteLLM can reach the endpoint:**
   ```python
   import litellm
   litellm.api_base = "https://api.mammouth.ai/v1"
   litellm.api_key = "your-api-key"
   # Will raise an error if endpoint is unreachable
   ```

## Performance and Cost Considerations

When choosing a model and provider:

- **Smaller models** (haiku, mini): Faster, cheaper, suitable for digests
- **Larger models** (opus, sonnet): Better quality, slower, more expensive
- **Local models**: Free after setup, but require sufficient hardware

For RSS digest generation, we recommend:
- **Budget-conscious**: `gpt-4.1-mini`, `claude-haiku`, `ollama/mistral`
- **Quality-focused**: `claude-3-sonnet`, `gpt-4o`
- **Balanced**: `claude-3-haiku`, `gpt-4.1-mini`

## More Information

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [LiteLLM Supported Providers](https://docs.litellm.ai/docs/providers/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Mammouth AI Documentation](https://docs.mammouth.ai/)
- [Anthropic Claude Documentation](https://docs.anthropic.com/)
