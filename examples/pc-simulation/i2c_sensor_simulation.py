#!/usr/bin/env python3
"""
I2C Sensor Simulation Example

This example demonstrates I2C communication with simulated sensors:
- BME280 Temperature/Pressure/Humidity sensor
- EEPROM memory device
- Device discovery and enumeration

All sensors are simulated and work on any PC without real hardware.
"""

import asyncio
import time
import struct
from edpmt import EDPMTransparent, EDPMClient

class I2CSensorDemo:
    def __init__(self):
        self.server = None
        self.client = None
    
    async def start_server(self):
        """Start EDPMT server in development mode with simulators"""
        print("🚀 Starting EDPMT server with I2C simulators...")
        self.server = EDPMTransparent(name="I2C-Simulator", config={
            'dev_mode': True,
            'hardware_simulators': True,
            'port': 8889  # Use different port to avoid conflicts
        })
        
        # Start server in background
        server_task = asyncio.create_task(self.server.start_server())
        await asyncio.sleep(2)  # Give server time to start
        
        return server_task
    
    async def connect_client(self):
        """Connect EDPMT client to the server"""
        print("🔌 Connecting to EDPMT server...")
        self.client = EDPMClient(url="https://localhost:8889")
        await asyncio.sleep(1)  # Give client time to connect
        print("✅ Connected to EDPMT server")
    
    async def discover_i2c_devices(self):
        """Scan I2C bus for available devices"""
        print("\n🔍 Scanning I2C bus for devices...")
        
        try:
            devices = await self.client.execute('scan', 'i2c')
            print(f"Found I2C devices: {[hex(addr) for addr in devices]}")
            
            # Typical simulated devices
            expected_devices = {
                0x76: "BME280 Temperature/Pressure/Humidity Sensor",
                0x50: "EEPROM Memory (24C32)",
                0x68: "DS3231 Real-Time Clock",
                0x48: "ADS1115 ADC"
            }
            
            for addr in devices:
                device_name = expected_devices.get(addr, "Unknown Device")
                print(f"  📡 0x{addr:02X}: {device_name}")
            
            return devices
            
        except Exception as e:
            print(f"❌ Error scanning I2C bus: {e}")
            return []
    
    async def read_bme280_sensor(self):
        """Read temperature, pressure, and humidity from BME280 sensor"""
        print("\n🌡️  Reading BME280 Temperature/Pressure/Humidity Sensor...")
        
        device_addr = 0x76
        
        try:
            # Read chip ID to verify sensor
            chip_id = await self.client.execute('read', 'i2c', 
                                              device=device_addr, register=0xD0, length=1)
            print(f"BME280 Chip ID: 0x{chip_id[0]:02X}")
            
            if chip_id[0] != 0x60:  # BME280 chip ID
                print("⚠️  Unexpected chip ID, but continuing with simulation...")
            
            # Configure sensor for normal mode
            # Set humidity control (ctrl_hum register)
            await self.client.execute('write', 'i2c', device=device_addr, 
                                    register=0xF2, data=[0x01])
            
            # Set temperature and pressure control (ctrl_meas register)
            await self.client.execute('write', 'i2c', device=device_addr, 
                                    register=0xF4, data=[0x27])
            
            # Set configuration (config register) 
            await self.client.execute('write', 'i2c', device=device_addr, 
                                    register=0xF5, data=[0xA0])
            
            # Wait for measurement
            await asyncio.sleep(0.1)
            
            # Read calibration data (simplified)
            print("📖 Reading sensor calibration data...")
            cal_data = await self.client.execute('read', 'i2c', 
                                                device=device_addr, register=0x88, length=24)
            
            # Read measurement data
            print("📊 Reading measurement data...")
            data = await self.client.execute('read', 'i2c', 
                                           device=device_addr, register=0xF7, length=8)
            
            # Parse raw data (simulated values will be realistic)
            pressure_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
            temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
            humidity_raw = (data[6] << 8) | data[7]
            
            # Convert to actual values (simplified calculation)
            # In real implementation, you'd use proper BME280 compensation formulas
            temperature = 20.0 + (temp_raw / 100000.0) * 5  # Simulated: 20-25°C
            pressure = 1013.25 + (pressure_raw / 1000000.0) * 50  # Simulated: ~1013 hPa
            humidity = 45.0 + (humidity_raw / 65536.0) * 20  # Simulated: 45-65% RH
            
            print(f"🌡️  Temperature: {temperature:.2f}°C")
            print(f"🌪️  Pressure: {pressure:.2f} hPa")
            print(f"💧 Humidity: {humidity:.2f}% RH")
            
            return temperature, pressure, humidity
            
        except Exception as e:
            print(f"❌ Error reading BME280: {e}")
            return None, None, None
    
    async def test_eeprom_memory(self):
        """Test EEPROM memory read/write operations"""
        print("\n💾 Testing EEPROM Memory (24C32)...")
        
        device_addr = 0x50
        
        try:
            # Write test data to EEPROM
            test_data = [0x48, 0x65, 0x6C, 0x6C, 0x6F]  # "Hello"
            memory_addr = 0x0000
            
            print(f"✍️  Writing data to EEPROM address 0x{memory_addr:04X}: {test_data}")
            
            # Write memory address (16-bit) and data
            write_data = [(memory_addr >> 8) & 0xFF, memory_addr & 0xFF] + test_data
            await self.client.execute('write_raw', 'i2c', device=device_addr, data=write_data)
            
            # Wait for write cycle
            await asyncio.sleep(0.01)
            
            # Read back data
            print("📖 Reading data back from EEPROM...")
            
            # Set memory address for reading
            addr_data = [(memory_addr >> 8) & 0xFF, memory_addr & 0xFF]
            await self.client.execute('write_raw', 'i2c', device=device_addr, data=addr_data)
            
            # Read data
            read_data = await self.client.execute('read_raw', 'i2c', device=device_addr, length=len(test_data))
            
            print(f"📝 Read data: {read_data}")
            print(f"📄 As ASCII: {''.join([chr(b) if 32 <= b <= 126 else '.' for b in read_data])}")
            
            # Verify data integrity
            if read_data == test_data:
                print("✅ EEPROM read/write test PASSED")
            else:
                print("❌ EEPROM read/write test FAILED")
                print(f"Expected: {test_data}")
                print(f"Got: {read_data}")
            
            return read_data == test_data
            
        except Exception as e:
            print(f"❌ Error testing EEPROM: {e}")
            return False
    
    async def continuous_monitoring(self, duration=30):
        """Continuously monitor sensors for specified duration"""
        print(f"\n📈 Starting continuous monitoring for {duration} seconds...")
        
        start_time = time.time()
        sample_count = 0
        
        try:
            while time.time() - start_time < duration:
                sample_count += 1
                current_time = time.time() - start_time
                
                # Read BME280 sensor
                temp, pressure, humidity = await self.read_bme280_sensor()
                
                if temp is not None:
                    print(f"[{current_time:6.1f}s] Sample #{sample_count:3d}: "
                          f"T={temp:5.1f}°C, P={pressure:7.1f}hPa, H={humidity:4.1f}%")
                
                # Wait before next sample
                await asyncio.sleep(2.0)
        
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
        
        print(f"📊 Monitoring completed: {sample_count} samples in {duration} seconds")
    
    async def run_demo(self):
        """Run complete I2C sensor demonstration"""
        print("🎯 I2C Sensor Simulation Demo")
        print("=" * 50)
        
        try:
            # Start server
            server_task = await self.start_server()
            
            # Connect client
            await self.connect_client()
            
            # Discover devices
            devices = await self.discover_i2c_devices()
            
            if not devices:
                print("❌ No I2C devices found. Check simulator configuration.")
                return
            
            # Test BME280 sensor
            if 0x76 in devices:
                await self.read_bme280_sensor()
            
            # Test EEPROM memory
            if 0x50 in devices:
                await self.test_eeprom_memory()
            
            # Optional: Continuous monitoring
            print("\n❓ Would you like to start continuous monitoring? (Ctrl+C to stop)")
            print("💡 In a real application, you could run this...")
            # await self.continuous_monitoring(30)  # Uncomment to enable
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
        finally:
            # Cleanup
            if self.client:
                await self.client.close()
            if self.server:
                await self.server.close()
        
        print("\n✅ I2C Sensor Demo completed!")

async def main():
    """Main entry point"""
    demo = I2CSensorDemo()
    await demo.run_demo()

if __name__ == "__main__":
    print("🖥️  PC-Based I2C Sensor Simulation")
    print("This demo works entirely with simulators - no real hardware needed!")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
