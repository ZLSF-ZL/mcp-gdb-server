"""MCP GDB Server — Remote GDB debugging via the Model Context Protocol."""

from fastmcp import FastMCP

from .manager import GDBManager
from .tools import register_tools

mcp = FastMCP("GDB-MCP-Server")
gdb = GDBManager()

register_tools(mcp, gdb)
