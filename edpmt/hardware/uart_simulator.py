"""
EDPMT UART Hardware Interface Simulator
=======================================
This module provides a simulated implementation of the UART hardware interface
for testing and development purposes when real hardware is not available.
"""

import logging
from typing import Dict, Optional

from .interfaces import UARTHardwareInterface

logger = logging.getLogger(__name__)


class SimulatedUARTInterface(UARTHardwareInterface):
    """Simulated UART Hardware Interface with loopback functionality."""

    def __init__(self, name: str = "Simulated-UART", config: Optional[Dict] = None):
        super().__init__(name, config)
        self.buffers = {}  # port -> circular buffer

    async def initialize(self) -> bool:
        """Initialize the simulated UART interface."""
        self.buffers.clear()
        self.is_initialized = True
        logger.info("UART simulator initialized")
        return True

    async def cleanup(self) -> None:
        """Clean up simulated UART resources."""
        self.buffers.clear()
        self.is_initialized = False
        logger.info("UART simulator cleaned up")

    async def write(self, port: str, data: bytes, baudrate: int = 9600) -> bool:
        """Simulate writing to a UART port (loopback)."""
        if not self.is_initialized:
            logger.error("UART simulator not initialized")
            return False

        if port not in self.buffers:
            self.buffers[port] = bytearray()

        self.buffers[port].extend(data)
        # Limit buffer to 4096 bytes
        if len(self.buffers[port]) > 4096:
            self.buffers[port] = self.buffers[port][-4096:]

        logger.info(f"[SIM] UART write to port {port}: {data.hex()}")
        return True

    async def read(self, port: str, length: int = 1024, baudrate: int = 9600, timeout: float = 1.0) -> bytes:
        """Simulate reading from a UART port (loopback)."""
        if not self.is_initialized:
            logger.error("UART simulator not initialized")
            return b''

        if port not in self.buffers or len(self.buffers[port]) == 0:
            logger.info(f"[SIM] UART read from port {port}: no data")
            return b''

        # Read up to 'length' bytes from buffer
        data = bytes(self.buffers[port][:length])
        self.buffers[port] = self.buffers[port][len(data):]
        logger.info(f"[SIM] UART read from port {port}: {data.hex()}")
        return data
