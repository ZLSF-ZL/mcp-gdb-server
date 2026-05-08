from __future__ import annotations

from fastmcp import FastMCP

from .manager import GDBManager, GDBNotRunningError


def _wrap(gdb_fn):
    """Decorator: catch GDBNotRunningError and return uniform error dict."""
    import functools

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except GDBNotRunningError as e:
                return {"status": "error", "data": str(e), "raw": ""}

        return wrapper

    return decorator(gdb_fn)


def register_tools(mcp: FastMCP, gdb: GDBManager) -> None:
    """Register all MCP tools with the given server instance."""

    # ── lifecycle ────────────────────────────────────────────────────

    @mcp.tool()
    @_wrap
    def start_debugging(command: str = "gdb") -> str:
        """Start a new GDB debugging session. Supports local, attach-pid, and remote modes."""
        return gdb.start(command)

    @mcp.tool()
    @_wrap
    def stop_debugging() -> str:
        """Terminate the current GDB debugging session."""
        return gdb.stop()

    @mcp.tool()
    @_wrap
    def interrupt() -> str:
        """Interrupt a running program (SIGINT/Ctrl+C)."""
        return gdb.interrupt()

    @mcp.tool()
    @_wrap
    def send_gdb_command(command: str, timeout: int = 10) -> str:
        """Send a raw command to GDB or stdin to the debugged program."""
        return gdb.execute(command, timeout)

    # ── breakpoints ──────────────────────────────────────────────────

    @mcp.tool()
    @_wrap
    def set_breakpoint(location: str, condition: str = "",
                       temporary: bool = False) -> dict:
        """Set a breakpoint at the given location.

        Args:
            location: function name, file:line, or *address.
            condition: optional gdb condition expression.
            temporary: if True, set a one-shot breakpoint (tbreak).
        """
        return gdb.set_breakpoint(location, condition, temporary)

    @mcp.tool()
    @_wrap
    def delete_breakpoint(number: int) -> dict:
        """Delete a breakpoint or watchpoint by number."""
        return gdb.delete_breakpoint(number)

    @mcp.tool()
    @_wrap
    def list_breakpoints() -> dict:
        """List all breakpoints, watchpoints, and catchpoints."""
        return gdb.list_breakpoints()

    @mcp.tool()
    @_wrap
    def enable_breakpoint(number: int) -> dict:
        """Enable a breakpoint by number."""
        return gdb.enable_breakpoint(number)

    @mcp.tool()
    @_wrap
    def disable_breakpoint(number: int) -> dict:
        """Disable a breakpoint by number."""
        return gdb.disable_breakpoint(number)

    # ── execution control ────────────────────────────────────────────

    @mcp.tool()
    @_wrap
    def step_into() -> dict:
        """Step one machine instruction (stepi)."""
        return gdb.step_into()

    @mcp.tool()
    @_wrap
    def step_over() -> dict:
        """Step one source line, stepping over calls (next)."""
        return gdb.step_over()

    @mcp.tool()
    @_wrap
    def step_out() -> dict:
        """Execute until the current function returns (finish)."""
        return gdb.step_out()

    @mcp.tool()
    @_wrap
    def continue_execution() -> dict:
        """Continue execution (continue)."""
        return gdb.continue_execution()

    # ── register inspection ──────────────────────────────────────────

    @mcp.tool()
    @_wrap
    def read_registers(registers: str = "") -> dict:
        """Read current register values.

        Args:
            registers: space-separated register names (e.g. "rax rsp rip").
                       Empty = all general-purpose registers.
        """
        reg_list = registers.split() if registers.strip() else None
        return gdb.read_registers(reg_list)

    # ── backtrace ────────────────────────────────────────────────────

    @mcp.tool()
    @_wrap
    def backtrace(depth: int = 20, detailed: bool = False) -> dict:
        """Print backtrace of all stack frames.

        Args:
            depth: max number of frames to show.
            detailed: include local variables per frame (bt full).
        """
        return gdb.backtrace(depth, detailed)

    # ── memory ───────────────────────────────────────────────────────

    @mcp.tool()
    @_wrap
    def read_memory(address: str = "$rip", count: int = 8,
                    size: int = 8, fmt: str = "x") -> dict:
        """Read memory at the given address.

        Args:
            address: address expression (e.g. "$rsp", "0x7fff...").
            count: number of elements to read.
            size: element size — 1 (byte), 2 (halfword), 4 (word), 8 (giant).
            fmt: output format — x (hex), d (decimal), s (string), i (instr).
        """
        return gdb.read_memory(address, count, size, fmt)

    @mcp.tool()
    @_wrap
    def search_memory(pattern: str, start: str = "$rip",
                      end: str = "$rip+0x1000", size: int = 8) -> dict:
        """Search a memory range for a value (GDB find).

        Args:
            pattern: hex value or string to search for (e.g. "0xdeadbeef").
            start: start address expression.
            end: end address expression.
            size: element size in bytes — 1, 2, 4, or 8.
        """
        return gdb.search_memory(pattern, start, end, size)

    # ── disassembly ──────────────────────────────────────────────────

    @mcp.tool()
    @_wrap
    def disassemble(address: str = "$rip", count: int = 20) -> dict:
        """Disassemble instructions at the given address.

        Args:
            address: address expression (defaults to $rip).
            count: number of instructions to show.
        """
        return gdb.disassemble(address, count)

    # ── evaluate ─────────────────────────────────────────────────────

    @mcp.tool()
    @_wrap
    def evaluate(expression: str) -> dict:
        """Evaluate a GDB expression and return the value (print).

        Args:
            expression: any valid GDB expression (variable, register, deref, …).
        """
        return gdb.evaluate(expression)

    # ── watchpoint ───────────────────────────────────────────────────

    @mcp.tool()
    @_wrap
    def set_watchpoint(expression: str, kind: str = "write") -> dict:
        """Set a hardware watchpoint on an expression.

        Args:
            expression: variable or address to watch.
            kind: "write" (watch), "read" (rwatch), or "access" (awatch).
        """
        return gdb.set_watchpoint(expression, kind)
