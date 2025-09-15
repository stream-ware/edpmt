#!/usr/bin/env python3
"""
EDPMT End-to-End Tests with Python
==================================
Comprehensive E2E testing of EDPMT server functionality using Python/aiohttp
"""

import asyncio
import aiohttp
import json
import time
import logging
import subprocess
import signal
import os
import sys
from datetime import datetime
from pathlib import Path

# Add EDPMT to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from edpmt import EDPMTransparent, EDPMClient
except ImportError:
    print("❌ EDPMT package not found. Please install with: pip install -e .")
    sys.exit(1)

class EDPMTEndToEndTests:
    def __init__(self):
        self.server = None
        self.server_process = None
        self.base_url = "https://localhost:8890"  # Use a different port for tests
        self.http_url = "http://localhost:8890"
        self.test_results = []
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for tests"""
        log_dir = Path("test-results")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"e2e_python_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.log_file = log_file
    
    async def start_test_server(self):
        """Start EDPMT server for testing"""
        self.logger.info("🚀 Starting EDPMT test server...")
        
        try:
            # Start server with development configuration
            self.server = EDPMTransparent(
                name="EDPMT-E2E-Test",
                config={
                    'dev_mode': True,
                    'port': 8890,
                    'host': 'localhost',
                    'tls': False,  # Disable TLS for testing to avoid certificate issues
                    'hardware_simulators': True
                }
            )
            
            # Start server in background task
            self.server_task = asyncio.create_task(self.server.start_server())
            
            # Wait for server to be ready
            await self.wait_for_server()
            
            self.logger.info("✅ Test server started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start test server: {e}")
            return False
    
    async def wait_for_server(self, timeout=60):
        """Wait for server to be ready"""
        self.logger.info(f"⏳ Waiting for server at {self.http_url}...")
        
        for attempt in range(timeout):
            try:
                self.logger.info(f"Attempt {attempt+1}/{timeout}: Checking server health...")
                async with aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(ssl=False)
                ) as session:
                    async with session.get(f"{self.http_url}/health") as response:
                        if response.status == 200:
                            self.logger.info("✅ Server is responding")
                            return True
                        else:
                            self.logger.info(f"Server responded with status {response.status}")
            except Exception as e:
                self.logger.info(f"Attempt {attempt+1}/{timeout}: Connection failed - {str(e)}")
            
            await asyncio.sleep(1)
        
        self.logger.error(f"❌ Server did not start within {timeout} seconds")
        raise TimeoutError(f"Server did not start within {timeout} seconds")
    
    async def cleanup(self):
        """Cleanup test server"""
        if self.server:
            self.logger.info("🛑 Stopping test server...")
            try:
                await self.server.close()
                self.server_task.cancel()
                await asyncio.sleep(1)
                self.logger.info("✅ Server stopped")
            except Exception as e:
                self.logger.warning(f"⚠️  Error stopping server: {e}")
    
    def record_test(self, name, passed, error=None, duration=None):
        """Record test result"""
        result = {
            'name': name,
            'passed': passed,
            'error': str(error) if error else None,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        duration_str = f" ({duration:.3f}s)" if duration else ""
        self.logger.info(f"{status}: {name}{duration_str}")
        
        if error:
            self.logger.error(f"  Error: {error}")
    
    async def run_test(self, test_name, test_func):
        """Run individual test with error handling"""
        start_time = time.time()
        
        try:
            await test_func()
            duration = time.time() - start_time
            self.record_test(test_name, True, duration=duration)
            return True
        except Exception as e:
            duration = time.time() - start_time
            self.record_test(test_name, False, error=e, duration=duration)
            return False
    
    # ==============================================================================
    # BASIC CONNECTIVITY TESTS
    # ==============================================================================
    
    async def test_health_check(self):
        """Test server health endpoint"""
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.get(f"{self.base_url}/health") as response:
                assert response.status == 200
                data = await response.json()
                assert data.get('status') == 'ok'
    
    async def test_server_info(self):
        """Test server info endpoint"""
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.get(f"{self.base_url}/info") as response:
                assert response.status == 200
                data = await response.json()
                assert 'name' in data
                assert 'version' in data
    
    async def test_web_ui_access(self):
        """Test web UI accessibility"""
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.get(f"{self.base_url}/") as response:
                assert response.status == 200
                content = await response.text()
                assert 'html' in content.lower()
    
    # ==============================================================================
    # GPIO API TESTS
    # ==============================================================================
    
    async def test_gpio_digital_output(self):
        """Test GPIO digital output control"""
        payload = {
            "action": "set",
            "target": "gpio",
            "params": {"pin": 17, "value": 1}
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.post(
                f"{self.base_url}/api/execute",
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data.get('success') is True
    
    async def test_gpio_digital_input(self):
        """Test GPIO digital input reading"""
        payload = {
            "action": "get",
            "target": "gpio",
            "params": {"pin": 18}
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.post(
                f"{self.base_url}/api/execute",
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data.get('success') is True
                assert 'data' in data
    
    async def test_gpio_pwm_control(self):
        """Test GPIO PWM control"""
        payload = {
            "action": "pwm",
            "target": "gpio", 
            "params": {"pin": 18, "frequency": 1000, "duty_cycle": 50}
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.post(
                f"{self.base_url}/api/execute",
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data.get('success') is True
    
    async def test_gpio_pin_configuration(self):
        """Test GPIO pin configuration"""
        payload = {
            "action": "config",
            "target": "gpio",
            "params": {"pin": 19, "mode": "out"}
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.post(
                f"{self.base_url}/api/execute", 
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data.get('success') is True
    
    # ==============================================================================
    # I2C API TESTS
    # ==============================================================================
    
    async def test_i2c_scan(self):
        """Test I2C bus scanning"""
        payload = {
            "action": "scan",
            "target": "i2c"
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.post(
                f"{self.base_url}/api/execute",
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data.get('success') is True
                assert 'data' in data
                assert isinstance(data['data'], list)
    
    async def test_i2c_read_device(self):
        """Test I2C device reading"""
        payload = {
            "action": "read",
            "target": "i2c",
            "params": {"device": 0x76, "register": 0xD0, "length": 1}
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.post(
                f"{self.base_url}/api/execute",
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data.get('success') is True
    
    async def test_i2c_write_device(self):
        """Test I2C device writing"""
        payload = {
            "action": "write",
            "target": "i2c", 
            "params": {"device": 0x76, "register": 0xF4, "data": [0x27]}
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.post(
                f"{self.base_url}/api/execute",
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data.get('success') is True
    
    # ==============================================================================
    # SPI API TESTS
    # ==============================================================================
    
    async def test_spi_transfer(self):
        """Test SPI data transfer"""
        payload = {
            "action": "transfer",
            "target": "spi",
            "params": {"data": [0x01, 0x02, 0x03, 0x04]}
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.post(
                f"{self.base_url}/api/execute",
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data.get('success') is True
                assert 'data' in data
    
    async def test_spi_configuration(self):
        """Test SPI interface configuration"""
        payload = {
            "action": "config",
            "target": "spi",
            "params": {"bus": 0, "device": 0, "speed": 1000000, "mode": 0}
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.post(
                f"{self.base_url}/api/execute",
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data.get('success') is True
    
    # ==============================================================================
    # UART API TESTS
    # ==============================================================================
    
    async def test_uart_write(self):
        """Test UART data writing"""
        payload = {
            "action": "write",
            "target": "uart",
            "params": {"data": "Hello UART"}
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.post(
                f"{self.base_url}/api/execute",
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data.get('success') is True
    
    async def test_uart_read(self):
        """Test UART data reading"""
        payload = {
            "action": "read",
            "target": "uart",
            "params": {"timeout": 1.0}
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.post(
                f"{self.base_url}/api/execute",
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data.get('success') is True
    
    # ==============================================================================
    # ERROR HANDLING TESTS
    # ==============================================================================
    
    async def test_invalid_action(self):
        """Test handling of invalid actions"""
        payload = {
            "action": "invalid_action",
            "target": "gpio"
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.post(
                f"{self.base_url}/api/execute",
                json=payload
            ) as response:
                # Should return error but not crash
                data = await response.json()
                assert data.get('success') is False
                assert 'error' in data
    
    async def test_invalid_target(self):
        """Test handling of invalid targets"""
        payload = {
            "action": "set",
            "target": "invalid_target"
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.post(
                f"{self.base_url}/api/execute",
                json=payload
            ) as response:
                data = await response.json()
                assert data.get('success') is False
                assert 'error' in data
    
    async def test_malformed_request(self):
        """Test handling of malformed requests"""
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            # Send invalid JSON
            async with session.post(
                f"{self.base_url}/api/execute",
                data="invalid json"
            ) as response:
                assert response.status == 400
    
    # ==============================================================================
    # PERFORMANCE TESTS
    # ==============================================================================
    
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        payload = {
            "action": "get",
            "target": "gpio", 
            "params": {"pin": 18}
        }
        
        async def make_request(session):
            async with session.post(
                f"{self.base_url}/api/execute",
                json=payload
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert data.get('success') is True
                return True
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            # Send 10 concurrent requests
            tasks = [make_request(session) for _ in range(10)]
            results = await asyncio.gather(*tasks)
            assert all(results)
    
    async def test_rapid_requests(self):
        """Test rapid sequential requests"""
        payload = {
            "action": "get",
            "target": "gpio",
            "params": {"pin": 18}
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            start_time = time.time()
            
            for _ in range(20):
                async with session.post(
                    f"{self.base_url}/api/execute",
                    json=payload
                ) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert data.get('success') is True
            
            duration = time.time() - start_time
            self.logger.info(f"20 rapid requests completed in {duration:.3f}s")
    
    # ==============================================================================
    # CLIENT API TESTS
    # ==============================================================================
    
    async def test_edpmt_client(self):
        """Test EDPMT client functionality"""
        client = EDPMClient(url=self.base_url)
        
        try:
            # Test GPIO operations
            await client.execute('set', 'gpio', pin=17, value=1)
            await client.execute('set', 'gpio', pin=17, value=0)
            
            # Test I2C operations
            devices = await client.execute('scan', 'i2c')
            assert isinstance(devices, list)
            
            # Test SPI operations
            result = await client.execute('transfer', 'spi', data=[1, 2, 3])
            assert result is not None
            
        finally:
            await client.close()
    
    # ==============================================================================
    # MAIN TEST RUNNER
    # ==============================================================================
    
    async def run_all_tests(self):
        """Run all E2E tests"""
        self.logger.info("🧪 Starting EDPMT End-to-End Tests")
        self.logger.info("=" * 50)
        
        # Start test server
        if not await self.start_test_server():
            self.logger.error("❌ Failed to start test server")
            return False
        
        try:
            # Basic connectivity tests
            await self.run_test("Health Check", self.test_health_check)
            await self.run_test("Server Info", self.test_server_info) 
            await self.run_test("Web UI Access", self.test_web_ui_access)
            
            # GPIO tests
            await self.run_test("GPIO Digital Output", self.test_gpio_digital_output)
            await self.run_test("GPIO Digital Input", self.test_gpio_digital_input)
            await self.run_test("GPIO PWM Control", self.test_gpio_pwm_control)
            await self.run_test("GPIO Pin Configuration", self.test_gpio_pin_configuration)
            
            # I2C tests
            await self.run_test("I2C Scan", self.test_i2c_scan)
            await self.run_test("I2C Read Device", self.test_i2c_read_device)
            await self.run_test("I2C Write Device", self.test_i2c_write_device)
            
            # SPI tests
            await self.run_test("SPI Transfer", self.test_spi_transfer)
            await self.run_test("SPI Configuration", self.test_spi_configuration)
            
            # UART tests
            await self.run_test("UART Write", self.test_uart_write)
            await self.run_test("UART Read", self.test_uart_read)
            
            # Error handling tests
            await self.run_test("Invalid Action", self.test_invalid_action)
            await self.run_test("Invalid Target", self.test_invalid_target)
            await self.run_test("Malformed Request", self.test_malformed_request)
            
            # Performance tests
            await self.run_test("Concurrent Requests", self.test_concurrent_requests)
            await self.run_test("Rapid Requests", self.test_rapid_requests)
            
            # Client API tests
            await self.run_test("EDPMT Client", self.test_edpmt_client)
            
        finally:
            await self.cleanup()
        
        # Generate test report
        return self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.logger.info("\n" + "=" * 50)
        self.logger.info("📊 E2E Test Results Summary")
        self.logger.info("=" * 50)
        self.logger.info(f"Total Tests: {total_tests}")
        self.logger.info(f"Passed: {passed_tests}")
        self.logger.info(f"Failed: {failed_tests}")
        self.logger.info(f"Success Rate: {success_rate:.1f}%")
        self.logger.info(f"Log File: {self.log_file}")
        
        if failed_tests > 0:
            self.logger.info("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    self.logger.info(f"  - {result['name']}: {result['error']}")
        
        if success_rate == 100:
            self.logger.info("\n🎉 ALL TESTS PASSED!")
            return True
        else:
            self.logger.info(f"\n❌ {failed_tests} TESTS FAILED")
            return False

async def main():
    """Main test runner"""
    tester = EDPMTEndToEndTests()
    
    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Tests interrupted by user")
        await tester.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        await tester.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
