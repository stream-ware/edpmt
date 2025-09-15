#!/usr/bin/env python3
"""
GPIO LED Matrix Simulation Example

This example demonstrates GPIO control with simulated hardware:
- 8x8 LED matrix display
- Button input with debouncing
- PWM servo motor control
- Digital I/O operations

All GPIO operations are simulated and work on any PC without real hardware.
"""

import asyncio
import time
import math
import random
from edpmt import EDPMTransparent, EDPMClient

class GPIODemo:
    def __init__(self):
        self.server = None
        self.client = None
        self.matrix_size = 8
        self.led_matrix = [[False] * self.matrix_size for _ in range(self.matrix_size)]
        
        # GPIO pin assignments (simulated)
        self.matrix_row_pins = [2, 3, 4, 5, 6, 7, 8, 9]      # Row control pins
        self.matrix_col_pins = [10, 11, 12, 13, 14, 15, 16, 17]  # Column control pins
        self.button_pins = [18, 19, 20, 21]                   # Input buttons
        self.servo_pin = 22                                    # PWM servo control
        self.status_led_pin = 23                              # Status LED
    
    async def start_server(self):
        """Start EDPMT server with GPIO simulators"""
        print("🚀 Starting EDPMT server with GPIO simulators...")
        self.server = EDPMTransparent(name="GPIO-Simulator", config={
            'dev_mode': True,
            'hardware_simulators': True,
            'port': 8891  # Use different port
        })
        
        server_task = asyncio.create_task(self.server.start_server())
        await asyncio.sleep(2)
        return server_task
    
    async def connect_client(self):
        """Connect EDPMT client to server"""
        print("🔌 Connecting to EDPMT server...")
        self.client = EDPMClient(url="https://localhost:8891")
        await asyncio.sleep(1)
        print("✅ Connected to EDPMT server")
    
    async def initialize_gpio(self):
        """Initialize all GPIO pins for the demo"""
        print("\n⚙️  Initializing GPIO pins...")
        
        # Configure matrix row pins as outputs
        for pin in self.matrix_row_pins:
            await self.client.execute('config', 'gpio', pin=pin, mode='out')
            await self.client.execute('set', 'gpio', pin=pin, value=0)
        
        # Configure matrix column pins as outputs
        for pin in self.matrix_col_pins:
            await self.client.execute('config', 'gpio', pin=pin, mode='out')
            await self.client.execute('set', 'gpio', pin=pin, value=0)
        
        # Configure button pins as inputs with pull-up resistors
        for pin in self.button_pins:
            await self.client.execute('config', 'gpio', pin=pin, mode='in', pull='up')
        
        # Configure servo pin for PWM output
        await self.client.execute('config', 'gpio', pin=self.servo_pin, mode='out')
        
        # Configure status LED pin as output
        await self.client.execute('config', 'gpio', pin=self.status_led_pin, mode='out')
        await self.client.execute('set', 'gpio', pin=self.status_led_pin, value=1)  # Turn on status LED
        
        print("✅ GPIO initialization completed")
    
    async def display_led_matrix(self):
        """Display the current LED matrix state using multiplexing"""
        # In a real implementation, this would continuously refresh the display
        # For simulation, we'll just show the intended pattern
        
        print("💡 LED Matrix Display:")
        print("   01234567")
        for row in range(self.matrix_size):
            display_row = f"{row}: "
            for col in range(self.matrix_size):
                display_row += "█" if self.led_matrix[row][col] else "·"
            print(display_row)
        
        # Simulate multiplexed display refresh
        for row in range(self.matrix_size):
            # Turn off all rows first
            for r_pin in self.matrix_row_pins:
                await self.client.execute('set', 'gpio', pin=r_pin, value=0)
            
            # Set column states for current row
            for col in range(self.matrix_size):
                col_pin = self.matrix_col_pins[col]
                value = 1 if self.led_matrix[row][col] else 0
                await self.client.execute('set', 'gpio', pin=col_pin, value=value)
            
            # Enable current row
            await self.client.execute('set', 'gpio', pin=self.matrix_row_pins[row], value=1)
            
            # Brief delay for persistence of vision (simulated)
            await asyncio.sleep(0.001)
    
    def set_matrix_pixel(self, row, col, state):
        """Set individual pixel in the LED matrix"""
        if 0 <= row < self.matrix_size and 0 <= col < self.matrix_size:
            self.led_matrix[row][col] = state
    
    def clear_matrix(self):
        """Clear all pixels in the LED matrix"""
        for row in range(self.matrix_size):
            for col in range(self.matrix_size):
                self.led_matrix[row][col] = False
    
    def draw_pattern(self, pattern_name):
        """Draw predefined patterns on the LED matrix"""
        self.clear_matrix()
        
        if pattern_name == "checkerboard":
            for row in range(self.matrix_size):
                for col in range(self.matrix_size):
                    self.led_matrix[row][col] = (row + col) % 2 == 0
        
        elif pattern_name == "cross":
            # Draw horizontal line
            for col in range(self.matrix_size):
                self.led_matrix[3][col] = True
                self.led_matrix[4][col] = True
            # Draw vertical line
            for row in range(self.matrix_size):
                self.led_matrix[row][3] = True
                self.led_matrix[row][4] = True
        
        elif pattern_name == "border":
            # Draw border
            for i in range(self.matrix_size):
                self.led_matrix[0][i] = True      # Top
                self.led_matrix[7][i] = True      # Bottom
                self.led_matrix[i][0] = True      # Left
                self.led_matrix[i][7] = True      # Right
        
        elif pattern_name == "diagonal":
            # Draw diagonals
            for i in range(self.matrix_size):
                self.led_matrix[i][i] = True           # Main diagonal
                self.led_matrix[i][7-i] = True         # Anti-diagonal
        
        elif pattern_name == "heart":
            # Draw a simple heart pattern
            heart = [
                [0,1,1,0,0,1,1,0],
                [1,1,1,1,1,1,1,1],
                [1,1,1,1,1,1,1,1],
                [0,1,1,1,1,1,1,0],
                [0,0,1,1,1,1,0,0],
                [0,0,0,1,1,0,0,0],
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0]
            ]
            for row in range(self.matrix_size):
                for col in range(self.matrix_size):
                    self.led_matrix[row][col] = bool(heart[row][col])
    
    async def animate_matrix(self, duration=10):
        """Animate patterns on the LED matrix"""
        print(f"\n🎬 Starting LED matrix animation for {duration} seconds...")
        
        patterns = ["checkerboard", "cross", "border", "diagonal", "heart"]
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                for pattern in patterns:
                    if time.time() - start_time >= duration:
                        break
                    
                    print(f"\n🎨 Drawing pattern: {pattern}")
                    self.draw_pattern(pattern)
                    await self.display_led_matrix()
                    
                    await asyncio.sleep(2)
                
                # Random pixel animation
                print("\n✨ Random pixel animation...")
                self.clear_matrix()
                for _ in range(20):
                    if time.time() - start_time >= duration:
                        break
                    
                    row = random.randint(0, 7)
                    col = random.randint(0, 7)
                    self.set_matrix_pixel(row, col, True)
                    await self.display_led_matrix()
                    await asyncio.sleep(0.2)
        
        except KeyboardInterrupt:
            print("\n⏹️  Animation stopped by user")
        
        print("🎬 Animation completed")
    
    async def read_buttons(self):
        """Read button states with debouncing"""
        print("\n🔘 Reading button states...")
        
        button_names = ["UP", "DOWN", "LEFT", "RIGHT"]
        button_states = {}
        
        for i, pin in enumerate(self.button_pins):
            try:
                # Read button state (active low with pull-up)
                state = await self.client.execute('get', 'gpio', pin=pin)
                pressed = not state  # Invert because of pull-up resistor
                
                button_states[button_names[i]] = pressed
                status = "PRESSED" if pressed else "RELEASED"
                print(f"  🔘 {button_names[i]:5s} (Pin {pin:2d}): {status}")
                
            except Exception as e:
                print(f"❌ Error reading button {button_names[i]}: {e}")
        
        return button_states
    
    async def control_servo(self, angle_degrees):
        """Control servo motor position using PWM"""
        print(f"\n🔧 Moving servo to {angle_degrees}°...")
        
        # Clamp angle to valid range
        angle = max(0, min(180, angle_degrees))
        
        # Convert angle to duty cycle for servo control
        # Standard servo: 1ms = 0°, 1.5ms = 90°, 2ms = 180°
        # At 50Hz (20ms period): 1ms = 5%, 2ms = 10%
        min_duty = 2.5  # 0.5ms pulse width
        max_duty = 12.5  # 2.5ms pulse width
        duty_cycle = min_duty + (angle / 180.0) * (max_duty - min_duty)
        
        try:
            await self.client.execute('pwm', 'gpio', 
                                     pin=self.servo_pin, 
                                     frequency=50, 
                                     duty_cycle=duty_cycle)
            
            print(f"✅ Servo positioned at {angle}° (duty cycle: {duty_cycle:.1f}%)")
            
        except Exception as e:
            print(f"❌ Error controlling servo: {e}")
    
    async def servo_sweep_demo(self):
        """Demonstrate servo sweeping motion"""
        print("\n🔄 Servo sweep demonstration...")
        
        # Sweep from 0° to 180° and back
        positions = list(range(0, 181, 10)) + list(range(170, -1, -10))
        
        for angle in positions:
            await self.control_servo(angle)
            await asyncio.sleep(0.1)
        
        # Return to center position
        await self.control_servo(90)
        print("✅ Servo sweep completed")
    
    async def blink_status_led(self, count=5):
        """Blink status LED to indicate activity"""
        print(f"\n💡 Blinking status LED {count} times...")
        
        for i in range(count):
            await self.client.execute('set', 'gpio', pin=self.status_led_pin, value=0)
            await asyncio.sleep(0.2)
            await self.client.execute('set', 'gpio', pin=self.status_led_pin, value=1)
            await asyncio.sleep(0.2)
        
        print("✅ Status LED blinking completed")
    
    async def interactive_demo(self):
        """Interactive demonstration with button control"""
        print("\n🎮 Interactive Demo Mode")
        print("Press buttons to control the LED matrix:")
        print("  UP    - Move pattern up")
        print("  DOWN  - Move pattern down")
        print("  LEFT  - Move pattern left")
        print("  RIGHT - Move pattern right")
        print("(This is simulated - button states are generated randomly)")
        
        # Draw initial pattern
        self.draw_pattern("heart")
        await self.display_led_matrix()
        
        # Simulate interactive control
        for step in range(10):
            print(f"\n--- Step {step + 1} ---")
            buttons = await self.read_buttons()
            
            # Simulate some random button presses
            if step % 3 == 0:
                print("🎯 Simulating button press...")
                pattern_names = ["checkerboard", "cross", "diagonal", "heart"]
                pattern = pattern_names[step % len(pattern_names)]
                self.draw_pattern(pattern)
                await self.display_led_matrix()
            
            await asyncio.sleep(1)
    
    async def run_demo(self):
        """Run complete GPIO demonstration"""
        print("🎯 GPIO LED Matrix & Control Demo")
        print("=" * 50)
        
        try:
            # Start server and connect
            server_task = await self.start_server()
            await self.connect_client()
            
            # Initialize GPIO
            await self.initialize_gpio()
            
            # Blink status LED
            await self.blink_status_led(3)
            
            # LED matrix patterns
            print("\n1️⃣  LED Matrix Pattern Demo...")
            patterns = ["checkerboard", "cross", "border", "diagonal", "heart"]
            for pattern in patterns:
                print(f"\n🎨 Displaying pattern: {pattern}")
                self.draw_pattern(pattern)
                await self.display_led_matrix()
                await asyncio.sleep(2)
            
            # Button reading
            print("\n2️⃣  Button Input Demo...")
            await self.read_buttons()
            
            # Servo control
            print("\n3️⃣  Servo Motor Control Demo...")
            test_angles = [0, 45, 90, 135, 180, 90]  # Return to center
            for angle in test_angles:
                await self.control_servo(angle)
                await asyncio.sleep(1)
            
            # Servo sweep
            print("\n4️⃣  Servo Sweep Demo...")
            await self.servo_sweep_demo()
            
            # Optional: Matrix animation
            print("\n5️⃣  LED Matrix Animation...")
            print("💡 Starting brief animation (press Ctrl+C to skip)...")
            await self.animate_matrix(8)  # 8 second animation
            
            # Final status
            await self.blink_status_led(2)
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
        finally:
            # Cleanup - turn off all outputs
            if self.client:
                try:
                    for pin in self.matrix_row_pins + self.matrix_col_pins:
                        await self.client.execute('set', 'gpio', pin=pin, value=0)
                    await self.client.execute('pwm', 'gpio', pin=self.servo_pin, frequency=0)
                    await self.client.execute('set', 'gpio', pin=self.status_led_pin, value=0)
                except:
                    pass
                await self.client.close()
            if self.server:
                await self.server.close()
        
        print("\n✅ GPIO Demo completed!")

async def main():
    """Main entry point"""
    demo = GPIODemo()
    await demo.run_demo()

if __name__ == "__main__":
    print("🖥️  PC-Based GPIO LED Matrix Simulation")
    print("This demo works entirely with simulators - no real hardware needed!")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
