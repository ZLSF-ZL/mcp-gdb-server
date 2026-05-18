from __future__ import annotations

import re
import shutil
from typing import Optional

import pexpect

PROMPT_PATTERNS = [
    r"\(gdb\)",
    r"pwndbg>",
    r"gef>",
    r"gdb-peda\$",
    r"\$",
]

# ── helpers ──────────────────────────────────────────────────────────

_RE_BP_INFO = re.compile(
    r"Breakpoint\s+(\d+)\s+at\s+(0x[0-9a-fA-F]+)"
    r"(?:\s+in\s+(\S+))?"
    r"(?:\s+(?:file\s+(\S+)|(\S+):(\d+)))?"
)

# x86-64 general-purpose registers (common CTF target)
_GPR_NAMES = [
    "rax", "rbx", "rcx", "rdx", "rsi", "rdi",
    "rbp", "rsp", "rip",
    "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15",
]


class GDBNotRunningError(RuntimeError):
    """Raised when an operation requires a running GDB session."""


class GDBManager:
    """Manages a GDB subprocess via pexpect."""

    def __init__(self) -> None:
        self._child: Optional[pexpect.spawn] = None
        self.timeout_message = "[MCP Info] Execution timed out (likely running)."

    # ── property ─────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._child is not None and self._child.isalive()

    # ── GDB detection ────────────────────────────────────────────────

    @staticmethod
    def detect_gdb() -> dict[str, str]:
        """Probe the system PATH for available GDB binaries."""
        found: dict[str, str] = {}
        for name in ["gdb-multiarch", "gdb"]:
            path = shutil.which(name)
            if path:
                found[name] = path
        return found

    @staticmethod
    def pick_gdb() -> str:
        """Return the most capable GDB binary available on the system."""
        detected = GDBManager.detect_gdb()
        return detected.get("gdb-multiarch") or detected.get("gdb") or "gdb"

    # ── lifecycle ────────────────────────────────────────────────────

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

            init_cmds = [
                "set pagination off",
                "set confirm off",
                "set width 0",
                "set height 0",
            ]
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

    def stop(self) -> str:
        """Terminate the inferior program and close GDB."""
        if self.is_running:
            self._run("kill")
            self._run("quit")
        if self._child:
            self._child.close()
            self._child = None
        return "Program killed and GDB session ended."

    def detach(self) -> str:
        """Detach GDB from the inferior, letting it continue running, then close GDB.

        Only meaningful for remote debugging (target remote / attach pid).
        """
        if self.is_running:
            self._run("detach")
            self._run("quit")
        if self._child:
            self._child.close()
            self._child = None
        return "GDB detached. Remote process continues running."

    def interrupt(self) -> str:
        if not self.is_running:
            raise GDBNotRunningError("GDB not running")

        self._child.sendintr()
        try:
            self._child.expect(PROMPT_PATTERNS, timeout=2)
            return f"Interrupted.\n{self._child.before}"
        except pexpect.TIMEOUT:
            return "Signal sent, but GDB prompt did not appear immediately."

    # ── low-level command helpers ────────────────────────────────────

    def execute(self, cmd: str, timeout: int = 10) -> str:
        """Send a command to GDB and return raw output (used by send_gdb_command)."""
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

    def _run(self, cmd: str, timeout: int = 10) -> str:
        """Internal: send a GDB command and return output stripped. Raises GDBNotRunningError."""
        if not self.is_running:
            raise GDBNotRunningError("GDB is not running.")
        self._child.sendline(cmd)
        try:
            self._child.expect(PROMPT_PATTERNS, timeout=timeout)
            return (self._child.before or "").strip()
        except pexpect.TIMEOUT:
            return (self._child.before or "").strip()

    # ── breakpoints ──────────────────────────────────────────────────

    def set_breakpoint(self, location: str, condition: str = "",
                       temporary: bool = False) -> dict:
        """Set a breakpoint. Returns structured info including number and address."""
        cmd = "tbreak" if temporary else "break"
        cmd += f" {location}"
        raw = self._run(cmd)

        # check for explicit failure
        if any(msg in raw.lower() for msg in ("not defined", "no symbol", "no source")):
            return {"status": "error", "data": raw, "raw": raw}

        data: dict = {}

        m = _RE_BP_INFO.search(raw)
        if m:
            data["number"] = int(m.group(1))
            data["address"] = m.group(2)
            if m.group(3):
                data["function"] = m.group(3)
            # file:line from either capture
            file_line = m.group(4) or m.group(5)
            line_no = m.group(5) or m.group(6)
            if file_line and line_no:
                data["file"] = file_line
                data["line"] = int(line_no)

        if not data:
            data["raw_info"] = raw

        # apply condition when GDB accepted the breakpoint
        if condition and "number" in data:
            self._run(f"condition {data['number']} {condition}")
            data["condition"] = condition

        return {
            "status": "ok",
            "data": data,
            "raw": raw,
        }

    def delete_breakpoint(self, number: int) -> dict:
        raw = self._run(f"delete {number}")
        err = "No breakpoint" in raw or "not found" in raw
        return {
            "status": "error" if err else "ok",
            "data": f"Deleted breakpoint {number}" if not err else raw,
            "raw": raw,
        }

    def list_breakpoints(self) -> dict:
        raw = self._run("info breakpoints")
        raw_stripped = raw.strip()
        if not raw_stripped or "No breakpoints" in raw_stripped:
            return {"status": "ok", "data": {"breakpoints": []}, "raw": raw_stripped}

        bps: list[dict] = []
        for line in raw_stripped.splitlines():
            # skip header line (starts with "Num") and blank lines
            if not line.strip() or line.strip().startswith("Num"):
                continue
            # skip continuation lines (no leading number); they are indented
            if not line[0].isdigit():
                continue

            parts = line.split(None, 5)  # max 6 columns
            bp: dict = {
                "number": int(parts[0]),
                "type": parts[1],
                "disp": parts[2],
                "enabled": parts[3] == "y",
            }
            if len(parts) >= 5:
                addr = parts[4]
                if addr.startswith("0x"):
                    bp["address"] = addr
                else:
                    # in case the address column is missing
                    bp["what"] = addr
            if len(parts) >= 6:
                bp["what"] = parts[5]
            bps.append(bp)

        return {"status": "ok", "data": {"breakpoints": bps}, "raw": raw_stripped}

    def enable_breakpoint(self, number: int) -> dict:
        raw = self._run(f"enable {number}")
        return {"status": "ok", "data": f"Enabled breakpoint {number}", "raw": raw}

    def disable_breakpoint(self, number: int) -> dict:
        raw = self._run(f"disable {number}")
        return {"status": "ok", "data": f"Disabled breakpoint {number}", "raw": raw}

    # ── execution control ────────────────────────────────────────────

    def step_into(self) -> dict:
        raw = self._run("stepi")
        return {"status": "ok", "data": raw, "raw": raw}

    def step_over(self) -> dict:
        raw = self._run("next")
        return {"status": "ok", "data": raw, "raw": raw}

    def step_out(self) -> dict:
        raw = self._run("finish")
        return {"status": "ok", "data": raw, "raw": raw}

    def continue_execution(self) -> dict:
        raw = self._run("continue")
        return {"status": "ok", "data": raw, "raw": raw}

    # ── register inspection ──────────────────────────────────────────

    def read_registers(self, registers: Optional[list[str]] = None) -> dict:
        """Return register values as a structured dict.

        If *registers* is None or empty, read x86-64 general-purpose
        registers plus any extra that GDB knows about.
        """
        if registers:
            cmd = "info registers " + " ".join(registers)
        else:
            cmd = "info registers"
        raw = self._run(cmd)

        regs: dict[str, str] = {}
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            tokens = line.split()
            # token[0] = name, token[1] = hex value
            if len(tokens) >= 2 and tokens[1].startswith("0x"):
                regs[tokens[0]] = tokens[1]
            elif len(tokens) >= 1 and tokens[0] in _GPR_NAMES:
                # might be on a different arch, store whatever's there
                regs[tokens[0]] = tokens[1] if len(tokens) > 1 else ""

        return {
            "status": "ok",
            "data": {"registers": regs},
            "raw": raw,
        }

    # ── backtrace ────────────────────────────────────────────────────

    def backtrace(self, depth: int = 20, detailed: bool = False) -> dict:
        cmd = f"bt {depth}" if not detailed else f"bt full {depth}"
        raw = self._run(cmd)

        frames: list[dict] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            # match "#N  ..." or "#N ..."
            m = re.match(r"^#(\d+)\s+(.*)", line)
            if not m:
                continue
            frame: dict = {"number": int(m.group(1)), "text": m.group(2)}
            # try to extract function name
            fm = re.match(r"(?:0x[0-9a-fA-F]+\s+in\s+)?(\S+)", m.group(2))
            if fm:
                frame["function"] = fm.group(1)
            # if detailed, check for local variable lines following
            frames.append(frame)

        return {
            "status": "ok",
            "data": {"frames": frames, "depth": len(frames)},
            "raw": raw,
        }

    # ── memory ───────────────────────────────────────────────────────

    def read_memory(self, address: str, count: int = 8,
                    size: int = 8, fmt: str = "x") -> dict:
        """Read memory and return structured hex dump.

        *size*: 1 (byte), 2 (halfword), 4 (word), 8 (giant).
        *fmt*: ``x`` (hex), ``d`` (decimal), ``s`` (string), ``i`` (instr).
        """
        if fmt == "i":
            # disassembly-style output
            cmd = f"x/{count}i {address}"
        else:
            cmd = f"x/{count}{fmt}{size} {address}"
        raw = self._run(cmd)

        entries: list[dict] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            # format: "ADDR:\tVALUE1\tVALUE2 ..."  or "=> ADDR:\tVALUE"
            m = re.match(r"^=>?\s*(0x[0-9a-fA-F]+):\t?(.*)", line)
            if m:
                addr = m.group(1)
                values = m.group(2).split()
                entries.append({"address": addr, "values": values})

        return {
            "status": "ok",
            "data": {"entries": entries, "count": count, "size": size, "format": fmt},
            "raw": raw,
        }

    def search_memory(self, pattern: str, start: str = "$rip",
                      end: str = "$rip+0x1000", size: int = 8) -> dict:
        """Search memory for a value (GDB ``find`` command).

        *pattern*: hex value like ``0xdeadbeef`` or string.
        *size*: element size in bytes (1=b, 2=h, 4=w, 8=g).
        """
        size_flag = {1: "b", 2: "h", 4: "w", 8: "g"}.get(size, "b")
        cmd = f"find /{size_flag} {start}, {end}, {pattern}"
        raw = self._run(cmd)

        addresses: list[str] = []
        for line in raw.splitlines():
            line = line.strip()
            if re.match(r"^0x[0-9a-fA-F]+", line) and "pattern" not in line:
                addresses.append(line.split()[0])

        return {
            "status": "ok",
            "data": {
                "addresses": addresses,
                "count": len(addresses),
                "pattern": pattern,
            },
            "raw": raw,
        }

    # ── disassembly ──────────────────────────────────────────────────

    def disassemble(self, address: str = "$rip", count: int = 20) -> dict:
        raw = self._run(f"x/{count}i {address}")

        instructions: list[dict] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            # "=> 0x... <SYM+OFF>:    INSN"  or  "   0x... <SYM+OFF>:    INSN"
            m = re.match(r"^=>?\s*(0x[0-9a-fA-F]+)(?:\s*<([^>]+)>)?:\s*(.*)", line)
            if m:
                instructions.append({
                    "address": m.group(1),
                    "symbol": m.group(2) or "",
                    "instruction": m.group(3),
                    "current_pc": line.startswith("=>"),
                })

        return {
            "status": "ok",
            "data": {
                "instructions": instructions,
                "count": len(instructions),
            },
            "raw": raw,
        }

    # ── evaluate ─────────────────────────────────────────────────────

    def evaluate(self, expression: str) -> dict:
        raw = self._run(f"print {expression}")
        # Try to extract the value part: "$N = VALUE"
        m = re.match(r"\$\d+\s*=\s*(.*)", raw.strip())
        value = m.group(1) if m else raw.strip()
        return {
            "status": "ok",
            "data": {"expression": expression, "value": value},
            "raw": raw,
        }

    # ── watchpoints ──────────────────────────────────────────────────

    def set_watchpoint(self, expression: str, kind: str = "write") -> dict:
        gdb_cmd = {"write": "watch", "read": "rwatch", "access": "awatch"}.get(kind, "watch")
        raw = self._run(f"{gdb_cmd} {expression}")

        m = re.search(r"(Hardware watchpoint|Watchpoint|Hardware access watchpoint)\s+(\d+)", raw)
        data: dict = {}
        if m:
            data["number"] = int(m.group(2))
            data["type"] = m.group(1)
        else:
            data["raw_info"] = raw

        return {"status": "ok", "data": data, "raw": raw}
