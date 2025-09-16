# EDPMT Complete Frontend Makefile
# Provides simple commands to run the complete visual programming and peripheral control solution

.PHONY: help install install-frontend install-websocket run dev dev-debug stop clean test setup check-deps

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
	
	# Create necessary directories
	@mkdir -p ${LOG_DIR} ${PROJECTS_DIR}
	
	# Start WebSocket server
	@echo "Starting WebSocket server on port ${WEBSOCKET_PORT}..."
	@cd websocket && \
	${PYTHON} server.py --port ${WEBSOCKET_PORT} --debug > ../${LOG_DIR}/websocket.log 2>&1 & \
	echo $$! > ../${WEBSOCKET_PID} && \
	echo "WebSocket server started (PID: $$!)"
	
	# Give WebSocket server a moment to start
	@echo -n "Waiting for WebSocket server to initialize"
	@for i in 1 2 3 4 5; do \
		sleep 1; \
		echo -n "."; \
	done
	@echo ""
	
	# Start frontend server
	@echo "Starting frontend server on port ${FRONTEND_PORT}..."
	@cd frontend && \
	${PYTHON} server.py --port ${FRONTEND_PORT} --ws-port ${WEBSOCKET_PORT} --debug > ../${LOG_DIR}/frontend.log 2>&1 & \
	echo $$! > ../${FRONTEND_PID} && \
	echo "Frontend server started (PID: $$!)"
	
	# Open browser after a short delay
	@echo -n "\n🌐 Waiting for servers to be ready"
	@for i in 1 2 3 4 5; do \
		sleep 1; \
		echo -n "."; \
	done
	@echo ""
	
	@echo "\n📋 Tailing logs (Ctrl+C to stop)..."
	@tail -f ${LOG_DIR}/*.log

# Run in development mode with debug output
dev-debug: stop install
	@echo "\n🚀 Starting development servers in DEBUG mode..."
	@echo "Frontend: http://localhost:${FRONTEND_PORT}"
	@echo "WebSocket: ws://localhost:${WEBSOCKET_PORT}/ws\n"
	
	# Create necessary directories
	@mkdir -p ${LOG_DIR} ${PROJECTS_DIR}
	
	# Start WebSocket server with debug
	@echo "Starting WebSocket server on port ${WEBSOCKET_PORT}..."
	@cd websocket && \
	PYTHONUNBUFFERED=1 \
	PYTHONPATH=$$PYTHONPATH:. \
	${PYTHON} -X dev server.py \
	  --port ${WEBSOCKET_PORT} \
	  --debug \
	  --log-level DEBUG \
	  --log-file ../${LOG_DIR}/websocket-debug.log \
	  > ../${LOG_DIR}/websocket-debug.log 2>&1 & \
	echo $$! > ../${WEBSOCKET_PID} && \
	echo "WebSocket server started (PID: $$!)"
	
	# Give WebSocket server a moment to start
	@echo -n "Waiting for WebSocket server to initialize"
	@for i in 1 2 3 4 5; do \
		sleep 1; \
		echo -n "."; \
	done
	@echo ""
	
	# Start frontend server with debug
	@echo "Starting frontend server on port ${FRONTEND_PORT}..."
	@cd frontend && \
	PYTHONUNBUFFERED=1 \
	PYTHONPATH=$$PYTHONPATH:. \
	${PYTHON} -X dev server.py \
	  --port ${FRONTEND_PORT} \
	  --ws-port ${WEBSOCKET_PORT} \
	  --debug \
	  --log-level DEBUG \
	  --log-file ../${LOG_DIR}/frontend-debug.log \
	  > ../${LOG_DIR}/frontend-debug.log 2>&1 & \
	echo $$! > ../${FRONTEND_PID} && \
	echo "Frontend server started (PID: $$!)"
	
	# Open browser after a short delay
	@echo -n "\n🌐 Waiting for servers to be ready"
	@for i in 1 2 3 4 5; do \
		sleep 1; \
		echo -n "."; \
	done
	@echo ""
	
	@echo "\n📋 Tailing debug logs (Ctrl+C to stop)..."
	@tail -f ${LOG_DIR}/*-debug.log

# Stop all services
stop:
	@echo "\n🛑 Stopping services..."
	@for pid_file in ${WEBSOCKET_PID} ${FRONTEND_PID}; do \
		if [ -f "$$pid_file" ]; then \
			pid=$$(cat $$pid_file); \
			if ps -p $$pid > /dev/null; then \
				echo "Stopping process $$pid..."; \
				kill -TERM $$pid 2>/dev/null || true; \
				( sleep 1 && kill -9 $$pid 2>/dev/null ) & \
				wait $$pid 2>/dev/null || true; \
			fi; \
			rm -f "$$pid_file"; \
		fi; \
	done
	@# Ensure ports are freed
	@for port in ${FRONTEND_PORT} ${WEBSOCKET_PORT}; do \
		if lsof -i :$$port >/dev/null 2>&1; then \
			echo "Freeing port $$port..."; \
			fuser -k $$port/tcp >/dev/null 2>&1 || true; \
		fi; \
	done
	@echo "All services stopped."

# Clean temporary files and logs
clean: stop
	@echo "\n🧹 Cleaning up..."
	rm -rf ${LOG_DIR}/*.log
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

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
