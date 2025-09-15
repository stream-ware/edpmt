#!/usr/bin/env python3
"""
EDPMT Complete Frontend Server
Serves the static frontend files and bridges WebSocket/HTTP communication with EDPMT backend
"""

import asyncio
import json
import logging
import os
import sys
import time
import websockets
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, urlparse
import threading

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file
except ImportError:
    print("Warning: python-dotenv not available, using system environment only")

# Add EDPMT to path
edpmt_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(edpmt_root))

try:
    from edpmt import EDPMTransparent
except ImportError as e:
    print(f"Error importing EDPMT: {e}")
    print("Please ensure EDPMT is properly installed")
    sys.exit(1)

# Configuration from environment variables
class Config:
    """Configuration loaded from .env file and environment variables"""
    
    # Server Configuration
    HTTP_PORT = int(os.getenv('HTTP_PORT', '8085'))
    WEBSOCKET_PORT = int(os.getenv('WEBSOCKET_PORT', '8086'))
    
    # Development Configuration
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    VERBOSE_LOGGING = os.getenv('VERBOSE_LOGGING', 'false').lower() == 'true'
    USE_HARDWARE_SIMULATORS = os.getenv('USE_HARDWARE_SIMULATORS', 'true').lower() == 'true'
    
    # File Paths
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    PROJECTS_DIR = os.getenv('PROJECTS_DIR', 'projects')
    STATIC_DIR = os.getenv('STATIC_DIR', '.')
    
    # Log Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # EDPMT Backend Configuration
    EDPMT_BACKEND_TIMEOUT = int(os.getenv('EDPMT_BACKEND_TIMEOUT', '30'))
    
    # Performance Configuration
    MAX_CONNECTIONS = int(os.getenv('MAX_CONNECTIONS', '100'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    
    @classmethod
    def print_config(cls):
        """Print current configuration for debugging"""
        print("📋 Current Configuration:")
        print(f"  HTTP Port: {cls.HTTP_PORT}")
        print(f"  WebSocket Port: {cls.WEBSOCKET_PORT}")
        print(f"  Debug: {cls.DEBUG}")
        print(f"  Hardware Simulators: {cls.USE_HARDWARE_SIMULATORS}")
        print(f"  Log Level: {cls.LOG_LEVEL}")
        print(f"  Projects Dir: {cls.PROJECTS_DIR}")
        print(f"  Static Dir: {cls.STATIC_DIR}")

# Setup logging with configuration from .env
log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if Config.DEBUG:
    Config.print_config()

class EDPMTFrontendHandler(SimpleHTTPRequestHandler):
    """HTTP handler for serving frontend files and API endpoints"""
    
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        self.directory = Path(__file__).parent
        super().__init__(*args, directory=str(self.directory), **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        # API endpoints
        if parsed_path.path.startswith('/api/'):
            self.handle_api_get(parsed_path)
        else:
            # Serve static files
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests for API endpoints"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.startswith('/api/'):
            self.handle_api_post(parsed_path)
        else:
            self.send_error(404, "Not Found")
    
    def handle_api_get(self, parsed_path):
        """Handle GET API requests"""
        endpoint = parsed_path.path[5:]  # Remove '/api/' prefix
        
        try:
            if endpoint == 'status':
                self.handle_status_request()
            elif endpoint == 'system-info':
                self.handle_system_info_request()
            elif endpoint == 'projects':
                self.handle_list_projects_request()
            else:
                self.send_error(404, f"API endpoint not found: {endpoint}")
        except Exception as e:
            logger.error(f"API GET error: {e}")
            self.send_json_error(500, str(e))
    
    def handle_api_post(self, parsed_path):
        """Handle POST API requests"""
        endpoint = parsed_path.path[5:]  # Remove '/api/' prefix
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if post_data:
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            if endpoint == 'execute':
                self.handle_execute_request(data)
            elif endpoint == 'save-project':
                self.handle_save_project_request(data)
            elif endpoint == 'load-project':
                self.handle_load_project_request(data)
            else:
                self.send_error(404, f"API endpoint not found: {endpoint}")
                
        except json.JSONDecodeError as e:
            self.send_json_error(400, f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"API POST error: {e}")
            self.send_json_error(500, str(e))
    
    def handle_status_request(self):
        """Get peripheral status from EDPMT backend"""
        try:
            if hasattr(self.server, 'edpmt_client') and self.server.edpmt_client:
                # Get status from EDPMT
                status = asyncio.run_coroutine_threadsafe(
                    self.server.edpmt_client.get_status(),
                    self.server.loop
                ).result(timeout=5)
                
                self.send_json_response(status)
            else:
                self.send_json_response({
                    'error': 'EDPMT backend not available',
                    'gpio': {},
                    'i2c': {'active': False, 'devices': []},
                    'spi': {'ready': False},
                    'uart': {'baudrate': 9600}
                })
        except Exception as e:
            logger.error(f"Status request failed: {e}")
            self.send_json_error(500, f"Status request failed: {e}")
    
    def handle_system_info_request(self):
        """Get system information"""
        try:
            system_info = {
                'platform': sys.platform,
                'python_version': sys.version,
                'edpmt_version': '1.0.0',
                'frontend_version': '1.0.0',
                'timestamp': time.time()
            }
            self.send_json_response(system_info)
        except Exception as e:
            self.send_json_error(500, str(e))
    
    def handle_execute_request(self, data):
        """Execute command on EDPMT backend"""
        try:
            action = data.get('action')
            params = data.get('params', {})
            
            if not action:
                self.send_json_error(400, "Action is required")
                return
            
            if hasattr(self.server, 'edpmt_client') and self.server.edpmt_client:
                # Execute on EDPMT
                result = asyncio.run_coroutine_threadsafe(
                    self.server.edpmt_client.execute(action, params),
                    self.server.loop
                ).result(timeout=10)
                
                self.send_json_response(result)
            else:
                # Simulate response for development
                self.send_json_response({
                    'action': action,
                    'params': params,
                    'result': 'simulated',
                    'timestamp': time.time()
                })
                
        except Exception as e:
            logger.error(f"Execute request failed: {e}")
            self.send_json_error(500, f"Execute request failed: {e}")
    
    def handle_list_projects_request(self):
        """List available projects"""
        try:
            projects_dir = self.directory / 'projects'
            projects = []
            
            if projects_dir.exists():
                for project_file in projects_dir.glob('*.json'):
                    try:
                        with open(project_file, 'r') as f:
                            project_data = json.load(f)
                            projects.append({
                                'name': project_data.get('name', project_file.stem),
                                'description': project_data.get('description', ''),
                                'filename': project_file.name,
                                'modified': project_file.stat().st_mtime
                            })
                    except Exception as e:
                        logger.warning(f"Failed to load project {project_file}: {e}")
            
            self.send_json_response({'projects': projects})
            
        except Exception as e:
            self.send_json_error(500, str(e))
    
    def handle_save_project_request(self, data):
        """Save a project"""
        try:
            name = data.get('name')
            project_data = data.get('project')
            
            if not name or not project_data:
                self.send_json_error(400, "Name and project data are required")
                return
            
            projects_dir = self.directory / 'projects'
            projects_dir.mkdir(exist_ok=True)
            
            # Add metadata
            project_data['name'] = name
            project_data['saved_at'] = time.time()
            project_data['version'] = '1.0'
            
            project_file = projects_dir / f"{name.replace(' ', '_').lower()}.json"
            with open(project_file, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            self.send_json_response({
                'success': True,
                'message': f'Project "{name}" saved successfully',
                'filename': project_file.name
            })
            
        except Exception as e:
            self.send_json_error(500, str(e))
    
    def handle_load_project_request(self, data):
        """Load a project"""
        try:
            name = data.get('name')
            if not name:
                self.send_json_error(400, "Project name is required")
                return
            
            projects_dir = self.directory / 'projects'
            project_file = projects_dir / f"{name.replace(' ', '_').lower()}.json"
            
            if not project_file.exists():
                self.send_json_error(404, f"Project '{name}' not found")
                return
            
            with open(project_file, 'r') as f:
                project_data = json.load(f)
            
            self.send_json_response(project_data)
            
        except Exception as e:
            self.send_json_error(500, str(e))
    
    def send_json_response(self, data):
        """Send JSON response"""
        response = json.dumps(data, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def send_json_error(self, code, message):
        """Send JSON error response"""
        error_data = {'error': message, 'code': code}
        response = json.dumps(error_data)
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Thread-safe HTTP server"""
    daemon_threads = True
    allow_reuse_address = True

class EDPMTWebSocketHandler:
    """WebSocket handler for real-time communication"""
    
    def __init__(self, edpmt_client=None):
        self.edpmt_client = edpmt_client
        self.clients = set()
    
    async def register_client(self, websocket):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"WebSocket client connected: {websocket.remote_address}")
        
        # Send initial status
        if self.edpmt_client:
            try:
                status = await self.edpmt_client.get_status()
                await websocket.send(json.dumps({
                    'type': 'status_update',
                    'data': status
                }))
            except Exception as e:
                logger.error(f"Failed to send initial status: {e}")
    
    async def unregister_client(self, websocket):
        """Unregister a WebSocket client"""
        self.clients.discard(websocket)
        logger.info(f"WebSocket client disconnected: {websocket.remote_address}")
    
    async def handle_message(self, websocket, message):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'command':
                await self.handle_command(websocket, data)
            elif message_type == 'subscribe':
                await self.handle_subscribe(websocket, data)
            elif message_type == 'ping':
                await websocket.send(json.dumps({'type': 'pong'}))
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from WebSocket: {e}")
        except Exception as e:
            logger.error(f"WebSocket message handling error: {e}")
    
    async def handle_command(self, websocket, data):
        """Handle command execution"""
        try:
            command_id = data.get('id')
            action = data.get('action')
            params = data.get('params', {})
            
            if not self.edpmt_client:
                response = {
                    'type': 'command_response',
                    'id': command_id,
                    'error': 'EDPMT backend not available'
                }
            else:
                # Execute command
                result = await self.edpmt_client.execute(action, params)
                response = {
                    'type': 'command_response',
                    'id': command_id,
                    'data': result
                }
            
            await websocket.send(json.dumps(response))
            
        except Exception as e:
            response = {
                'type': 'command_response',
                'id': data.get('id'),
                'error': str(e)
            }
            await websocket.send(json.dumps(response))
    
    async def handle_subscribe(self, websocket, data):
        """Handle event subscription"""
        events = data.get('events', [])
        logger.info(f"Client subscribed to events: {events}")
        # In a full implementation, we would track subscriptions per client
    
    async def broadcast(self, message):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
        
        disconnected = set()
        
        for websocket in self.clients:
            try:
                await websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.clients.discard(websocket)
    
    async def start_status_broadcaster(self):
        """Start periodic status broadcasting"""
        while True:
            try:
                if self.edpmt_client and self.clients:
                    status = await self.edpmt_client.get_status()
                    await self.broadcast({
                        'type': 'status_update',
                        'data': status
                    })
                
                await asyncio.sleep(2)  # Broadcast every 2 seconds
                
            except Exception as e:
                logger.error(f"Status broadcast error: {e}")
                await asyncio.sleep(5)

class EDPMTFrontendServer:
    """Main server class that combines HTTP and WebSocket servers"""
    
    def __init__(self, http_port=8085, ws_port=8086, edpmt_config=None):
        self.http_port = http_port
        self.ws_port = ws_port
        self.edpmt_config = edpmt_config or {}
        
        self.edpmt_client = None
        self.http_server = None
        self.ws_handler = None
        self.loop = None
        
    async def start_edpmt_client(self):
        """Start EDPMT client"""
        try:
            logger.info("Starting EDPMT client...")
            
            # Use hardware simulators for development
            config = {
                'hardware_simulators': True,
                'enable_web_ui': False,  # We're providing our own frontend
                **self.edpmt_config
            }
            
            self.edpmt_client = EDPMTransparent(config=config)
            await self.edpmt_client.start_server()
            
            logger.info("EDPMT client started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start EDPMT client: {e}")
            logger.info("Continuing without EDPMT backend (simulation mode)")
            return False
    
    def start_http_server(self):
        """Start HTTP server for static files and API"""
        try:
            logger.info(f"Starting HTTP server on port {self.http_port}...")
            
            self.http_server = ThreadedHTTPServer(
                ('0.0.0.0', self.http_port),
                EDPMTFrontendHandler
            )
            
            # Pass references to the server
            self.http_server.edpmt_client = self.edpmt_client
            self.http_server.loop = self.loop
            
            # Start in a separate thread
            http_thread = threading.Thread(
                target=self.http_server.serve_forever,
                daemon=True
            )
            http_thread.start()
            
            logger.info(f"HTTP server started on http://0.0.0.0:{self.http_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")
            return False
    
    async def websocket_handler(self, websocket, path):
        """WebSocket connection handler"""
        await self.ws_handler.register_client(websocket)
        
        try:
            async for message in websocket:
                await self.ws_handler.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await self.ws_handler.unregister_client(websocket)
    
    async def start_websocket_server(self):
        """Start WebSocket server"""
        try:
            logger.info(f"Starting WebSocket server on port {self.ws_port}...")
            
            self.ws_handler = EDPMTWebSocketHandler(self.edpmt_client)
            
            # Start WebSocket server
            start_server = websockets.serve(
                self.websocket_handler,
                '0.0.0.0',
                self.ws_port,
                ping_interval=30,
                ping_timeout=10
            )
            
            await start_server
            
            # Start status broadcaster
            asyncio.create_task(self.ws_handler.start_status_broadcaster())
            
            logger.info(f"WebSocket server started on ws://0.0.0.0:{self.ws_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            return False
    
    async def run(self):
        """Run the complete server"""
        logger.info("Starting EDPMT Complete Frontend Server...")
        
        # Store event loop reference
        self.loop = asyncio.get_running_loop()
        
        # Start EDPMT client (optional)
        await self.start_edpmt_client()
        
        # Start HTTP server
        if not self.start_http_server():
            logger.error("Failed to start HTTP server")
            return False
        
        # Start WebSocket server
        if not await self.start_websocket_server():
            logger.error("Failed to start WebSocket server")
            return False
        
        logger.info("=" * 60)
        logger.info("🚀 EDPMT Complete Frontend Server is running!")
        logger.info(f"📄 Frontend: http://localhost:{self.http_port}")
        logger.info(f"🔌 WebSocket: ws://localhost:{self.ws_port}")
        logger.info(f"🎯 Backend: {'Connected' if self.edpmt_client else 'Simulation Mode'}")
        logger.info("=" * 60)
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
            if self.http_server:
                self.http_server.shutdown()
        
        return True

def main():
    """Main entry point - uses configuration from .env file"""
    import argparse
    
    # Still allow command-line overrides for specific use cases
    parser = argparse.ArgumentParser(description='EDPMT Complete Frontend Server')
    parser.add_argument('--http-port', type=int, default=Config.HTTP_PORT, 
                        help=f'HTTP server port (default: {Config.HTTP_PORT})')
    parser.add_argument('--ws-port', type=int, default=Config.WEBSOCKET_PORT, 
                        help=f'WebSocket server port (default: {Config.WEBSOCKET_PORT})')
    parser.add_argument('--hardware-simulators', action='store_true', default=Config.USE_HARDWARE_SIMULATORS,
                        help='Use hardware simulators (for development)')
    parser.add_argument('--verbose', '-v', action='store_true', default=Config.VERBOSE_LOGGING, 
                        help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose or Config.VERBOSE_LOGGING:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🔍 Verbose logging enabled")
    
    # Print configuration for debugging
    if Config.DEBUG:
        logger.info("Starting with configuration from .env file")
    
    # EDPMT configuration
    edpmt_config = {
        'hardware_simulators': args.hardware_simulators
    }
    
    logger.info(f"🚀 Starting server with HTTP:{args.http_port}, WS:{args.ws_port}")
    logger.info(f"🔧 Hardware simulators: {args.hardware_simulators}")
    
    # Create and run server
    server = EDPMTFrontendServer(
        http_port=args.http_port,
        ws_port=args.ws_port,
        edpmt_config=edpmt_config
    )
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
