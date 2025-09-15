# EDPMT (Electronic Device Protocol Management Transparent) Makefile

# Default target
all: setup-dev install test-all

# ==============================================================================
# DEVELOPMENT SETUP
# ==============================================================================

# Setup development environment
setup-dev:
	@echo "🔧 Setting up EDPMT development environment..."
	@mkdir -p tests
	@mkdir -p test-results  
	@mkdir -p examples/gpio-frontend
	@mkdir -p logs
	@echo "✅ Development environment ready"

# Install package in development mode
install:
	@echo "📦 Installing EDPMT in development mode..."
	@echo "🔍 Checking setuptools..."
	@python3 -c "import setuptools" 2>/dev/null || pip3 install setuptools --user 2>/dev/null || pip3 install setuptools --break-system-packages 2>/dev/null
	@echo "🔧 Installing EDPMT..."
	@pip3 install -e . --user 2>/dev/null || pip3 install -e . --break-system-packages 2>/dev/null || { \
		echo "⚠️  Standard installation failed. Trying alternative methods..."; \
		echo "💡 Method 1: User installation"; \
		pip3 install -e . --user || { \
			echo "💡 Method 2: Break system packages (use with caution)"; \
			pip3 install -e . --break-system-packages || { \
				echo "❌ All installation methods failed."; \
				echo "💡 Please try:"; \
				echo "   1. Create virtual environment: python3 -m venv venv && source venv/bin/activate"; \
				echo "   2. Use pipx: brew install pipx && pipx install -e ."; \
				echo "   3. Manual PYTHONPATH: export PYTHONPATH=$$PWD:$$PYTHONPATH"; \
				exit 1; \
			}; \
		}; \
	}
	@echo "🧪 Verifying installation..."
	@python3 -c "import edpmt; print(f'✅ EDPMT {edpmt.__version__} installed successfully')" || echo "❌ Installation verification failed"
	@echo "🎯 Testing CLI entry points..."
	@which edpmt >/dev/null && echo "✅ CLI available at: $$(which edpmt)" || echo "⚠️  CLI not in PATH - try: export PATH=$$HOME/.local/bin:$$PATH"

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
	@python3 -m venv venv
	@echo "📦 Installing EDPMT in virtual environment..."
	@venv/bin/pip install --upgrade pip setuptools
	@venv/bin/pip install -e .
	@echo "✅ Virtual environment setup complete!"
	@echo "💡 To activate: source venv/bin/activate"
	@echo "💡 Then run: edpmt server --dev"

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
test-e2e-python:
	@echo "🐍 Running E2E tests with Python..."
	@python tests/test_e2e_complete.py
	@echo "✅ Python E2E tests complete"

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
test-all: test-e2e-bash test-e2e-python test-gpio test-i2c test-spi test-uart test-examples
	@echo "🎉 All EDPMT tests complete!"

# Standard test target (alias for test-all)
test: test-all

# ==============================================================================
# SERVER OPERATIONS
# ==============================================================================

# Start EDPMT server in development mode
server-dev:
	@echo "🚀 Starting EDPMT server in development mode..."
	edpmt server --dev --port 8888

# Start EDPMT server with TLS
server-tls:
	@echo "🔐 Starting EDPMT server with TLS..."
	edpmt server --tls --port 8888

# Start GPIO frontend demo
frontend-demo:
	@echo "🎨 Starting GPIO frontend demo..."
	@python examples/gpio-frontend/app.py

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
	@echo "Development:"
	@echo "  make setup-dev      - Setup development environment"
	@echo "  make install        - Install EDPMT in dev mode"
	@echo "  make install-all    - Install with all dependencies"
	@echo ""
	@echo "Docker Operations:"
	@echo "  make build          - Build Docker containers"
	@echo "  make start          - Start EDPMT environment"
	@echo "  make stop           - Stop environment"
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
	@echo "  make server-tls     - Start server with TLS"
	@echo "  make frontend-demo  - Start GPIO frontend demo"
	@echo ""
	@echo "Validation:"
	@echo "  make validate       - Validate EDPMT setup"
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

.PHONY: all setup-dev install install-all build start stop test-e2e-bash test-e2e-python test-gpio test-i2c test-spi test-uart test-examples test-all server-dev server-tls frontend-demo validate health-check test-frontend docs-examples clean clean-python logs logs-server monitor-frontend publish help
