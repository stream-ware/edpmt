# EDPMT (Electronic Device Protocol Management Transparent) Makefile

# Default target
all: setup-dev install test-all

# ==============================================================================
# DEVELOPMENT SETUP
# ==============================================================================

# Setup development environment
setup-dev:
	@bash scripts/setup-dev.sh

# Install package in development mode
install:
	@bash scripts/install.sh

# Install with all optional dependencies
install-all:
	@echo "📦 Installing EDPMT with all dependencies..."
	pip install -e .[all]
	@echo "✅ EDPMT with all dependencies installed"

# Development setup using PYTHONPATH (no installation required)
dev-setup:
	@echo "🛠️  Setting up EDPMT for development using PYTHONPATH..."
	@echo "📁 Project root: $$(pwd)"
	@echo "🐍 Python version: $$(python3 --version)"
	@echo "📝 Testing EDPMT import..."
	@PYTHONPATH="$$(pwd):$$PYTHONPATH" python3 -c "import edpmt; print(f'✅ EDPMT {edpmt.__version__} loaded via PYTHONPATH')" || { \
		echo "❌ EDPMT import failed"; \
		echo "💡 Make sure you're in the correct directory: $$(pwd)"; \
		exit 1; \
	}
	@echo "🎯 Creating CLI wrapper script..."
	@mkdir -p bin
	@echo '#!/bin/bash' > bin/edpmt
	@echo 'export PYTHONPATH="'"$$(pwd)"':$$PYTHONPATH"' >> bin/edpmt
	@echo 'python3 -m edpmt.cli "$$@"' >> bin/edpmt
	@chmod +x bin/edpmt
	@echo "✅ Development setup complete!"
	@echo "💡 To use EDPMT:"
	@echo "   1. Add to PATH: export PATH=$$(pwd)/bin:$$PATH"
	@echo "   2. Or use directly: ./bin/edpmt server --dev"
	@echo "   3. Or set PYTHONPATH: export PYTHONPATH=$$(pwd):$$PYTHONPATH"

# Create and setup virtual environment
venv-setup:
	@echo "🐍 Creating virtual environment..."
	@python3 -m venv venv --without-pip 2>/dev/null || python3 -m venv venv
	@echo "📦 Installing EDPMT in virtual environment..."
	@venv/bin/python -m ensurepip --upgrade 2>/dev/null || echo "pip already available"
	@venv/bin/pip install --upgrade pip setuptools || echo "⚠️  Pip upgrade failed, continuing..."
	@venv/bin/pip install -e . || { \
		echo "⚠️  Standard pip install failed, trying alternatives..."; \
		venv/bin/pip install -e . --user 2>/dev/null || \
		echo "❌ Virtual environment installation failed"; \
		echo "💡 Try manually: source venv/bin/activate && pip install -e ."; \
		exit 1; \
	}
	@echo "✅ Virtual environment setup complete!"
	@echo "💡 To activate: source venv/bin/activate"
	@echo "💡 Then run: edpmt server --dev"

# ==============================================================================
# PRE-FLIGHT (DYNAMIC PORTS)
# ==============================================================================

.PHONY: preflight
preflight: ## Reserve ports and update .env/config via PortKeeper (pk.config.json)
	@echo "🧩 Preflighting ports via PortKeeper..."
	@if command -v portkeeper >/dev/null 2>&1; then \
		if [ -f pk.config.json ]; then \
			portkeeper prepare --config pk.config.json; \
			echo "✅ Preflight done"; \
		else \
			echo "ℹ️ pk.config.json not found. Create one in project root to use preflight."; \
			echo "   Example: see PortKeeper README (prepare section)."; \
		fi; \
	else \
		echo "❌ PortKeeper CLI not found. Install it and re-run: pip install -e ../dynapsys/portkeeper"; \
		exit 1; \
	fi

# ==============================================================================
# DOCKER OPERATIONS
# ==============================================================================

# Build Docker containers
build:
	@echo "🔨 Building EDPMT Docker containers..."
	docker-compose -f examples/docker/docker-compose.yml build
	@echo "✅ Build complete"

# Start EDPMT environment
start:
	@echo "🚀 Starting EDPMT environment..."
	docker-compose -f examples/docker/docker-compose.yml up -d
	@echo "✅ Environment started"
	@echo "🌐 EDPMT Server: https://localhost:8888"
	@echo "📊 Grafana: http://localhost:3000 (admin/admin)"

# Stop environment
stop:
	@echo "🛑 Stopping EDPMT environment..."
	docker-compose -f examples/docker/docker-compose.yml down
	@echo "✅ Environment stopped"

# ==============================================================================
# TESTING
# ==============================================================================

# Run E2E tests with bash/curl
test-e2e-bash:
	@echo "🧪 Running E2E tests with bash/curl..."
	@bash ./test-e2e-bash.sh
	@echo "✅ Bash E2E tests complete"

# Run E2E tests with Python
test-e2e-python: start-test-server
	@echo "🐍 Running E2E tests with Python..."
	@python tests/test_e2e_complete.py
	@echo "✅ Python E2E tests complete"
	@$(MAKE) stop-test-server

# Start test server for E2E tests
start-test-server:
	@echo "🚀 Starting test server for E2E tests..."
	@python tests/manual_server_test.py > test-results/test_server.log 2>&1 &
	@echo $$! > test-results/test_server.pid
	@echo "⏳ Waiting for test server to start..."
	@sleep 5
	@attempt=1; max_attempts=12; while [ $$attempt -le $$max_attempts ]; do \
		echo "⏳ Attempt $$attempt/$$max_attempts: Checking if test server is responding..."; \
		if wget -q -O /dev/null http://localhost:8888/health 2> wget_error.log; then \
			echo "✅ Test server started"; \
			exit 0; \
		fi; \
		echo "⚠️ Test server not responding, waiting 5 more seconds..."; \
		echo "📋 Checking test server log for errors..."; \
		tail -n 5 test-results/test_server.log || echo "Log file not accessible"; \
		echo "📋 Wget error log:"; \
		cat wget_error.log || echo "Wget error log not accessible"; \
		echo "📋 Checking network status for port 8888..."; \
		if command -v ss >/dev/null 2>&1; then \
			echo "📋 ss output for port 8888:"; \
			ss -tuln | grep 8888 || echo "No process listening on port 8888"; \
		else \
			echo "📋 netstat output for port 8888:"; \
			netstat -tuln | grep 8888 || echo "No process listening on port 8888"; \
		fi; \
		sleep 5; \
		attempt=$$((attempt+1)); \
		done; \
		echo "❌ Test server failed to start after $$max_attempts attempts, check test-results/test_server.log"; \
		echo "📋 Last 10 lines of test server log:"; \
		tail -n 10 test-results/test_server.log || echo "Log file not accessible"; \
		exit 1

# Stop test server after E2E tests
stop-test-server:
	@echo "🛑 Stopping test server..."
	@if [ -f test-results/test_server.pid ]; then \
		kill `cat test-results/test_server.pid` 2>/dev/null || true; \
		rm -f test-results/test_server.pid; \
	fi
	@echo "✅ Test server stopped"

# Test GPIO functionality
test-gpio:
	@echo "🔌 Testing GPIO protocols..."
	@python tests/test_gpio.py
	@echo "✅ GPIO tests complete"

# Test I2C protocols
test-i2c:
	@echo "🔗 Testing I2C protocols..."
	@python tests/test_i2c.py
	@echo "✅ I2C tests complete"

# Test SPI protocols  
test-spi:
	@echo "⚡ Testing SPI protocols..."
	@python tests/test_spi.py
	@echo "✅ SPI tests complete"

# Test UART protocols
test-uart:
	@echo "📡 Testing UART protocols..."
	@python tests/test_uart.py
	@echo "✅ UART tests complete"

# Test simulation examples
test-examples:
	@echo "🎯 Testing PC simulation examples..."
	@python examples/pc-simulation/i2c_sensor_simulation.py &
	@sleep 5 && kill $! || true
	@python examples/pc-simulation/spi_communication.py &
	@sleep 5 && kill $! || true
	@echo "✅ Example tests complete"

# Run all tests
test-all: test-e2e-bash test-e2e-python test-gpio test-i2c test-spi test-uart test-examples test-transparent test-utils test-integration
	@echo "🎉 All EDPMT tests complete!"

# Standard test target (alias for test-all)
test: test-all

# Test EDPMTransparent functionality
test-transparent:
	@echo "🔍 Testing EDPMTransparent functionality..."
	@python tests/test_transparent.py
	@echo "✅ EDPMTransparent tests complete"

# Test utility functions
test-utils:
	@echo "🔧 Testing utility functions..."
	@python tests/test_utils.py
	@echo "✅ Utility tests complete"

# Test integration between modules
test-integration:
	@echo "🔗 Testing module integration..."
	@python tests/test_integration.py
	@echo "✅ Integration tests complete"

# ==============================================================================
# SERVER OPERATIONS
# ==============================================================================

# Start EDPMT server in development mode
server-dev: ## Start development server (requires installation)
	@echo "Starting EDPMT server in development mode..."
	@./bin/edpmt server --dev

server-dev-sim: ## Start development server with hardware simulators
	@echo "Starting EDPMT server in development mode with simulators..."
	./bin/edpmt server --dev --hardware-simulators
	# timeout 30s ./bin/edpmt server --dev --hardware-simulators

server-tls: ## Start production TLS server (requires installation)
	@echo "Starting EDPMT server with TLS..."
	@./bin/edpmt server

# Start GPIO frontend demo
frontend-demo:
	@bash scripts/frontend-demo.sh

# ==============================================================================
# VALIDATION & HEALTH CHECKS
# ==============================================================================

# Run quick validation
validate:
	@echo "🔍 Validating EDPMT setup..."
	@python -c "import edpmt; print('✅ EDPMT Package OK')" 2>/dev/null || echo "❌ EDPMT Package NOT FOUND"
	@python -c "import aiohttp; print('✅ aiohttp OK')" 2>/dev/null || echo "❌ aiohttp missing"
	@python -c "import cryptography; print('✅ cryptography OK')" 2>/dev/null || echo "❌ cryptography missing"
	@python -c "import websockets; print('✅ websockets OK')" 2>/dev/null || echo "❌ websockets missing"
	@echo "✅ Validation complete"

# Troubleshoot installation issues
troubleshoot:
	@bash scripts/troubleshoot-install.sh

# Health check for running server
health-check:
	@echo "🏥 Performing EDPMT health check..."
	@curl -k -s https://localhost:8888/health || curl -s http://localhost:8888/health || echo "❌ Server not responding"

# Test GPIO frontend connectivity
test-frontend:
	@echo "🎨 Testing GPIO frontend..."
	@curl -s http://localhost:5000/health || echo "❌ Frontend not responding"

# ==============================================================================
# DOCUMENTATION
# ==============================================================================

# Generate documentation for all examples
docs-examples:
	@echo "📚 Generating documentation for examples..."
	@python scripts/generate_example_docs.py
	@echo "✅ Example documentation generated"

# ==============================================================================
# CLEANUP
# ==============================================================================

# Clean up
clean:
	@echo "🧹 Cleaning up EDPMT environment..."
	@docker-compose -f examples/docker/docker-compose.yml down -v 2>/dev/null || true
	@docker system prune -f 2>/dev/null || true
	@rm -rf test-results/*.log 2>/dev/null || true
	@rm -rf logs/*.log 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Clean Python cache
clean-python:
	@echo "🧹 Cleaning Python cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "*.pyo" -delete 2>/dev/null || true
	@echo "✅ Python cache cleaned"

# ==============================================================================
# MONITORING
# ==============================================================================

# Show logs
logs:
	@docker-compose -f examples/docker/docker-compose.yml logs -f || echo "No Docker logs available"

# Show EDPMT server logs
logs-server:
	@tail -f logs/edpmt-server.log 2>/dev/null || echo "No server logs found"

# Monitor GPIO frontend
monitor-frontend:
	@tail -f logs/gpio-frontend.log 2>/dev/null || echo "No frontend logs found"

# ==============================================================================
# PUBLISHING
# ==============================================================================
publish: ## Publish project to PyPI
	@bash scripts/publish.sh

# Help
help:
	@echo "EDPMT (Electronic Device Protocol Management Transparent)"
	@echo "========================================================"
	@echo ""
	@echo "🚀 Quick Start (Recommended):"
	@echo "  make dev-setup      - Setup PYTHONPATH-based development (no pip install)"
	@echo "  ./bin/edpmt server --dev --port 8877  - Start server after dev-setup"
	@echo "  ./bin/edpmt info    - Show system information"
	@echo "  ./bin/edpmt --help  - Show CLI help"
	@echo ""
	@echo "📦 Installation Methods:"
	@echo "  make dev-setup      - PYTHONPATH setup (bypasses externally-managed-environment)"
	@echo "  make venv-setup     - Create isolated virtual environment"
	@echo "  make install        - Traditional pip installation (may fail on managed envs)"
	@echo "  make setup-dev      - Setup development directories"
	@echo "  make install-all    - Install with all optional dependencies"
	@echo ""
	@echo "Docker Operations:"
	@echo "  make build          - Build Docker containers"
	@echo "  make start          - Start EDPMT environment"
	@echo "  make stop           - Stop environment"
	@echo ""
	@echo "Pre-flight (Dynamic Ports):"
	@echo "  make preflight      - Reserve ports and update .env/config via PortKeeper (pk.config.json)"
	@echo ""
	@echo "Testing:"
	@echo "  make test-e2e-bash  - Run E2E tests with bash/curl"
	@echo "  make test-e2e-python- Run E2E tests with Python"
	@echo "  make test-gpio      - Test GPIO functionality"
	@echo "  make test-i2c       - Test I2C protocols"
	@echo "  make test-spi       - Test SPI protocols"
	@echo "  make test-uart      - Test UART protocols"
	@echo "  make test-examples  - Test simulation examples"
	@echo "  make test-all       - Run all tests"
	@echo ""
	@echo "Server Operations:"
	@echo "  make server-dev     - Start server in dev mode"
	@echo "  make server-dev-sim - Start server in dev mode with hardware simulators"
	@echo "  make server-tls     - Start server with TLS"
	@echo "  make frontend-demo  - Start GPIO frontend demo"
	@echo ""
	@echo "Validation:"
	@echo "  make validate       - Validate EDPMT setup"
	@echo "  make troubleshoot   - Troubleshoot installation issues"
	@echo "  make health-check   - Check server health"
	@echo "  make test-frontend  - Test frontend connectivity"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs-examples  - Generate example docs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Clean environment"
	@echo "  make clean-python   - Clean Python cache"
	@echo ""
	@echo "Monitoring:"
	@echo "  make logs           - Show Docker logs"
	@echo "  make logs-server    - Show server logs"
	@echo "  make monitor-frontend - Monitor frontend logs"
	@echo ""
	@echo "Publishing:"
	@echo "  make publish        - Publish to PyPI"

# === ALL SERVICES MANAGEMENT ===
.PHONY: start stop status logs restart preflight

start: ## Start all EDPMT services (server + visual programming interface)
	@chmod +x scripts/start-all.sh
	@scripts/start-all.sh

stop: ## Stop all EDPMT services and free all ports
	@chmod +x scripts/stop-all.sh
	@scripts/stop-all.sh

status: ## Check status of all EDPMT services
	@chmod +x scripts/status-all.sh
	@scripts/status-all.sh

logs: ## View logs from all services
	@echo "📋 EDPMT Server Logs:"
	@echo "====================="
	@if [ -f /tmp/edpmt-server.log ]; then \
		tail -n 50 /tmp/edpmt-server.log; \
	else \
		echo "No server log found"; \
	fi
	@echo ""
	@echo "📋 Visual Programming Logs:"
	@echo "==========================="
	@if [ -f /tmp/edpmt-visual.log ]; then \
		tail -n 20 /tmp/edpmt-visual.log; \
	else \
		echo "No visual programming log found"; \
	fi

restart: stop start ## Restart all EDPMT services

.PHONY: all setup-dev install install-all build start stop test-e2e-bash test-e2e-python test-gpio test-i2c test-spi test-uart test-examples test-all server-dev server-dev-sim server-tls frontend-demo validate troubleshoot health-check test-frontend docs-examples clean clean-python logs logs-server monitor-frontend publish help preflight
