#!/bin/bash

echo "🔍 Troubleshooting EDPMT installation issues..."
echo "🐍 Checking Python environment:"
echo "   Python version: $(python3 --version 2>/dev/null || echo 'Not found')"
echo "   Pip version: $(pip3 --version 2>/dev/null || echo 'Not found')"
echo "   Python path: $(which python3 2>/dev/null || echo 'Not found')"
echo "   Pip path: $(which pip3 2>/dev/null || echo 'Not found')"

echo "
📦 Checking EDPMT installation:"
if pip3 show edpmt >/dev/null 2>&1; then
    echo "   EDPMT is installed at: $(pip3 show edpmt | grep Location | cut -d ' ' -f 2)"
    echo "   EDPMT version: $(pip3 show edpmt | grep Version | cut -d ' ' -f 2)"
else
    echo "   ❌ EDPMT is not installed in this environment."
fi

echo "
🧪 Testing EDPMT import:"
if python3 -c "import edpmt; print('✅ EDPMT imported successfully')" 2>/dev/null; then
    echo "   ✅ Import successful"
else
    echo "   ❌ Import failed. EDPMT module not found in Python path."
    echo "   💡 PYTHONPATH: $PYTHONPATH"
fi

echo "
🔧 Suggested fixes:"
echo "   1. Ensure you're using the correct Python environment."
if [ -d "venv" ]; then
    echo "      Virtual environment found. Activate with: source venv/bin/activate"
fi
echo "   2. Reinstall EDPMT with: bash scripts/install.sh"
echo "   3. Force reinstall with: pip3 install -e . --force-reinstall --user"
echo "   4. Check if CLI is in PATH: export PATH=$HOME/.local/bin:$PATH"
echo "   5. Run directly with Python: python3 -m edpmt.cli server --dev"

echo "
📋 Running direct module test:"
python3 -m edpmt.cli server --help >/dev/null 2>&1 && echo "   ✅ Direct module execution works! Use 'python3 -m edpmt.cli server --dev' to start server." || echo "   ❌ Direct module execution failed."

echo "
💡 For further assistance, check logs or contact support."
