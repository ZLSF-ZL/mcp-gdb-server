#!/usr/bin/env bash
# Stop, disable, and remove mcp_gdb_server systemd service.
# Usage: ./uninstall_service.sh

set -euo pipefail

SERVICE="mcp-gdb-server.service"
BINARY="/usr/local/bin/mcp_gdb_server"

echo "==> Stopping service ..."
sudo systemctl stop "$SERVICE" 2>/dev/null || true

echo "==> Disabling auto-start ..."
sudo systemctl disable "$SERVICE" 2>/dev/null || true

echo "==> Removing service unit ..."
sudo rm -f "/etc/systemd/system/$SERVICE"
sudo systemctl daemon-reload

echo "==> Removing binary ..."
sudo rm -f "$BINARY"

echo "==> Done. Service '$SERVICE' has been removed."
