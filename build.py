#!/usr/bin/env python3
"""Build mcp_gdb_server into a standalone binary using PyInstaller.

Usage:
    python build.py              # production build (onefile)
    python build.py --debug      # debug build (onedir, no console hide)
    python build.py --clean      # clean cache before building
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
BUILD_DIR = ROOT / "build"
DIST_DIR = ROOT / "dist"
SPEC_DIR = ROOT


def build(debug: bool = False, clean: bool = False) -> Path:
    if clean and BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        for spec in ROOT.glob("*.spec"):
            spec.unlink()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        "--specpath",
        str(SPEC_DIR),
        "--name",
        "mcp_gdb_server",
        "--collect-all",
        "fastmcp",
        "--copy-metadata",
        "fastmcp",
    ]

    if debug:
        cmd.append("--debug")
        cmd.append("--onedir")
    else:
        cmd.append("--onefile")
        cmd.append("--strip")

    cmd.append(str(ROOT / "mcp_gdb_server.py"))

    print("==> Building mcp_gdb_server ...")
    subprocess.run(cmd, check=True, cwd=ROOT)

    binary = DIST_DIR / "mcp_gdb_server"
    print(f"==> Done: {binary}")
    size = os.path.getsize(binary)
    print(f"    Size: {size / 1024 / 1024:.1f} MiB")
    return binary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build mcp_gdb_server binary")
    parser.add_argument("--debug", action="store_true", help="debug build (onedir, verbose)")
    parser.add_argument("--clean", action="store_true", help="clean build cache before building")
    args = parser.parse_args()

    build(debug=args.debug, clean=args.clean)
