# EDPMT Complete Frontend Makefile
# Provides simple commands to run the complete visual programming and peripheral control solution

.PHONY: help install run dev stop clean test setup check-deps

# Default target
help:
	@echo "EDPMT Complete Frontend - Visual Programming & Peripheral Control"
	@echo "================================================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make install     - Install dependencies and setup environment"
	@echo "  make run         - Run complete solution (production mode)"
	@echo "  make dev         - Run in development mode with simulators (dynamic ports)"
	@echo "  make setup       - Create example projects and setup directories"
	@echo "  make test        - Test the frontend and backend integration"
	@echo "  make check-deps  - Check if all dependencies are installed"
	@echo "  make stop        - Stop running servers"
	@echo "  make clean       - Clean temporary files and logs"
	@echo ""
	@echo "Quick start:"
	@echo "  1. make install"
	@echo "  2. make dev"
	@echo "  3. Open http://localhost:$(HTTP_PORT) in your browser (dynamic port)"
	@echo ""

# Variables
PYTHON := python3
PIP := pip3
PORT_MANAGER := port_manager.py
SERVER_SCRIPT := server.py
LOG_DIR := logs
PROJECTS_DIR := projects
STATIC_DIR := static

# Load environment variables from .env (for display purposes)
-include .env
export

# Default ports (will be overridden by .env after allocation)
HTTP_PORT ?= 8085
WEBSOCKET_PORT ?= 8085

# Check if dependencies are installed
check-deps:
	@PYTHON=$(PYTHON) bash scripts/check_deps.sh

# Install dependencies using requirements.txt
install:
	@PYTHON=$(PYTHON) PIP=$(PIP) bash scripts/install.sh

# Setup directories and example projects
setup:
	@PYTHON=$(PYTHON) PROJECTS_DIR=$(PROJECTS_DIR) LOG_DIR=$(LOG_DIR) bash scripts/setup.sh

# Run in development mode (unified server serves static + WebSocket under /ws)
dev: stop check-deps test setup check-ports
	@HTTP_PORT=$(HTTP_PORT) PYTHON=$(PYTHON) SERVER_SCRIPT=$(SERVER_SCRIPT) LOG_DIR=$(LOG_DIR) bash scripts/dev.sh

# Check if target port is free (returns non-zero if busy)
check-ports:
	@HTTP_PORT=$(HTTP_PORT) bash scripts/check_ports.sh

# Stop development server
stop:
	@echo "🛑 Stopping development server..."
	@pkill -f "$(SERVER_SCRIPT)" || echo "Server was not running."
	@echo "✅ Server stopped."

# Clean temporary files
clean:
	@echo "🧹 Cleaning up..."
	@rm -rf $(LOG_DIR)/*.log 2>/dev/null && echo "✅ Cleared log files" || echo "ℹ️  No log files to clean"
	@rm -rf __pycache__ 2>/dev/null && echo "✅ Cleared Python cache" || echo "ℹ️  No Python cache to clean"
	@rm -rf .pytest_cache 2>/dev/null && echo "✅ Cleared test cache" || echo "ℹ️  No test cache to clean"
	@find . -name "*.pyc" -delete 2>/dev/null && echo "✅ Cleared Python bytecode" || echo "ℹ️  No bytecode files found"
	@echo "✅ Cleanup completed"

# Advanced targets for development

# Run with custom ports
run-custom:
	@PYTHON=$(PYTHON) SERVER_SCRIPT=$(SERVER_SCRIPT) bash scripts/run_custom.sh

# Monitor logs in real-time
logs:
	@echo "📄 Monitoring server logs (Ctrl+C to stop)..."
	@tail -f $(LOG_DIR)/server*.log 2>/dev/null || (echo "❌ No log files found. Start the server first." && exit 1)

# Show server status
status:
	@HTTP_PORT=$(HTTP_PORT) LOG_DIR=$(LOG_DIR) PROJECTS_DIR=$(PROJECTS_DIR) SERVER_SCRIPT=$(SERVER_SCRIPT) bash scripts/status.sh

# Show all available targets
targets:
	@echo "Available Makefile targets:"
	@echo "=========================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) 2>/dev/null || \
	grep -E '^[a-zA-Z_-]+:' $(MAKEFILE_LIST) | grep -v '^#' | sed 's/:.*//g' | sort

# Test the complete solution (starts a temporary server and probes endpoints)
test: check-deps
	@PYTHON=$(PYTHON) SERVER_SCRIPT=$(SERVER_SCRIPT) LOG_DIR=$(LOG_DIR) bash scripts/test.sh

# Continuous monitoring: check endpoints every 5s and tail logs
monitor:
	@HTTP_PORT=$(HTTP_PORT) LOG_DIR=$(LOG_DIR) bash scripts/monitor.sh

# Start dev then monitor continuously
dev-watch: dev monitor

# Docker support (bonus)
docker-build:
	@echo "🐳 Building Docker image..."
	@docker build -t edpmt-frontend . || (echo "❌ Docker build failed" && exit 1)
	@echo "✅ Docker image built successfully"

docker-run:
	@echo "🐳 Running Docker container..."
	@docker run -d -p $(HTTP_PORT):$(HTTP_PORT) -p $(WEBSOCKET_PORT):$(WEBSOCKET_PORT) \
		--name edpmt-frontend edpmt-frontend || \
		(echo "❌ Docker run failed" && exit 1)
	@echo "✅ Docker container started"
	@echo "📄 Frontend: http://localhost:$(HTTP_PORT)"

docker-stop:
	@echo "🐳 Stopping Docker container..."
	@docker stop edpmt-frontend 2>/dev/null && docker rm edpmt-frontend 2>/dev/null || true
	@echo "✅ Docker container stopped"

# Show quick reference
quick-ref:
	@echo "EDPMT Complete Frontend - Quick Reference"
	@echo "========================================"
	@echo ""
	@echo "🚀 Start Development:  make dev"
	@echo "🚀 Start Production:   make run"
	@echo "🛑 Stop Servers:       make stop"
	@echo "🧪 Run Tests:          make test"
	@echo "🧹 Clean Files:        make clean"
	@echo ""
	@echo "📄 Frontend URL:       http://localhost:$(HTTP_PORT)"
	@echo "🔌 WebSocket URL:      ws://localhost:$(HTTP_PORT)/ws"
	@echo "📁 Projects Dir:       $(PROJECTS_DIR)/"
	@echo "📄 Logs Dir:           $(LOG_DIR)/"
	@echo ""
	@echo "💡 For help: make help"

# Create project backup
backup:
	@echo "💾 Creating project backup..."
	@backup_name="projects_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz"; \
	tar -czf "$$backup_name" $(PROJECTS_DIR)/ $(LOG_DIR)/ 2>/dev/null && \
	echo "✅ Backup created: $$backup_name" || \
	echo "❌ Backup failed"
