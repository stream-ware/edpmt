#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_BIN="${PYTHON:-python3}"
SERVER_SCRIPT="${SERVER_SCRIPT:-server.py}"
LOG_DIR="${LOG_DIR:-$APP_DIR/logs}"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Cleanup function
cleanup() {
    if [ -n "${TEST_PID:-}" ]; then
        kill -9 "$TEST_PID" 2>/dev/null || true
    fi
    rm -f "$APP_DIR/.server-test.pid" 2>/dev/null || true
}
trap cleanup EXIT

echo "🧪 Testing EDPMT Complete Frontend..."

# 1) Check Python imports
echo "1) Python imports..."
"$PYTHON_BIN" -c "
import sys
sys.path.insert(0, '../../..')
import edpmt
print('✅ EDPMT import successful')
import websockets, asyncio, json, aiohttp, aiohttp_cors
print('✅ Python dependencies available')
"

# 2) Check module load
echo "2) Module load..."
"$PYTHON_BIN" -c "
import sys
sys.path.insert(0, '.')
from server import EDPMTWebServer
print('✅ Server module loads correctly')
"

# 3) Check static assets
echo "3) Static assets..."
[ -f "$APP_DIR/index.html" ] || { echo "❌ Frontend HTML missing"; exit 1; }
[ -f "$APP_DIR/styles.css" ] || { echo "❌ Frontend CSS missing"; exit 1; }
[ -d "$APP_DIR/js" ] || { echo "❌ JavaScript directory missing"; exit 1; }
[ -f "$APP_DIR/js/main.js" ] || { echo "❌ Main JavaScript missing"; exit 1; }
[ -f "$APP_DIR/js/edpmt-client.js" ] || { echo "❌ EDPMT client missing"; exit 1; }
echo "✅ All static assets found"

# 4) Check example projects
echo "4) Example projects..."
mkdir -p "$APP_DIR/projects"
if ls "$APP_DIR"/projects/*.json >/dev/null 2>&1; then
    echo "✅ Example projects found"
else
    echo "ℹ️  No example projects (run 'make setup')"
fi

# 5) Start test server and check endpoints
echo "5) Starting test server..."
TEST_PORT=$(python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1', 0)); print(s.getsockname()[1]); s.close()")
echo "   • Test server will use port: $TEST_PORT"

# Start server in background
HTTP_PORT="$TEST_PORT" "$PYTHON_BIN" "$APP_DIR/$SERVER_SCRIPT" > "$LOG_DIR/server-test.log" 2>&1 &
TEST_PID=$!
echo "$TEST_PID" > "$APP_DIR/.server-test.pid"

# Wait for server to start
MAX_WAIT=20
for i in $(seq 1 $MAX_WAIT); do
    if curl -s "http://localhost:${TEST_PORT}/" >/dev/null; then
        echo "   • Server started successfully"
        break
    fi
    if [ $i -eq $MAX_WAIT ]; then
        echo "❌ Server failed to start"
        tail -n 20 "$LOG_DIR/server-test.log" || true
        exit 1
    fi
    sleep 1
done

# Test endpoints
endpoints=(
    "/"
    "/api/status"
    "/api/projects"
    "/runtime-config.js"
)

for endpoint in "${endpoints[@]}"; do
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${TEST_PORT}${endpoint}" || true)
    if [ "$status_code" = "200" ]; then
        echo "   • ${endpoint} -> ✅ 200"
    else
        echo "   • ${endpoint} -> ❌ ${status_code}"
        echo "   • Last 20 lines of server log:"
        tail -n 20 "$LOG_DIR/server-test.log" || true
        exit 1
    fi
done

# Test WebSocket
echo "   • Testing WebSocket connection..."
if ! python3 -c "
import asyncio, websockets, sys, os, json

async def test_ws():
    try:
        async with websockets.connect(f'ws://localhost:{os.environ['TEST_PORT']}/ws') as ws:
            await ws.send(json.dumps({'type': 'ping'}))
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            if json.loads(response).get('type') == 'pong':
                print('✅ WebSocket handshake successful')
                return True
    except Exception as e:
        print(f'❌ WebSocket test failed: {str(e)}')
        return False

asyncio.get_event_loop().run_until_complete(test_ws())
"; then
    echo "❌ WebSocket test failed"
    exit 1
fi

echo "✅ All tests passed!"

# Cleanup
cleanup
trap - EXIT
