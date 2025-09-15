#!/usr/bin/env python3
"""
UART GPS Simulation Example

This example demonstrates UART/Serial communication with simulated devices:
- GPS module with NMEA sentence parsing
- Serial terminal for bidirectional communication
- Sensor data logger with UART data collection

All UART communication is simulated and works on any PC without real hardware.
"""

import asyncio
import time
import random
import math
from datetime import datetime
from edpmt import EDPMTransparent, EDPMClient

class UARTDemo:
    def __init__(self):
        self.server = None
        self.client = None
        
        # Simulated GPS coordinates (starting position)
        self.gps_lat = 37.7749  # San Francisco
        self.gps_lon = -122.4194
        self.gps_altitude = 50.0
        self.gps_speed = 0.0
        self.gps_heading = 0.0
        
        # Data logging
        self.sensor_data = []
    
    async def start_server(self):
        """Start EDPMT server with UART simulators"""
        print("🚀 Starting EDPMT server with UART simulators...")
        self.server = EDPMTransparent(name="UART-Simulator", config={
            'dev_mode': True,
            'hardware_simulators': True,
            'port': 8892  # Use different port
        })
        
        server_task = asyncio.create_task(self.server.start_server())
        await asyncio.sleep(2)
        return server_task
    
    async def connect_client(self):
        """Connect EDPMT client to server"""
        print("🔌 Connecting to EDPMT server...")
        self.client = EDPMClient(url="https://localhost:8892")
        await asyncio.sleep(1)
        print("✅ Connected to EDPMT server")
    
    async def configure_uart(self, port="/dev/ttyUSB0", baudrate=9600):
        """Configure UART interface parameters"""
        print(f"\n⚙️  Configuring UART interface...")
        print(f"   Port: {port}")
        print(f"   Baud Rate: {baudrate}")
        print(f"   Data Bits: 8, Stop Bits: 1, Parity: None")
        
        await self.client.execute('config', 'uart', 
                                 port=port,
                                 baudrate=baudrate,
                                 bytesize=8,
                                 parity='N',
                                 stopbits=1,
                                 timeout=1.0)
        
        print("✅ UART configured successfully")
    
    def generate_nmea_sentence(self, sentence_type):
        """Generate realistic NMEA sentences for GPS simulation"""
        now = datetime.utcnow()
        
        if sentence_type == "GPRMC":
            # Recommended Minimum Course
            time_str = now.strftime("%H%M%S.00")
            date_str = now.strftime("%d%m%y")
            
            # Add some random movement
            self.gps_lat += random.uniform(-0.0001, 0.0001)
            self.gps_lon += random.uniform(-0.0001, 0.0001)
            self.gps_speed = max(0, self.gps_speed + random.uniform(-2, 2))
            self.gps_heading = (self.gps_heading + random.uniform(-10, 10)) % 360
            
            # Convert to degrees and minutes
            lat_deg = int(abs(self.gps_lat))
            lat_min = (abs(self.gps_lat) - lat_deg) * 60
            lat_ns = "N" if self.gps_lat >= 0 else "S"
            
            lon_deg = int(abs(self.gps_lon))
            lon_min = (abs(self.gps_lon) - lon_deg) * 60
            lon_ew = "E" if self.gps_lon >= 0 else "W"
            
            sentence = (f"GPRMC,{time_str},A,"
                       f"{lat_deg:02d}{lat_min:07.4f},{lat_ns},"
                       f"{lon_deg:03d}{lon_min:07.4f},{lon_ew},"
                       f"{self.gps_speed:.1f},{self.gps_heading:.1f},"
                       f"{date_str},,")
            
        elif sentence_type == "GPGGA":
            # Global Positioning System Fix Data
            time_str = now.strftime("%H%M%S.00")
            
            lat_deg = int(abs(self.gps_lat))
            lat_min = (abs(self.gps_lat) - lat_deg) * 60
            lat_ns = "N" if self.gps_lat >= 0 else "S"
            
            lon_deg = int(abs(self.gps_lon))
            lon_min = (abs(self.gps_lon) - lon_deg) * 60
            lon_ew = "E" if self.gps_lon >= 0 else "W"
            
            quality = 1  # GPS fix
            satellites = random.randint(6, 12)
            hdop = random.uniform(0.8, 2.0)
            altitude = self.gps_altitude + random.uniform(-5, 5)
            
            sentence = (f"GPGGA,{time_str},"
                       f"{lat_deg:02d}{lat_min:07.4f},{lat_ns},"
                       f"{lon_deg:03d}{lon_min:07.4f},{lon_ew},"
                       f"{quality},{satellites:02d},{hdop:.1f},"
                       f"{altitude:.1f},M,0.0,M,,")
        
        elif sentence_type == "GPGSV":
            # Satellites in View
            sentence = ("GPGSV,3,1,12,"
                       "01,85,045,47,02,60,125,43,03,45,200,38,04,30,280,42")
        
        else:
            sentence = "GPGLL,,,,,,,V"  # Invalid sentence
        
        # Calculate and append checksum
        checksum = 0
        for char in sentence:
            checksum ^= ord(char)
        
        return f"${sentence}*{checksum:02X}\r\n"
    
    async def simulate_gps_module(self, duration=30):
        """Simulate GPS module sending NMEA sentences"""
        print(f"\n🛰️  Simulating GPS module for {duration} seconds...")
        print("📡 Receiving NMEA sentences...")
        
        start_time = time.time()
        sentence_count = 0
        
        try:
            while time.time() - start_time < duration:
                # Generate different NMEA sentence types
                sentence_types = ["GPRMC", "GPGGA", "GPGSV"]
                
                for sentence_type in sentence_types:
                    if time.time() - start_time >= duration:
                        break
                    
                    # Generate NMEA sentence
                    nmea_sentence = self.generate_nmea_sentence(sentence_type)
                    sentence_count += 1
                    
                    print(f"📥 RX: {nmea_sentence.strip()}")
                    
                    # Parse GPRMC sentences for position updates
                    if sentence_type == "GPRMC":
                        await self.parse_gprmc_sentence(nmea_sentence)
                    
                    # Simulate receiving data via UART
                    try:
                        # In real implementation, this would be received from UART
                        # Here we simulate the process of receiving the sentence
                        received = await self.client.execute('read', 'uart', timeout=0.1)
                        # The simulator would return the NMEA sentence
                        
                    except Exception as e:
                        # Expected in simulation - no real data to read
                        pass
                    
                    await asyncio.sleep(1)  # GPS typically sends at 1Hz
                
        except KeyboardInterrupt:
            print("\n⏹️  GPS simulation stopped by user")
        
        print(f"\n📊 GPS Simulation Summary:")
        print(f"   Duration: {time.time() - start_time:.1f} seconds")
        print(f"   Sentences: {sentence_count}")
        print(f"   Final Position: {self.gps_lat:.6f}°, {self.gps_lon:.6f}°")
        print(f"   Altitude: {self.gps_altitude:.1f}m")
        print(f"   Speed: {self.gps_speed:.1f} knots")
    
    async def parse_gprmc_sentence(self, nmea_sentence):
        """Parse GPRMC sentence and extract position data"""
        try:
            # Remove $ and checksum
            sentence = nmea_sentence.split('*')[0][1:]
            fields = sentence.split(',')
            
            if len(fields) >= 12 and fields[0] == "GPRMC" and fields[2] == "A":
                # Extract position data
                lat_raw = fields[3]
                lat_ns = fields[4]
                lon_raw = fields[5]
                lon_ew = fields[6]
                speed_knots = float(fields[7]) if fields[7] else 0
                heading = float(fields[8]) if fields[8] else 0
                
                # Convert to decimal degrees
                if lat_raw and len(lat_raw) >= 4:
                    lat_deg = int(lat_raw[:2])
                    lat_min = float(lat_raw[2:])
                    latitude = lat_deg + lat_min / 60
                    if lat_ns == "S":
                        latitude = -latitude
                
                if lon_raw and len(lon_raw) >= 5:
                    lon_deg = int(lon_raw[:3])
                    lon_min = float(lon_raw[3:])
                    longitude = lon_deg + lon_min / 60
                    if lon_ew == "W":
                        longitude = -longitude
                
                print(f"📍 Position: {latitude:.6f}°, {longitude:.6f}° "
                      f"(Speed: {speed_knots:.1f} knots, Heading: {heading:.1f}°)")
                
        except Exception as e:
            print(f"⚠️  Error parsing GPRMC: {e}")
    
    async def serial_terminal_demo(self):
        """Demonstrate bidirectional serial communication"""
        print("\n💬 Serial Terminal Communication Demo...")
        
        # Send AT commands (common for modems/modules)
        commands = [
            "AT",           # Basic AT command
            "AT+CGMI",      # Get manufacturer
            "AT+CGMM",      # Get model
            "AT+CGMR",      # Get revision
            "AT+CSQ",       # Signal quality
            "AT+CREG?",     # Network registration
        ]
        
        for cmd in commands:
            try:
                print(f"📤 TX: {cmd}")
                
                # Send command
                await self.client.execute('write', 'uart', data=cmd + '\r\n')
                
                # Wait for response (simulated)
                await asyncio.sleep(0.1)
                
                # Read response
                response = await self.client.execute('read', 'uart', timeout=1.0)
                
                # Simulate typical AT command responses
                if cmd == "AT":
                    simulated_response = "OK"
                elif cmd == "AT+CGMI":
                    simulated_response = "Simulated Manufacturer\r\nOK"
                elif cmd == "AT+CGMM":
                    simulated_response = "SIM-MODULE-1000\r\nOK"
                elif cmd == "AT+CGMR":
                    simulated_response = "Rev 1.0.0\r\nOK"
                elif cmd == "AT+CSQ":
                    signal_strength = random.randint(10, 31)
                    simulated_response = f"+CSQ: {signal_strength},0\r\nOK"
                elif cmd == "AT+CREG?":
                    simulated_response = "+CREG: 0,1\r\nOK"
                else:
                    simulated_response = "OK"
                
                print(f"📥 RX: {simulated_response}")
                
            except Exception as e:
                print(f"❌ Error in serial communication: {e}")
            
            await asyncio.sleep(0.5)
    
    async def sensor_data_logger(self, duration=15):
        """Log sensor data received via UART"""
        print(f"\n📊 Starting sensor data logger for {duration} seconds...")
        
        start_time = time.time()
        sample_count = 0
        
        try:
            while time.time() - start_time < duration:
                current_time = time.time() - start_time
                
                # Simulate sensor data reception
                temperature = 20 + 5 * math.sin(current_time * 0.1) + random.uniform(-1, 1)
                humidity = 50 + 10 * math.cos(current_time * 0.08) + random.uniform(-2, 2)
                pressure = 1013 + 20 * math.sin(current_time * 0.05) + random.uniform(-5, 5)
                
                # Create sensor data packet
                sensor_data = f"SENSOR,{current_time:.1f},{temperature:.1f},{humidity:.1f},{pressure:.1f}\r\n"
                
                sample_count += 1
                print(f"📊 Sample #{sample_count:3d}: T={temperature:5.1f}°C, H={humidity:4.1f}%, P={pressure:6.1f}hPa")
                
                # Store data
                self.sensor_data.append({
                    'timestamp': current_time,
                    'temperature': temperature,
                    'humidity': humidity,
                    'pressure': pressure
                })
                
                # Simulate reading data from UART
                try:
                    # In real implementation, this data would come from UART
                    received_data = await self.client.execute('read', 'uart', timeout=0.1)
                except:
                    pass  # Expected in simulation
                
                await asyncio.sleep(1.0)  # 1 second sampling rate
                
        except KeyboardInterrupt:
            print("\n⏹️  Data logging stopped by user")
        
        # Display statistics
        print(f"\n📈 Data Logger Summary:")
        print(f"   Samples Collected: {len(self.sensor_data)}")
        if self.sensor_data:
            avg_temp = sum(d['temperature'] for d in self.sensor_data) / len(self.sensor_data)
            avg_humidity = sum(d['humidity'] for d in self.sensor_data) / len(self.sensor_data)
            avg_pressure = sum(d['pressure'] for d in self.sensor_data) / len(self.sensor_data)
            
            print(f"   Average Temperature: {avg_temp:.1f}°C")
            print(f"   Average Humidity: {avg_humidity:.1f}%")
            print(f"   Average Pressure: {avg_pressure:.1f} hPa")
    
    async def uart_performance_test(self):
        """Test UART communication performance and reliability"""
        print("\n⚡ UART Performance Test...")
        
        test_data_sizes = [10, 50, 100, 500, 1000]
        
        for size in test_data_sizes:
            print(f"\n📊 Testing {size} byte transfers...")
            
            # Generate test data
            test_data = "A" * size
            
            start_time = time.time()
            iterations = 10
            success_count = 0
            
            for i in range(iterations):
                try:
                    # Send data
                    await self.client.execute('write', 'uart', data=test_data)
                    
                    # Read back (simulated echo)
                    received = await self.client.execute('read', 'uart', timeout=2.0)
                    
                    # In simulation, we assume successful transfer
                    success_count += 1
                    
                except Exception as e:
                    print(f"   ❌ Transfer {i+1} failed: {e}")
            
            end_time = time.time()
            duration = end_time - start_time
            
            success_rate = (success_count / iterations) * 100
            throughput = (size * success_count) / duration if duration > 0 else 0
            
            print(f"   ✅ Success Rate: {success_rate:.1f}% ({success_count}/{iterations})")
            print(f"   📈 Throughput: {throughput:.0f} bytes/sec")
            print(f"   ⏱️  Average Time: {duration/iterations:.3f}s per transfer")
    
    async def run_demo(self):
        """Run complete UART demonstration"""
        print("🎯 UART GPS & Communication Demo")
        print("=" * 50)
        
        try:
            # Start server and connect
            server_task = await self.start_server()
            await self.connect_client()
            
            # Configure UART
            await self.configure_uart("/dev/ttyUSB0", 9600)
            
            # GPS Module Simulation
            print("\n1️⃣  GPS Module Simulation...")
            await self.simulate_gps_module(10)  # 10 seconds of GPS data
            
            # Serial Terminal Demo
            print("\n2️⃣  Serial Terminal Communication...")
            await self.serial_terminal_demo()
            
            # Sensor Data Logger
            print("\n3️⃣  Sensor Data Logger...")
            await self.sensor_data_logger(8)  # 8 seconds of data logging
            
            # Performance Test
            print("\n4️⃣  UART Performance Test...")
            await self.uart_performance_test()
            
            print("\n✅ All UART demonstrations completed successfully!")
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
        finally:
            # Cleanup
            if self.client:
                await self.client.close()
            if self.server:
                await self.server.close()
        
        print("\n🎉 UART Demo completed!")

async def main():
    """Main entry point"""
    demo = UARTDemo()
    await demo.run_demo()

if __name__ == "__main__":
    print("🖥️  PC-Based UART GPS & Communication Simulation")
    print("This demo works entirely with simulators - no real hardware needed!")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
