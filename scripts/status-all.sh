#!/bin/bash

# EDPMT All Services Status Script
echo "📊 EDPMT Services Status"
echo "========================"

# Load configuration if available
if [ -f /tmp/edpmt-pids/config.env ]; then
    source /tmp/edpmt-pids/config.env
    echo "📋 Configuration loaded from /tmp/edpmt-pids/config.env"
    echo ""
else
    echo "⚠️  No configuration file found"
    echo ""
fi

# Function to check service status
check_service_status() {
    local service_name=$1
    local pid_file=$2
    local expected_port=$3
    
    echo "🔍 $service_name:"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "   • Status: ✅ Running (PID: $pid)"
            
            # Get process info
            local process_info=$(ps -p "$pid" -o pid,ppid,etime,cmd --no-headers 2>/dev/null)
            if [ ! -z "$process_info" ]; then
                echo "   • Process: $process_info"
            fi
            
            # Check memory usage
            local memory=$(ps -p "$pid" -o rss --no-headers 2>/dev/null)
            if [ ! -z "$memory" ]; then
                echo "   • Memory: $((memory / 1024)) MB"
            fi
        else
            echo "   • Status: ❌ Not running (stale PID file)"
            rm -f "$pid_file"
        fi
    else
        echo "   • Status: ❌ Not running (no PID file)"
    fi
    
    # Check port
    if [ ! -z "$expected_port" ]; then
        if lsof -Pi :$expected_port -sTCP:LISTEN -t >/dev/null 2>&1; then
            local port_pid=$(lsof -Pi :$expected_port -sTCP:LISTEN -t 2>/dev/null)
            echo "   • Port $expected_port: ✅ In use (PID: $port_pid)"
        else
            echo "   • Port $expected_port: ❌ Free"
        fi
    fi
    
    echo ""
}

# Check individual services
check_service_status "EDPMT Server" "/tmp/edpmt-pids/server.pid" "$EDPMT_PORT"
check_service_status "Visual Programming Interface" "/tmp/edpmt-pids/visual.pid" "$VISUAL_PORT"

# Check for any other EDPMT processes
echo "🔍 Other EDPMT Processes:"
EDPMT_PROCESSES=$(pgrep -f "edpmt" 2>/dev/null || true)
if [ ! -z "$EDPMT_PROCESSES" ]; then
    echo "$EDPMT_PROCESSES" | while read pid; do
        if [ ! -z "$pid" ]; then
            local process_info=$(ps -p "$pid" -o pid,etime,cmd --no-headers 2>/dev/null)
            echo "   • PID $pid: $process_info"
        fi
    done
else
    echo "   • No additional EDPMT processes found"
fi
echo ""

# Check Python HTTP servers
echo "🔍 Python HTTP Servers:"
PYTHON_SERVERS=$(pgrep -f "python.*http.server" 2>/dev/null || true)
if [ ! -z "$PYTHON_SERVERS" ]; then
    echo "$PYTHON_SERVERS" | while read pid; do
        if [ ! -z "$pid" ]; then
            local process_info=$(ps -p "$pid" -o pid,etime,cmd --no-headers 2>/dev/null)
            echo "   • PID $pid: $process_info"
        fi
    done
else
    echo "   • No Python HTTP servers found"
fi
echo ""

# Port overview
echo "🌐 Port Overview:"
for port in 8888 8080 5000 3000; do
    if lsof -Pi :$port -sTCP:LISTEN >/dev/null 2>&1; then
        local port_info=$(lsof -Pi :$port -sTCP:LISTEN -F p,c,n 2>/dev/null | head -3)
        local port_pid=$(echo "$port_info" | grep "^p" | cut -c2-)
        local port_cmd=$(echo "$port_info" | grep "^c" | cut -c2-)
        echo "   • Port $port: ⚠️  In use by $port_cmd (PID: $port_pid)"
    else
        echo "   • Port $port: ✅ Available"
    fi
done
echo ""

# System resources
echo "💾 System Resources:"
echo "   • Load Average: $(uptime | awk '{print $(NF-2) $(NF-1) $NF}')"
echo "   • Memory Usage: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2 " (" $3/$2*100 "% used)"}')"
echo "   • Disk Usage: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
echo ""

# Service URLs (if running)
if [ ! -z "$EDPMT_PORT" ] && [ ! -z "$VISUAL_PORT" ]; then
    if lsof -Pi :$EDPMT_PORT -sTCP:LISTEN >/dev/null 2>&1 && lsof -Pi :$VISUAL_PORT -sTCP:LISTEN >/dev/null 2>&1; then
        echo "🔗 Service URLs:"
        echo "   • EDPMT Server: https://localhost:$EDPMT_PORT"
        echo "   • Visual Programming: http://localhost:$VISUAL_PORT"
        echo "   • WebSocket: wss://localhost:$EDPMT_PORT/ws"
        echo ""
    fi
fi

# Log files
echo "📋 Log Files:"
for log_file in /tmp/edpmt-server.log /tmp/edpmt-visual.log; do
    if [ -f "$log_file" ]; then
        local size=$(du -h "$log_file" | cut -f1)
        local lines=$(wc -l < "$log_file")
        echo "   • $log_file: $size ($lines lines)"
    else
        echo "   • $log_file: Not found"
    fi
done
