#!/bin/bash

# EDPMT All Services Startup Script
echo "🚀 Starting EDPMT All Services..."

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Port is busy
    else
        return 0  # Port is available
    fi
}

# Function to find available port starting from given port
find_available_port() {
    local start_port=$1
    local current_port=$start_port
    
    while ! check_port $current_port; do
        current_port=$((current_port + 1))
        if [ $current_port -gt $((start_port + 100)) ]; then
            echo "❌ Could not find available port in range $start_port-$((start_port + 100))"
            exit 1
        fi
    done
    
    echo $current_port
}

# Detect PortKeeper CLI
if command -v portkeeper >/dev/null 2>&1; then
    USE_PORTKEEPER=1
    echo "🔑 PortKeeper detected — using coordinated reservations"
else
    USE_PORTKEEPER=0
    echo "ℹ️ PortKeeper not found — falling back to local finder"
fi

# Reserve port helper (prefers PortKeeper)
reserve_port() {
    local preferred=$1
    local range_start=$2
    local range_end=$3
    local env_key=$4
    local host=${5:-127.0.0.1}

    if [ "$USE_PORTKEEPER" -eq 1 ]; then
        # Reserve and write to project .env atomically
        portkeeper reserve \
            --preferred "$preferred" \
            --range "$range_start" "$range_end" \
            --host "$host" \
            --owner "edpmt" \
            --write-env "$env_key" \
            --env-path .env \
            >/tmp/portkeeper-"$env_key".json || true
        # Load env and echo the value
        if [ -f .env ]; then
            set -a; . ./.env; set +a
            eval "echo \${$env_key}"
            return
        fi
    fi
    # Fallback using built-in finder
    echo "$(find_available_port "$preferred")"
}

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "edpmt.*server" 2>/dev/null || true
pkill -f "python.*http.server" 2>/dev/null || true
sleep 2

# Find available ports (prefer PortKeeper)
SERVICE_HOST="127.0.0.1"
FRONTEND_HOST="127.0.0.1"

# Optional preflight with PortKeeper config (reserves ports and writes outputs)
if command -v portkeeper >/dev/null 2>&1 && [ -f pk.config.json ]; then
    echo "🧩 Preflight: portkeeper prepare --config pk.config.json"
    portkeeper prepare --config pk.config.json || true
    # Load env to pick up SERVICE_PORT/FRONTEND_PORT if set
    if [ -f .env ]; then set -a; . ./.env; set +a; fi
fi

# If FRONTEND_PORT wasn't set by preflight, reserve it now (generic key)
FRONTEND_PORT="${FRONTEND_PORT:-$(reserve_port 8080 8080 8180 FRONTEND_PORT "$FRONTEND_HOST")}" 

# Persist/complete backend env (generic keys)
if [ ! -f .env ]; then
    touch .env
fi
grep -q '^SERVICE_HOST=' .env 2>/dev/null || echo "SERVICE_HOST=$SERVICE_HOST" >> .env
grep -q '^FRONTEND_PORT=' .env 2>/dev/null || echo "FRONTEND_PORT=$FRONTEND_PORT" >> .env
grep -q '^FRONTEND_HOST=' .env 2>/dev/null || echo "FRONTEND_HOST=$FRONTEND_HOST" >> .env

echo "📡 Using (preflight) ports:"
echo "   • Service (backend): ${SERVICE_HOST}:${SERVICE_PORT:-?}"
echo "   • Frontend (UI):     ${FRONTEND_HOST}:${FRONTEND_PORT}"

# Create PID file directory
mkdir -p /tmp/edpmt-pids

# Start EDPMT server in background
echo "🌐 Starting Service (EDPMT) with auto-port..."
cd "$(dirname "$0")/.."

nohup edpmt server --dev --host "$SERVICE_HOST" --auto-port > /tmp/edpmt-server.log 2>&1 &
EDPMT_PID=$!
echo $EDPMT_PID > /tmp/edpmt-pids/server.pid

# Wait for server to start
echo "⏳ Waiting for EDPMT server to initialize..."
sleep 3

# Check if server started successfully
if ! kill -0 $EDPMT_PID 2>/dev/null; then
    echo "❌ EDPMT server failed to start. Check logs:"
    tail -n 20 /tmp/edpmt-server.log
    exit 1
fi

# Read SERVICE_PORT written by server into .env (wait until available)
SERVICE_PORT="${SERVICE_PORT:-}"
for i in {1..20}; do
  if grep -q '^SERVICE_PORT=' .env 2>/dev/null; then
    SERVICE_PORT=$(grep '^SERVICE_PORT=' .env | cut -d= -f2)
    if [ -n "$SERVICE_PORT" ]; then break; fi
  fi
  # Backward-compat alias
  if grep -q '^EDPMT_PORT=' .env 2>/dev/null; then
    SERVICE_PORT=$(grep '^EDPMT_PORT=' .env | cut -d= -f2)
    if [ -n "$SERVICE_PORT" ]; then break; fi
  fi
  sleep 0.3
done
if [ -z "$SERVICE_PORT" ]; then
  echo "❌ Failed to read SERVICE_PORT from .env after starting server"
  tail -n 20 /tmp/edpmt-server.log || true
  exit 1
fi

echo "📡 Using ports:"
echo "   • Service (backend): ${SERVICE_HOST}:${SERVICE_PORT}"
echo "   • Frontend (UI):     ${FRONTEND_HOST}:${FRONTEND_PORT}"

# Start Frontend (static UI)
echo "🎨 Starting Frontend on port $FRONTEND_PORT..."
cd examples/visual-programming

# Inject runtime-config.js for the frontend (generic window.RUNTIME + alias)
cat > runtime-config.js << EOF
// Runtime configuration injected by start-all.sh
window.RUNTIME = {
    httpUrl: 'https://localhost:$SERVICE_PORT',
    wsUrl: 'wss://localhost:$SERVICE_PORT/ws'
};
// Backward compatibility alias
window.EDPMT_RUNTIME = window.RUNTIME;
EOF

# Also write config.json for consumers/tools that expect JSON
cat > config.json << EOF
{
  "httpUrl": "https://localhost:$SERVICE_PORT",
  "wsUrl": "wss://localhost:$SERVICE_PORT/ws",
  "visualUrl": "http://localhost:$FRONTEND_PORT"
}
EOF

echo "🔄 Updated frontend configuration (runtime-config.js and config.json)"

nohup python3 -m http.server $FRONTEND_PORT > /tmp/edpmt-visual.log 2>&1 &
VISUAL_PID=$!
echo $VISUAL_PID > /tmp/edpmt-pids/visual.pid

# Wait for visual interface to start
sleep 2

# Check if visual interface started successfully
if ! kill -0 $VISUAL_PID 2>/dev/null; then
    echo "❌ Visual Programming Interface failed to start. Check logs:"
    tail -n 10 /tmp/edpmt-visual.log
    exit 1
fi

echo ""
echo "✅ All services started successfully!"
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    EDPMT Services Running                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Service (Backend):"
echo "   • URL: https://localhost:$SERVICE_PORT"
echo "   • API: https://localhost:$SERVICE_PORT/api/execute"
echo "   • WebSocket: wss://localhost:$SERVICE_PORT/ws"
echo "   • PID: $EDPMT_PID"
echo ""
echo "🎨 Frontend:"
echo "   • URL: http://localhost:$FRONTEND_PORT"
echo "   • Interface: Drag & Drop Blocks"
echo "   • PID: $VISUAL_PID"
echo ""
echo "📋 Management:"
echo "   • Stop all services: make stop"
echo "   • View logs: make logs"
echo "   • Check status: make status"
echo ""
echo "🔗 Quick access:"
echo "   • Open Frontend: http://localhost:$FRONTEND_PORT"
echo "   • Server connects to: wss://localhost:$SERVICE_PORT/ws"
echo ""

# Save port configuration for other scripts
cat > /tmp/edpmt-pids/config.env << EOF
SERVICE_PORT=$SERVICE_PORT
FRONTEND_PORT=$FRONTEND_PORT
EDPMT_PID=$EDPMT_PID
VISUAL_PID=$VISUAL_PID
# Backward-compat aliases
EDPMT_PORT=$SERVICE_PORT
VISUAL_PORT=$FRONTEND_PORT
EOF

echo "Services are running in background. Use 'make stop' to stop all services."
