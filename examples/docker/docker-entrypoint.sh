#!/bin/bash
set -e

# EDPMT Docker Entrypoint Script
# Handles initialization, hardware detection, and service startup

echo "🚀 Starting EDPMT Transparent Server..."
echo "   Version: 1.0.0"
echo "   Build: $(date)"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Detect hardware platform
detect_platform() {
    if [ -f /proc/cpuinfo ]; then
        if grep -q "Raspberry Pi" /proc/cpuinfo; then
            echo "raspberry_pi"
        elif grep -q "NVIDIA Tegra" /proc/cpuinfo; then
            echo "nvidia_jetson"
        else
            echo "linux_generic"
        fi
    else
        echo "unknown"
    fi
}

# Check hardware access permissions
check_hardware_access() {
    local platform=$1
    log "🔍 Checking hardware access permissions..."
    
    # Check GPIO access
    if [ -c /dev/gpiomem ]; then
        log "✅ GPIO access: Available (/dev/gpiomem)"
    elif [ -c /dev/mem ]; then
        log "⚠️  GPIO access: Available via /dev/mem (requires root)"
    else
        log "❌ GPIO access: Not available"
    fi
    
    # Check I2C access
    if [ -c /dev/i2c-1 ]; then
        log "✅ I2C access: Available (/dev/i2c-1)"
    else
        log "❌ I2C access: Not available"
    fi
    
    # Check SPI access  
    if [ -c /dev/spidev0.0 ]; then
        log "✅ SPI access: Available (/dev/spidev0.0)"
    else
        log "❌ SPI access: Not available"
    fi
    
    # Check UART access
    if [ -c /dev/ttyAMA0 ] || [ -c /dev/serial0 ]; then
        log "✅ UART access: Available"
    else
        log "❌ UART access: Not available"
    fi
}

# Initialize EDPMT configuration
init_config() {
    log "⚙️  Initializing EDPMT configuration..."
    
    # Create config directories if they don't exist
    mkdir -p /root/.edpm/{certs,logs,config}
    
    # Set permissions
    chmod 755 /root/.edpm
    chmod 700 /root/.edpm/certs
    chmod 755 /root/.edpm/logs
    chmod 755 /root/.edpm/config
    
    # Initialize default config if not exists
    if [ ! -f /root/.edpm/config/edpm.json ]; then
        log "📝 Creating default configuration..."
        python3 -c "
from edpmt.utils import ConfigManager
config = ConfigManager()
config.save_config()
print('✅ Default configuration created')
"
    fi
    
    log "✅ Configuration initialized"
}

# Wait for hardware to be ready
wait_for_hardware() {
    log "⏳ Waiting for hardware to be ready..."
    
    # Give the system time to initialize hardware interfaces
    sleep 2
    
    # Test basic system access
    if [ -r /proc/cpuinfo ]; then
        log "✅ System information accessible"
    fi
    
    log "✅ Hardware initialization complete"
}

# Generate TLS certificates if needed
setup_tls() {
    if [ "${EDPM_TLS:-true}" = "true" ]; then
        log "🔐 Setting up TLS certificates..."
        
        if [ ! -f /root/.edpm/certs/edpm.crt ] || [ ! -f /root/.edpm/certs/edpm.key ]; then
            log "📜 Generating self-signed certificates..."
            python3 -c "
from edpmt.utils import generate_certificates
from pathlib import Path
cert_dir = Path('/root/.edpm/certs')
cert_dir.mkdir(parents=True, exist_ok=True)
generate_certificates(
    cert_dir / 'edpm.crt',
    cert_dir / 'edpm.key',
    common_name='edpmt-server'
)
print('✅ TLS certificates generated')
"
        else
            log "✅ TLS certificates already exist"
        fi
    else
        log "⚠️  TLS disabled - running in insecure mode"
    fi
}

# Main initialization
main() {
    log "🔧 EDPMT Docker Container Starting..."
    
    # Detect platform
    PLATFORM=$(detect_platform)
    log "🖥️  Platform detected: $PLATFORM"
    
    # Check hardware access
    check_hardware_access "$PLATFORM"
    
    # Wait for hardware
    wait_for_hardware
    
    # Initialize configuration
    init_config
    
    # Setup TLS if enabled
    setup_tls
    
    # Print final status
    log "🎯 Configuration Summary:"
    log "   • Platform: $PLATFORM"
    log "   • TLS: ${EDPM_TLS:-true}"
    log "   • Host: ${EDPM_HOST:-0.0.0.0}"
    log "   • Port: ${EDPM_PORT:-8888}"
    log "   • Development Mode: ${EDPM_DEV:-false}"
    
    # Print access URLs
    PROTOCOL="https"
    if [ "${EDPM_TLS:-true}" = "false" ]; then
        PROTOCOL="http"
    fi
    
    log "🌐 Access Points:"
    log "   • Web Interface: $PROTOCOL://localhost:${EDPM_PORT:-8888}"
    log "   • REST API: $PROTOCOL://localhost:${EDPM_PORT:-8888}/api/execute"
    log "   • WebSocket: ${PROTOCOL/http/ws}://localhost:${EDPM_PORT:-8888}/ws"
    log "   • Health Check: $PROTOCOL://localhost:${EDPM_PORT:-8888}/health"
    
    log "🚀 Starting EDPMT server..."
    
    # Execute the main command
    exec "$@"
}

# Handle signals gracefully
cleanup() {
    log "🛑 Received shutdown signal, cleaning up..."
    # Kill any background processes
    jobs -p | xargs -r kill
    log "✅ Cleanup complete"
    exit 0
}

trap cleanup SIGTERM SIGINT

# Run main function
main "$@"
