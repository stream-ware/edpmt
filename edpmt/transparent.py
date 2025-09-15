#!/usr/bin/env python3
"""
EDPM Transparent - Core Implementation
Simple, Secure, Universal Hardware Communication

Single file, zero configuration, automatic protocol selection
"""

import os
import json
import asyncio
import ssl
import logging
import time
import datetime
import hashlib
import random
from typing import Any, Dict, Optional, Union, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class TransportType(Enum):
    """Automatic transport selection based on context"""
    LOCAL = "local"      # Same machine - IPC/Unix socket
    NETWORK = "network"  # Network - TLS encrypted
    BROWSER = "browser"  # Browser - WebSocket Secure (WSS)
    AUTO = "auto"        # Automatic selection


@dataclass
class Message:
    """Universal message format - simple and transparent"""
    action: str          # What to do
    target: str          # Where to do it (gpio, i2c, etc.)
    params: Dict = None  # Parameters
    id: str = None       # Message ID (auto-generated)
    timestamp: float = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}
        if self.id is None:
            self.id = self._generate_id()
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def _generate_id(self) -> str:
        """Simple time-based ID (sortable)"""
        return f"{int(time.time() * 1000000):x}"
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, data: str) -> 'Message':
        return cls(**json.loads(data))


class Stats:
    def __init__(self):
        self.messages_sent = 0
        self.messages_received = 0
        self.errors = 0


class EDPMTransparent:
    """
    Main EDPM class - transparent, simple, secure
    Zero configuration required - everything auto-detected
    """
    
    def __init__(self, name: str = None, config: Dict[str, Any] = None):
        self.name = name or f"edpm_{random.randint(100000, 999999)}"
        self.config = config or {}
        self.transport_type = TransportType.LOCAL  # Default to local
        self.tls_enabled = self.config.get('tls', True)
        self.dev_mode = self.config.get('dev_mode', False)
        self.host = self.config.get('host', '0.0.0.0')
        self.port = int(self.config.get('port', 8888))
        self.use_simulators = self.config.get('hardware_simulators', False)
        self.stats = Stats()
        self.logger = logging.getLogger(f"EDPM.{self.name}")
        self.logger.info(f"EDPM Transparent initialized: {self.name}")
        self.logger.info(f"Transport: {self.transport_type.value}, TLS: {self.tls_enabled}")

        # Hardware interfaces will be initialized dynamically
        self.hardware_interfaces = None
        self.hardware_future = None
        self._initialize_hardware()

    def _initialize_hardware(self):
        """Initialize hardware interfaces with fallback to simulators based on config."""
        import asyncio
        from .hardware.factory import HardwareInterfaceFactory
        self.use_simulators = self.config.get('hardware_simulators', False)
        self.logger.info(f"Initializing hardware interfaces (simulators: {self.use_simulators})")
        # Use ensure_future to run the coroutine in the existing event loop
        self.hardware_future = asyncio.ensure_future(
            HardwareInterfaceFactory.create_all_interfaces(use_simulators=self.use_simulators, config=self.config)
        )
        # Since we're in __init__ and might not be in an async context, we'll handle this in start_server
        self.logger.info("Hardware initialization scheduled")

    async def start_server(self):
        """Start the appropriate server based on transport type."""
        if not self.hardware_interfaces and self.hardware_future:
            self.logger.info("Completing hardware initialization before starting server")
            try:
                self.hardware_interfaces = await self.hardware_future
                self.logger.info(f"Initialized hardware interfaces: {list(self.hardware_interfaces.keys())}")
            except Exception as e:
                self.logger.error(f"Failed to initialize hardware interfaces: {e}")
                self.hardware_interfaces = {}
                self.logger.warning("Continuing without hardware interfaces")
        if self.transport_type == TransportType.LOCAL:
            await self._start_ipc_server()
        elif self.transport_type == TransportType.NETWORK:
            await self._start_network_server()
        elif self.transport_type == TransportType.BROWSER:
            await self._start_websocket_server()
        else:
            raise ValueError(f"Unsupported transport type: {self.transport_type}")

    async def _start_network_server(self):
        """Start network server with optional TLS"""
        from aiohttp import web
        import aiohttp_cors
        
        app = web.Application()
        
        # Add CORS for browser access
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Routes
        app.router.add_post('/api/execute', self._handle_http_request)
        app.router.add_get('/ws', self._handle_websocket)
        app.router.add_get('/', self._handle_index)
        app.router.add_get('/health', self._handle_health)
        
        # Apply CORS
        for route in list(app.router.routes()):
            cors.add(route)
        
        # SSL context for HTTPS/WSS
        ssl_context = None
        if self.tls_enabled:
            ssl_context = ssl.create_default_context()
            # For self-signed certs in development
            if self.dev_mode:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
        
        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(
            runner, 
            self.host, 
            self.port,
            ssl_context=ssl_context
        )
        
        await site.start()
        
        protocol = "https" if self.tls_enabled else "http"
        self.logger.info(f"Server running at {protocol}://{self.host}:{self.port}")

    async def _start_ipc_server(self):
        """Start IPC server for local communication"""
        if self.transport_type != TransportType.LOCAL:
            self.logger.info("IPC server not started (not in local mode)")
            return
        
        # Check if ipc_path exists in config, provide a default if not
        ipc_path = self.config.get('ipc_path', '/tmp/edpmt.sock')
        self.logger.info(f"IPC server would start at {ipc_path}")
        # Actual implementation would create a Unix socket server here
        # self.ipc_server = await asyncio.start_unix_server(...)
    
    async def _start_websocket_server(self):
        """Start WebSocket server"""
        # For browser mode, use network server with WebSocket support
        await self._start_network_server()

    async def execute(self, action: str, target: str, **params) -> Any:
        """
        Execute any action on any target - single universal method
        
        Examples:
            await edpm.execute('set', 'gpio', pin=17, value=1)
            await edpm.execute('read', 'i2c', device=0x76)
            await edpm.execute('play', 'audio', frequency=440)
        """
        # Validate action and target
        valid_actions = ['set', 'get', 'read', 'write', 'scan', 'transfer', 'pwm', 'play', 'list', 'connect', 'disconnect', 'send', 'receive', 'configure', 'record']
        valid_targets = list(self.hardware_interfaces.keys()) + ['audio']
        
        if action not in valid_actions:
            self.logger.warning(f"Invalid action requested: {action}")
            return {"success": False, "error": f"Invalid action: {action}. Valid actions are {valid_actions}"}
        
        if target not in valid_targets:
            self.logger.warning(f"Invalid target requested: {target}")
            return {"success": False, "error": f"Invalid target: {target}. Valid targets are {valid_targets}"}
        
        message = Message(action=action, target=target, params=params)
        
        # Log the request
        self.logger.info(f"Executing: {message.action} {message.target} {message.params}")
        self.stats.messages_received += 1

        try:
            # Route to appropriate hardware interface
            if target in self.hardware_interfaces:
                result = await self.hardware_interfaces[target].execute(action, **params)
                self.stats.messages_sent += 1
                return {"success": True, "result": result, "id": message.id}
            else:
                # Handle non-hardware targets or future extensions
                self.stats.errors += 1
                return {"success": False, "error": f"Target {target} not implemented", "id": message.id}
        except Exception as e:
            # Log error and return structured response
            self.logger.error(f"Error executing {message.action} on {message.target}: {e}")
            self.stats.errors += 1
            return {"success": False, "error": str(e), "id": message.id}

    # === Server Mode ===
    
    async def _handle_http_request(self, request):
        """Handle HTTP API requests"""
        from aiohttp import web
        
        try:
            data = await request.json()
            message = Message(**data)
            
            result = await self.execute(
                message.action,
                message.target,
                **message.params
            )
            
            return web.json_response({
                'success': True,
                'result': result,
                'id': message.id
            })
        except Exception as e:
            self.logger.error(f"Request error: {e}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=400)

    async def _handle_websocket(self, request):
        """Handle WebSocket connections"""
        from aiohttp import web
        
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        client_id = f"ws_{time.time()}"
        # self.connections[client_id] = ws
        
        self.logger.info(f"WebSocket client connected: {client_id}")
        
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        message = Message.from_json(msg.data)
                        
                        result = await self.execute(
                            message.action,
                            message.target,
                            **message.params
                        )
                        
                        await ws.send_json({
                            'success': True,
                            'result': result,
                            'id': message.id
                        })
                    except Exception as e:
                        await ws.send_json({
                            'success': False,
                            'error': str(e)
                        })
        finally:
            # self.connections.pop(client_id, None)
            self.logger.info(f"WebSocket client disconnected: {client_id}")
        
        return ws
    
    async def _handle_health(self, request):
        """Health check endpoint"""
        from aiohttp import web
        
        return web.json_response({
            'status': 'healthy',
            'name': self.name,
            'transport': self.transport_type.value,
            'tls': self.tls_enabled,
            'stats': {
                'messages_sent': self.stats.messages_sent,
                'messages_received': self.stats.messages_received,
                'errors': self.stats.errors
            },
            'uptime': time.time() - self.stats.messages_received
        })
    
    async def _handle_index(self, request):
        """Serve simple web UI"""
        from aiohttp import web
        from .web_ui import get_web_ui
        
        return web.Response(text=get_web_ui(), content_type='text/html')

    async def shutdown(self):
        """Shut down the server and clean up resources."""
        self.logger.info("Shutting down EDPM Transparent server")
        if self.hardware_interfaces:
            for interface_name, interface in self.hardware_interfaces.items():
                self.logger.info(f"Cleaning up hardware interface: {interface_name}")
                try:
                    await interface.cleanup()
                except Exception as e:
                    self.logger.warning(f"Error cleaning up {interface_name}: {e}")
            self.hardware_interfaces = None
        self.logger.info("Server shutdown complete")


class EDPMClient:
    """Simple client for EDPM - transparent and easy"""
    
    def __init__(self, url: str = None, use_tls: bool = None):
        """
        Initialize client with auto-detection
        
        Args:
            url: Server URL (auto-detected if None)
            use_tls: Use TLS (auto-detected from URL)
        """
        self.url = url or os.environ.get('EDPM_URL', 'http://localhost:8888')
        self.use_tls = use_tls if use_tls is not None else self.url.startswith('https')
        self.ws = None
        self.session = None
        
        # Setup SSL if needed
        if self.use_tls:
            self.ssl_context = ssl.create_default_context()
            # For self-signed certs in development
            if os.environ.get('EDPM_DEV'):
                self.ssl_context.check_hostname = False
                self.ssl_context.verify_mode = ssl.CERT_NONE
    
    async def execute(self, action: str, target: str, **params) -> Any:
        """Execute command on server - simple and transparent"""
        message = Message(action=action, target=target, params=params)
        
        # Use WebSocket if connected
        if self.ws:
            await self.ws.send(message.to_json())
            response = await self.ws.recv()
            data = json.loads(response)
        else:
            # Use HTTP
            import aiohttp
            
            if not self.session:
                connector = aiohttp.TCPConnector(ssl=self.ssl_context if self.use_tls else None)
                self.session = aiohttp.ClientSession(connector=connector)
            
            async with self.session.post(
                f"{self.url}/api/execute",
                json=asdict(message),
                ssl=self.ssl_context if self.use_tls else None
            ) as resp:
                data = await resp.json()
        
        if data.get('success'):
            return data.get('result')
        else:
            raise Exception(data.get('error', 'Unknown error'))
    
    async def connect_websocket(self):
        """Connect via WebSocket for real-time communication"""
        import websockets
        
        ws_url = self.url.replace('http', 'ws') + '/ws'
        
        if self.use_tls:
            self.ws = await websockets.connect(ws_url, ssl=self.ssl_context)
        else:
            self.ws = await websockets.connect(ws_url)
        
        self.logger.info(f"WebSocket connected to {ws_url}")
    
    async def close(self):
        """Close client connections"""
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
    
    # Convenience methods
    async def gpio_set(self, pin: int, value: int):
        """Set GPIO pin value"""
        return await self.execute('set', 'gpio', pin=pin, value=value)
    
    async def gpio_get(self, pin: int):
        """Get GPIO pin value"""
        return await self.execute('get', 'gpio', pin=pin)
    
    async def i2c_scan(self):
        """Scan I2C bus"""
        return await self.execute('scan', 'i2c')
    
    async def i2c_read(self, device: int, register: int, length: int = 1):
        """Read from I2C device"""
        return await self.execute('read', 'i2c', 
                                 device=device, 
                                 register=register, 
                                 length=length)
    
    async def i2c_write(self, device: int, register: int, data: bytes):
        """Write to I2C device"""
        return await self.execute('write', 'i2c',
                                 device=device,
                                 register=register,
                                 data=data)
