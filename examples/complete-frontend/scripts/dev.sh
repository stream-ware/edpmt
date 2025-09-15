#!/usr/bin/env bash
set -euo pipefail

# Script directory and app root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

# Env defaults
PYTHON_BIN="${PYTHON:-python3}"
HTTP_PORT="${HTTP_PORT:-8085}"
SERVER_SCRIPT="${SERVER_SCRIPT:-server.py}"
LOG_DIR="${LOG_DIR:-$APP_DIR/logs}"

mkdir -p "$LOG_DIR"

echo "🚀 Starting EDPMT Complete Frontend (Development Mode)..."
echo "🔧 Using hardware simulators - safe for development"

echo "🔥 Launching server on http://localhost:${HTTP_PORT} ..."
"$PYTHON_BIN" "$APP_DIR/$SERVER_SCRIPT" --http-port "$HTTP_PORT" --verbose > "$LOG_DIR/server-dev.log" 2>&1 &

echo ""
echo "✅ Server is running in the background."
echo "   - Frontend:  http://localhost:${HTTP_PORT}"
echo "   - WebSocket: ws://localhost:${HTTP_PORT}/ws"
echo "   - Logs:      $LOG_DIR/server-dev.log"
echo "   - Stop:      make stop"
