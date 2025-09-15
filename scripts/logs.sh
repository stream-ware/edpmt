#!/bin/bash

# EDPMT All Services Logs Viewer
echo " EDPMT Services Logs"
echo "======================"

# Function to show log file info
show_log_info() {
    local log_file=$1
    local service_name=$2
    
    if [ -f "$log_file" ]; then
        local size=$(du -h "$log_file" | cut -f1)
        local lines=$(wc -l < "$log_file")
        local modified=$(date -r "$log_file" "+%Y-%m-%d %H:%M:%S")
        echo " $service_name Log ($log_file)"
        echo "   • Size: $size"
        echo "   • Lines: $lines"
        echo "   • Modified: $modified"
        echo ""
    else
        echo " $service_name Log: Not found"
        echo ""
    fi
}

# Check command line arguments
FOLLOW_MODE=false
LINES=50

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW_MODE=true
            shift
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -f, --follow     Follow log output (like tail -f)"
            echo "  -n, --lines N    Show last N lines (default: 50)"
            echo "  -h, --help       Show this help"
            echo ""
            echo "Examples:"
            echo "  $0               Show last 50 lines from all logs"
            echo "  $0 -n 100        Show last 100 lines from all logs"
            echo "  $0 -f            Follow all logs in real-time"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Show log file information
show_log_info "/tmp/edpmt-server.log" "EDPMT Server"
show_log_info "/tmp/edpmt-visual.log" "Visual Programming Interface"

if [ "$FOLLOW_MODE" = true ]; then
    echo " Following logs in real-time (Press Ctrl+C to stop)..."
    echo "======================================================="
    
    # Follow both logs if they exist
    LOG_FILES=""
    if [ -f "/tmp/edpmt-server.log" ]; then
        LOG_FILES="/tmp/edpmt-server.log"
    fi
    if [ -f "/tmp/edpmt-visual.log" ]; then
        LOG_FILES="$LOG_FILES /tmp/edpmt-visual.log"
    fi
    
    if [ ! -z "$LOG_FILES" ]; then
        tail -f $LOG_FILES
    else
        echo " No log files found to follow"
        exit 1
    fi
else
    # Show last N lines from each log
    echo " EDPMT Server Logs (last $LINES lines):"
    echo "========================================="
    if [ -f "/tmp/edpmt-server.log" ]; then
        tail -n "$LINES" /tmp/edpmt-server.log
    else
        echo " No server log found"
    fi
    
    echo ""
    echo " Visual Programming Logs (last $LINES lines):"
    echo "==============================================="
    if [ -f "/tmp/edpmt-visual.log" ]; then
        tail -n "$LINES" /tmp/edpmt-visual.log
    else
        echo " No visual programming log found"
    fi
fi

echo ""
echo " Tips:"
echo "   • Use 'make logs -f' to follow logs in real-time"
echo "   • Use 'make logs -n 100' to show more lines"
echo "   • Use 'make status' to check service status"
