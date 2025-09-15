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
from typing import Any, Dict, Optional, Union, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('EDPM')


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


class EDPMTransparent:
    """
    Main EDPM class - transparent, simple, secure
    Zero configuration required - everything auto-detected
    """
    
    def __init__(self, 
                 name: str = None,
                 transport: TransportType = TransportType.AUTO,
                 tls: bool = None,
                 config: Dict = None):
        """
        Initialize EDPM with automatic configuration
        
        Args:
            name: Instance name (auto-generated if None)
            transport: Transport type (auto-detected if AUTO)
            tls: Enable TLS (auto-enabled for network transport)
            config: Optional configuration override
        """
        self.name = name or f"edpm_{os.getpid()}"
        self.transport = self._detect_transport() if transport == TransportType.AUTO else transport
        self.tls_enabled = tls if tls is not None else (self.transport == TransportType.NETWORK)
        self.config = config or self._default_config()
        
        # State
        self.handlers = {}
        self.connections = {}
        self.ssl_context = None
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # Hardware interfaces (lazy loading)
        self._gpio = None
        self._i2c = None
        self._spi = None
        self._uart = None
        
        logger.info(f"EDPM Transparent initialized: {self.name}")
        logger.info(f"Transport: {self.transport.value}, TLS: {self.tls_enabled}")
        
        # Auto-setup TLS if needed
        if self.tls_enabled:
            self._setup_tls()
    
    def _detect_transport(self) -> TransportType:
        """Automatically detect best transport method"""
        # Check if running in browser (WASM)
        if 'pyodide' in str(type(os)):
            return TransportType.BROWSER
        
        # Check if network interface needed
        if os.environ.get('EDPM_REMOTE') or os.environ.get('EDPM_PORT'):
            return TransportType.NETWORK
        
        # Default to local
        return TransportType.LOCAL
    
    def _default_config(self) -> Dict:
        """Generate default configuration"""
        return {
            'port': int(os.environ.get('EDPM_PORT', 8888)),
            'host': os.environ.get('EDPM_HOST', '0.0.0.0'),
            'ipc_path': os.environ.get('EDPM_IPC', f'/tmp/edpm_{self.name}.sock'),
            'cert_dir': os.environ.get('EDPM_CERTS', Path.home() / '.edpm' / 'certs'),
            'auto_reconnect': True,
            'timeout': 30,
            'buffer_size': 10000
        }
    
    def _setup_tls(self):
        """Setup TLS with auto-generated certificates"""
        from .utils import generate_certificates
        
        cert_dir = Path(self.config['cert_dir'])
        cert_dir.mkdir(parents=True, exist_ok=True)
        
        cert_file = cert_dir / 'edpm.crt'
        key_file = cert_dir / 'edpm.key'
        
        # Generate self-signed certificate if not exists
        if not cert_file.exists() or not key_file.exists():
            logger.info("Generating TLS certificates...")
            generate_certificates(cert_file, key_file)
        
        # Create SSL context
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_context.load_cert_chain(cert_file, key_file)
        
        # For development - accept self-signed certs
        if os.environ.get('EDPM_DEV'):
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
        
        logger.info("TLS configured successfully")
    
    # === Simple Universal API ===
    
    async def execute(self, action: str, target: str, **params) -> Any:
        """
        Execute any action on any target - single universal method
        
        Examples:
            await edpm.execute('set', 'gpio', pin=17, value=1)
            await edpm.execute('read', 'i2c', device=0x76)
            await edpm.execute('play', 'audio', frequency=440)
        """
        message = Message(action=action, target=target, params=params)
        
        # Log for transparency
        logger.debug(f"Execute: {action} on {target} with {params}")
        
        # Route to appropriate handler
        handler = self.handlers.get(target)
        if handler:
            result = await handler(message)
        else:
            result = await self._default_handler(message)
        
        # Convert bytes to list for JSON serialization for all hardware operations
        if isinstance(result, bytes):
            result = list(result)
        
        # Update stats
        self.stats['messages_sent'] += 1
        self.stats['messages_received'] += 1
        
        return result
    
    async def _default_handler(self, message: Message) -> Any:
        """Default handler for hardware operations"""
        target = message.target
        action = message.action
        params = message.params
        
        # GPIO operations
        if target == 'gpio':
            if action == 'set':
                return await self.gpio_set(params['pin'], params['value'])
            elif action == 'get':
                return await self.gpio_get(params['pin'])
            elif action == 'pwm':
                return await self.gpio_pwm(
                    params['pin'], 
                    params.get('frequency', 1000),
                    params.get('duty_cycle', 50)
                )
        
        # I2C operations
        elif target == 'i2c':
            if action == 'scan':
                return await self.i2c_scan()
            elif action == 'read':
                return await self.i2c_read(
                    params.get('device'),
                    params.get('register'),
                    params.get('length', 1)
                )
            elif action == 'write':
                return await self.i2c_write(
                    params.get('device'),
                    params.get('register'),
                    params.get('data')
                )
        
        # SPI operations
        elif target == 'spi':
            if action == 'transfer':
                return await self.spi_transfer(
                    params.get('data'),
                    params.get('bus', 0),
                    params.get('device', 0)
                )
        
        # UART operations
        elif target == 'uart':
            if action == 'write':
                return await self.uart_write(
                    params.get('data'),
                    params.get('port', '/dev/ttyUSB0')
                )
            elif action == 'read':
                return await self.uart_read(
                    params.get('port', '/dev/ttyUSB0'),
                    params.get('length', 1)
                )
        
        # Audio operations
        elif target == 'audio':
            if action == 'play':
                return await self.audio_play(
                    params.get('frequency', 440),
                    params.get('duration', 1.0)
                )
        
        # Unknown target/action
        else:
            raise ValueError(f"Unknown target/action: {target}/{action}")
    
    # === Hardware Abstraction Layer (Simple) ===
    
    async def gpio_set(self, pin: int, value: int) -> bool:
        """Set GPIO pin value"""
        if not self._gpio:
            self._gpio = await self._init_gpio()
        
        try:
            await self._gpio.set(pin, value)
            logger.info(f"GPIO {pin} = {value}")
            return True
        except Exception as e:
            logger.error(f"GPIO error: {e}")
            self.stats['errors'] += 1
            return False
    
    async def gpio_get(self, pin: int) -> int:
        """Get GPIO pin value"""
        if not self._gpio:
            self._gpio = await self._init_gpio()
        
        try:
            value = await self._gpio.get(pin)
            logger.info(f"GPIO {pin} read: {value}")
            return value
        except Exception as e:
            logger.error(f"GPIO read error: {e}")
            self.stats['errors'] += 1
            return -1
    
    async def gpio_pwm(self, pin: int, frequency: float, duty_cycle: float) -> bool:
        """Start PWM on GPIO pin"""
        if not self._gpio:
            self._gpio = await self._init_gpio()
        
        try:
            await self._gpio.pwm(pin, frequency, duty_cycle)
            logger.info(f"PWM on {pin}: {frequency}Hz @ {duty_cycle}%")
            return True
        except Exception as e:
            logger.error(f"PWM error: {e}")
            self.stats['errors'] += 1
            return False
    
    async def i2c_scan(self) -> list:
        """Scan I2C bus for devices"""
        if not self._i2c:
            self._i2c = await self._init_i2c()
        
        try:
            devices = await self._i2c.scan()
            logger.info(f"I2C devices found: {[hex(d) for d in devices]}")
            return devices
        except Exception as e:
            logger.error(f"I2C scan error: {e}")
            self.stats['errors'] += 1
            return []
    
    async def i2c_read(self, device: int, register: int, length: int = 1) -> bytes:
        """Read from I2C device"""
        if not self._i2c:
            self._i2c = await self._init_i2c()
        
        try:
            data = await self._i2c.read(device, register, length)
            logger.debug(f"I2C read from {hex(device)}:{hex(register)}: {data.hex()}")
            return data
        except Exception as e:
            logger.error(f"I2C read error: {e}")
            self.stats['errors'] += 1
            return b''
    
    async def i2c_write(self, device: int, register: int, data: bytes) -> bool:
        """Write to I2C device"""
        if not self._i2c:
            self._i2c = await self._init_i2c()
        
        try:
            await self._i2c.write(device, register, data)
            logger.debug(f"I2C write to {hex(device)}:{hex(register)}: {data.hex()}")
            return True
        except Exception as e:
            logger.error(f"I2C write error: {e}")
            self.stats['errors'] += 1
            return False
    
    async def spi_transfer(self, data: bytes, bus: int = 0, device: int = 0) -> bytes:
        """Transfer data via SPI"""
        if not self._spi:
            self._spi = await self._init_spi()
        
        try:
            result = await self._spi.transfer(data, bus, device)
            logger.debug(f"SPI transfer on bus {bus}, device {device}: {data.hex()} -> {result.hex()}")
            return result
        except Exception as e:
            logger.error(f"SPI error: {e}")
            self.stats['errors'] += 1
            return b''
    
    async def uart_write(self, data: bytes, port: str = '/dev/ttyUSB0') -> bool:
        """Write data to UART port"""
        if not self._uart:
            self._uart = await self._init_uart()
        
        try:
            await self._uart.write(port, data)
            logger.debug(f"UART write to {port}: {data.hex()}")
            return True
        except Exception as e:
            logger.error(f"UART write error: {e}")
            self.stats['errors'] += 1
            return False
    
    async def uart_read(self, port: str = '/dev/ttyUSB0', length: int = 1) -> bytes:
        """Read data from UART port"""
        if not self._uart:
            self._uart = await self._init_uart()
        
        try:
            data = await self._uart.read(port, length)
            logger.debug(f"UART read from {port}: {data.hex()}")
            return data
        except Exception as e:
            logger.error(f"UART read error: {e}")
            self.stats['errors'] += 1
            return b''
    
    async def audio_play(self, frequency: float, duration: float) -> bool:
        """Play audio tone"""
        logger.info(f"Playing {frequency}Hz for {duration}s")
        # Simulate or use actual audio library
        await asyncio.sleep(duration)
        return True
    
    async def _init_gpio(self):
        """Initialize GPIO interface with proper async initialization"""
        from .hardware import GPIOInterface, GPIOSimulator
        
        # Try real hardware first
        try:
            interface = GPIOInterface()
            await interface.initialize()
            logger.info("Real GPIO interface initialized")
            return interface
        except (ImportError, Exception) as e:
            logger.warning(f"GPIO hardware not available ({e}), using simulator")
            
        # Fall back to simulator
        try:
            simulator = GPIOSimulator()
            await simulator.initialize()
            logger.info("GPIO simulator initialized")
            return simulator
        except Exception as e:
            logger.error(f"Failed to initialize GPIO simulator: {e}")
            raise
    
    async def _init_i2c(self):
        """Initialize I2C interface with proper async initialization"""
        from .hardware import I2CInterface, I2CSimulator
        
        # Try real hardware first
        try:
            interface = I2CInterface()
            await interface.initialize()
            logger.info("Real I2C interface initialized")
            return interface
        except (ImportError, Exception) as e:
            logger.warning(f"I2C hardware not available ({e}), using simulator")
            
        # Fall back to simulator
        try:
            simulator = I2CSimulator()
            await simulator.initialize()
            logger.info("I2C simulator initialized")
            return simulator
        except Exception as e:
            logger.error(f"Failed to initialize I2C simulator: {e}")
            raise
    
    async def _init_spi(self):
        """Initialize SPI interface with proper async initialization"""
        from .hardware import SPIInterface, SPISimulator
        
        # Try real hardware first
        try:
            interface = SPIInterface()
            await interface.initialize()
            logger.info("Real SPI interface initialized")
            return interface
        except (ImportError, Exception) as e:
            logger.warning(f"SPI hardware not available ({e}), using simulator")
            
        # Fall back to simulator
        try:
            simulator = SPISimulator()
            await simulator.initialize()
            logger.info("SPI simulator initialized")
            return simulator
        except Exception as e:
            logger.error(f"Failed to initialize SPI simulator: {e}")
            raise
    
    async def _init_uart(self):
        """Initialize UART interface with proper async initialization"""
        from .hardware import UARTInterface, UARTSimulator
        
        # Try real hardware first
        try:
            interface = UARTInterface()
            await interface.initialize()
            logger.info("Real UART interface initialized")
            return interface
        except (ImportError, Exception) as e:
            logger.warning(f"UART hardware not available ({e}), using simulator")
            
        # Fall back to simulator
        try:
            simulator = UARTSimulator()
            await simulator.initialize()
            logger.info("UART simulator initialized")
            return simulator
        except Exception as e:
            logger.error(f"Failed to initialize UART simulator: {e}")
            raise
    
    # === Server Mode ===
    
    async def start_server(self):
        """Start EDPM server based on transport type"""
        if self.transport == TransportType.LOCAL:
            await self._start_ipc_server()
        elif self.transport == TransportType.NETWORK:
            await self._start_network_server()
        elif self.transport == TransportType.BROWSER:
            await self._start_websocket_server()
    
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
        ssl_context = self.ssl_context if self.tls_enabled else None
        
        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(
            runner, 
            self.config['host'], 
            self.config['port'],
            ssl_context=ssl_context
        )
        
        await site.start()
        
        protocol = "https" if self.tls_enabled else "http"
        logger.info(f"Server running at {protocol}://{self.config['host']}:{self.config['port']}")
    
    async def _start_ipc_server(self):
        """Start IPC server using Unix domain socket"""
        # Implementation for IPC server
        logger.info(f"IPC server would start at {self.config['ipc_path']}")
        # For now, fall back to network server
        await self._start_network_server()
    
    async def _start_websocket_server(self):
        """Start WebSocket server"""
        # For browser mode, use network server with WebSocket support
        await self._start_network_server()
    
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
            logger.error(f"Request error: {e}")
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
        self.connections[client_id] = ws
        
        logger.info(f"WebSocket client connected: {client_id}")
        
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
            self.connections.pop(client_id, None)
            logger.info(f"WebSocket client disconnected: {client_id}")
        
        return ws
    
    async def _handle_health(self, request):
        """Health check endpoint"""
        from aiohttp import web
        
        return web.json_response({
            'status': 'healthy',
            'name': self.name,
            'transport': self.transport.value,
            'tls': self.tls_enabled,
            'stats': self.stats,
            'uptime': time.time() - self.stats['start_time']
        })
    
    async def _handle_index(self, request):
        """Serve simple web UI"""
        from aiohttp import web
        from .web_ui import get_web_ui
        
        return web.Response(text=get_web_ui(), content_type='text/html')


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
        
        logger.info(f"WebSocket connected to {ws_url}")
    
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
