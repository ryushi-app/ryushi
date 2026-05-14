"""CLI entry point for the feed server.

This module provides a command-line interface for running the
Ryushi feed server using uvicorn.

Usage:
    ryushi-feeds                    # Run with defaults
    ryushi-feeds --port 8080        # Custom port
    ryushi-feeds --db feeds.db      # Custom database path
    ryushi-feeds --base-url https://example.com  # Set base URL

Environment variables:
    RYUSHI_FEEDS_PORT: Server port (default: 8000)
    RYUSHI_FEEDS_HOST: Server host (default: 0.0.0.0)
    RYUSHI_FEEDS_DB: Database path (default: feeds.db)
    RYUSHI_FEEDS_BASE_URL: Base URL for feed links
"""

import argparse
import os
import sys


def main() -> None:
    """Run the feed server."""
    parser = argparse.ArgumentParser(
        description="Ryushi Feed Server - Serves AI-generated digest feeds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ryushi-feeds                          Run on default port 8000
  ryushi-feeds --port 8080              Run on port 8080
  ryushi-feeds --db /data/feeds.db      Use custom database path
  ryushi-feeds --reload                 Enable auto-reload for development

Environment variables:
  RYUSHI_FEEDS_PORT      Server port (default: 8000)
  RYUSHI_FEEDS_HOST      Server host (default: 0.0.0.0)
  RYUSHI_FEEDS_DB        Database path (default: feeds.db)
  RYUSHI_FEEDS_BASE_URL  Base URL for feed links
        """,
    )

    parser.add_argument(
        "--host",
        default=os.environ.get("RYUSHI_FEEDS_HOST", "0.0.0.0"),
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("RYUSHI_FEEDS_PORT", "8000")),
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--db",
        default=os.environ.get("RYUSHI_FEEDS_DB", "feeds.db"),
        help="Path to SQLite database (default: feeds.db)",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("RYUSHI_FEEDS_BASE_URL", ""),
        help="Base URL for feed links (e.g., https://example.com)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level (default: info)",
    )

    args = parser.parse_args()

    # Set environment variables for the server to pick up
    os.environ["RYUSHI_FEEDS_DB"] = args.db
    os.environ["RYUSHI_FEEDS_BASE_URL"] = args.base_url

    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is not installed.", file=sys.stderr)
        print("Install it with: pip install uvicorn[standard]", file=sys.stderr)
        sys.exit(1)

    print(f"Starting Ryushi Feed Server on {args.host}:{args.port}")
    print(f"Database: {args.db}")
    if args.base_url:
        print(f"Base URL: {args.base_url}")
    print()
    print("Endpoints:")
    print("  GET /health                     Health check")
    print("  GET /feeds                      List available feeds")
    print("  GET /feeds/{slug}/atom.xml      Get Atom feed")
    print()

    uvicorn.run(
        "ryushi.feeds.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        factory=False,
    )


if __name__ == "__main__":
    main()
