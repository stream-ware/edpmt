"""
EDPMT I2C Hardware Interface Simulator
======================================
This module provides a simulated implementation of the I2C hardware interface
for testing and development purposes when real hardware is not available.
"""

import logging
import random
from typing import Dict, List, Optional

from .interfaces import I2CHardwareInterface

logger = logging.getLogger(__name__)


class SimulatedI2CInterface(I2CHardwareInterface):
    """Simulated I2C Hardware Interface with common device emulation."""

    def __init__(self, name: str = "Simulated-I2C", config: Optional[Dict] = None):
        super().__init__(name, config)
        self.devices = {
            0x76: "BME280",  # Temperature/Humidity/Pressure sensor
            0x48: "ADS1115", # ADC
            0x20: "PCF8574", # GPIO expander
            0x68: "DS3231",  # RTC
            0x3C: "SSD1306", # OLED display
        }
        self.memory = {}

    async def initialize(self) -> bool:
        """Initialize the simulated I2C interface with virtual devices."""
        self.memory.clear()
        self.is_initialized = True
        logger.info("I2C simulator initialized with virtual devices")
        for addr, name in self.devices.items():
            logger.info(f"  - {hex(addr)}: {name}")
        return True

    async def cleanup(self) -> None:
        """Clean up simulated I2C resources."""
        self.memory.clear()
        self.is_initialized = False
        logger.info("I2C simulator cleaned up")

    async def scan(self, bus: int = 1) -> List[int]:
        """Return list of simulated devices."""
        if not self.is_initialized:
            logger.error("I2C simulator not initialized")
            return []

        devices = list(self.devices.keys())
        logger.info(f"[SIM] I2C scan on bus {bus} found devices: {[hex(d) for d in devices]}")
        return devices

    async def read(self, device: int, register: int, length: int = 1, bus: int = 1) -> bytes:
        """Simulate reading from an I2C device."""
        if not self.is_initialized:
            logger.error("I2C simulator not initialized")
            return b''

        if device not in self.devices:
            logger.error(f"[SIM] I2C device {hex(device)} not found")
            return b''

        data = self._generate_device_data(device, register, length)
        logger.info(f"[SIM] I2C read from device {hex(device)}, register {hex(register)}: {data.hex()}")
        return data

    async def write(self, device: int, data: bytes, bus: int = 1) -> bool:
        """Simulate writing to an I2C device."""
        if not self.is_initialized:
            logger.error("I2C simulator not initialized")
            return False

        if device not in self.devices:
            logger.error(f"[SIM] I2C device {hex(device)} not found")
            return False

        if len(data) < 1:
            logger.error(f"[SIM] I2C write to device {hex(device)} with empty data")
            return False

        register = data[0]
        value = data[1:] if len(data) > 1 else b''
        if device not in self.memory:
            self.memory[device] = {}
        self.memory[device][register] = value
        logger.info(f"[SIM] I2C write to device {hex(device)}, register {hex(register)}: {value.hex() if value else 'empty'}")
        return True

    def _generate_device_data(self, device: int, register: int, length: int) -> bytes:
        """Generate realistic data for different device types."""
        device_name = self.devices.get(device, "Unknown")
        if device in self.memory and register in self.memory[device]:
            stored = self.memory[device][register]
            if len(stored) >= length:
                return stored[:length]

        if device_name == "BME280":  # Temperature/Humidity/Pressure sensor
            if register == 0xF7:  # Pressure
                return bytes([0x5A, 0xF0, 0x00][:length])
            elif register == 0xFA:  # Temperature
                return bytes([0x08, 0x8E, 0x00][:length])
            elif register == 0xFD:  # Humidity
                return bytes([0x2D][:length])
            else:
                return bytes([random.randint(0, 255) for _ in range(length)])
        elif device_name == "ADS1115":  # ADC
            return bytes([random.randint(0, 255) for _ in range(min(length, 2))])
        elif device_name == "DS3231":  # RTC
            if register == 0x00:  # Seconds
                return bytes([self._dec_to_bcd(int(time.time()) % 60)][:length])
            elif register == 0x01:  # Minutes
                return bytes([self._dec_to_bcd(int(time.time() / 60) % 60)][:length])
            elif register == 0x02:  # Hours
                return bytes([self._dec_to_bcd(int(time.time() / 3600) % 24)][:length])
            else:
                return bytes([random.randint(0, 255) for _ in range(length)])
        else:
            return bytes([random.randint(0, 255) for _ in range(length)])

    def _dec_to_bcd(self, decimal: int) -> int:
        """Convert decimal to BCD (Binary Coded Decimal)."""
        return ((decimal // 10) << 4) | (decimal % 10)
