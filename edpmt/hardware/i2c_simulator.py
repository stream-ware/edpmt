"""
EDPMT I2C Hardware Interface Simulator
======================================
This module provides a simulated implementation of the I2C hardware interface
for testing and development purposes when real hardware is not available.
"""

import logging
from typing import Dict, Any, List, Optional

from .interfaces import I2CInterface

logger = logging.getLogger(__name__)


class SimulatedI2C(I2CInterface):
    """Simulated I2C interface for testing without real hardware."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(name="Simulated I2C", config=config)
        self.logger = logging.getLogger(__name__)
        self.devices = {0x48: "Temperature Sensor", 0x76: "Pressure Sensor"}  # Simulated devices
        self.initialized = True
        self.logger.info("Simulated I2C interface created")

    async def initialize(self) -> bool:
        """Initialize the simulated I2C interface."""
        self.logger.info("Initializing simulated I2C interface")
        self.initialized = True
        return True

    async def cleanup(self) -> None:
        """Cleanup resources (none needed for simulator)."""
        self.logger.info("Cleaning up simulated I2C interface")
        self.initialized = False

    async def scan(self) -> List[int]:
        """Return a list of simulated device addresses on the I2C bus."""
        self.logger.info("Scanning simulated I2C bus")
        return list(self.devices.keys())

    async def read(self, device_address: int, register: Optional[int] = None, length: int = 1) -> bytes:
        """Read data from a simulated I2C device."""
        if device_address not in self.devices:
            raise ValueError(f"No device found at address {hex(device_address)}")
        self.logger.info(f"Reading {length} bytes from simulated I2C device at {hex(device_address)}")
        # Simulate some data based on device type
        if device_address == 0x48:  # Temperature sensor
            return bytes([25, 0])  # Simulate 25.0 degrees Celsius
        elif device_address == 0x76:  # Pressure sensor
            return bytes([101, 3, 0])  # Simulate 1013 hPa
        return bytes([0] * length)  # Default empty data

    async def write(self, device_address: int, data: bytes, register: Optional[int] = None) -> None:
        """Write data to a simulated I2C device."""
        if device_address not in self.devices:
            raise ValueError(f"No device found at address {hex(device_address)}")
        self.logger.info(f"Writing {len(data)} bytes to simulated I2C device at {hex(device_address)}")
        # No actual write operation needed for simulator

    async def execute(self, action: str, **params) -> Any:
        """Execute a command on the simulated I2C interface."""
        if action == "scan":
            return await self.scan()
        elif action == "read":
            return await self.read(params.get("device", 0), params.get("register"), params.get("length", 1))
        elif action == "write":
            await self.write(params.get("device", 0), params.get("data", b""), params.get("register"))
            return True
        else:
            raise ValueError(f"Unsupported action: {action}")
