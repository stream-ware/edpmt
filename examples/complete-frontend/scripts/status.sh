#!/usr/bin/env bash
set -euo pipefail

HTTP_PORT="${HTTP_PORT:-8085}"
SERVER_SCRIPT="${SERVER_SCRIPT:-server.py}"
LOG_DIR="${LOG_DIR:-logs}"
PROJECTS_DIR="${PROJECTS_DIR:-projects}"

echo "🔍 EDPMT Complete Frontend Status:"
echo "=================================="

if pgrep -f "$SERVER_SCRIPT" >/dev/null 2>&1; then
  echo "🟢 Server: Running"
else
  echo "🔴 Server: Stopped"
fi

if curl -s "http://localhost:${HTTP_PORT}/api/status" >/dev/null 2>&1; then
  echo "🟢 HTTP API: Responsive"
else
  echo "🔴 HTTP API: Not responding"
fi

if ls "$LOG_DIR"/server*.log >/dev/null 2>&1; then
  echo "📄 Logs: Available in $LOG_DIR/"
else
  echo "📄 Logs: None found"
fi

if [ -d "$PROJECTS_DIR" ]; then
  count=$(ls "$PROJECTS_DIR"/*.json 2>/dev/null | wc -l | tr -d ' ')
  echo "📁 Projects: ${count} projects available"
else
  echo "📁 Projects: Directory not found"
fi
