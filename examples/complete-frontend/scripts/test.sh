#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_BIN="${PYTHON:-python3}"
SERVER_SCRIPT="${SERVER_SCRIPT:-server.py}"
LOG_DIR="${LOG_DIR:-$APP_DIR/logs}"

mkdir -p "$LOG_DIR"

echo "🧪 Testing EDPMT Complete Frontend..."

echo "1) Python imports..."
$PYTHON_BIN - <<'PY'
import sys
sys.path.insert(0, '../../..')
import edpmt
print('✅ EDPMT import successful')
import websockets, asyncio, json, aiohttp, aiohttp_cors
print('✅ Python dependencies available')
PY

echo "2) Module load..."
$PYTHON_BIN - <<'PY'
from server import EDPMTWebServer
print('✅ Server module loads correctly')
PY

echo "3) Static assets..."
[ -f "$APP_DIR/index.html" ] && echo "✅ Frontend HTML found" || { echo "❌ Frontend HTML missing"; exit 1; }
[ -f "$APP_DIR/styles.css" ] && echo "✅ Frontend CSS found" || { echo "❌ Frontend CSS missing"; exit 1; }
[ -d "$APP_DIR/js" ] && echo "✅ JavaScript directory found" || { echo "❌ JavaScript directory missing"; exit 1; }
[ -f "$APP_DIR/js/main.js" ] && echo "✅ Main JavaScript found" || { echo "❌ Main JavaScript missing"; exit 1; }
[ -f "$APP_DIR/js/edpmt-client.js" ] && echo "✅ EDPMT client found" || { echo "❌ EDPMT client missing"; exit 1; }

echo "4) Example projects..."
mkdir -p "$APP_DIR/projects"
if ls "$APP_DIR"/projects/*.json >/dev/null 2>&1; then
  echo "✅ Example projects found"
else
  echo "ℹ️  No example projects (run 'make setup')"
fi

echo "5) Temporary server health checks..."
# Find free port
TEST_PORT=$($PYTHON_BIN - <<'PY'
import socket
s=socket.socket(); s.bind(('127.0.0.1',0))
print(s.getsockname()[1])
s.close()
PY
)

echo "   • Starting test server on ${TEST_PORT}..."
"$PYTHON_BIN" "$APP_DIR/$SERVER_SCRIPT" --http-port "$TEST_PORT" > "$LOG_DIR/server-test.log" 2>&1 &
PID=$!
echo $PID > "$APP_DIR/.server-test.pid"

# Wait up to 20s for HTTP 200
for i in $(seq 1 20); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${TEST_PORT}/" || true)
  if [ "$code" = "200" ]; then echo "   • HTTP ready (200)"; break; fi
  sleep 1
  if [ $i -eq 20 ]; then
    echo "❌ Server failed to start"
    tail -n 100 "$LOG_DIR/server-test.log" || true
    kill "$PID" 2>/dev/null || true
    rm -f "$APP_DIR/.server-test.pid"
    exit 1
  fi
done

status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${TEST_PORT}/api/status" || true)
proj_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${TEST_PORT}/api/projects" || true)
rc_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${TEST_PORT}/runtime-config.js" || true)

echo "   • /api/status -> ${status_code}"
echo "   • /api/projects -> ${proj_code}"
echo "   • /runtime-config.js -> ${rc_code}"
if [ "$status_code" != "200" ] || [ "$proj_code" != "200" ] || [ "$rc_code" != "200" ]; then
  echo "❌ Endpoint checks failed"
  tail -n 100 "$LOG_DIR/server-test.log" || true
  kill "$PID" 2>/dev/null || true
  rm -f "$APP_DIR/.server-test.pid"
  exit 1
fi

# WebSocket handshake check
TEST_PORT="$TEST_PORT" "$PYTHON_BIN" - <<'PY'
import asyncio, os, sys
import websockets
port = int(os.environ['TEST_PORT'])
async def main():
    try:
        async with websockets.connect(f"ws://localhost:{port}/ws") as ws:
            await ws.send('{"type":"ping"}')
        print("   • WebSocket handshake OK")
    except Exception as e:
        print(f"❌ WebSocket check failed: {e}")
        sys.exit(1)
asyncio.run(main())
PY

# Cleanup server
kill "$PID" 2>/dev/null || true
rm -f "$APP_DIR/.server-test.pid"

echo "✅ All tests passed!"
