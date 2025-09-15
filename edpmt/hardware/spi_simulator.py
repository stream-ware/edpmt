"""
EDPMT SPI Hardware Interface Simulator
======================================
This module provides a simulated implementation of the SPI hardware interface
for testing and development purposes when real hardware is not available.
"""

import logging
from typing import Dict, Optional

from .interfaces import SPIHardwareInterface

logger = logging.getLogger(__name__)


class SimulatedSPIInterface(SPIHardwareInterface):
    """Simulated SPI Hardware Interface for testing without real hardware."""

    def __init__(self, name: str = "Simulated-SPI", config: Optional[Dict] = None):
        super().__init__(name, config)
        self.devices = {}

    async def initialize(self) -> bool:
        """Initialize the simulated SPI interface."""
        self.devices.clear()
        self.is_initialized = True
        logger.info("SPI simulator initialized")
        return True

    async def cleanup(self) -> None:
        """Clean up simulated SPI resources."""
        self.devices.clear()
        self.is_initialized = False
        logger.info("SPI simulator cleaned up")

    async def transfer(self, data: bytes, bus: int = 0, device: int = 0) -> bytes:
        """Simulate SPI transfer."""
        if not self.is_initialized:
            logger.error("SPI simulator not initialized")
            return b''

        # Echo back the data with some modifications (typical for SPI devices)
        response = bytes([(b ^ 0xFF) & 0xFF for b in data])
        logger.info(f"[SIM] SPI transfer on bus {bus}, device {device}: {data.hex()} -> {response.hex()}")
        return response

    async def configure(self, bus: int = 0, device: int = 0, mode: int = 0, speed: int = 1000000) -> bool:
        """Simulate configuring SPI settings."""
        if not self.is_initialized:
            logger.error("SPI simulator not initialized")
            return False

        logger.info(f"[SIM] SPI configured on bus {bus}, device {device}: mode {mode}, speed {speed}Hz")
        return True
