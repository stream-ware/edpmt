# EDPMT Complete Frontend Makefile
# Provides simple commands to run the complete visual programming and peripheral control solution

.PHONY: help install install-frontend install-websocket run dev dev-debug stop clean test setup check-deps logs

# Default target
help:
	@echo "EDPMT Complete Frontend - Visual Programming & Peripheral Control"
	@echo "================================================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make install           - Install all dependencies"
	@echo "  make install-frontend  - Install frontend service dependencies"
	@echo "  make install-websocket - Install WebSocket service dependencies"
	@echo "  make run               - Run complete solution (production mode)"
	@echo "  make dev               - Run in development mode"
	@echo "  make dev-debug         - Run in development mode with debug output"
	@echo "  make stop              - Stop all services"
	@echo "  make clean             - Clean temporary files and logs"
	@echo "  make test              - Run tests"
	@echo "  make logs              - Show logs"
	@echo ""
	@echo "Quick start:"
	@echo "  1. make install"
	@echo "  2. make dev"
	@echo "  3. Open http://localhost:8085 in your browser"
	@echo ""

# Variables
PYTHON := python3
PIP := pip3
LOG_DIR := logs
PROJECTS_DIR := projects
STATIC_DIR := static
JS_DIR := js
HOST := 0.0.0.0

# Service PIDs
FRONTEND_PID := .frontend.pid
WEBSOCKET_PID := .websocket.pid

# Load environment variables from .env
-include .env

# Default ports (can be overridden in .env)
FRONTEND_PORT ?= 8085
WEBSOCKET_PORT ?= 8086

# Check if dependencies are installed
check-deps:
	@echo "Checking Python version..."
	@${PYTHON} --version
	@echo "\nChecking pip version..."
	@${PIP} --version

# Install all dependencies
install: check-deps
	@echo "\n🚀 Installing all dependencies..."
	${MAKE} install-frontend
	${MAKE} install-websocket
	mkdir -p ${LOG_DIR} ${PROJECTS_DIR} ${STATIC_DIR}/js
	cp -r ${JS_DIR}/*.js ${STATIC_DIR}/js/
	cp runtime-config.js ${STATIC_DIR}/

# Install frontend service dependencies
install-frontend:
	@echo "\n📦 Installing frontend service dependencies..."
	cd frontend && ${PIP} install -r requirements.txt

# Install WebSocket service dependencies
install-websocket:
	@echo "\n🔌 Installing WebSocket service dependencies..."
	cd websocket && ${PIP} install -r requirements.txt

# Run in development mode
dev: stop install
	@echo "\n🚀 Starting development servers..."
	@echo "Frontend: http://localhost:${FRONTEND_PORT}"
	@echo "WebSocket: ws://localhost:${WEBSOCKET_PORT}/ws\n"
	@echo "Starting WebSocket server..."
	@cd websocket && \
	  nohup python3 -u server.py \
	    --host ${HOST} \
	    --port ${WEBSOCKET_PORT} \
	    --log-level ${LOG_LEVEL} \
	    --log-file ${LOG_DIR}/websocket.log > /dev/null 2>&1 & echo $$! > ${WEBSOCKET_PID}
	@echo "Starting frontend server..."
	@cd frontend && \
	  nohup python3 -u server.py \
	    --host ${HOST} \
	    --port ${FRONTEND_PORT} \
	    --ws-port ${WEBSOCKET_PORT} \
	    --log-level ${LOG_LEVEL} \
	    --log-file ${LOG_DIR}/frontend.log > /dev/null 2>&1 & echo $$! > ${FRONTEND_PID}
	@echo "Servers started. Check logs with 'make logs'"

# Run in development mode with debug output
dev-debug: stop install
	@echo "\n🚀 Starting development servers in DEBUG mode..."
	@echo "Frontend: http://localhost:${FRONTEND_PORT}"
	@echo "WebSocket: ws://localhost:${WEBSOCKET_PORT}/ws\n"
	@echo "Starting WebSocket server..."
	@cd websocket && \
	  PYTHONUNBUFFERED=1 python3 -u server.py \
	    --host ${HOST} \
	    --port ${WEBSOCKET_PORT} \
	    --log-level DEBUG \
	    --debug \
	    --log-file ${LOG_DIR}/websocket-debug.log &
	@echo $$! > ${WEBSOCKET_PID}
	@echo "Starting frontend server..."
	@cd frontend && \
	  PYTHONUNBUFFERED=1 python3 -u server.py \
	    --host ${HOST} \
	    --port ${FRONTEND_PORT} \
	    --ws-port ${WEBSOCKET_PORT} \
	    --log-level DEBUG \
	    --debug \
	    --log-file ${LOG_DIR}/frontend-debug.log &
	@echo $$! > ${FRONTEND_PID}
	@echo "Servers started in debug mode. Logs are being written to ${LOG_DIR}/*.log"

# Stop development servers
stop:
	@echo "\n🛑 Stopping servers..."
	@if [ -f ${FRONTEND_PID} ]; then \
		kill -9 $$(cat ${FRONTEND_PID}) 2>/dev/null || true; \
		rm -f ${FRONTEND_PID}; \
	fi
	@if [ -f ${WEBSOCKET_PID} ]; then \
		kill -9 $$(cat ${WEBSOCKET_PID}) 2>/dev/null || true; \
		rm -f ${WEBSOCKET_PID}; \
	fi
	@# Kill any processes using the ports
	@for port in ${FRONTEND_PORT} ${WEBSOCKET_PORT}; do \
		lsof -ti :$$port | xargs -r kill -9 2>/dev/null || true; \
	done
	@echo "Servers stopped"

# Show logs
logs:
	@echo "\n📄 Showing logs (Ctrl+C to exit)..."
	@tail -f ${LOG_DIR}/*.log

# Clean up
clean: stop
	@echo "\n🧹 Cleaning up..."
	@rm -rf ${LOG_DIR}/*.log
	@rm -f ${FRONTEND_PID} ${WEBSOCKET_PID}
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	@echo "Clean complete"

# Run tests
test:
	@echo "\n🧪 Running tests..."
	${PYTHON} -m pytest tests/

# Setup development environment
setup: check-deps install
	@echo "\n✅ Development environment is ready!"

# Create a default .env file if it doesn't exist
.env:
	@echo "Creating default .env file..."
	@echo "# EDPMT Complete Frontend Configuration" > .env
	@echo "FRONTEND_PORT=${FRONTEND_PORT}" >> .env
	@echo "WEBSOCKET_PORT=${WEBSOCKET_PORT}" >> .env
	@echo "DEBUG=true" >> .env
	@echo "LOG_LEVEL=INFO" >> .env
	@echo "USE_HARDWARE_SIMULATORS=true" >> .env

# Include .env file
-include .env
