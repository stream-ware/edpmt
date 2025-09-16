#!/usr/bin/env python3
"""
EDPMT WebSocket Server
Handles WebSocket connections and hardware interactions.
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from pathlib import Path

from aiohttp import web
import aiohttp_cors

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available, using system environment only")

# Add EDPMT to path for local development
edpmt_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(edpmt_root))

try:
    from edpmt import EDPMTransparent
    from edpmt.utils import get_system_info
except ImportError as e:
    print(f"Error importing EDPMT: {e}")
    print("Please ensure EDPMT is properly installed")
    sys.exit(1)

# --- Configuration ---
class Config:
    """Configuration loaded from .env file and environment variables"""
    WS_PORT = int(os.getenv('WS_PORT', '8086'))
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    USE_HARDWARE_SIMULATORS = os.getenv('USE_HARDWARE_SIMULATORS', 'true').lower() == 'true'

# Setup logging
def setup_logging(level='INFO', log_file=None):
    """Configure logging."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )
    
    # Set log level for aiohttp and other libraries
    logging.getLogger('aiohttp').setLevel(log_level)
    logging.getLogger('asyncio').setLevel(log_level)

class WebSocketServer:
    """WebSocket server for handling hardware interactions."""

    def __init__(self, host='0.0.0.0', port=8086, debug=False, log_level='INFO', log_file=None):
        """Initialize the WebSocket server.
        
        Args:
            host (str): Host to bind to
            port (int): Port to listen on
            debug (bool): Enable debug mode
            log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file (str, optional): Path to log file
        """
        self.host = host
        self.port = port
        self.debug = debug
        
        # Configure logging
        setup_logging(log_level, log_file)
        
        if self.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug("Debug mode enabled")
        
        self.app = web.Application()
        self.routes = web.RouteTableDef()
        self.setup_middleware()
        self.setup_routes()
        self.app.add_routes(self.routes)
        
        # WebSocket connections
        self.websockets = set()
        
        # Initialize EDPMT client
        self.edpmt_client = None
        self.init_edpmt()

    def init_edpmt(self):
        """Initialize EDPMT client."""
        try:
            logger.info("Initializing EDPMT client...")
            config = {'hardware_simulators': Config.USE_HARDWARE_SIMULATORS}
            self.edpmt_client = EDPMTransparent(config=config)
            logger.info("EDPMT client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize EDPMT client: {e}. Running in simulation mode.")

    def _map_action(self, action: str, params: dict):
        """Map composite action strings to EDPMTransparent (action, target, **params)."""
        if action in ('get-system-info', 'get-status'):
            return ('__local__', '__system__', params)
        if action in ('execute-project', 'stop-execution'):
            return ('__local__', '__project__', params)
        if '-' in action:
            target, act = action.split('-', 1)
            return (act, target, params)
        if 'target' in params:
            tgt = params.pop('target')
            return (action, tgt, params)
        return (None, None, params)

    async def start_edpmt_client(self):
        """Initialize and start the EDPMT backend client."""
        try:
            logger.info("Starting EDPMT client...")
            await self.edpmt_client.start_server()
            logger.info("EDPMT client started successfully.")
        except Exception as e:
            logger.error(f"Failed to start EDPMT client: {e}. Running in simulation mode.")

    async def websocket_handler(self, request):
        """Handle WebSocket connections."""
        logger.info("New WebSocket connection request")
        
        # Check origin
        origin = request.headers.get('Origin')
        allowed_origins = [
            f"http://{self.host}:{self.port}",
            f"http://127.0.0.1:{self.port}",
            f"http://localhost:{self.port}"
        ]
        
        if origin and origin.rstrip('/') not in [o.rstrip('/') for o in allowed_origins]:
            logger.warning(f"Rejected WebSocket connection from unauthorized origin: {origin}")
            return aiohttp.web.Response(status=403, text="Forbidden: Origin not allowed")
        
        # Set CORS headers
        headers = {
            'Access-Control-Allow-Origin': origin or '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Allow-Credentials': 'true'
        }
        
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS':
            return aiohttp.web.Response(status=200, headers=headers)
        
        # Proceed with WebSocket upgrade
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Add connection to active connections
        self.websockets.add(ws)
        logger.info(f"WebSocket connection established. Total connections: {len(self.websockets)}")
        
        try:
            # Send initial system info
            await ws.send_json({'type': 'system_info', 'data': get_system_info()})
            
            # Listen for messages
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    await self.handle_ws_message(ws, msg.data)
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WebSocket connection closed with exception {ws.exception()}")
        finally:
            # Clean up connection
            self.websockets.discard(ws)
            logger.info(f"WebSocket connection closed. Remaining connections: {len(self.websockets)}")
        
        return ws

    async def handle_ws_message(self, ws, message):
        """Process incoming WebSocket messages."""
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'command':
                action = data.get('action')
                params = data.get('params', {})
                edpm_action, edpm_target, edpm_params = self._map_action(action, params)
                
                # Handle local/special actions
                if edpm_action == '__local__' and edpm_target == '__system__':
                    if action == 'get-system-info' or action == 'get-status':
                        result = {'system': get_system_info()}
                    else:
                        result = {'ok': True}
                elif edpm_action == '__local__' and edpm_target == '__project__':
                    # Project execution handling
                    if action == 'execute-project':
                        result = {'accepted': True, 'timestamp': int(asyncio.get_running_loop().time()*1000)}
                    elif action == 'stop-execution':
                        result = {'stopped': True}
                    else:
                        result = {'ok': True}
                elif self.edpmt_client and edpm_action and edpm_target:
                    # Route to EDPMTransparent
                    result = await self.edpmt_client.execute(edpm_action, edpm_target, **edpm_params)
                else:
                    result = {'error': f'Unknown action: {action}'}
                
                await ws.send_json({'type': 'command_response', 'id': data.get('id'), 'data': result})
                
            elif msg_type == 'ping':
                await ws.send_json({'type': 'pong'})
                
        except Exception as e:
            logger.error(f"Failed to handle WebSocket message: {e}")
            await ws.send_json({'type': 'error', 'message': str(e)})

    async def broadcast_system_info(self):
        """Periodically broadcast system info to all connected clients."""
        while True:
            await asyncio.sleep(5)
            if self.websockets:
                info = get_system_info()
                message = json.dumps({'type': 'system_info_update', 'data': info})
                for ws in self.websockets:
                    await ws.send_str(message)

    def setup_middleware(self):
        """Set up CORS middleware for the WebSocket server."""
        # Configure CORS with specific origins and methods
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_origin=[
                    f"http://{self.host}:{self.port}",
                    f"http://127.0.0.1:{self.port}",
                    f"http://localhost:{self.port}"
                ]
            )
        })

        # Add CORS to all routes, ignoring duplicate OPTIONS handlers
        for route in list(self.app.router.routes()):
            try:
                cors.add(route)
            except RuntimeError as e:
                if "Cannot add a route with the same path and method" in str(e):
                    # Skip duplicate route errors
                    logger.warning(f"Skipping duplicate route: {route}")
                else:
                    logger.error(f"Error adding CORS to route {route}: {e}")
                    raise

    def setup_routes(self):
        """Set up all routes for the WebSocket server."""
        self.routes.add_get('/ws', self.websocket_handler)
        
        # Add HTTP endpoints for WebSocket-fallback
        self.routes.add_get('/api/status', self.status_handler)
        self.routes.add_post('/api/execute', self.execute_handler)

    async def status_handler(self, request):
        """Return system status for HTTP fallback."""
        try:
            info = get_system_info()
            return web.json_response({'system': info})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def execute_handler(self, request):
        """Execute actions over HTTP (fallback for WS)."""
        try:
            body = await request.json()
            action = body.get('action')
            params = body.get('params', {})
            edpm_action, edpm_target, edpm_params = self._map_action(action, params)
            
            if edpm_action == '__local__' and edpm_target == '__system__':
                result = {'system': get_system_info()}
            elif edpm_action == '__local__' and edpm_target == '__project__':
                if action == 'execute-project':
                    result = {'accepted': True}
                else:
                    result = {'stopped': True}
            elif self.edpmt_client and edpm_action and edpm_target:
                result = await self.edpmt_client.execute(edpm_action, edpm_target, **edpm_params)
            else:
                result = {'error': f'Unknown action: {action}'}
                
            return web.json_response(result)
        except Exception as e:
            logger.exception("/api/execute failed")
            return web.json_response({'error': str(e)}, status=500)

    async def run(self):
        """Run the WebSocket server."""
        await self.start_edpmt_client()
        
        # Create and run the server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        
        logger.info(f"🚀 WebSocket server starting on ws://{self.host}:{self.port}")
        await site.start()

        # Start background tasks
        asyncio.create_task(self.broadcast_system_info())

        logger.info("✅ WebSocket server is running. Press Ctrl+C to stop.")
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            await runner.cleanup()
            logger.info("WebSocket server shut down.")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='EDPMT WebSocket Server')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                      help='Host to bind to')
    parser.add_argument('--port', type=int, default=8086,
                      help='Port to listen on')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug mode')
    parser.add_argument('--log-level', type=str, default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                      help='Logging level')
    parser.add_argument('--log-file', type=str, default=None,
                      help='Log file path')
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    server = WebSocketServer(
        host=args.host,
        port=args.port,
        debug=args.debug,
        log_level=args.log_level,
        log_file=args.log_file
    )
    asyncio.run(server.run())

if __name__ == '__main__':
    main()
