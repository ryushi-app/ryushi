"""Main entry point for Ryushi application.

This module provides the main application that combines:
- Feed server for serving Atom feeds
- Scheduler for automated digest generation
- Job API for manual triggering and monitoring
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from ryushi.feeds.server import create_app as create_feeds_app
from ryushi.scheduler import DigestScheduler, scheduler_router, set_scheduler

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_CONFIG_PATH = "config.yaml"
DEFAULT_JOBS_DB_PATH = "jobs.db"
DEFAULT_FEEDS_DB_PATH = "feeds.db"


def create_app(
    config_path: str | Path | None = None,
    jobs_db_path: str | Path | None = None,
    feeds_db_path: str | Path | None = None,
    base_url: str = "",
) -> FastAPI:
    """Create the main Ryushi FastAPI application.

    Args:
        config_path: Path to config.yaml (default: config.yaml).
        jobs_db_path: Path to jobs SQLite database (default: jobs.db).
        feeds_db_path: Path to feeds SQLite database (default: feeds.db).
        base_url: Base URL for feed links.

    Returns:
        Configured FastAPI application.
    """
    config_path = config_path or os.environ.get("RYUSHI_CONFIG", DEFAULT_CONFIG_PATH)
    jobs_db_path = jobs_db_path or os.environ.get("RYUSHI_JOBS_DB", DEFAULT_JOBS_DB_PATH)
    feeds_db_path = feeds_db_path or os.environ.get("RYUSHI_FEEDS_DB", DEFAULT_FEEDS_DB_PATH)
    base_url = base_url or os.environ.get("RYUSHI_BASE_URL", "")

    # Create scheduler
    scheduler = DigestScheduler.from_config_file(
        config_path=config_path,
        jobs_db_path=jobs_db_path,
        feeds_db_path=feeds_db_path,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan manager."""
        # Startup
        logger.info("Starting Ryushi application...")
        await scheduler.start()
        set_scheduler(scheduler)
        logger.info("Scheduler started with %d jobs", len(scheduler.get_category_slugs()))
        yield
        # Shutdown
        logger.info("Shutting down Ryushi application...")
        await scheduler.stop()
        logger.info("Shutdown complete")

    # Create main app
    app = FastAPI(
        title="Ryushi",
        description="AI-powered RSS digest service",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Create feeds sub-application
    feeds_app = create_feeds_app(db_path=feeds_db_path, base_url=base_url)

    # Mount feeds routes
    app.mount("/feeds", feeds_app, name="feeds")

    # Include scheduler routes
    app.include_router(scheduler_router)

    # Health check that combines both services
    @app.get("/health")
    async def health_check():
        """Combined health check endpoint."""
        return {
            "status": "ok",
            "scheduler": {
                "running": scheduler._running,
                "jobs_count": len(scheduler.get_category_slugs()),
            },
        }

    return app


def run():
    """Run the Ryushi application."""
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    host = os.environ.get("RYUSHI_HOST", "0.0.0.0")
    port = int(os.environ.get("RYUSHI_PORT", "8000"))

    print(f"Starting Ryushi on {host}:{port}")
    print("Endpoints:")
    print("  GET  /health                     Combined health check")
    print("  GET  /jobs                       List scheduled jobs")
    print("  GET  /jobs/{slug}/status         Get job status")
    print("  POST /jobs/{slug}/run            Trigger job manually")
    print("  GET  /jobs/{slug}/history        Get job history")
    print("  GET  /feeds/{slug}/atom.xml      Get Atom feed")
    print("  GET  /feeds                      List available feeds")
    print()

    uvicorn.run(
        "ryushi.main:create_app",
        host=host,
        port=port,
        reload=False,
        factory=True,
    )


if __name__ == "__main__":
    run()
