#!/bin/bash

# Navigate to the config service directory
cd "$(dirname "$0")/../config_service"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start the configuration service
echo "Starting Configuration Service..."
python main.py
