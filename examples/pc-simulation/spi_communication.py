#!/usr/bin/env python3
"""
SPI Communication Simulation Example

This example demonstrates SPI communication with simulated devices:
- MAX31855 Thermocouple amplifier
- MCP3008 8-channel ADC
- SPI Flash memory device

All devices are simulated and work on any PC without real hardware.
"""

import asyncio
import time
import random
import struct
from edpmt import EDPMTransparent, EDPMClient

class SPIDemo:
    def __init__(self):
        self.server = None
        self.client = None
    
    async def start_server(self):
        """Start EDPMT server with SPI simulators"""
        print("🚀 Starting EDPMT server with SPI simulators...")
        self.server = EDPMTransparent(name="SPI-Simulator", config={
            'dev_mode': True,
            'hardware_simulators': True,
            'port': 8890  # Use different port
        })
        
        server_task = asyncio.create_task(self.server.start_server())
        await asyncio.sleep(2)
        return server_task
    
    async def connect_client(self):
        """Connect EDPMT client to server"""
        print("🔌 Connecting to EDPMT server...")
        self.client = EDPMClient(url="https://localhost:8890")
        await asyncio.sleep(1)
        print("✅ Connected to EDPMT server")
    
    async def configure_spi(self):
        """Configure SPI interface parameters"""
        print("\n⚙️  Configuring SPI interface...")
        
        # Configure SPI bus 0, device 0
        await self.client.execute('config', 'spi', 
                                 bus=0, device=0, 
                                 speed=1000000,  # 1 MHz
                                 mode=0,         # CPOL=0, CPHA=0
                                 bits=8)         # 8-bit words
        
        print("✅ SPI configured: Bus=0, Device=0, Speed=1MHz, Mode=0, Bits=8")
    
    async def read_max31855_thermocouple(self):
        """Read temperature from MAX31855 thermocouple amplifier"""
        print("\n🌡️  Reading MAX31855 Thermocouple Amplifier...")
        
        try:
            # MAX31855 requires 32-bit read (4 bytes)
            # Send dummy bytes to clock out data
            response = await self.client.execute('transfer', 'spi', data=[0x00, 0x00, 0x00, 0x00])
            
            if len(response) != 4:
                print(f"❌ Unexpected response length: {len(response)}")
                return None
            
            # Combine bytes into 32-bit value (big-endian)
            raw_data = (response[0] << 24) | (response[1] << 16) | (response[2] << 8) | response[3]
            
            print(f"📡 Raw SPI data: {[hex(b) for b in response]} -> 0x{raw_data:08X}")
            
            # Parse MAX31855 data format
            # Bits 31-18: Thermocouple temperature (14 bits, signed)
            # Bit 16: Fault flag
            # Bits 15-4: Internal temperature (12 bits, signed)
            # Bits 3-0: Fault status
            
            # Extract thermocouple temperature (bits 31-18)
            tc_raw = (raw_data >> 18) & 0x3FFF
            if tc_raw & 0x2000:  # Sign extension for negative temperatures
                tc_raw |= 0xC000
                tc_temp = -((~tc_raw & 0x3FFF) + 1) * 0.25
            else:
                tc_temp = tc_raw * 0.25
            
            # Extract internal temperature (bits 15-4) 
            int_raw = (raw_data >> 4) & 0xFFF
            if int_raw & 0x800:  # Sign extension
                int_raw |= 0xF000
                int_temp = -((~int_raw & 0xFFF) + 1) * 0.0625
            else:
                int_temp = int_raw * 0.0625
            
            # Check fault flags
            fault = (raw_data >> 16) & 0x01
            fault_bits = raw_data & 0x07
            
            print(f"🔥 Thermocouple Temperature: {tc_temp:.2f}°C")
            print(f"🏠 Internal Temperature: {int_temp:.2f}°C")
            
            if fault:
                fault_msgs = []
                if fault_bits & 0x01:
                    fault_msgs.append("Open Circuit")
                if fault_bits & 0x02:
                    fault_msgs.append("Short to GND")
                if fault_bits & 0x04:
                    fault_msgs.append("Short to VCC")
                print(f"⚠️  Fault detected: {', '.join(fault_msgs)}")
            else:
                print("✅ No faults detected")
            
            return tc_temp, int_temp, fault_bits
            
        except Exception as e:
            print(f"❌ Error reading MAX31855: {e}")
            return None, None, None
    
    async def read_mcp3008_adc(self):
        """Read all channels from MCP3008 8-channel ADC"""
        print("\n📊 Reading MCP3008 8-Channel ADC...")
        
        try:
            channel_data = []
            
            for channel in range(8):
                # MCP3008 command: Start bit + Single/Diff + Channel (3 bits) + Don't care
                # For single-ended channel N: 11000NNN0
                cmd_byte = 0x01  # Start bit
                addr_byte = (0x80 | (channel << 4))  # Single-ended + channel
                
                # Send 3-byte command and receive 3-byte response
                response = await self.client.execute('transfer', 'spi', 
                                                   data=[cmd_byte, addr_byte, 0x00])
                
                if len(response) != 3:
                    print(f"❌ Unexpected response length for channel {channel}: {len(response)}")
                    continue
                
                # Extract 10-bit ADC value from response
                # Response format: X-X-X-X-X-B9-B8-B7, B6-B5-B4-B3-B2-B1-B0-X
                adc_value = ((response[1] & 0x03) << 8) | response[2]
                
                # Convert to voltage (assuming 3.3V reference)
                voltage = (adc_value / 1023.0) * 3.3
                
                channel_data.append((adc_value, voltage))
                print(f"📈 Channel {channel}: {adc_value:4d} (0x{adc_value:03X}) = {voltage:.3f}V")
            
            # Calculate statistics
            voltages = [v for _, v in channel_data]
            avg_voltage = sum(voltages) / len(voltages)
            min_voltage = min(voltages)
            max_voltage = max(voltages)
            
            print(f"\n📊 ADC Statistics:")
            print(f"   Average: {avg_voltage:.3f}V")
            print(f"   Minimum: {min_voltage:.3f}V")
            print(f"   Maximum: {max_voltage:.3f}V")
            print(f"   Range: {max_voltage - min_voltage:.3f}V")
            
            return channel_data
            
        except Exception as e:
            print(f"❌ Error reading MCP3008: {e}")
            return []
    
    async def test_spi_flash_memory(self):
        """Test SPI flash memory operations"""
        print("\n💾 Testing SPI Flash Memory...")
        
        try:
            # Read JEDEC ID (command 0x9F)
            print("🔍 Reading JEDEC ID...")
            id_response = await self.client.execute('transfer', 'spi', data=[0x9F, 0x00, 0x00, 0x00])
            
            if len(id_response) >= 4:
                manufacturer = id_response[1]
                device_type = id_response[2]  
                capacity = id_response[3]
                
                print(f"📋 Flash ID: Mfg=0x{manufacturer:02X}, Type=0x{device_type:02X}, Cap=0x{capacity:02X}")
                
                # Decode common manufacturers
                mfg_names = {
                    0xEF: "Winbond",
                    0xC2: "Macronix", 
                    0x20: "Micron/ST",
                    0x1F: "Atmel",
                    0xBF: "SST"
                }
                mfg_name = mfg_names.get(manufacturer, "Unknown")
                print(f"📂 Manufacturer: {mfg_name}")
            
            # Read status register (command 0x05)
            print("\n📄 Reading status register...")
            status_response = await self.client.execute('transfer', 'spi', data=[0x05, 0x00])
            if len(status_response) >= 2:
                status = status_response[1]
                print(f"📊 Status Register: 0x{status:02X}")
                print(f"   Busy: {'Yes' if status & 0x01 else 'No'}")
                print(f"   Write Enable: {'Yes' if status & 0x02 else 'No'}")
                print(f"   Block Protect: {(status >> 2) & 0x0F}")
            
            # Read data from address 0x000000 (command 0x03)
            print("\n📖 Reading flash data...")
            read_addr = 0x000000
            read_response = await self.client.execute('transfer', 'spi', 
                                                    data=[0x03,  # Read command
                                                          (read_addr >> 16) & 0xFF,  # Address high
                                                          (read_addr >> 8) & 0xFF,   # Address mid
                                                          read_addr & 0xFF,          # Address low
                                                          0x00, 0x00, 0x00, 0x00,   # Dummy bytes
                                                          0x00, 0x00, 0x00, 0x00])
            
            if len(read_response) > 4:
                data_bytes = read_response[4:]  # Skip command and address
                print(f"📄 Data at 0x{read_addr:06X}: {[hex(b) for b in data_bytes]}")
                ascii_data = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data_bytes])
                print(f"📝 As ASCII: '{ascii_data}'")
            
            print("✅ SPI Flash memory test completed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing SPI flash: {e}")
            return False
    
    async def spi_performance_test(self):
        """Test SPI communication performance"""
        print("\n⚡ SPI Performance Test...")
        
        try:
            # Test different data sizes
            test_sizes = [1, 4, 16, 64, 256]
            
            for size in test_sizes:
                test_data = list(range(size))  # Generate test pattern
                
                start_time = time.time()
                iterations = 100
                
                for _ in range(iterations):
                    response = await self.client.execute('transfer', 'spi', data=test_data)
                
                end_time = time.time()
                duration = end_time - start_time
                
                bytes_transferred = size * iterations * 2  # Send + receive
                throughput = bytes_transferred / duration
                
                print(f"📊 Size: {size:3d} bytes, "
                      f"Time: {duration:.3f}s, "
                      f"Throughput: {throughput:.0f} bytes/sec")
            
            print("✅ Performance test completed")
            
        except Exception as e:
            print(f"❌ Error in performance test: {e}")
    
    async def run_demo(self):
        """Run complete SPI demonstration"""
        print("🎯 SPI Communication Demo")
        print("=" * 50)
        
        try:
            # Start server and connect
            server_task = await self.start_server()
            await self.connect_client()
            
            # Configure SPI
            await self.configure_spi()
            
            # Test MAX31855 thermocouple
            print("\n1️⃣  Testing MAX31855 Thermocouple...")
            await self.read_max31855_thermocouple()
            
            # Test MCP3008 ADC
            print("\n2️⃣  Testing MCP3008 ADC...")
            await self.read_mcp3008_adc()
            
            # Test SPI Flash
            print("\n3️⃣  Testing SPI Flash Memory...")
            await self.test_spi_flash_memory()
            
            # Performance test
            print("\n4️⃣  Running Performance Test...")
            await self.spi_performance_test()
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
        finally:
            # Cleanup
            if self.client:
                await self.client.close()
            if self.server:
                await self.server.close()
        
        print("\n✅ SPI Communication Demo completed!")

async def main():
    """Main entry point"""
    demo = SPIDemo()
    await demo.run_demo()

if __name__ == "__main__":
    print("🖥️  PC-Based SPI Communication Simulation")
    print("This demo works entirely with simulators - no real hardware needed!")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
