#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔍 Verifying EDPMT Frontend installation...${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}⚠️  Warning: Running as root is not recommended.${NC}"
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MINOR" -lt 7 ]; then
    echo -e "${RED}❌ Python 3.7 or higher is required. Found Python ${PYTHON_VERSION}${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} is installed${NC}"
fi

# Check required directories
REQUIRED_DIRS=("frontend" "websocket" "js" "logs" "projects")
MISSING_DIRS=()

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        MISSING_DIRS+=("$dir")
    fi
done

if [ ${#MISSING_DIRS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Missing required directories: ${MISSING_DIRS[*]}${NC}"
    echo -e "Creating missing directories..."
    mkdir -p "${MISSING_DIRS[@]}"
else
    echo -e "${GREEN}✓ All required directories exist${NC}"
fi

# Check required files
REQUIRED_FILES=(
    "frontend/server.py"
    "websocket/server.py"
    "js/edpmt-client.js"
    "js/block-editor.js"
    "js/page-editor.js"
    "js/main.js"
    "index.html"
    "styles.css"
)
MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing required files:${NC}"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    exit 1
else
    echo -e "${GREEN}✓ All required files exist${NC}"
fi

# Check and install Python dependencies
echo -e "\n${YELLOW}🔍 Checking Python dependencies...${NC}"
REQUIREMENTS_FILES=(
    "requirements.txt"
    "frontend/requirements.txt"
    "websocket/requirements.txt"
)

for req_file in "${REQUIREMENTS_FILES[@]}"; do
    if [ -f "$req_file" ]; then
        echo -e "Installing dependencies from ${req_file}..."
        pip3 install -r "$req_file"
    else
        echo -e "${YELLOW}⚠️  ${req_file} not found, skipping...${NC}"
    fi
done

# Set up static files
echo -e "\n${YELLOW}📂 Setting up static files...${NC}"
mkdir -p static/js
cp -n js/*.js static/js/ 2>/dev/null || true
cp -n runtime-config.js static/ 2>/dev/null || true

# Fix file permissions
echo -e "\n${YELLOW}🔒 Setting file permissions...${NC}"
chmod -R u+rwX,go+rX,go-w .
chmod +x scripts/*.sh 2>/dev/null || true

# Verify server startup
echo -e "\n${YELLOW}🚀 Verifying server startup...${NC}"
make stop >/dev/null 2>&1
make dev >/dev/null 2>&1 &
SERVER_PID=$!
sleep 5  # Give servers time to start

# Check if servers are running
if pgrep -f "python3.*frontend/server.py" >/dev/null && \
   pgrep -f "python3.*websocket/server.py" >/dev/null; then
    echo -e "${GREEN}✓ Servers started successfully${NC}"
    
    # Test frontend endpoint
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8085 | grep -q "200"; then
        echo -e "${GREEN}✓ Frontend server is responding${NC}"
    else
        echo -e "${RED}❌ Frontend server is not responding on port 8085${NC}"
    fi
    
    # Test WebSocket endpoint
    if nc -z localhost 8086; then
        echo -e "${GREEN}✓ WebSocket server is running on port 8086${NC}"
    else
        echo -e "${RED}❌ WebSocket server is not running on port 8086${NC}"
    fi
    
    # Stop servers
    make stop >/dev/null 2>&1
else
    echo -e "${RED}❌ Failed to start servers${NC}"
    echo -e "\n${YELLOW}📄 Checking logs...${NC}"
    tail -n 20 logs/*.log 2>/dev/null || echo "No log files found"
    make stop >/dev/null 2>&1
    exit 1
fi

echo -e "\n${GREEN}✅ Verification complete!${NC}"
echo -e "To start the development servers, run: ${YELLOW}make dev${NC}"
echo -e "To start with debug output: ${YELLOW}make dev-debug${NC}"
echo -e "To view logs: ${YELLOW}make logs${NC}"

exit 0