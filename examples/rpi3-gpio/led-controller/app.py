#!/usr/bin/env python3
"""
Raspberry Pi 3 LED Controller Example
Complete project demonstrating EDPMT GPIO control with Docker support

This example shows:
- GPIO LED control (multiple LEDs)
- PWM for LED brightness
- Pattern generation (blink, fade, rainbow)
- Web interface integration
- Docker deployment
- Error handling and logging
"""

import asyncio
import json
import logging
import time
from typing import List, Dict
import signal
import sys
from pathlib import Path

# EDPMT imports
from edpmt import EDPMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('LED_Controller')


class LEDController:
    """Advanced LED controller with patterns and effects"""
    
    def __init__(self, edpm_url: str = "https://localhost:8888"):
        self.client = EDPMClient(edpm_url)
        self.led_pins = [17, 18, 19, 20, 21]  # GPIO pins for LEDs
        self.running = False
        self.current_pattern = None
        self.brightness = 100  # 0-100%
        
        # Pattern definitions
        self.patterns = {
            'blink': self.pattern_blink,
            'fade': self.pattern_fade,
            'chase': self.pattern_chase,
            'rainbow': self.pattern_rainbow,
            'heartbeat': self.pattern_heartbeat,
            'random': self.pattern_random,
        }
        
        logger.info(f"LED Controller initialized with {len(self.led_pins)} LEDs")
    
    async def initialize(self):
        """Initialize LED controller and test connection"""
        try:
            logger.info("Testing EDPMT connection...")
            
            # Test connection
            result = await self.client.execute('get', 'gpio', pin=2)  # Test pin
            logger.info("✅ EDPMT connection successful")
            
            # Initialize all LEDs to OFF
            logger.info("Initializing LEDs...")
            for pin in self.led_pins:
                await self.client.gpio_set(pin, 0)
                logger.info(f"LED on pin {pin} initialized (OFF)")
            
            logger.info("✅ LED Controller ready")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def cleanup(self):
        """Clean up resources and turn off all LEDs"""
        logger.info("🧹 Cleaning up LED Controller...")
        
        try:
            # Turn off all LEDs
            for pin in self.led_pins:
                await self.client.gpio_set(pin, 0)
            
            # Close client connection
            await self.client.close()
            
            logger.info("✅ Cleanup complete")
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")
    
    async def set_led(self, led_index: int, state: bool):
        """Set individual LED state"""
        if 0 <= led_index < len(self.led_pins):
            pin = self.led_pins[led_index]
            await self.client.gpio_set(pin, 1 if state else 0)
    
    async def set_led_brightness(self, led_index: int, brightness: float):
        """Set LED brightness using PWM (0.0 to 1.0)"""
        if 0 <= led_index < len(self.led_pins):
            pin = self.led_pins[led_index]
            duty_cycle = max(0, min(100, brightness * 100))
            await self.client.execute('pwm', 'gpio', 
                                    pin=pin, 
                                    frequency=1000, 
                                    duty_cycle=duty_cycle)
    
    async def set_all_leds(self, states: List[bool]):
        """Set all LEDs at once"""
        tasks = []
        for i, state in enumerate(states[:len(self.led_pins)]):
            tasks.append(self.set_led(i, state))
        
        await asyncio.gather(*tasks)
    
    async def clear_all_leds(self):
        """Turn off all LEDs"""
        await self.set_all_leds([False] * len(self.led_pins))
    
    # Pattern implementations
    async def pattern_blink(self, speed: float = 1.0):
        """Simple blink pattern"""
        while self.running and self.current_pattern == 'blink':
            await self.set_all_leds([True] * len(self.led_pins))
            await asyncio.sleep(0.5 / speed)
            
            await self.clear_all_leds()
            await asyncio.sleep(0.5 / speed)
    
    async def pattern_fade(self, speed: float = 1.0):
        """Fade in/out pattern"""
        while self.running and self.current_pattern == 'fade':
            # Fade in
            for brightness in range(0, 101, 5):
                if not self.running or self.current_pattern != 'fade':
                    break
                
                brightness_val = brightness / 100.0
                tasks = []
                for i in range(len(self.led_pins)):
                    tasks.append(self.set_led_brightness(i, brightness_val))
                
                await asyncio.gather(*tasks)
                await asyncio.sleep(0.05 / speed)
            
            # Fade out
            for brightness in range(100, -1, -5):
                if not self.running or self.current_pattern != 'fade':
                    break
                
                brightness_val = brightness / 100.0
                tasks = []
                for i in range(len(self.led_pins)):
                    tasks.append(self.set_led_brightness(i, brightness_val))
                
                await asyncio.gather(*tasks)
                await asyncio.sleep(0.05 / speed)
    
    async def pattern_chase(self, speed: float = 1.0):
        """Chase/knight rider pattern"""
        while self.running and self.current_pattern == 'chase':
            # Forward chase
            for i in range(len(self.led_pins)):
                if not self.running or self.current_pattern != 'chase':
                    break
                
                await self.clear_all_leds()
                await self.set_led(i, True)
                await asyncio.sleep(0.2 / speed)
            
            # Backward chase
            for i in range(len(self.led_pins) - 2, 0, -1):
                if not self.running or self.current_pattern != 'chase':
                    break
                
                await self.clear_all_leds()
                await self.set_led(i, True)
                await asyncio.sleep(0.2 / speed)
    
    async def pattern_rainbow(self, speed: float = 1.0):
        """Rainbow effect using brightness variations"""
        while self.running and self.current_pattern == 'rainbow':
            for phase in range(0, 360, 10):
                if not self.running or self.current_pattern != 'rainbow':
                    break
                
                tasks = []
                for i, pin in enumerate(self.led_pins):
                    # Create rainbow effect using sine waves
                    import math
                    brightness = (math.sin(math.radians(phase + i * 72)) + 1) / 2
                    tasks.append(self.set_led_brightness(i, brightness))
                
                await asyncio.gather(*tasks)
                await asyncio.sleep(0.05 / speed)
    
    async def pattern_heartbeat(self, speed: float = 1.0):
        """Heartbeat pattern (double pulse)"""
        while self.running and self.current_pattern == 'heartbeat':
            # First pulse
            await self.set_all_leds([True] * len(self.led_pins))
            await asyncio.sleep(0.1 / speed)
            await self.clear_all_leds()
            await asyncio.sleep(0.1 / speed)
            
            # Second pulse
            await self.set_all_leds([True] * len(self.led_pins))
            await asyncio.sleep(0.1 / speed)
            await self.clear_all_leds()
            await asyncio.sleep(0.5 / speed)
    
    async def pattern_random(self, speed: float = 1.0):
        """Random LED activation"""
        import random
        
        while self.running and self.current_pattern == 'random':
            states = [random.choice([True, False]) for _ in self.led_pins]
            await self.set_all_leds(states)
            await asyncio.sleep(0.3 / speed)
    
    async def start_pattern(self, pattern_name: str, speed: float = 1.0):
        """Start a pattern"""
        if pattern_name not in self.patterns:
            logger.error(f"Unknown pattern: {pattern_name}")
            return False
        
        # Stop current pattern
        await self.stop_pattern()
        
        logger.info(f"🌟 Starting pattern: {pattern_name} (speed: {speed}x)")
        self.current_pattern = pattern_name
        self.running = True
        
        # Start pattern in background
        asyncio.create_task(self.patterns[pattern_name](speed))
        
        return True
    
    async def stop_pattern(self):
        """Stop current pattern"""
        if self.current_pattern:
            logger.info(f"⏹️  Stopping pattern: {self.current_pattern}")
            self.current_pattern = None
            self.running = False
            
            # Wait a bit for pattern to stop
            await asyncio.sleep(0.1)
            
            # Clear all LEDs
            await self.clear_all_leds()
    
    async def get_status(self) -> Dict:
        """Get current controller status"""
        return {
            'running': self.running,
            'current_pattern': self.current_pattern,
            'led_count': len(self.led_pins),
            'led_pins': self.led_pins,
            'brightness': self.brightness,
            'available_patterns': list(self.patterns.keys())
        }


class LEDControllerServer:
    """HTTP server for LED controller web interface"""
    
    def __init__(self, controller: LEDController, port: int = 8080):
        self.controller = controller
        self.port = port
        self.app = None
    
    async def start_server(self):
        """Start the web server"""
        from aiohttp import web, web_request
        import aiohttp_cors
        
        app = web.Application()
        
        # Add CORS support
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # API routes
        app.router.add_post('/api/pattern/start', self.start_pattern)
        app.router.add_post('/api/pattern/stop', self.stop_pattern)
        app.router.add_get('/api/status', self.get_status)
        app.router.add_post('/api/led/set', self.set_led)
        app.router.add_post('/api/led/clear', self.clear_leds)
        
        # Static files
        app.router.add_get('/', self.index)
        
        # Add CORS to all routes
        for route in list(app.router.routes()):
            cors.add(route)
        
        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"🌐 LED Controller web interface: http://0.0.0.0:{self.port}")
    
    async def start_pattern(self, request):
        """API: Start LED pattern"""
        from aiohttp import web
        
        try:
            data = await request.json()
            pattern = data.get('pattern', 'blink')
            speed = float(data.get('speed', 1.0))
            
            success = await self.controller.start_pattern(pattern, speed)
            
            return web.json_response({
                'success': success,
                'message': f'Pattern {pattern} started' if success else 'Failed to start pattern'
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=400)
    
    async def stop_pattern(self, request):
        """API: Stop current pattern"""
        from aiohttp import web
        
        await self.controller.stop_pattern()
        return web.json_response({'success': True, 'message': 'Pattern stopped'})
    
    async def get_status(self, request):
        """API: Get controller status"""
        from aiohttp import web
        
        status = await self.controller.get_status()
        return web.json_response(status)
    
    async def set_led(self, request):
        """API: Set individual LED"""
        from aiohttp import web
        
        try:
            data = await request.json()
            led_index = int(data.get('led', 0))
            state = bool(data.get('state', False))
            
            await self.controller.set_led(led_index, state)
            
            return web.json_response({
                'success': True,
                'message': f'LED {led_index} set to {state}'
            })
        except Exception as e:
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=400)
    
    async def clear_leds(self, request):
        """API: Clear all LEDs"""
        from aiohttp import web
        
        await self.controller.clear_all_leds()
        return web.json_response({'success': True, 'message': 'All LEDs cleared'})
    
    async def index(self, request):
        """Serve main HTML page"""
        from aiohttp import web
        
        html = """<!DOCTYPE html>
<html>
<head>
    <title>EDPMT LED Controller</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        h1 { color: #333; text-align: center; }
        .controls { margin: 20px 0; }
        .pattern-buttons { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0; }
        button { padding: 15px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .pattern-btn { background: #4CAF50; color: white; }
        .pattern-btn:hover { background: #45a049; }
        .stop-btn { background: #f44336; color: white; }
        .stop-btn:hover { background: #da190b; }
        .led-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 20px 0; }
        .led { width: 60px; height: 60px; border-radius: 50%; border: 3px solid #333; cursor: pointer; }
        .led.on { background: #ff4444; box-shadow: 0 0 20px #ff4444; }
        .led.off { background: #333; }
        .status { background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .speed-control { margin: 20px 0; }
        input[type="range"] { width: 100%; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚦 EDPMT LED Controller</h1>
        
        <div class="status" id="status">
            <strong>Status:</strong> <span id="status-text">Loading...</span>
        </div>
        
        <div class="controls">
            <h3>🎨 Pattern Control</h3>
            <div class="pattern-buttons">
                <button class="pattern-btn" onclick="startPattern('blink')">💡 Blink</button>
                <button class="pattern-btn" onclick="startPattern('fade')">🌅 Fade</button>
                <button class="pattern-btn" onclick="startPattern('chase')">🏃 Chase</button>
                <button class="pattern-btn" onclick="startPattern('rainbow')">🌈 Rainbow</button>
                <button class="pattern-btn" onclick="startPattern('heartbeat')">💓 Heartbeat</button>
                <button class="pattern-btn" onclick="startPattern('random')">🎲 Random</button>
            </div>
            <button class="stop-btn" onclick="stopPattern()">⏹️ Stop All</button>
            
            <div class="speed-control">
                <label for="speed">Speed: <span id="speed-value">1.0x</span></label>
                <input type="range" id="speed" min="0.1" max="3.0" step="0.1" value="1.0" onchange="updateSpeed()">
            </div>
        </div>
        
        <div class="controls">
            <h3>💡 Individual LED Control</h3>
            <div class="led-grid" id="leds">
                <!-- LEDs will be generated by JavaScript -->
            </div>
            <button onclick="clearAllLEDs()">Clear All</button>
        </div>
    </div>

    <script>
        let currentSpeed = 1.0;
        
        // Initialize LEDs
        function initLEDs() {
            const ledsContainer = document.getElementById('leds');
            for (let i = 0; i < 5; i++) {
                const led = document.createElement('div');
                led.className = 'led off';
                led.title = `LED ${i} (GPIO ${17 + i})`;
                led.onclick = () => toggleLED(i);
                ledsContainer.appendChild(led);
            }
        }
        
        // Update status
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                document.getElementById('status-text').textContent = 
                    status.running ? `Running: ${status.current_pattern}` : 'Idle';
            } catch (e) {
                document.getElementById('status-text').textContent = 'Connection Error';
            }
        }
        
        // Start pattern
        async function startPattern(pattern) {
            try {
                await fetch('/api/pattern/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({pattern: pattern, speed: currentSpeed})
                });
                updateStatus();
            } catch (e) {
                alert('Failed to start pattern');
            }
        }
        
        // Stop pattern
        async function stopPattern() {
            try {
                await fetch('/api/pattern/stop', {method: 'POST'});
                updateStatus();
            } catch (e) {
                alert('Failed to stop pattern');
            }
        }
        
        // Toggle LED
        async function toggleLED(index) {
            const led = document.querySelectorAll('.led')[index];
            const newState = !led.classList.contains('on');
            
            try {
                await fetch('/api/led/set', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({led: index, state: newState})
                });
                
                led.classList.toggle('on', newState);
                led.classList.toggle('off', !newState);
            } catch (e) {
                alert('Failed to toggle LED');
            }
        }
        
        // Clear all LEDs
        async function clearAllLEDs() {
            try {
                await fetch('/api/led/clear', {method: 'POST'});
                document.querySelectorAll('.led').forEach(led => {
                    led.classList.remove('on');
                    led.classList.add('off');
                });
            } catch (e) {
                alert('Failed to clear LEDs');
            }
        }
        
        // Update speed
        function updateSpeed() {
            currentSpeed = parseFloat(document.getElementById('speed').value);
            document.getElementById('speed-value').textContent = currentSpeed.toFixed(1) + 'x';
        }
        
        // Initialize
        initLEDs();
        updateStatus();
        setInterval(updateStatus, 2000);
    </script>
</body>
</html>"""
        
        return web.Response(text=html, content_type='text/html')


async def main():
    """Main application entry point"""
    import os
    
    # Get EDPM server URL from environment
    edpm_url = os.getenv('EDPM_URL', 'https://localhost:8888')
    web_port = int(os.getenv('LED_CONTROLLER_PORT', 8080))
    
    logger.info("🚀 Starting EDPMT LED Controller Example")
    logger.info(f"   EDPM Server: {edmp_url}")
    logger.info(f"   Web Interface: http://0.0.0.0:{web_port}")
    
    # Create controller
    controller = LEDController(edmp_url)
    
    # Initialize
    if not await controller.initialize():
        logger.error("Failed to initialize LED controller")
        return 1
    
    # Create and start web server
    server = LEDControllerServer(controller, web_port)
    await server.start_server()
    
    # Setup graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(controller.cleanup())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("✅ LED Controller ready!")
    logger.info("Press Ctrl+C to stop")
    
    try:
        # Keep running
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await controller.cleanup()
    
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
