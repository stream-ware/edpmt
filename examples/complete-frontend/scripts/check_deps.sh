#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"

echo "🔍 Checking dependencies..."

if [ ! -f requirements.txt ]; then
  echo "❌ requirements.txt not found. Cannot check dependencies."
  exit 1
fi

# Validate Python requirements
$PYTHON_BIN - <<'PY' 2>/dev/null || { echo "❌ Missing Python dependencies. Run 'make install' first."; exit 1; }
import pkg_resources, pathlib
reqs = [r.strip() for r in pathlib.Path('requirements.txt').read_text().splitlines() if r.strip() and not r.strip().startswith('#')]
pkg_resources.require(reqs)
print('✅ Python requirements satisfied')
PY

# Check EDPMT availability
$PYTHON_BIN - <<'PY' 2>/dev/null || { echo "❌ EDPMT not found. Please install EDPMT first."; exit 1; }
import sys
sys.path.insert(0, '../..')
import edpmt
print('✅ EDPMT available')
PY

# Check curl
if ! command -v curl >/dev/null 2>&1; then
  echo "❌ 'curl' is required for health checks"
  exit 1
fi

echo "✅ All dependencies are available"
