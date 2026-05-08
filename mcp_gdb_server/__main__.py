"""Entry point: python -m mcp_gdb_server"""

import os

from . import mcp

host = os.environ.get("MCP_HOST", "0.0.0.0")
port = int(os.environ.get("MCP_PORT", "8000"))

mcp.run(transport="sse", host=host, port=port)
