#!/usr/bin/env python3
"""
EDPMT Complete Frontend Server
Serves the static frontend files and bridges WebSocket/HTTP communication with EDPMT backend
using a modern, unified `aiohttp` server.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# --- New Imports for aiohttp --- 
from aiohttp import web
import aiohttp_cors

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file
except ImportError:
    print("Warning: python-dotenv not available, using system environment only")

# Add EDPMT to path for local development
edpmt_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(edpmt_root))

try:
    from edpmt import EDPMTransparent
    from edpmt.utils import get_system_info
except ImportError as e:
    print(f"Error importing EDPMT: {e}")
    print("Please ensure EDPMT is properly installed")
    sys.exit(1)

# --- Simplified Configuration --- 
class Config:
    """Configuration loaded from .env file and environment variables"""
    HTTP_PORT = int(os.getenv('HTTP_PORT', '8085'))
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    VERBOSE_LOGGING = os.getenv('VERBOSE_LOGGING', 'false').lower() == 'true'
    USE_HARDWARE_SIMULATORS = os.getenv('USE_HARDWARE_SIMULATORS', 'true').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    STATIC_DIR = Path(__file__).parent

# Setup logging
log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- New aiohttp-based Server --- 
class EDPMTWebServer:
    """A unified web server for EDPMT frontend using aiohttp."""

    def __init__(self):
        self.app = web.Application()
        self.edpmt_client = None
        self.websockets = set()
        self.projects_dir = Config.STATIC_DIR / 'projects'

    def _map_action(self, action: str, params: dict):
        """Map composite action strings to EDPMTransparent (action, target, **params).
        Returns a tuple (edpm_action, edpm_target, edpm_params) or None if special/non-hardware.
        """
        # Special actions handled locally
        if action in ('get-system-info', 'get-status'):
            return ('__local__', '__system__', params)
        if action in ('execute-project', 'stop-execution'):
            return ('__local__', '__project__', params)

        # Composite actions like 'gpio-set', 'i2c-scan', 'spi-transfer', 'uart-read'...
        if '-' in action:
            target, act = action.split('-', 1)
            return (act, target, params)
        # Fallback: if target provided explicitly
        if 'target' in params:
            tgt = params.pop('target')
            return (action, tgt, params)
        # Unknown mapping
        return (None, None, params)

    async def start_edpmt_client(self):
        """Initializes and starts the EDPMT backend client."""
        try:
            logger.info("Starting EDPMT client...")
            config = {'hardware_simulators': Config.USE_HARDWARE_SIMULATORS}
            self.edpmt_client = EDPMTransparent(config=config)
            await self.edpmt_client.start_server()
            logger.info("EDPMT client started successfully.")
        except Exception as e:
            logger.error(f"Failed to start EDPMT client: {e}. Running in simulation mode.")

    # --- WebSocket Handlers ---
    async def websocket_handler(self, request):
        """Handles WebSocket connections."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websockets.add(ws)
        logger.info(f"WebSocket client connected: {request.remote}")
        try:
            # Send initial system info
            await ws.send_json({'type': 'system_info', 'data': get_system_info()})
            # Listen for messages
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    await self.handle_ws_message(ws, msg.data)
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WebSocket connection closed with exception {ws.exception()}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.websockets.discard(ws)
            logger.info(f"WebSocket client disconnected: {request.remote}")
        return ws

    async def handle_ws_message(self, ws, message):
        """Processes incoming WebSocket messages."""
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
                    # Stub project execution for now
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
        """Periodically broadcasts system info to all connected clients."""
        while True:
            await asyncio.sleep(5)
            if self.websockets:
                info = get_system_info()
                message = json.dumps({'type': 'system_info_update', 'data': info})
                for ws in self.websockets:
                    await ws.send_str(message)

    # --- HTTP API Handlers ---
    async def runtime_config_handler(self, request):
        """Serves a dynamic JS config file for the frontend."""
        config_js = f"""
window.runtimeConfig = {{
    wsUrl: `ws://${{window.location.hostname}}:{Config.HTTP_PORT}/ws`,
    httpUrl: `http://${{window.location.hostname}}:{Config.HTTP_PORT}`
}};
"""
        return web.Response(text=config_js, content_type='application/javascript')

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

    async def list_projects_handler(self, request):
        """Lists available projects from the projects directory."""
        projects = []
        if self.projects_dir.exists():
            for f in self.projects_dir.glob('*.json'):
                try:
                    with open(f, 'r') as fh:
                        data = json.load(fh)
                    projects.append({
                        'name': data.get('name', f.stem),
                        'description': data.get('description', ''),
                        'filename': f.name,
                    })
                except Exception:
                    projects.append({'name': f.stem, 'filename': f.name})
        return web.json_response({'projects': projects})

    async def save_project_handler(self, request):
        try:
            body = await request.json()
            name = body.get('name')
            project = body.get('project')
            if not name or not project:
                return web.json_response({'error': 'name and project required'}, status=400)
            self.projects_dir.mkdir(exist_ok=True)
            file_path = self.projects_dir / f"{name.replace(' ', '_').lower()}.json"
            with open(file_path, 'w') as fh:
                json.dump({**project, 'name': name}, fh, indent=2)
            return web.json_response({'success': True, 'filename': file_path.name})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def load_project_handler(self, request):
        try:
            body = await request.json()
            name = body.get('name')
            if not name:
                return web.json_response({'error': 'name required'}, status=400)
            file_path = self.projects_dir / f"{name.replace(' ', '_').lower()}.json"
            if not file_path.exists():
                return web.json_response({'error': 'not found'}, status=404)
            with open(file_path, 'r') as fh:
                data = json.load(fh)
            return web.json_response(data)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    def setup_middleware(self):
        """Configure middleware for the server."""
        # Enable CORS for all routes
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
            )
        })

        # Configure CORS on all routes
        for route in list(self.app.router.routes()):
            cors.add(route)

    def setup_routes(self):
        """Set up all routes for the web server."""
        # Serve static files from the root
        self.app.router.add_static(
            '/',
            path=str(Config.STATIC_DIR),
            name='static',
            show_index=True
        )

        # API routes
        self.app.router.add_get('/api/status', self.status_handler)
        self.app.router.add_get('/api/projects', self.list_projects_handler)
        self.app.router.add_post('/api/execute', self.execute_handler)
        self.app.router.add_post('/api/save-project', self.save_project_handler)
        self.app.router.add_post('/api/load-project', self.load_project_handler)
        self.app.router.add_get('/runtime-config.js', self.runtime_config_handler)
        self.app.router.add_get('/ws', self.websocket_handler)

        # No catch-all route needed when serving static files from root

    async def run(self):
        """Configure and run the web server."""
        await self.start_edpmt_client()
        
        # Setup routes and middleware
        self.setup_routes()
        self.setup_middleware()

        # Create and run the server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', Config.HTTP_PORT)
        
        logger.info(f"🚀 Server starting on http://0.0.0.0:{Config.HTTP_PORT}")
        await site.start()

        # Start background tasks
        asyncio.create_task(self.broadcast_system_info())

        logger.info("✅ Server is running. Press Ctrl+C to stop.")
        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            pass
        finally:
            await runner.cleanup()
            logger.info("Server shut down.")

def main():
    """Main entry point."""
    server = EDPMTWebServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")

if __name__ == '__main__':
    main()
