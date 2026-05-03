#!/usr/bin/env bash
# Build and install mcp_gdb_server as a systemd service.
# Usage: ./install_service.sh [--debug]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BINARY="/usr/local/bin/mcp_gdb_server"
SERVICE="mcp-gdb-server.service"

BINARY_SRC="$SCRIPT_DIR/dist/mcp_gdb_server"
if [ -f "$BINARY_SRC" ]; then
    echo "==> Binary already exists, skipping build ..."
else
    echo "==> Building binary ..."
    "$SCRIPT_DIR/build.py" ${1:+--debug}
fi

echo "==> Installing binary to $BINARY ..."
sudo cp "$SCRIPT_DIR/dist/mcp_gdb_server" "$BINARY"
sudo chmod +x "$BINARY"

echo "==> Installing systemd service ..."
sudo cp "$SCRIPT_DIR/$SERVICE" /etc/systemd/system/
sudo systemctl daemon-reload

echo "==> Enabling and starting service ..."
sudo systemctl enable --now mcp-gdb-server.service

echo "==> Status:"
systemctl status mcp-gdb-server.service --no-pager
