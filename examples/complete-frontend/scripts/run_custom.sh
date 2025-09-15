#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_BIN="${PYTHON:-python3}"
SERVER_SCRIPT="${SERVER_SCRIPT:-server.py}"
LOG_DIR="${LOG_DIR:-$APP_DIR/logs}"

mkdir -p "$LOG_DIR"

read -p "HTTP port [8086]: " http_port
HTTP_PORT="${http_port:-8086}"

echo "⚙️  Starting server on http://localhost:${HTTP_PORT} (WebSocket at /ws)"
HTTP_PORT="$HTTP_PORT" "$PYTHON_BIN" "$APP_DIR/$SERVER_SCRIPT" > "$LOG_DIR/server-custom.log" 2>&1 &
PID=$!

echo "✅ Server started with PID $PID"
echo "   - Frontend:  http://localhost:${HTTP_PORT}"
echo "   - WebSocket: ws://localhost:${HTTP_PORT}/ws"
echo "   - Logs:      $LOG_DIR/server-custom.log"
