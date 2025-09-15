#!/usr/bin/env python3
"""
Manual test script to start EDPMTransparent server
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add EDPMT to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from edpmt.transparent import EDPMTransparent
except ImportError:
    print("❌ EDPMT package not found. Please install with: pip install -e .")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 Starting manual test of EDPMTransparent server...")
    
    try:
        # Create server with development configuration
        logger.info("🔧 Creating EDPMTransparent instance with config: dev_mode=True, port=8888, host=127.0.0.1, tls=False, hardware_simulators=True")
        server = EDPMTransparent(
            name="EDPMT-Manual-Test",
            config={
                'dev_mode': True,
                'port': 8888,
                'host': '127.0.0.1',
                'tls': False,  # Disable TLS for testing to avoid certificate issues
                'hardware_simulators': True
            }
        )
        
        logger.info("🚀 Starting server...")
        # Start server
        await server.start_server()
        
        logger.info("✅ Server started successfully on http://127.0.0.1:8888")
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
