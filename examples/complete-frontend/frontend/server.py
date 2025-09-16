#!/usr/bin/env python3
"""
EDPMT Frontend Server
Serves the static frontend files and provides project management APIs.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
import argparse
import time

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

# --- Configuration ---
class Config:
    """Configuration loaded from .env file and environment variables"""
    HTTP_PORT = int(os.getenv('FRONTEND_PORT', '8085'))
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    STATIC_DIR = Path(__file__).parent.parent  # Points to complete-frontend directory
    PROJECTS_DIR = STATIC_DIR / 'projects'

class FrontendServer:
    """Frontend server for serving static files and handling project management."""

    def __init__(self, host='0.0.0.0', port=8085, ws_port=8086, debug=False, log_level='INFO', log_file=None):
        """Initialize the frontend server.
        
        Args:
            host (str): Host to bind to
            port (int): Port to listen on
            ws_port (int): WebSocket server port
            debug (bool): Enable debug mode
            log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file (str, optional): Path to log file
        """
        self.host = host
        self.port = port
        self.ws_port = ws_port
        self.debug = debug
        
        # Configure logging
        self.setup_logging(log_level, log_file)
        
        self.app = web.Application()
        self.setup_middleware()
        self.setup_routes()
        
        # WebSocket client for backend communication
        self.ws_url = f"ws://localhost:{ws_port}/ws"
        self.ws = None
        
        logger.info(f"Frontend server initialized (WebSocket: {self.ws_url})")

    def setup_logging(self, level='INFO', log_file=None):
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
        
        if self.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug("Debug mode enabled")

    async def list_projects_handler(self, request):
        """Lists available projects from the projects directory."""
        projects = []
        if Config.PROJECTS_DIR.exists():
            for f in Config.PROJECTS_DIR.glob('*.json'):
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
                return web.json_response(
                    {'error': 'name and project required'}, status=400)
            
            Config.PROJECTS_DIR.mkdir(exist_ok=True)
            file_path = Config.PROJECTS_DIR / f"{name.replace(' ', '_').lower()}.json"
            with open(file_path, 'w') as fh:
                json.dump({**project, 'name': name}, fh, indent=2)
            return web.json_response(
                {'success': True, 'filename': file_path.name})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def load_project_handler(self, request):
        try:
            body = await request.json()
            name = body.get('name')
            if not name:
                return web.json_response(
                    {'error': 'name required'}, status=400)
            
            file_path = Config.PROJECTS_DIR / f"{name.replace(' ', '_').lower()}.json"
            if not file_path.exists():
                return web.json_response(
                    {'error': 'not found'}, status=404)
            
            with open(file_path, 'r') as fh:
                data = json.load(fh)
            return web.json_response(data)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    def setup_middleware(self):
        """Set up middleware for the frontend server."""
        # Error handling middleware
        @web.middleware
        async def error_middleware(request, handler):
            try:
                response = await handler(request)
                if response.status == 404:
                    return await self.index_handler(request)
                return response
            except web.HTTPException as ex:
                if ex.status == 404:
                    return await self.index_handler(request)
                raise
            except Exception as e:
                self.logger.error(f"Error handling request {request.rel_url}: {str(e)}")
                return web.json_response(
                    {"error": "Internal server error", "details": str(e)},
                    status=500
                )

        self.app.middlewares.append(error_middleware)

        # CORS middleware setup
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allow_origin=[
                    f"http://{self.host}:{self.port}",
                    f"http://127.0.0.1:{self.port}",
                    f"http://localhost:{self.port}",
                    "http://localhost:8085",
                    "http://127.0.0.1:8085"
                ]
            )
        })

        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            try:
                cors.add(route)
            except RuntimeError as e:
                if "Cannot add a route with the same path and method" in str(e):
                    self.logger.warning(f"Skipping duplicate route: {route}")
                else:
                    self.logger.error(f"Error adding CORS to route {route}: {e}")
                    raise

    def setup_routes(self):
        """Set up all routes for the frontend server."""
        # Add API routes
        self.app.router.add_route('GET', '/api/status', self.status_handler)
        
        # Add static files
        static_path = Path(__file__).parent.parent / 'static'
        if static_path.exists():
            self.app.router.add_static('/static/', path=str(static_path))
        
        # Serve index.html for all other routes (SPA support)
        self.app.router.add_route('GET', '/{path:.*}', self.index_handler)
        self.app.router.add_route('GET', '/', self.index_handler)

    async def runtime_config_handler(self, request):
        """Serve the runtime configuration."""
        config = {
            'ws_url': f'ws://{self.host}:{self.ws_port}/ws',
            'api_url': f'http://{self.host}:{self.port}/api',
            'debug': self.debug
        }
        
        js = f'window.EDPMT_CONFIG = {json.dumps(config, indent=2)};'
        return web.Response(
            text=js,
            content_type='application/javascript',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Allow-Credentials': 'true'
            }
        )
    
    async def index_handler(self, request):
        """Serve the main index.html file."""
        index_path = Path(__file__).parent.parent / 'index.html'
        if not index_path.exists():
            return web.Response(status=404, text='Not Found')
            
        with open(index_path, 'r') as f:
            content = f.read()
            
        # Update base URL in index.html if needed
        base_url = f"http://{self.host}:{self.port}"
        content = content.replace('href="/', f'href="{base_url}/')
        content = content.replace('src="/', f'src="{base_url}/')
            
        return web.Response(
            text=content,
            content_type='text/html',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Allow-Credentials': 'true'
            }
        )

    async def status_handler(self, request):
        """Handle status requests."""
        return web.json_response({
            'status': 'ok',
            'service': 'frontend',
            'port': self.port,
            'websocket_port': self.ws_port,
            'timestamp': time.time()
        })

    async def run(self):
        """Run the frontend server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        
        logger.info(f"🚀 Frontend server starting on http://{self.host}:{self.port}")
        await site.start()

        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            await runner.cleanup()
            logger.info("Frontend server shut down.")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='EDPMT Frontend Server')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                      help='Host to bind to')
    parser.add_argument('--port', type=int, default=8085,
                      help='Port to listen on')
    parser.add_argument('--ws-port', type=int, default=8086,
                      help='WebSocket server port')
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
    server = FrontendServer(
        host=args.host,
        port=args.port,
        ws_port=args.ws_port,
        debug=args.debug,
        log_level=args.log_level,
        log_file=args.log_file
    )
    asyncio.run(server.run())

if __name__ == '__main__':
    main()
