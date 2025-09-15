#!/bin/bash

echo "🎨 Starting GPIO frontend demo..."
if ! python3 -c "import edpmt" 2>/dev/null; then
    echo "❌ EDPMT package not found. Please install with: make install"
    exit 1
fi
python3 examples/gpio-frontend/app.py
