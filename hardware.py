#!/usr/bin/env python3
"""
EDPMT Hardware Abstraction Layer
Real hardware interfaces and simulators for development

Provides unified async interface for GPIO, I2C, SPI, and UART communication
with automatic fallback to simulators when hardware is not available.
"""

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Union

logger = logging.getLogger('EDPM.Hardware')


# === Abstract Base Classes ===

class HardwareInterface(ABC):
    """Base class for all hardware interfaces"""
    
    def __init__(self):
        self.is_simulator = False
        self.name = self.__class__.__name__
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    @abstractmethod
    async def initialize(self):
        """Initialize the hardware interface"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Clean up resources"""
        pass


# === GPIO Interface ===

class GPIOInterface(HardwareInterface):
    """Real GPIO interface for Raspberry Pi"""
    
    def __init__(self):
        super().__init__()
        self.gpio = None
        self.pwm_instances = {}
        self.initialized_pins = set()
    
    async def initialize(self):
        """Initialize RPi.GPIO"""
        try:
            import RPi.GPIO as GPIO
            self.gpio = GPIO
            self.gpio.setmode(GPIO.BCM)
            self.gpio.setwarnings(False)
            logger.info("GPIO interface initialized (RPi.GPIO)")
        except ImportError as e:
            logger.error(f"RPi.GPIO not available: {e}")
            raise ImportError("RPi.GPIO required for GPIO operations")
    
    async def cleanup(self):
        """Clean up GPIO resources"""
        if self.gpio:
            # Stop all PWM instances
            for pwm in self.pwm_instances.values():
                pwm.stop()
            self.pwm_instances.clear()
            
            # Clean up GPIO
            self.gpio.cleanup()
            logger.info("GPIO cleaned up")
    
    async def set(self, pin: int, value: int):
        """Set GPIO pin to HIGH (1) or LOW (0)"""
        if pin not in self.initialized_pins:
            self.gpio.setup(pin, self.gpio.OUT)
            self.initialized_pins.add(pin)
        
        self.gpio.output(pin, value)
        logger.debug(f"GPIO pin {pin} set to {value}")
    
    async def get(self, pin: int) -> int:
        """Read GPIO pin value"""
        if pin not in self.initialized_pins:
            self.gpio.setup(pin, self.gpio.IN, pull_up_down=self.gpio.PUD_UP)
            self.initialized_pins.add(pin)
        
        value = self.gpio.input(pin)
        logger.debug(f"GPIO pin {pin} read: {value}")
        return value
    
    async def pwm(self, pin: int, frequency: float, duty_cycle: float):
        """Start PWM on GPIO pin"""
        if pin not in self.initialized_pins:
            self.gpio.setup(pin, self.gpio.OUT)
            self.initialized_pins.add(pin)
        
        # Stop existing PWM if any
        if pin in self.pwm_instances:
            self.pwm_instances[pin].stop()
        
        # Create new PWM instance
        pwm = self.gpio.PWM(pin, frequency)
        pwm.start(duty_cycle)
        self.pwm_instances[pin] = pwm
        
        logger.debug(f"PWM started on pin {pin}: {frequency}Hz @ {duty_cycle}%")


class GPIOSimulator(HardwareInterface):
    """GPIO simulator for development and testing"""
    
    def __init__(self):
        super().__init__()
        self.is_simulator = True
        self.pins = {}
        self.pwm_pins = {}
    
    async def initialize(self):
        logger.info("GPIO simulator initialized")
    
    async def cleanup(self):
        self.pins.clear()
        self.pwm_pins.clear()
        logger.info("GPIO simulator cleaned up")
    
    async def set(self, pin: int, value: int):
        """Simulate setting GPIO pin"""
        self.pins[pin] = value
        logger.info(f"[SIM] GPIO pin {pin} set to {value}")
    
    async def get(self, pin: int) -> int:
        """Simulate reading GPIO pin"""
        # Return stored value or random for unset pins
        value = self.pins.get(pin, random.randint(0, 1))
        logger.info(f"[SIM] GPIO pin {pin} read: {value}")
        return value
    
    async def pwm(self, pin: int, frequency: float, duty_cycle: float):
        """Simulate PWM on GPIO pin"""
        self.pwm_pins[pin] = {'freq': frequency, 'duty': duty_cycle}
        logger.info(f"[SIM] PWM on pin {pin}: {frequency}Hz @ {duty_cycle}%")


# === I2C Interface ===

class I2CInterface(HardwareInterface):
    """Real I2C interface using smbus2"""
    
    def __init__(self, bus: int = 1):
        super().__init__()
        self.bus_num = bus
        self.bus = None
    
    async def initialize(self):
        """Initialize I2C bus"""
        try:
            import smbus2
            self.bus = smbus2.SMBus(self.bus_num)
            logger.info(f"I2C interface initialized on bus {self.bus_num}")
        except ImportError as e:
            logger.error(f"smbus2 not available: {e}")
            raise ImportError("smbus2 required for I2C operations")
    
    async def cleanup(self):
        """Clean up I2C resources"""
        if self.bus:
            self.bus.close()
            logger.info("I2C interface cleaned up")
    
    async def scan(self) -> List[int]:
        """Scan I2C bus for devices"""
        devices = []
        for addr in range(0x03, 0x78):  # Valid I2C address range
            try:
                self.bus.read_byte(addr)
                devices.append(addr)
            except OSError:
                pass  # Device not present
        
        logger.debug(f"I2C scan found devices: {[hex(d) for d in devices]}")
        return devices
    
    async def read(self, device: int, register: int, length: int = 1) -> bytes:
        """Read from I2C device register"""
        try:
            if length == 1:
                data = [self.bus.read_byte_data(device, register)]
            else:
                data = self.bus.read_i2c_block_data(device, register, length)
            
            result = bytes(data)
            logger.debug(f"I2C read from {hex(device)}:{hex(register)}: {result.hex()}")
            return result
        except OSError as e:
            logger.error(f"I2C read error: {e}")
            raise
    
    async def write(self, device: int, register: int, data: bytes):
        """Write to I2C device register"""
        try:
            if len(data) == 1:
                self.bus.write_byte_data(device, register, data[0])
            else:
                self.bus.write_i2c_block_data(device, register, list(data))
            
            logger.debug(f"I2C write to {hex(device)}:{hex(register)}: {data.hex()}")
        except OSError as e:
            logger.error(f"I2C write error: {e}")
            raise


class I2CSimulator(HardwareInterface):
    """I2C simulator with common device emulation"""
    
    def __init__(self):
        super().__init__()
        self.is_simulator = True
        self.devices = {
            0x76: "BME280",      # Temperature/Humidity/Pressure sensor
            0x48: "ADS1115",     # ADC
            0x20: "PCF8574",     # GPIO expander
            0x68: "DS3231",      # RTC
            0x3C: "SSD1306",     # OLED display
        }
        self.memory = {}
    
    async def initialize(self):
        logger.info("I2C simulator initialized with virtual devices")
        for addr, name in self.devices.items():
            logger.info(f"  - {hex(addr)}: {name}")
    
    async def cleanup(self):
        self.memory.clear()
        logger.info("I2C simulator cleaned up")
    
    async def scan(self) -> List[int]:
        """Return list of simulated devices"""
        devices = list(self.devices.keys())
        logger.info(f"[SIM] I2C scan found devices: {[hex(d) for d in devices]}")
        return devices
    
    async def read(self, device: int, register: int, length: int = 1) -> bytes:
        """Simulate reading from I2C device"""
        if device not in self.devices:
            raise OSError(f"Device {hex(device)} not found")
        
        # Generate realistic data based on device type
        data = self._generate_device_data(device, register, length)
        
        logger.debug(f"[SIM] I2C read from {hex(device)}:{hex(register)}: {data.hex()}")
        return data
    
    async def write(self, device: int, register: int, data: bytes):
        """Simulate writing to I2C device"""
        if device not in self.devices:
            raise OSError(f"Device {hex(device)} not found")
        
        key = f"{device:02x}:{register:02x}"
        self.memory[key] = data
        
        logger.debug(f"[SIM] I2C write to {hex(device)}:{hex(register)}: {data.hex()}")
    
    def _generate_device_data(self, device: int, register: int, length: int) -> bytes:
        """Generate realistic data for different device types"""
        device_name = self.devices.get(device, "Unknown")
        
        if device == 0x76:  # BME280
            if register == 0xD0:  # Chip ID
                return b'\x60'
            elif register == 0xF7:  # Pressure data
                return bytes([0x80, 0x00, 0x00] + [0] * (length - 3))
        
        elif device == 0x48:  # ADS1115
            if register == 0x00:  # Conversion register
                # Simulate ADC reading
                value = random.randint(0, 32767)
                return value.to_bytes(2, 'big')
        
        elif device == 0x68:  # DS3231 RTC
            if register == 0x00:  # Time registers
                # Return current time in BCD format
                now = time.localtime()
                return bytes([
                    self._dec_to_bcd(now.tm_sec),
                    self._dec_to_bcd(now.tm_min),
                    self._dec_to_bcd(now.tm_hour)
                ][:length])
        
        # Default: return random data
        return bytes([random.randint(0, 255) for _ in range(length)])
    
    def _dec_to_bcd(self, decimal: int) -> int:
        """Convert decimal to BCD (Binary Coded Decimal)"""
        return ((decimal // 10) << 4) + (decimal % 10)


# === SPI Interface ===

class SPIInterface(HardwareInterface):
    """Real SPI interface using spidev"""
    
    def __init__(self):
        super().__init__()
        self.spi = None
        self.connections = {}
    
    async def initialize(self):
        """Initialize SPI"""
        try:
            import spidev
            self.spidev = spidev
            logger.info("SPI interface initialized")
        except ImportError as e:
            logger.error(f"spidev not available: {e}")
            raise ImportError("spidev required for SPI operations")
    
    async def cleanup(self):
        """Clean up SPI connections"""
        for spi in self.connections.values():
            spi.close()
        self.connections.clear()
        logger.info("SPI interface cleaned up")
    
    async def transfer(self, data: bytes, bus: int = 0, device: int = 0) -> bytes:
        """Transfer data via SPI"""
        key = f"{bus}:{device}"
        
        if key not in self.connections:
            spi = self.spidev.SpiDev()
            spi.open(bus, device)
            spi.max_speed_hz = 1000000  # 1MHz default
            self.connections[key] = spi
        
        spi = self.connections[key]
        result = spi.xfer2(list(data))
        
        response = bytes(result)
        logger.debug(f"SPI transfer on {bus}:{device}: {data.hex()} -> {response.hex()}")
        return response


class SPISimulator(HardwareInterface):
    """SPI simulator for development"""
    
    def __init__(self):
        super().__init__()
        self.is_simulator = True
        self.devices = {}
    
    async def initialize(self):
        logger.info("SPI simulator initialized")
    
    async def cleanup(self):
        self.devices.clear()
        logger.info("SPI simulator cleaned up")
    
    async def transfer(self, data: bytes, bus: int = 0, device: int = 0) -> bytes:
        """Simulate SPI transfer"""
        # Echo back the data with some modifications (typical for SPI devices)
        response = bytes([(b ^ 0xFF) & 0xFF for b in data])
        
        logger.info(f"[SIM] SPI transfer on {bus}:{device}: {data.hex()} -> {response.hex()}")
        return response


# === UART Interface ===

class UARTInterface(HardwareInterface):
    """Real UART interface using pyserial"""
    
    def __init__(self):
        super().__init__()
        self.connections = {}
    
    async def initialize(self):
        """Initialize UART (serial) interface"""
        try:
            import serial
            self.serial = serial
            logger.info("UART interface initialized")
        except ImportError as e:
            logger.error(f"pyserial not available: {e}")
            raise ImportError("pyserial required for UART operations")
    
    async def cleanup(self):
        """Clean up UART connections"""
        for ser in self.connections.values():
            ser.close()
        self.connections.clear()
        logger.info("UART interface cleaned up")
    
    async def write(self, port: str, data: bytes, baudrate: int = 9600):
        """Write data to UART port"""
        if port not in self.connections:
            ser = self.serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1.0
            )
            self.connections[port] = ser
        
        ser = self.connections[port]
        bytes_written = ser.write(data)
        
        logger.debug(f"UART write to {port}: {data.hex()} ({bytes_written} bytes)")
    
    async def read(self, port: str, length: int = 1, baudrate: int = 9600) -> bytes:
        """Read data from UART port"""
        if port not in self.connections:
            ser = self.serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1.0
            )
            self.connections[port] = ser
        
        ser = self.connections[port]
        data = ser.read(length)
        
        logger.debug(f"UART read from {port}: {data.hex()} ({len(data)} bytes)")
        return data


class UARTSimulator(HardwareInterface):
    """UART simulator with loopback functionality"""
    
    def __init__(self):
        super().__init__()
        self.is_simulator = True
        self.buffers = {}  # port -> circular buffer
    
    async def initialize(self):
        logger.info("UART simulator initialized")
    
    async def cleanup(self):
        self.buffers.clear()
        logger.info("UART simulator cleaned up")
    
    async def write(self, port: str, data: bytes, baudrate: int = 9600):
        """Simulate writing to UART port (loopback)"""
        if port not in self.buffers:
            self.buffers[port] = bytearray()
        
        # Add to buffer for loopback
        self.buffers[port].extend(data)
        
        logger.info(f"[SIM] UART write to {port}: {data.hex()} @ {baudrate} baud")
    
    async def read(self, port: str, length: int = 1, baudrate: int = 9600) -> bytes:
        """Simulate reading from UART port (loopback)"""
        if port not in self.buffers:
            self.buffers[port] = bytearray()
        
        buffer = self.buffers[port]
        
        if len(buffer) >= length:
            # Return data from buffer
            data = bytes(buffer[:length])
            del buffer[:length]
        else:
            # Generate some random data if buffer is empty
            data = bytes([random.randint(0, 255) for _ in range(length)])
        
        logger.info(f"[SIM] UART read from {port}: {data.hex()} @ {baudrate} baud")
        return data


# === Hardware Detection and Factory Functions ===

def detect_hardware_platform() -> str:
    """Detect the current hardware platform"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read().lower()
            if 'raspberry pi' in cpuinfo:
                return 'raspberry_pi'
            elif 'nvidia tegra' in cpuinfo:
                return 'nvidia_jetson'
    except (FileNotFoundError, PermissionError):
        pass
    
    import platform
    system = platform.system().lower()
    
    if system == 'linux':
        return 'linux_pc'
    elif system == 'windows':
        return 'windows_pc'
    elif system == 'darwin':
        return 'macos'
    
    return 'unknown'


def create_gpio_interface() -> Union[GPIOInterface, GPIOSimulator]:
    """Create appropriate GPIO interface based on platform"""
    platform = detect_hardware_platform()
    
    if platform == 'raspberry_pi':
        try:
            return GPIOInterface()
        except ImportError:
            logger.warning("RPi.GPIO not available, falling back to simulator")
            return GPIOSimulator()
    else:
        logger.info(f"Platform {platform} detected, using GPIO simulator")
        return GPIOSimulator()


def create_i2c_interface(bus: int = 1) -> Union[I2CInterface, I2CSimulator]:
    """Create appropriate I2C interface based on platform"""
    platform = detect_hardware_platform()
    
    if platform in ['raspberry_pi', 'nvidia_jetson', 'linux_pc']:
        try:
            return I2CInterface(bus)
        except ImportError:
            logger.warning("smbus2 not available, falling back to simulator")
            return I2CSimulator()
    else:
        logger.info(f"Platform {platform} detected, using I2C simulator")
        return I2CSimulator()


def create_spi_interface() -> Union[SPIInterface, SPISimulator]:
    """Create appropriate SPI interface based on platform"""
    platform = detect_hardware_platform()
    
    if platform in ['raspberry_pi', 'nvidia_jetson', 'linux_pc']:
        try:
            return SPIInterface()
        except ImportError:
            logger.warning("spidev not available, falling back to simulator")
            return SPISimulator()
    else:
        logger.info(f"Platform {platform} detected, using SPI simulator")
        return SPISimulator()


def create_uart_interface() -> Union[UARTInterface, UARTSimulator]:
    """Create appropriate UART interface based on platform"""
    try:
        return UARTInterface()
    except ImportError:
        logger.warning("pyserial not available, falling back to simulator")
        return UARTSimulator()
