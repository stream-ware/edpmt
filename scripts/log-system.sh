#!/bin/bash

# Enhanced Logging System for Codialog Project
# Captures, analyzes, and provides auto-fix for all Makefile commands

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/logs"
SYSTEM_LOG_DIR="$LOG_DIR/system"
COMMAND_LOG_DIR="$LOG_DIR/commands"
ERROR_LOG_DIR="$LOG_DIR/errors"
ANALYSIS_LOG_DIR="$LOG_DIR/analysis"

# Create log directories
create_log_structure() {
    echo -e "${BLUE}Creating log directory structure...${NC}"
    mkdir -p "$LOG_DIR"/{app,debug,error,system,commands,errors,analysis,docker,database,bitwarden,tests}
    touch "$LOG_DIR/system/system.log"
    touch "$LOG_DIR/commands/commands.log"
    touch "$LOG_DIR/errors/errors.log"
    touch "$LOG_DIR/analysis/analysis.log"
    echo -e "${GREEN}Log structure created successfully${NC}"
}

# Enhanced logging function
log_enhanced() {
    local level="$1"
    local component="$2"
    local message="$3"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Log to appropriate files
    echo "[$timestamp] [$level] [$component] $message" >> "$LOG_DIR/system/system.log"
    
    case $level in
        "ERROR")
            echo "[$timestamp] [$component] $message" >> "$LOG_DIR/errors/errors.log"
            echo -e "${RED}[$level]${NC} [$component] $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[$level]${NC} [$component] $message"
            ;;
        "INFO")
            echo -e "${GREEN}[$level]${NC} [$component] $message"
            ;;
        "DEBUG")
            echo "[$timestamp] [$component] $message" >> "$LOG_DIR/debug/debug.log"
            echo -e "${BLUE}[$level]${NC} [$component] $message"
            ;;
    esac
}

# Execute command with enhanced logging
execute_with_logging() {
    local command="$1"
    local component="${2:-SYSTEM}"
    local log_file="$COMMAND_LOG_DIR/${component,,}.log"
    
    log_enhanced "INFO" "$component" "Executing: $command"
    
    # Create command-specific log file
    mkdir -p "$COMMAND_LOG_DIR"
    
    # Execute command and capture both stdout and stderr
    if eval "$command" 2>&1 | tee -a "$log_file"; then
        log_enhanced "INFO" "$component" "Command completed successfully"
        return 0
    else
        local exit_code=$?
        log_enhanced "ERROR" "$component" "Command failed with exit code: $exit_code"
        analyze_error "$component" "$command" "$exit_code"
        return $exit_code
    fi
}

# Analyze errors and provide auto-fix suggestions
analyze_error() {
    local component="$1"
    local command="$2"
    local exit_code="$3"
    local analysis_file="$ANALYSIS_LOG_DIR/${component,,}_analysis.log"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] Analyzing error for $component" >> "$analysis_file"
    echo "Command: $command" >> "$analysis_file"
    echo "Exit Code: $exit_code" >> "$analysis_file"
    
    # Get recent error logs
    local recent_errors=$(tail -20 "$LOG_DIR/errors/errors.log" 2>/dev/null || echo "No recent errors")
    
    # Analyze common error patterns and suggest fixes
    case "$component" in
        "DATABASE"|"DB")
            analyze_database_errors "$analysis_file" "$recent_errors"
            ;;
        "DOCKER")
            analyze_docker_errors "$analysis_file" "$recent_errors"
            ;;
        "RUST"|"CARGO")
            analyze_rust_errors "$analysis_file" "$recent_errors"
            ;;
        "NODE"|"NPM")
            analyze_node_errors "$analysis_file" "$recent_errors"
            ;;
        "BITWARDEN"|"BW")
            analyze_bitwarden_errors "$analysis_file" "$recent_errors"
            ;;
        *)
            analyze_generic_errors "$analysis_file" "$recent_errors"
            ;;
    esac
    
    # Display analysis results
    echo -e "${YELLOW}Error Analysis for $component:${NC}"
    tail -10 "$analysis_file"
}

# Specific error analyzers
analyze_database_errors() {
    local analysis_file="$1"
    local recent_errors="$2"
    
    echo "Database Error Analysis:" >> "$analysis_file"
    
    if echo "$recent_errors" | grep -q "connection.*refused\|timeout\|Failed to connect"; then
        echo "ISSUE: Database connection failed" >> "$analysis_file"
        echo "SUGGESTED FIX: Run 'make docker-up' to start PostgreSQL" >> "$analysis_file"
        echo "ALTERNATIVE: Check if DATABASE_URL is correct in .env" >> "$analysis_file"
        
        echo -e "${YELLOW}Auto-fix suggestion: Database connection issue${NC}"
        echo -e "${BLUE}Run: make docker-up${NC}"
    fi
    
    if echo "$recent_errors" | grep -q "permission denied\|authentication failed"; then
        echo "ISSUE: Database authentication failed" >> "$analysis_file"
        echo "SUGGESTED FIX: Check database credentials in .env file" >> "$analysis_file"
        echo "ALTERNATIVE: Reset database with 'make db-reset'" >> "$analysis_file"
    fi
}

analyze_docker_errors() {
    local analysis_file="$1"
    local recent_errors="$2"
    
    echo "Docker Error Analysis:" >> "$analysis_file"
    
    if echo "$recent_errors" | grep -q "Cannot connect to the Docker daemon"; then
        echo "ISSUE: Docker daemon not running" >> "$analysis_file"
        echo "SUGGESTED FIX: Start Docker service: sudo systemctl start docker" >> "$analysis_file"
        
        echo -e "${YELLOW}Auto-fix suggestion: Docker daemon not running${NC}"
        echo -e "${BLUE}Run: sudo systemctl start docker${NC}"
    fi
    
    if echo "$recent_errors" | grep -q "port.*already in use\|bind.*address already in use"; then
        echo "ISSUE: Port already in use" >> "$analysis_file"
        echo "SUGGESTED FIX: Stop conflicting services with 'make docker-down'" >> "$analysis_file"
        echo "ALTERNATIVE: Check running processes with 'sudo lsof -i :5432'" >> "$analysis_file"
    fi
}

analyze_rust_errors() {
    local analysis_file="$1"
    local recent_errors="$2"
    
    echo "Rust/Cargo Error Analysis:" >> "$analysis_file"
    
    if echo "$recent_errors" | grep -q "connect_timeout.*found\|no method.*connect_timeout"; then
        echo "ISSUE: SQLx API usage error" >> "$analysis_file"
        echo "SUGGESTED FIX: Use correct SQLx connection timeout API" >> "$analysis_file"
        echo "ALTERNATIVE: Update sqlx crate version" >> "$analysis_file"
        
        echo -e "${YELLOW}Auto-fix suggestion: SQLx API error${NC}"
        echo -e "${BLUE}Check SQLx documentation for correct timeout usage${NC}"
    fi
    
    if echo "$recent_errors" | grep -q "compilation failed\|error.*compiling"; then
        echo "ISSUE: Compilation failed" >> "$analysis_file"
        echo "SUGGESTED FIX: Run 'cargo clean' then 'cargo build'" >> "$analysis_file"
        echo "ALTERNATIVE: Check for syntax errors in Rust code" >> "$analysis_file"
    fi
}

analyze_node_errors() {
    local analysis_file="$1"
    local recent_errors="$2"
    
    echo "Node/NPM Error Analysis:" >> "$analysis_file"
    
    if echo "$recent_errors" | grep -q "MODULE_NOT_FOUND\|Cannot resolve module"; then
        echo "ISSUE: Missing Node.js dependencies" >> "$analysis_file"
        echo "SUGGESTED FIX: Run 'npm install' or 'yarn install'" >> "$analysis_file"
    fi
    
    if echo "$recent_errors" | grep -q "EACCES.*permission denied"; then
        echo "ISSUE: Permission denied for npm operations" >> "$analysis_file"
        echo "SUGGESTED FIX: Use 'npm install --no-optional' or check npm permissions" >> "$analysis_file"
    fi
}

analyze_bitwarden_errors() {
    local analysis_file="$1"
    local recent_errors="$2"
    
    echo "Bitwarden Error Analysis:" >> "$analysis_file"
    
    if echo "$recent_errors" | grep -q "not logged in\|authentication required"; then
        echo "ISSUE: Bitwarden not authenticated" >> "$analysis_file"
        echo "SUGGESTED FIX: Run 'make bw-unlock' to authenticate" >> "$analysis_file"
    fi
    
    if echo "$recent_errors" | grep -q "vault locked\|session.*expired"; then
        echo "ISSUE: Bitwarden vault locked" >> "$analysis_file"
        echo "SUGGESTED FIX: Unlock vault with 'make bw-unlock'" >> "$analysis_file"
    fi
}

analyze_generic_errors() {
    local analysis_file="$1"
    local recent_errors="$2"
    
    echo "Generic Error Analysis:" >> "$analysis_file"
    
    if echo "$recent_errors" | grep -q "Permission denied\|EACCES"; then
        echo "ISSUE: Permission denied" >> "$analysis_file"
        echo "SUGGESTED FIX: Check file permissions or run with appropriate privileges" >> "$analysis_file"
    fi
    
    if echo "$recent_errors" | grep -q "No such file or directory"; then
        echo "ISSUE: File not found" >> "$analysis_file"
        echo "SUGGESTED FIX: Ensure all required files exist, run 'make setup'" >> "$analysis_file"
    fi
}

# Generate comprehensive log report
generate_log_report() {
    local report_file="$LOG_DIR/analysis/daily_report_$(date +%Y%m%d).log"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "=== CODIALOG LOG REPORT - $timestamp ===" > "$report_file"
    echo "" >> "$report_file"
    
    # System status
    echo "SYSTEM STATUS:" >> "$report_file"
    echo "- Total log entries: $(wc -l < "$LOG_DIR/system/system.log" 2>/dev/null || echo "0")" >> "$report_file"
    echo "- Error entries: $(wc -l < "$LOG_DIR/errors/errors.log" 2>/dev/null || echo "0")" >> "$report_file"
    echo "- Commands executed: $(ls -1 "$COMMAND_LOG_DIR" 2>/dev/null | wc -l || echo "0")" >> "$report_file"
    echo "" >> "$report_file"
    
    # Recent errors
    echo "RECENT ERRORS (last 10):" >> "$report_file"
    tail -10 "$LOG_DIR/errors/errors.log" 2>/dev/null >> "$report_file" || echo "No recent errors" >> "$report_file"
    echo "" >> "$report_file"
    
    # Component analysis
    echo "COMPONENT ANALYSIS:" >> "$report_file"
    shopt -s nullglob
    log_files=("$COMMAND_LOG_DIR"/*.log)
    if [ ${#log_files[@]} -gt 0 ]; then
        for component_log in "${log_files[@]}"; do
            if [[ -f "$component_log" ]]; then
                local component_name=$(basename "$component_log" .log)
                echo "- $component_name: $(wc -l < "$component_log") log entries" >> "$report_file"
            fi
        done
    else
        echo "- No component logs found" >> "$report_file"
    fi
    shopt -u nullglob
    
    echo -e "${GREEN}Log report generated: $report_file${NC}"
}

# Clean old logs (keep last 7 days)
clean_old_logs() {
    log_enhanced "INFO" "CLEANUP" "Cleaning logs older than 7 days"
    
    find "$LOG_DIR" -name "*.log" -mtime +7 -exec rm {} \; 2>/dev/null || true
    find "$LOG_DIR" -name "*_report_*.log" -mtime +7 -exec rm {} \; 2>/dev/null || true
    
    log_enhanced "INFO" "CLEANUP" "Old logs cleaned successfully"
}

# Auto-fix attempt based on analysis
auto_fix_attempt() {
    local component="$1"
    local analysis_file="$ANALYSIS_LOG_DIR/${component,,}_analysis.log"
    
    if [[ ! -f "$analysis_file" ]]; then
        log_enhanced "WARN" "AUTO_FIX" "No analysis file found for $component"
        return 1
    fi
    
    log_enhanced "INFO" "AUTO_FIX" "Attempting auto-fix for $component"
    
    # Read suggested fixes from analysis
    local suggested_fix=$(grep "SUGGESTED FIX:" "$analysis_file" | head -1 | cut -d':' -f2- | xargs)
    
    if [[ -n "$suggested_fix" ]]; then
        echo -e "${YELLOW}Suggested fix: $suggested_fix${NC}"
        echo -e "${BLUE}Would you like to apply this fix? (y/N):${NC}"
        
        # For automation, we can add auto-apply logic here
        # For now, we just log the suggestion
        log_enhanced "INFO" "AUTO_FIX" "Suggested fix for $component: $suggested_fix"
    else
        log_enhanced "WARN" "AUTO_FIX" "No automatic fix available for $component"
    fi
}

# Main function
main() {
    local action="${1:-help}"
    
    case "$action" in
        "init")
            create_log_structure
            log_enhanced "INFO" "SYSTEM" "Log system initialized"
            ;;
        "execute")
            execute_with_logging "$2" "$3"
            ;;
        "analyze")
            analyze_error "$2" "$3" "$4"
            ;;
        "report")
            generate_log_report
            ;;
        "clean")
            clean_old_logs
            ;;
        "auto-fix")
            auto_fix_attempt "$2"
            ;;
        "help")
            echo -e "${GREEN}Codialog Log System${NC}"
            echo "Usage: $0 [action] [args...]"
            echo ""
            echo "Actions:"
            echo "  init                   - Initialize log directory structure"
            echo "  execute <cmd> <comp>   - Execute command with logging"
            echo "  analyze <comp> <cmd> <code> - Analyze error for component"
            echo "  report                 - Generate log report"
            echo "  clean                  - Clean old logs"
            echo "  auto-fix <comp>        - Attempt auto-fix for component"
            echo "  help                   - Show this help"
            ;;
        *)
            echo -e "${RED}Unknown action: $action${NC}"
            exit 1
            ;;
    esac
}

# Initialize log system if not already done
if [[ ! -d "$LOG_DIR/system" ]]; then
    create_log_structure
fi

# Only run main function if script is executed directly, not sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
