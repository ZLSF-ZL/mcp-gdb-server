#!/usr/bin/env python3
"""MCP GDB Server — CLI entry point.

作为 mcp_gdb_server 包的独立入口，与 python -m mcp_gdb_server 功能相同。
不影响 mcp_gdb_server/ 目录中各文件的结构和后续修改。

Usage:
    python mcp_gdb_server.py
    python mcp_gdb_server.py 9000
    MCP_HOST=127.0.0.1 MCP_PORT=9000 python mcp_gdb_server.py
"""

import argparse
import os
import sys

from mcp_gdb_server import mcp

DEFAULT_PORT = 8000

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
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio"],
        default="sse",
        help="transport protocol (default: sse)",
    )
    args = parser.parse_args()

    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = args.port or int(os.environ.get("MCP_PORT", str(DEFAULT_PORT)))

    try:
        if args.transport == "stdio":
            mcp.run(transport="stdio")
        else:
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
