"""
EDPMT SPI Hardware Interface using spidev
=========================================
This module provides a concrete implementation of the SPI hardware interface
using the spidev library for real SPI communication on Linux systems.
"""

import logging
from typing import Dict, Optional

try:
    import spidev
except ImportError:
    spidev = None

from .interfaces import SPIHardwareInterface

logger = logging.getLogger(__name__)


class SpidevSPIInterface(SPIHardwareInterface):
    """SPI Hardware Interface implementation using spidev for Linux systems."""

    def __init__(self, name: str = "Spidev-SPI", config: Optional[Dict] = None):
        super().__init__(name, config)
        self.spidev = spidev
        self.connections = {}

    async def initialize(self) -> bool:
        """Initialize the SPI interface using spidev."""
        if self.spidev is None:
            logger.error("spidev library not available")
            return False

        try:
            logger.info("SPI interface initialized")
            self.is_initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize SPI: {e}")
            self.is_initialized = False
            return False

    async def cleanup(self) -> None:
        """Clean up SPI resources."""
        if self.is_initialized:
            for spi in self.connections.values():
                try:
                    spi.close()
                except Exception as e:
                    logger.warning(f"Error closing SPI connection: {e}")
            self.connections.clear()
            logger.info("SPI interface cleaned up")
            self.is_initialized = False

    async def transfer(self, data: bytes, bus: int = 0, device: int = 0) -> bytes:
        """Transfer data over SPI."""
        if not self.is_initialized:
            logger.error("SPI interface not initialized")
            return b''

        connection_key = (bus, device)
        if connection_key not in self.connections:
            try:
                spi = self.spidev.SpiDev()
                spi.open(bus, device)
                spi.max_speed_hz = 1000000  # 1MHz default
                spi.mode = 0  # Default mode
                self.connections[connection_key] = spi
            except Exception as e:
                logger.error(f"Failed to open SPI connection on bus {bus}, device {device}: {e}")
                return b''

        try:
            spi = self.connections[connection_key]
            response = spi.xfer2(list(data))
            result = bytes(response)
            logger.debug(f"SPI transfer on bus {bus}, device {device}: {data.hex()} -> {result.hex()}")
            return result
        except Exception as e:
            logger.error(f"Error during SPI transfer on bus {bus}, device {device}: {e}")
            return b''

    async def configure(self, bus: int = 0, device: int = 0, mode: int = 0, speed: int = 1000000) -> bool:
        """Configure SPI settings."""
        if not self.is_initialized:
            logger.error("SPI interface not initialized")
            return False

        connection_key = (bus, device)
        if connection_key not in self.connections:
            try:
                spi = self.spidev.SpiDev()
                spi.open(bus, device)
                self.connections[connection_key] = spi
            except Exception as e:
                logger.error(f"Failed to open SPI connection on bus {bus}, device {device}: {e}")
                return False

        try:
            spi = self.connections[connection_key]
            spi.max_speed_hz = speed
            spi.mode = mode
            logger.info(f"SPI configured on bus {bus}, device {device}: mode {mode}, speed {speed}Hz")
            return True
        except Exception as e:
            logger.error(f"Error configuring SPI on bus {bus}, device {device}: {e}")
            return False

    def is_supported(self) -> bool:
        """Check if spidev is supported on the current platform."""
        return self.spidev is not None
