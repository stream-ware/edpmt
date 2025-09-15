#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"
PIP_BIN="${PIP:-pip3}"

if [ ! -f requirements.txt ]; then
  echo "❌ requirements.txt not found"
  exit 1
fi

echo "📦 Installing dependencies from requirements.txt..."
"$PIP_BIN" install --user --break-system-packages -r requirements.txt

echo "🏗️  Checking EDPMT..."
if "$PYTHON_BIN" -c "import sys; sys.path.insert(0, '../..'); import edpmt; print('✅ EDPMT available')" 2>/dev/null; then
  :
else
  echo "Installing EDPMT in editable mode..."
  (cd ../.. && "$PIP_BIN" install --user -e .)
  "$PYTHON_BIN" -c "import sys; sys.path.insert(0, '../..'); import edpmt; print('✅ EDPMT available')"
fi

echo "✅ Installation check completed successfully"
