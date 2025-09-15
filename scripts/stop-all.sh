#!/bin/bash

# EDPMT All Services Stop Script
echo "🛑 Stopping EDPMT All Services..."

# Load configuration if available
if [ -f /tmp/edpmt-pids/config.env ]; then
    source /tmp/edpmt-pids/config.env
    echo "📋 Found running services configuration"
else
    echo "⚠️  No configuration found, attempting to stop all matching processes"
fi

# Function to stop process by PID file
stop_by_pid_file() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "🔌 Stopping $service_name (PID: $pid)..."
            kill "$pid"
            
            # Wait up to 10 seconds for graceful shutdown
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "⚡ Force stopping $service_name..."
                kill -9 "$pid"
            fi
            
            echo "✅ $service_name stopped"
        else
            echo "ℹ️  $service_name was not running"
        fi
        rm -f "$pid_file"
    else
        echo "ℹ️  No PID file found for $service_name"
    fi
}

# Stop services by PID files
if [ -d /tmp/edpmt-pids ]; then
    stop_by_pid_file "EDPMT Server" "/tmp/edpmt-pids/server.pid"
    stop_by_pid_file "Visual Programming Interface" "/tmp/edpmt-pids/visual.pid"
fi

# Additional cleanup - kill any remaining processes
echo "🧹 Cleaning up any remaining processes..."

# Kill EDPMT server processes
EDPMT_PIDS=$(pgrep -f "edpmt.*server" 2>/dev/null || true)
if [ ! -z "$EDPMT_PIDS" ]; then
    echo "🔌 Stopping remaining EDPMT server processes: $EDPMT_PIDS"
    echo "$EDPMT_PIDS" | xargs kill 2>/dev/null || true
    sleep 2
    # Force kill if still running
    EDPMT_PIDS=$(pgrep -f "edpmt.*server" 2>/dev/null || true)
    if [ ! -z "$EDPMT_PIDS" ]; then
        echo "⚡ Force stopping EDPMT servers: $EDPMT_PIDS"
        echo "$EDPMT_PIDS" | xargs kill -9 2>/dev/null || true
    fi
fi

# Kill Visual Programming Interface processes
VISUAL_PIDS=$(pgrep -f "python.*http.server" 2>/dev/null || true)
if [ ! -z "$VISUAL_PIDS" ]; then
    echo "🔌 Stopping Visual Programming Interface processes: $VISUAL_PIDS"
    echo "$VISUAL_PIDS" | xargs kill 2>/dev/null || true
    sleep 1
    # Force kill if still running
    VISUAL_PIDS=$(pgrep -f "python.*http.server" 2>/dev/null || true)
    if [ ! -z "$VISUAL_PIDS" ]; then
        echo "⚡ Force stopping Visual Programming Interface: $VISUAL_PIDS"
        echo "$VISUAL_PIDS" | xargs kill -9 2>/dev/null || true
    fi
fi

# Free up ports used by configuration
if [ ! -z "$EDPMT_PORT" ]; then
    echo "🔓 Freeing port $EDPMT_PORT..."
    fuser -k $EDPMT_PORT/tcp 2>/dev/null || true
fi

if [ ! -z "$VISUAL_PORT" ]; then
    echo "🔓 Freeing port $VISUAL_PORT..."
    fuser -k $VISUAL_PORT/tcp 2>/dev/null || true
fi

# Also free common ports
echo "🔓 Freeing common EDPMT ports..."
for port in 8888 8080 5000 3000; do
    fuser -k $port/tcp 2>/dev/null || true
done

# Cleanup temporary files
echo "🗑️  Cleaning up temporary files..."
rm -rf /tmp/edpmt-pids
rm -f /tmp/edpmt-server.log
rm -f /tmp/edpmt-visual.log

echo ""
echo "✅ All EDPMT services stopped successfully!"
echo ""
echo "📊 Port Status:"
for port in 8888 8080 5000; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "   • Port $port: ⚠️  Still in use"
    else
        echo "   • Port $port: ✅ Free"
    fi
done

echo ""
echo "🚀 To start services again: make start"
