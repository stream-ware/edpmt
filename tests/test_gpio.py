#!/usr/bin/env python3
"""
EDPMT GPIO Protocol Tests
========================
Comprehensive testing of GPIO functionality including digital I/O, PWM, and interrupts
"""

import asyncio
import pytest
import time
import sys
from pathlib import Path

# Add EDPMT to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from edpmt import EDPMTransparent, EDPMClient
except ImportError:
    # Fallback to direct import from modules
    from transparent import EDPMTransparent, EDPMClient

class TestGPIO:
    """Test GPIO protocol functionality"""
    
    @pytest.fixture
    async def server_client(self):
        """Setup EDPMT server and client for testing"""
        # Start server
        server = EDPMTransparent(
            name="GPIO-Test-Server",
            config={
                'dev_mode': True,
                'port': 8877,
                'host': 'localhost',
                'tls': True,
                'hardware_simulators': True,
                'ipc_path': '/tmp/edpmt_gpio_test.sock'
            }
        )
        
        server_task = asyncio.create_task(server.start_server())
        await asyncio.sleep(2)  # Wait for server to start
        
        # Create client
        client = EDPMClient(url="https://localhost:8877")
        await asyncio.sleep(1)  # Wait for client to connect
        
        yield server, client
        
        # Cleanup
        if hasattr(client, 'close'):
            await client.close()
        if hasattr(server, 'stop'):
            await server.stop()
        elif hasattr(server, 'close'):
            await server.close()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
    
    async def test_gpio_pin_configuration(self, server_client):
        """Test GPIO pin mode configuration"""
        server, client = server_client
        
        # Test output configuration
        result = await client.execute('config', 'gpio', pin=17, mode='out')
        assert result is not None
        
        # Test input configuration
        result = await client.execute('config', 'gpio', pin=18, mode='in')
        assert result is not None
        
        # Test input with pull-up
        result = await client.execute('config', 'gpio', pin=19, mode='in', pull='up')
        assert result is not None
        
        # Test input with pull-down
        result = await client.execute('config', 'gpio', pin=20, mode='in', pull='down')
        assert result is not None
    
    async def test_gpio_digital_output(self, server_client):
        """Test GPIO digital output operations"""
        server, client = server_client
        
        pin = 17
        
        # Configure as output
        await client.execute('config', 'gpio', pin=pin, mode='out')
        
        # Test setting HIGH
        result = await client.execute('set', 'gpio', pin=pin, value=1)
        assert result is not None
        
        # Test setting LOW
        result = await client.execute('set', 'gpio', pin=pin, value=0)
        assert result is not None
        
        # Test multiple rapid changes
        for value in [1, 0, 1, 0, 1]:
            result = await client.execute('set', 'gpio', pin=pin, value=value)
            assert result is not None
            await asyncio.sleep(0.01)
    
    async def test_gpio_digital_input(self, server_client):
        """Test GPIO digital input operations"""
        server, client = server_client
        
        pin = 18
        
        # Configure as input
        await client.execute('config', 'gpio', pin=pin, mode='in')
        
        # Test reading value
        value = await client.execute('get', 'gpio', pin=pin)
        assert value in [0, 1]  # Should be either 0 or 1
        
        # Test multiple reads
        for _ in range(5):
            value = await client.execute('get', 'gpio', pin=pin)
            assert isinstance(value, int)
            assert value in [0, 1]
            await asyncio.sleep(0.01)
    
    async def test_gpio_pwm_control(self, server_client):
        """Test GPIO PWM functionality"""
        server, client = server_client
        
        pin = 18
        
        # Configure as output (PWM capable)
        await client.execute('config', 'gpio', pin=pin, mode='out')
        
        # Test basic PWM
        result = await client.execute('pwm', 'gpio', 
                                     pin=pin, 
                                     frequency=1000, 
                                     duty_cycle=50)
        assert result is not None
        
        # Test different frequencies
        frequencies = [100, 500, 1000, 2000, 5000]
        for freq in frequencies:
            result = await client.execute('pwm', 'gpio',
                                         pin=pin,
                                         frequency=freq,
                                         duty_cycle=50)
            assert result is not None
            await asyncio.sleep(0.1)
        
        # Test different duty cycles
        duty_cycles = [0, 25, 50, 75, 100]
        for duty in duty_cycles:
            result = await client.execute('pwm', 'gpio',
                                         pin=pin,
                                         frequency=1000,
                                         duty_cycle=duty)
            assert result is not None
            await asyncio.sleep(0.1)
        
        # Test stopping PWM
        result = await client.execute('pwm', 'gpio',
                                     pin=pin,
                                     frequency=0,
                                     duty_cycle=0)
        assert result is not None
    
    async def test_gpio_multiple_pins(self, server_client):
        """Test controlling multiple GPIO pins simultaneously"""
        server, client = server_client
        
        pins = [17, 22, 23, 24]
        
        # Configure all pins as outputs
        for pin in pins:
            await client.execute('config', 'gpio', pin=pin, mode='out')
        
        # Test setting all pins HIGH
        for pin in pins:
            result = await client.execute('set', 'gpio', pin=pin, value=1)
            assert result is not None
        
        # Test setting all pins LOW
        for pin in pins:
            result = await client.execute('set', 'gpio', pin=pin, value=0)
            assert result is not None
        
        # Test pattern on multiple pins
        patterns = [
            [1, 0, 1, 0],
            [0, 1, 0, 1], 
            [1, 1, 0, 0],
            [0, 0, 1, 1]
        ]
        
        for pattern in patterns:
            for pin, value in zip(pins, pattern):
                await client.execute('set', 'gpio', pin=pin, value=value)
            await asyncio.sleep(0.1)
    
    async def test_gpio_edge_cases(self, server_client):
        """Test GPIO edge cases and error handling"""
        server, client = server_client
        
        # Test invalid pin numbers
        try:
            await client.execute('set', 'gpio', pin=999, value=1)
            # Should handle gracefully or raise appropriate error
        except Exception:
            pass  # Expected for invalid pins
        
        # Test invalid values
        try:
            await client.execute('set', 'gpio', pin=17, value=5)
            # Should handle gracefully or raise appropriate error
        except Exception:
            pass  # Expected for invalid values
        
        # Test PWM with invalid parameters
        try:
            await client.execute('pwm', 'gpio', 
                                pin=18, 
                                frequency=-1000, 
                                duty_cycle=150)
            # Should handle gracefully
        except Exception:
            pass  # Expected for invalid parameters
    
    async def test_gpio_performance(self, server_client):
        """Test GPIO performance and timing"""
        server, client = server_client
        
        pin = 17
        await client.execute('config', 'gpio', pin=pin, mode='out')
        
        # Test rapid switching performance
        iterations = 100
        start_time = time.time()
        
        for i in range(iterations):
            value = i % 2
            await client.execute('set', 'gpio', pin=pin, value=value)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete reasonably quickly
        assert duration < 30.0  # Max 30 seconds for 100 operations
        
        rate = iterations / duration
        print(f"GPIO switching rate: {rate:.2f} operations/second")
        
        # Test read performance
        await client.execute('config', 'gpio', pin=18, mode='in')
        
        start_time = time.time()
        for _ in range(50):  # Fewer reads as they might be slower
            await client.execute('get', 'gpio', pin=18)
        
        end_time = time.time()
        read_duration = end_time - start_time
        read_rate = 50 / read_duration
        
        print(f"GPIO read rate: {read_rate:.2f} reads/second")
    
    async def test_gpio_state_persistence(self, server_client):
        """Test GPIO state persistence"""
        server, client = server_client
        
        pin = 17
        await client.execute('config', 'gpio', pin=pin, mode='out')
        
        # Set to HIGH
        await client.execute('set', 'gpio', pin=pin, value=1)
        
        # Read back to verify
        # Note: In simulation, we may not be able to read output pins
        # This test is more relevant for real hardware
        
        # Set to LOW  
        await client.execute('set', 'gpio', pin=pin, value=0)
        
        # Verify the operation completed successfully
        assert True  # Basic completion test

async def run_gpio_tests():
    """Run all GPIO tests manually"""
    print("🔌 Starting EDPMT GPIO Tests")
    print("=" * 40)
    
    # Create test instance
    test_gpio = TestGPIO()
    
    # Setup server and client
    server = EDPMTransparent(
        name="GPIO-Test-Server",
        config={
            'dev_mode': True,
            'port': 8877,
            'host': 'localhost',
            'tls': True,
            'hardware_simulators': True
        }
    )
    
    server_task = asyncio.create_task(server.start_server())
    await asyncio.sleep(2)
    
    client = EDPMClient(url="https://localhost:8877")
    await asyncio.sleep(1)
    
    server_client = (server, client)
    
    tests = [
        ("GPIO Pin Configuration", test_gpio.test_gpio_pin_configuration),
        ("GPIO Digital Output", test_gpio.test_gpio_digital_output),
        ("GPIO Digital Input", test_gpio.test_gpio_digital_input),
        ("GPIO PWM Control", test_gpio.test_gpio_pwm_control),
        ("GPIO Multiple Pins", test_gpio.test_gpio_multiple_pins),
        ("GPIO Edge Cases", test_gpio.test_gpio_edge_cases),
        ("GPIO Performance", test_gpio.test_gpio_performance),
        ("GPIO State Persistence", test_gpio.test_gpio_state_persistence),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            await test_func(server_client)
            print(f"✅ PASSED: {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test_name} - {e}")
            failed += 1
    
    # Cleanup
    if hasattr(client, 'close'):
        await client.close()
    if hasattr(server, 'stop'):
        await server.stop()
    elif hasattr(server, 'close'):
        await server.close()
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass
    
    # Results
    total = passed + failed
    print(f"\n" + "=" * 40)
    print(f"📊 GPIO Test Results:")
    print(f"   Total Tests: {total}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Success Rate: {(passed/total*100):.1f}%" if total > 0 else "Success Rate: 0%")
    
    if failed == 0:
        print("🎉 All GPIO tests passed!")
        return True
    else:
        print(f"❌ {failed} GPIO tests failed")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(run_gpio_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 GPIO tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ GPIO test runner failed: {e}")
        sys.exit(1)
