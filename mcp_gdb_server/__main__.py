"""Entry point: python -m mcp_gdb_server"""

from . import mcp

mcp.run(transport="sse", host="0.0.0.0", port=8000)
