from __future__ import annotations

import pexpect
from typing import Optional

PROMPT_PATTERNS = [
    r"\(gdb\)",
    r"pwndbg>",
    r"gef>",
    r"gdb-peda\$",
    r"\$",
]


class GDBNotRunningError(RuntimeError):
    """Raised when an operation requires a running GDB session."""


class GDBManager:
    """Manages a GDB subprocess via pexpect."""

    def __init__(self) -> None:
        self._child: Optional[pexpect.spawn] = None
        self.timeout_message = "[MCP Info] Execution timed out (likely running)."

    @property
    def is_running(self) -> bool:
        return self._child is not None and self._child.isalive()

    def start(self, command: str = "gdb", init_timeout: int = 5) -> str:
        if self.is_running:
            self._child.close()

        try:
            self._child = pexpect.spawn(command, encoding="utf-8", timeout=5)

            try:
                self._child.expect(PROMPT_PATTERNS, timeout=init_timeout)
                startup_msg = self._child.before or ""
            except pexpect.TIMEOUT:
                startup_msg = self._child.before or "GDB started (no prompt detected yet)"

            init_cmds = ["set pagination off", "set confirm off", "set width 0", "set height 0"]
            for cmd in init_cmds:
                self._child.sendline(cmd)
                try:
                    self._child.expect(PROMPT_PATTERNS, timeout=1)
                except pexpect.TIMEOUT:
                    pass

            return f"GDB Started successfully.\nCommand: {command}\n\nInitial Output:\n{startup_msg}"

        except Exception as e:
            if self._child:
                self._child.close()
                self._child = None
            return f"Failed to start GDB: {str(e)}"

    def execute(self, cmd: str, timeout: int = 10) -> str:
        if not self.is_running:
            raise GDBNotRunningError("GDB is not running. Please use start_debugging first.")

        self._child.sendline(cmd)

        try:
            self._child.expect(PROMPT_PATTERNS, timeout=timeout)
            return self._child.before or ""
        except pexpect.TIMEOUT:
            current_output = self._child.before or ""
            return f"{current_output}\n\n{self.timeout_message}"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def interrupt(self) -> str:
        if not self.is_running:
            raise GDBNotRunningError("GDB not running")

        self._child.sendintr()
        try:
            self._child.expect(PROMPT_PATTERNS, timeout=2)
            return f"Interrupted.\n{self._child.before}"
        except pexpect.TIMEOUT:
            return "Signal sent, but GDB prompt did not appear immediately."

    def stop(self) -> str:
        if self._child:
            self._child.close()
            self._child = None
        return "GDB Session ended."
