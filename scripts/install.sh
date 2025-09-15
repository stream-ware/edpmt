#!/bin/bash

echo "📦 Installing EDPMT in development mode..."
echo "🔍 Checking setuptools..."
python3 -c "import setuptools" 2>/dev/null || pip3 install setuptools --user 2>/dev/null || pip3 install setuptools --break-system-packages 2>/dev/null
echo "🔧 Installing EDPMT..."
# First, try to uninstall any existing installation to avoid conflicts
pip3 uninstall edpmt -y 2>/dev/null || true
echo "📦 Performing clean installation..."
pip3 install -e . --user 2>/dev/null || pip3 install -e . --break-system-packages 2>/dev/null || { \
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
echo "🧪 Verifying installation..."
# Check if edpmt can be imported
python3 -c "import edpmt; print('✅ EDPMT module imported successfully')" 2>/dev/null || { \
    echo "❌ Installation verification failed - module cannot be imported"; \
    echo "💡 Additional troubleshooting:"; \
    echo "   1. Check Python version: python3 --version"; \
    echo "   2. Check pip version: pip3 --version"; \
    echo "   3. Check installation location: pip3 show edpmt"; \
    echo "   4. Try reinstalling with: pip3 install -e . --force-reinstall --user"; \
    exit 1; \
}
echo "🎯 Testing CLI entry points..."
which edpmt >/dev/null && echo "✅ CLI available at: $$(which edpmt)" || { \
    echo "⚠️  CLI not in PATH"; \
    echo "💡 Try: export PATH=$$HOME/.local/bin:$$PATH"; \
    echo "💡 Or use full path: $$(python3 -c 'import site; print(site.USER_BASE + "/bin")')/edpmt"; \
}
# Additional check for version attribute
python3 -c "import edpmt; print(hasattr(edpmt, '__version__') and f'✅ EDPMT version: {edpmt.__version__}' or '⚠️  Version attribute not found')" 2>/dev/null || true
