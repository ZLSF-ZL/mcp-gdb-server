"""Entry point for compiled binary (PyInstaller).

Usage:
    ./mcp_gdb_server              # default port 8000
    ./mcp_gdb_server 9000         # custom port
"""

import argparse
import os
import sys

from mcp_gdb_server import mcp

DEFAULT_PORT = 8000

# ── Logging config ──────────────────────────────────────────────────
# Suppress uvicorn.error traceback noise on Ctrl+C shutdown
# (KeyboardInterrupt / CancelledError during asyncio shutdown).
_LOG_CONFIG: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": ["default"], "level": "WARNING", "propagate": False},
        "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP GDB Server")
    parser.add_argument(
        "port",
        nargs="?",
        type=int,
        default=None,
        help=f"listen port (default: {DEFAULT_PORT}, env: MCP_PORT)",
    )
    args = parser.parse_args()

    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = args.port or int(os.environ.get("MCP_PORT", DEFAULT_PORT))

    try:
        mcp.run(
            transport="sse",
            host=host,
            port=port,
            uvicorn_config={"log_config": _LOG_CONFIG},
        )
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
