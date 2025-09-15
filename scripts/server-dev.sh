#!/bin/bash

echo "🚀 Starting EDPMT server in development mode..."

# Function to check if a port is available
function is_port_available() {
    local port=$1
    if ! command -v netstat &> /dev/null; then
        echo "netstat not found, using alternative method"
        ! ss -tuln | grep -q ":$port "
    else
        ! netstat -tuln | grep -q ":$port "
    fi
}

# Function to find an available port
function find_available_port() {
    local start_port=$1
    local end_port=$2
    local port=$start_port
    while [ $port -le $end_port ]; do
        if is_port_available $port; then
            echo $port
            return 0
        fi
        port=$((port + 1))
    done
    echo ""
    return 1
}

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env"
    set -a
    source .env
    set +a
fi

# Default port range if not set in .env
EDPM_PORT_RANGE_START=${EDPM_PORT_RANGE_START:-8888}
EDPM_PORT_RANGE_END=${EDPM_PORT_RANGE_END:-8898}

# Find an available port
PORT=$(find_available_port $EDPM_PORT_RANGE_START $EDPM_PORT_RANGE_END)
if [ -z "$PORT" ]; then
    echo "❌ No available port found in range $EDPM_PORT_RANGE_START to $EDPM_PORT_RANGE_END"
    exit 1
else
    echo "🌐 Using port: $PORT"
fi

# Start the server with the selected port
edpmt server --dev --port $PORT
