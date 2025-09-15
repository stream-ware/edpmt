#!/usr/bin/env python3
"""
EDPMT GPIO Frontend - Interactive GPIO Visualization
===================================================
Flask-based web frontend for real-time GPIO control and monitoring with Raspberry Pi
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import sys
from pathlib import Path

# Add EDPMT to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from edpmt import EDPMClient
except ImportError:
    print("❌ EDPMT package not found. Please install with: pip install -e .")
    sys.exit(1)

class GPIOFrontend:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'edpmt-gpio-frontend-secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # EDPMT client
        self.edpmt_client = None
        self.edpmt_url = "https://localhost:8888"
        
        # GPIO state tracking
        self.gpio_pins = {}
        self.gpio_monitoring = False
        self.monitoring_thread = None
        
        # Setup logging
        self.setup_logging()
        
        # Initialize GPIO pin configuration
        self.init_gpio_pins()
        
        # Setup Flask routes and Socket.IO events
        self.setup_routes()
        self.setup_socketio()
    
    def setup_logging(self):
        """Setup logging for frontend"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "gpio-frontend.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def init_gpio_pins(self):
        """Initialize GPIO pin configuration for Raspberry Pi"""
        # Raspberry Pi GPIO pin mapping (BCM numbering)
        gpio_pin_info = {
            2: {'name': 'GPIO2 (SDA)', 'type': 'i2c', 'mode': 'in', 'value': 0, 'pullup': True},
            3: {'name': 'GPIO3 (SCL)', 'type': 'i2c', 'mode': 'in', 'value': 0, 'pullup': True},
            4: {'name': 'GPIO4', 'type': 'gpio', 'mode': 'in', 'value': 0, 'pullup': False},
            5: {'name': 'GPIO5', 'type': 'gpio', 'mode': 'in', 'value': 0, 'pullup': False},
            6: {'name': 'GPIO6', 'type': 'gpio', 'mode': 'in', 'value': 0, 'pullup': False},
            7: {'name': 'GPIO7 (CE1)', 'type': 'spi', 'mode': 'out', 'value': 1, 'pullup': False},
            8: {'name': 'GPIO8 (CE0)', 'type': 'spi', 'mode': 'out', 'value': 1, 'pullup': False},
            9: {'name': 'GPIO9 (MISO)', 'type': 'spi', 'mode': 'in', 'value': 0, 'pullup': False},
            10: {'name': 'GPIO10 (MOSI)', 'type': 'spi', 'mode': 'out', 'value': 0, 'pullup': False},
            11: {'name': 'GPIO11 (SCLK)', 'type': 'spi', 'mode': 'out', 'value': 0, 'pullup': False},
            12: {'name': 'GPIO12 (PWM0)', 'type': 'pwm', 'mode': 'out', 'value': 0, 'pullup': False, 'pwm': {'freq': 0, 'duty': 0}},
            13: {'name': 'GPIO13 (PWM1)', 'type': 'pwm', 'mode': 'out', 'value': 0, 'pullup': False, 'pwm': {'freq': 0, 'duty': 0}},
            14: {'name': 'GPIO14 (TXD)', 'type': 'uart', 'mode': 'out', 'value': 1, 'pullup': False},
            15: {'name': 'GPIO15 (RXD)', 'type': 'uart', 'mode': 'in', 'value': 1, 'pullup': True},
            16: {'name': 'GPIO16', 'type': 'gpio', 'mode': 'in', 'value': 0, 'pullup': False},
            17: {'name': 'GPIO17', 'type': 'gpio', 'mode': 'out', 'value': 0, 'pullup': False},
            18: {'name': 'GPIO18 (PWM)', 'type': 'pwm', 'mode': 'out', 'value': 0, 'pullup': False, 'pwm': {'freq': 0, 'duty': 0}},
            19: {'name': 'GPIO19', 'type': 'gpio', 'mode': 'in', 'value': 0, 'pullup': False},
            20: {'name': 'GPIO20', 'type': 'gpio', 'mode': 'in', 'value': 0, 'pullup': False},
            21: {'name': 'GPIO21', 'type': 'gpio', 'mode': 'in', 'value': 0, 'pullup': False},
            22: {'name': 'GPIO22', 'type': 'gpio', 'mode': 'in', 'value': 0, 'pullup': False},
            23: {'name': 'GPIO23', 'type': 'gpio', 'mode': 'out', 'value': 0, 'pullup': False},
            24: {'name': 'GPIO24', 'type': 'gpio', 'mode': 'out', 'value': 0, 'pullup': False},
            25: {'name': 'GPIO25', 'type': 'gpio', 'mode': 'in', 'value': 0, 'pullup': False},
            26: {'name': 'GPIO26', 'type': 'gpio', 'mode': 'in', 'value': 0, 'pullup': False},
            27: {'name': 'GPIO27', 'type': 'gpio', 'mode': 'in', 'value': 0, 'pullup': False}
        }
        
        for pin, info in gpio_pin_info.items():
            self.gpio_pins[pin] = {
                **info,
                'last_change': datetime.now().isoformat(),
                'interrupt_enabled': False,
                'change_count': 0
            }
    
    async def connect_edpmt(self):
        """Connect to EDPMT server"""
        try:
            if self.edpmt_client:
                await self.edpmt_client.close()
            
            self.edpmt_client = EDPMClient(url=self.edpmt_url)
            self.logger.info(f"✅ Connected to EDPMT server at {self.edpmt_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to EDPMT server: {e}")
            return False
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('gpio_dashboard.html')
        
        @self.app.route('/health')
        def health():
            return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})
        
        @self.app.route('/api/gpio/pins')
        def get_gpio_pins():
            """Get all GPIO pin states"""
            return jsonify(self.gpio_pins)
        
        @self.app.route('/api/gpio/pin/<int:pin>', methods=['GET', 'POST'])
        def gpio_pin_control(pin):
            """Control individual GPIO pin"""
            if request.method == 'GET':
                if pin in self.gpio_pins:
                    return jsonify(self.gpio_pins[pin])
                else:
                    return jsonify({'error': 'Pin not found'}), 404
            
            elif request.method == 'POST':
                if pin not in self.gpio_pins:
                    return jsonify({'error': 'Pin not found'}), 404
                
                data = request.json
                return asyncio.run(self._handle_gpio_control(pin, data))
        
        @self.app.route('/api/gpio/monitor', methods=['POST'])
        def toggle_monitoring():
            """Toggle GPIO monitoring"""
            data = request.json
            enable = data.get('enable', False)
            
            if enable and not self.gpio_monitoring:
                self.start_gpio_monitoring()
            elif not enable and self.gpio_monitoring:
                self.stop_gpio_monitoring()
            
            return jsonify({
                'monitoring': self.gpio_monitoring,
                'message': f'GPIO monitoring {"enabled" if self.gpio_monitoring else "disabled"}'
            })
    
    async def _handle_gpio_control(self, pin, data):
        """Handle GPIO pin control request"""
        try:
            if not self.edpmt_client:
                if not await self.connect_edpmt():
                    return jsonify({'error': 'EDPMT connection failed'}), 503
            
            action = data.get('action')
            pin_info = self.gpio_pins[pin]
            
            if action == 'set_mode':
                # Set pin mode (input/output)
                mode = data.get('mode', 'in')
                pull = data.get('pull', 'none')
                
                pull_param = None
                if pull == 'up':
                    pull_param = 'up'
                elif pull == 'down':
                    pull_param = 'down'
                
                config_params = {'pin': pin, 'mode': mode}
                if pull_param:
                    config_params['pull'] = pull_param
                
                await self.edpmt_client.execute('config', 'gpio', **config_params)
                
                pin_info['mode'] = mode
                pin_info['pullup'] = (pull == 'up')
                pin_info['last_change'] = datetime.now().isoformat()
                
                # Emit update to all connected clients
                self.socketio.emit('gpio_update', {'pin': pin, 'data': pin_info})
                
                return jsonify({'success': True, 'pin': pin, 'mode': mode, 'pull': pull})
            
            elif action == 'set_value':
                # Set pin value (for output pins)
                if pin_info['mode'] != 'out':
                    return jsonify({'error': 'Pin is not configured as output'}), 400
                
                value = data.get('value', 0)
                await self.edpmt_client.execute('set', 'gpio', pin=pin, value=value)
                
                pin_info['value'] = value
                pin_info['last_change'] = datetime.now().isoformat()
                
                self.socketio.emit('gpio_update', {'pin': pin, 'data': pin_info})
                
                return jsonify({'success': True, 'pin': pin, 'value': value})
            
            elif action == 'get_value':
                # Read pin value
                value = await self.edpmt_client.execute('get', 'gpio', pin=pin)
                
                pin_info['value'] = value
                pin_info['last_change'] = datetime.now().isoformat()
                
                self.socketio.emit('gpio_update', {'pin': pin, 'data': pin_info})
                
                return jsonify({'success': True, 'pin': pin, 'value': value})
            
            elif action == 'set_pwm':
                # Set PWM parameters
                frequency = data.get('frequency', 1000)
                duty_cycle = data.get('duty_cycle', 50)
                
                await self.edpmt_client.execute('pwm', 'gpio', 
                                              pin=pin, 
                                              frequency=frequency, 
                                              duty_cycle=duty_cycle)
                
                if 'pwm' not in pin_info:
                    pin_info['pwm'] = {}
                pin_info['pwm']['freq'] = frequency
                pin_info['pwm']['duty'] = duty_cycle
                pin_info['last_change'] = datetime.now().isoformat()
                
                self.socketio.emit('gpio_update', {'pin': pin, 'data': pin_info})
                
                return jsonify({'success': True, 'pin': pin, 'frequency': frequency, 'duty_cycle': duty_cycle})
            
            elif action == 'toggle_interrupt':
                # Toggle interrupt monitoring for pin
                enable = data.get('enable', False)
                pin_info['interrupt_enabled'] = enable
                pin_info['last_change'] = datetime.now().isoformat()
                
                self.socketio.emit('gpio_update', {'pin': pin, 'data': pin_info})
                
                return jsonify({'success': True, 'pin': pin, 'interrupt_enabled': enable})
            
            else:
                return jsonify({'error': 'Unknown action'}), 400
                
        except Exception as e:
            self.logger.error(f"GPIO control error for pin {pin}: {e}")
            return jsonify({'error': str(e)}), 500
    
    def setup_socketio(self):
        """Setup Socket.IO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            self.logger.info(f"Client connected: {request.sid}")
            emit('gpio_pins', self.gpio_pins)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.logger.info(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('request_gpio_update')
        def handle_gpio_update():
            """Send current GPIO state to client"""
            emit('gpio_pins', self.gpio_pins)
        
        @self.socketio.on('gpio_control')
        def handle_gpio_control(data):
            """Handle GPIO control from WebSocket"""
            pin = data.get('pin')
            if pin and pin in self.gpio_pins:
                result = asyncio.run(self._handle_gpio_control(pin, data))
                emit('gpio_control_result', result)
    
    def start_gpio_monitoring(self):
        """Start GPIO monitoring thread"""
        if not self.gpio_monitoring:
            self.gpio_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("🔍 GPIO monitoring started")
    
    def stop_gpio_monitoring(self):
        """Stop GPIO monitoring"""
        self.gpio_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        self.logger.info("🛑 GPIO monitoring stopped")
    
    def _monitoring_loop(self):
        """GPIO monitoring loop - runs in separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._async_monitoring_loop())
        except Exception as e:
            self.logger.error(f"Monitoring loop error: {e}")
        finally:
            loop.close()
    
    async def _async_monitoring_loop(self):
        """Async GPIO monitoring loop"""
        if not self.edpmt_client:
            await self.connect_edpmt()
        
        while self.gpio_monitoring:
            try:
                # Check input pins for changes
                for pin, pin_info in self.gpio_pins.items():
                    if pin_info['mode'] == 'in' and pin_info['interrupt_enabled']:
                        try:
                            # Read current value
                            current_value = await self.edpmt_client.execute('get', 'gpio', pin=pin)
                            
                            # Check if value changed
                            if current_value != pin_info['value']:
                                old_value = pin_info['value']
                                pin_info['value'] = current_value
                                pin_info['last_change'] = datetime.now().isoformat()
                                pin_info['change_count'] += 1
                                
                                # Emit interrupt event
                                self.socketio.emit('gpio_interrupt', {
                                    'pin': pin,
                                    'old_value': old_value,
                                    'new_value': current_value,
                                    'timestamp': pin_info['last_change'],
                                    'change_count': pin_info['change_count']
                                })
                                
                                # Emit pin update
                                self.socketio.emit('gpio_update', {'pin': pin, 'data': pin_info})
                                
                                self.logger.info(f"🔔 GPIO{pin} interrupt: {old_value} → {current_value}")
                        
                        except Exception as e:
                            self.logger.warning(f"Error reading GPIO{pin}: {e}")
                
                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(1)
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the Flask application"""
        self.logger.info(f"🚀 Starting GPIO Frontend on {host}:{port}")
        self.logger.info(f"🌐 GPIO Dashboard: http://{host}:{port}")
        
        # Start GPIO monitoring by default
        self.start_gpio_monitoring()
        
        try:
            self.socketio.run(self.app, host=host, port=port, debug=debug)
        except KeyboardInterrupt:
            self.logger.info("👋 Shutting down GPIO Frontend...")
            self.stop_gpio_monitoring()
            if self.edpmt_client:
                asyncio.run(self.edpmt_client.close())

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='EDPMT GPIO Frontend')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--edpmt-url', default='https://localhost:8888', help='EDPMT server URL')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create and run frontend
    frontend = GPIOFrontend()
    frontend.edpmt_url = args.edpmt_url
    
    frontend.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()
