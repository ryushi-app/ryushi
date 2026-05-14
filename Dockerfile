# Ryushi - AI-powered RSS digest service
# Multi-stage build for minimal image size

# Stage 1: Build environment with uv
FROM python:3.13-slim AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency files and source code
COPY pyproject.toml uv.lock ./
COPY ryushi/ ./ryushi/

# Install the package with dependencies (production only, no dev deps)
# Creates a virtual environment at .venv
RUN uv sync --frozen --no-dev

# Stage 2: Runtime image
FROM python:3.13-slim AS runtime

WORKDIR /app

# Copy virtual environment from builder (includes installed ryushi package)
COPY --from=builder /app/.venv /app/.venv

# Create data directory for databases and config
RUN mkdir -p /data

# Environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV RYUSHI_CONFIG=/data/config.yaml
ENV RYUSHI_JOBS_DB=/data/jobs.db
ENV RYUSHI_FEEDS_DB=/data/feeds.db
ENV RYUSHI_HOST=0.0.0.0
ENV RYUSHI_PORT=8000

# Expose the default port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application using the installed entry point
CMD ["ryushi"]
