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
	@echo "  make allocate-ports - Allocate ports using portkeeper"
	@echo "  make release-ports  - Release allocated ports"
	@echo "  make port-status    - Show current port allocations"
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
HTTP_PORT ?= 8086
WEBSOCKET_PORT ?= 8086

# Check if dependencies are installed
check-deps:
	@echo "🔍 Checking dependencies..."
	@[ -f requirements.txt ] || (echo "❌ requirements.txt not found. Cannot check dependencies." && exit 1)
	@$(PYTHON) -c "import pkg_resources; [pkg_resources.require(r) for r in open('requirements.txt', 'r').read().splitlines() if r and not r.startswith('#')]" 2>/dev/null || \
		(echo "❌ Missing Python dependencies. Run 'make install' first." && exit 1)
	@$(PYTHON) -c "import sys; sys.path.insert(0, '../..'); import edpmt" 2>/dev/null || \
		(echo "❌ EDPMT not found. Please install EDPMT first." && exit 1)
	@echo "✅ All dependencies are available"

# Install dependencies using requirements.txt
install:
	@echo "📦 Installing dependencies from requirements.txt..."
	@$(PIP) install --user --break-system-packages -r requirements.txt
	@echo "🏗️  Checking EDPMT..."
	@$(PYTHON) -c "import sys; sys.path.insert(0, '../..'); import edpmt; print('✅ EDPMT available')" || \
		(echo "Installing EDPMT in editable mode..." && cd ../.. && $(PIP) install --user -e .)
	@echo "✅ Installation check completed successfully"

# Setup directories and example projects
setup:
	@echo "🏗️  Setting up directories and example projects..."
	@mkdir -p $(LOG_DIR)
	@mkdir -p $(PROJECTS_DIR)
	@echo "📁 Created directories: $(LOG_DIR), $(PROJECTS_DIR)"
	@$(PYTHON) -c "import json; \
		projects = [ \
			{'name': 'LED Blink', 'description': 'Simple LED blinking pattern', 'blocks': [{'type': 'start', 'position': {'x': 50, 'y': 50}, 'params': {}}, {'type': 'loop', 'position': {'x': 200, 'y': 50}, 'params': {'count': 10}}, {'type': 'gpio-output', 'position': {'x': 350, 'y': 50}, 'params': {'pin': 18, 'value': '1'}}, {'type': 'delay', 'position': {'x': 500, 'y': 50}, 'params': {'duration': 500}}, {'type': 'gpio-output', 'position': {'x': 650, 'y': 50}, 'params': {'pin': 18, 'value': '0'}}, {'type': 'delay', 'position': {'x': 800, 'y': 50}, 'params': {'duration': 500}}], 'version': '1.0'}, \
			{'name': 'Button Monitor', 'description': 'Monitor button presses and control LED', 'blocks': [{'type': 'start', 'position': {'x': 50, 'y': 50}, 'params': {}}, {'type': 'gpio-input', 'position': {'x': 200, 'y': 50}, 'params': {'pin': 2, 'mode': 'pull-up'}}, {'type': 'condition', 'position': {'x': 350, 'y': 50}, 'params': {'operator': '==', 'value': '0'}}, {'type': 'gpio-output', 'position': {'x': 500, 'y': 30}, 'params': {'pin': 18, 'value': '1'}}, {'type': 'gpio-output', 'position': {'x': 500, 'y': 90}, 'params': {'pin': 18, 'value': '0'}}], 'version': '1.0'}, \
			{'name': 'Traffic Light', 'description': 'Three-LED traffic light sequence', 'blocks': [{'type': 'start', 'position': {'x': 50, 'y': 50}, 'params': {}}, {'type': 'loop', 'position': {'x': 200, 'y': 50}, 'params': {'infinite': True}}, {'type': 'gpio-output', 'position': {'x': 350, 'y': 30}, 'params': {'pin': 18, 'value': '1'}}, {'type': 'delay', 'position': {'x': 500, 'y': 30}, 'params': {'duration': 3000}}, {'type': 'gpio-output', 'position': {'x': 650, 'y': 30}, 'params': {'pin': 18, 'value': '0'}}, {'type': 'gpio-output', 'position': {'x': 350, 'y': 70}, 'params': {'pin': 19, 'value': '1'}}, {'type': 'delay', 'position': {'x': 500, 'y': 70}, 'params': {'duration': 1000}}, {'type': 'gpio-output', 'position': {'x': 650, 'y': 70}, 'params': {'pin': 19, 'value': '0'}}, {'type': 'gpio-output', 'position': {'x': 350, 'y': 110}, 'params': {'pin': 20, 'value': '1'}}, {'type': 'delay', 'position': {'x': 500, 'y': 110}, 'params': {'duration': 3000}}, {'type': 'gpio-output', 'position': {'x': 650, 'y': 110}, 'params': {'pin': 20, 'value': '0'}}], 'version': '1.0'} \
		]; \
		[open(f'$(PROJECTS_DIR)/{p[\"name\"].replace(\" \", \"_\").lower()}.json', 'w').write(json.dumps(p, indent=2)) for p in projects]"
	@echo "✅ Setup completed - example projects created"

# Run in development mode (unified server serves static + WebSocket under /ws)
dev: stop check-deps setup
	@echo "🚀 Starting EDPMT Complete Frontend (Development Mode)..."
	@echo "🔧 Using hardware simulators - safe for development"
	@echo ""
	@$(PYTHON) $(SERVER_SCRIPT) --http-port $(HTTP_PORT) --verbose > $(LOG_DIR)/server-dev.log 2>&1 &
	@echo ""
	@echo "✅ Server is running in the background."
	@echo "   - Frontend available at: http://localhost:$(HTTP_PORT)"
	@echo "   - WebSocket endpoint:   ws://localhost:$(HTTP_PORT)/ws"
	@echo "   - Use 'make stop' to shut down the server."
	@echo "   - Logs are in the '$(LOG_DIR)' directory."
	@echo ""

# Run without port allocation (use existing ports from .env)
dev-quick: check-deps setup
	@echo "⚡ Starting EDPMT Complete Frontend (Quick Start - No Port Allocation)..."
	@echo "📄 Frontend will be available at: http://localhost:$(HTTP_PORT)"
	@echo "🔌 WebSocket server will run on: ws://localhost:$(WEBSOCKET_PORT)"
	@echo "🔧 Using existing ports from .env file"
	@echo ""
	@$(PYTHON) $(SERVER_SCRIPT) 2>&1 | tee $(LOG_DIR)/server-dev-quick.log

# Stop development server
stop:
	@echo "🛑 Stopping development server..."
	@pkill -f "^$(PYTHON) $(SERVER_SCRIPT)" || echo "Server was not running."
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
	@read -p "HTTP port [8086]: " http_port; \
	read -p "WebSocket port [8086]: " ws_port; \
	$(PYTHON) $(SERVER_SCRIPT) \
		--http-port $${http_port:-8086} \
		--ws-port $${ws_port:-8086} \
		--hardware-simulators \
		--verbose

# Monitor logs in real-time
logs:
	@echo "📄 Monitoring server logs (Ctrl+C to stop)..."
	@tail -f $(LOG_DIR)/server*.log 2>/dev/null || (echo "❌ No log files found. Start the server first." && exit 1)

# Show server status
status:
	@echo "🔍 EDPMT Complete Frontend Status:"
	@echo "=================================="
	@pgrep -f "$(SERVER_SCRIPT)" >/dev/null && echo "🟢 Server: Running" || echo "🔴 Server: Stopped"
	@curl -s http://localhost:$(FRONTEND_PORT)/api/status >/dev/null 2>&1 && echo "🟢 HTTP API: Responsive" || echo "🔴 HTTP API: Not responding"
	@test -f $(LOG_DIR)/server*.log && echo "📄 Logs: Available in $(LOG_DIR)/" || echo "📄 Logs: None found"
	@test -d $(PROJECTS_DIR) && echo "📁 Projects: $(shell ls $(PROJECTS_DIR)/*.json 2>/dev/null | wc -l) projects available" || echo "📁 Projects: Directory not found"

# Create project backup
backup:
	@echo "💾 Creating project backup..."
	@backup_name="projects_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz"; \
	tar -czf "$$backup_name" $(PROJECTS_DIR)/ $(LOG_DIR)/ 2>/dev/null && \
	echo "✅ Backup created: $$backup_name" || \
	echo "❌ Backup failed"

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
	@echo "📄 Frontend URL:       http://localhost:$(FRONTEND_PORT)"
	@echo "🔌 WebSocket URL:      ws://localhost:$(WEBSOCKET_PORT)"
	@echo "📁 Projects Dir:       $(PROJECTS_DIR)/"
	@echo "📄 Logs Dir:           $(LOG_DIR)/"
	@echo ""
	@echo "💡 For help: make help"

# Docker support (bonus)
docker-build:
	@echo "🐳 Building Docker image..."
	@docker build -t edpmt-frontend . || (echo "❌ Docker build failed" && exit 1)
	@echo "✅ Docker image built successfully"

docker-run:
	@echo "🐳 Running Docker container..."
	@docker run -d -p $(FRONTEND_PORT):$(FRONTEND_PORT) -p $(WEBSOCKET_PORT):$(WEBSOCKET_PORT) \
		--name edpmt-frontend edpmt-frontend || \
		(echo "❌ Docker run failed" && exit 1)
	@echo "✅ Docker container started"
	@echo "📄 Frontend: http://localhost:$(FRONTEND_PORT)"

docker-stop:
	@echo "🐳 Stopping Docker container..."
	@docker stop edpmt-frontend 2>/dev/null && docker rm edpmt-frontend 2>/dev/null || true
	@echo "✅ Docker container stopped"

# Show all available targets
targets:
	@echo "Available Makefile targets:"
	@echo "=========================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) 2>/dev/null || \
	grep -E '^[a-zA-Z_-]+:' $(MAKEFILE_LIST) | grep -v '^#' | sed 's/:.*//g' | sort
