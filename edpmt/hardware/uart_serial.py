"""
EDPMT UART Hardware Interface using pyserial
============================================
This module provides a concrete implementation of the UART hardware interface
using the pyserial library for real serial communication.
"""

import logging
from typing import Dict, Optional

try:
    import serial
except ImportError:
    serial = None

from .interfaces import UARTHardwareInterface

logger = logging.getLogger(__name__)


class SerialUARTInterface(UARTHardwareInterface):
    """UART Hardware Interface implementation using pyserial."""

    def __init__(self, name: str = "Serial-UART", config: Optional[Dict] = None):
        super().__init__(name, config)
        self.serial = serial
        self.connections = {}

    async def initialize(self) -> bool:
        """Initialize the UART interface using pyserial."""
        if self.serial is None:
            logger.error("pyserial library not available")
            return False

        try:
            logger.info("UART interface initialized")
            self.is_initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize UART: {e}")
            self.is_initialized = False
            return False

    async def cleanup(self) -> None:
        """Clean up UART resources."""
        if self.is_initialized:
            for ser in self.connections.values():
                try:
                    ser.close()
                except Exception as e:
                    logger.warning(f"Error closing UART connection: {e}")
            self.connections.clear()
            logger.info("UART interface cleaned up")
            self.is_initialized = False

    async def write(self, port: str, data: bytes, baudrate: int = 9600) -> bool:
        """Write data to a UART port."""
        if not self.is_initialized:
            logger.error("UART interface not initialized")
            return False

        if port not in self.connections:
            try:
                ser = self.serial.Serial(port, baudrate, timeout=1)
                self.connections[port] = ser
            except Exception as e:
                logger.error(f"Failed to open UART port {port}: {e}")
                return False

        try:
            ser = self.connections[port]
            ser.write(data)
            logger.debug(f"UART write to port {port}: {data.hex()}")
            return True
        except Exception as e:
            logger.error(f"Error writing to UART port {port}: {e}")
            return False

    async def read(self, port: str, length: int = 1024, baudrate: int = 9600, timeout: float = 1.0) -> bytes:
        """Read data from a UART port."""
        if not self.is_initialized:
            logger.error("UART interface not initialized")
            return b''

        if port not in self.connections:
            try:
                ser = self.serial.Serial(port, baudrate, timeout=timeout)
                self.connections[port] = ser
            except Exception as e:
                logger.error(f"Failed to open UART port {port}: {e}")
                return b''

        try:
            ser = self.connections[port]
            data = ser.read(length)
            logger.debug(f"UART read from port {port}: {data.hex()}")
            return data
        except Exception as e:
            logger.error(f"Error reading from UART port {port}: {e}")
            return b''

    def is_supported(self) -> bool:
        """Check if pyserial is supported on the current platform."""
        return self.serial is not None
