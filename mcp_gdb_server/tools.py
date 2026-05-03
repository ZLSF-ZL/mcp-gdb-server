from __future__ import annotations

import subprocess

from fastmcp import FastMCP

from .manager import GDBManager, GDBNotRunningError


def register_tools(mcp: FastMCP, gdb: GDBManager) -> None:
    """Register all MCP tools with the given server instance."""

    @mcp.tool()
    def start_debugging(command: str = "gdb") -> str:
        """Start a new GDB debugging session. Supports local, attach-pid, and remote modes."""
        return gdb.start(command)

    @mcp.tool()
    def send_gdb_command(command: str, timeout: int = 10) -> str:
        """Send a command to GDB or stdin to the debugged program."""
        try:
            return gdb.execute(command, timeout)
        except GDBNotRunningError as e:
            return str(e)

    @mcp.tool()
    def interrupt() -> str:
        """Interrupt a running program (SIGINT/Ctrl+C)."""
        try:
            return gdb.interrupt()
        except GDBNotRunningError as e:
            return str(e)

    @mcp.tool()
    def stop_debugging() -> str:
        """Terminate the current GDB debugging session."""
        return gdb.stop()

    @mcp.tool()
    def run_shell_command(command: str, timeout: int = 10) -> str:
        """Execute a shell command on the host system."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = f"Command: {command}\nExit Code: {result.returncode}\n\n"
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            return output.strip()
        except subprocess.TimeoutExpired as e:
            output = f"Command: {command}\nError: Timed out after {timeout}s.\n"
            if e.stdout:
                output += f"\nPartial STDOUT:\n{e.stdout.decode('utf-8', errors='ignore')}\n"
            if e.stderr:
                output += f"\nPartial STDERR:\n{e.stderr.decode('utf-8', errors='ignore')}\n"
            return output
        except Exception as e:
            return f"Error executing shell command: {str(e)}"
