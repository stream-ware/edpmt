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

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Kill any existing server process
pkill -f "$SERVER_SCRIPT" 2>/dev/null || true

echo "🚀 Starting EDPMT Complete Frontend (Development Mode)..."
echo "🔧 Using hardware simulators - safe for development"
echo "🌐 HTTP port: $HTTP_PORT"

# Start the server in the background
HTTP_PORT="$HTTP_PORT" \
"$PYTHON_BIN" "$APP_DIR/$SERVER_SCRIPT" > "$LOG_DIR/server-dev.log" 2>&1 &
SERVER_PID=$!

# Small delay to let the server start
sleep 2

# Verify server started
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "❌ Failed to start server. Check logs: $LOG_DIR/server-dev.log"
    tail -n 20 "$LOG_DIR/server-dev.log"
    exit 1
fi

echo ""
echo "✅ Server is running in the background."
echo "   - Frontend:  http://localhost:${HTTP_PORT}"
echo "   - WebSocket: ws://localhost:${HTTP_PORT}/ws"
echo "   - Logs:      $LOG_DIR/server-dev.log"
echo "   - Stop:      make stop"

# Wait for server to exit
trap 'kill $SERVER_PID 2>/dev/null' EXIT
wait $SERVER_PID
