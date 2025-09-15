#!/usr/bin/env bash
set -euo pipefail

HTTP_PORT="${HTTP_PORT:-8085}"
LOG_DIR="${LOG_DIR:-logs}"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Create log file if it doesn't exist
touch "$LOG_DIR/server-dev.log"

echo "📡 Monitoring http://localhost:${HTTP_PORT} every 5s (Ctrl+C to stop)..."

trap 'kill $TAIL_PID 2>/dev/null || true' EXIT

# Start tailing the log in the background
tail -n 50 -F "$LOG_DIR/server-dev.log" 2>/dev/null &
TAIL_PID=$!

# Function to check HTTP status
check_http() {
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${HTTP_PORT}/" 2>/dev/null || true)
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${HTTP_PORT}/api/status" 2>/dev/null || true)
    echo "$(date '+%Y-%m-%d %H:%M:%S') | / -> ${http_code:-down} | /api/status -> ${status_code:-down}"
}

# Main monitoring loop
while true; do
    check_http
    sleep 5
done
