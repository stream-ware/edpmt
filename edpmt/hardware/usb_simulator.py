"""
EDPMT USB Hardware Interface Simulator
======================================
This module provides a simulated implementation of the USB hardware interface
for testing and development purposes when real hardware is not available.
"""

import logging
import random
from typing import Dict, List, Optional

from .interfaces import USBHardwareInterface

logger = logging.getLogger(__name__)


class SimulatedUSBInterface(USBHardwareInterface):
    """Simulated USB Hardware Interface for testing without real hardware."""

    def __init__(self, name: str = "Simulated-USB", config: Optional[Dict] = None):
        super().__init__(name, config)
        self.simulated_devices = [
            {'id': '04B4:6500', 'vendor_id': 0x04B4, 'product_id': 0x6500, 'manufacturer': 'Cypress', 'product': 'USB Keyboard', 'serial': 'SN123456'},
            {'id': '046D:C077', 'vendor_id': 0x046D, 'product_id': 0xC077, 'manufacturer': 'Logitech', 'product': 'USB Mouse', 'serial': 'SN789012'},
            {'id': '0781:5567', 'vendor_id': 0x0781, 'product_id': 0x5567, 'manufacturer': 'SanDisk', 'product': 'USB Flash Drive', 'serial': 'SN345678'}
        ]
        self.device_buffers = {}

    async def initialize(self) -> bool:
        """Initialize the simulated USB interface."""
        self.device_buffers.clear()
        self.is_initialized = True
        logger.info("USB simulator initialized")
        return True

    async def cleanup(self) -> None:
        """Clean up simulated USB resources."""
        self.device_buffers.clear()
        self.connected_devices.clear()
        self.is_initialized = False
        logger.info("USB simulator cleaned up")

    async def list_devices(self) -> List[Dict[str, Any]]:
        """List simulated USB devices."""
        if not self.is_initialized:
            logger.error("USB simulator not initialized")
            return []

        logger.info(f"[SIM] USB scan found {len(self.simulated_devices)} devices")
        return self.simulated_devices

    async def connect(self, device_id: str) -> bool:
        """Simulate connecting to a USB device."""
        if not self.is_initialized:
            logger.error("USB simulator not initialized")
            return False

        if any(dev['id'] == device_id for dev in self.simulated_devices):
            self.connected_devices[device_id] = None  # No real device object in simulation
            if device_id not in self.device_buffers:
                self.device_buffers[device_id] = bytearray()
            logger.info(f"[SIM] Connected to USB device {device_id}")
            return True
        else:
            logger.error(f"[SIM] USB device {device_id} not found")
            return False

    async def disconnect(self, device_id: str) -> bool:
        """Simulate disconnecting from a USB device."""
        if not self.is_initialized:
            logger.error("USB simulator not initialized")
            return False

        if device_id in self.connected_devices:
            del self.connected_devices[device_id]
            logger.info(f"[SIM] Disconnected from USB device {device_id}")
            return True
        else:
            logger.warning(f"[SIM] USB device {device_id} not connected")
            return False

    async def send_data(self, device_id: str, data: bytes) -> bool:
        """Simulate sending data to a USB device."""
        if not self.is_initialized:
            logger.error("USB simulator not initialized")
            return False

        if device_id not in self.connected_devices:
            logger.error(f"[SIM] USB device {device_id} not connected")
            return False

        if device_id not in self.device_buffers:
            self.device_buffers[device_id] = bytearray()

        self.device_buffers[device_id].extend(data)
        # Limit buffer to 4096 bytes
        if len(self.device_buffers[device_id]) > 4096:
            self.device_buffers[device_id] = self.device_buffers[device_id][-4096:]

        logger.info(f"[SIM] USB data sent to {device_id}: {data.hex()}")
        return True

    async def receive_data(self, device_id: str, length: int = 1024, timeout: float = 1.0) -> bytes:
        """Simulate receiving data from a USB device."""
        if not self.is_initialized:
            logger.error("USB simulator not initialized")
            return b''

        if device_id not in self.connected_devices:
            logger.error(f"[SIM] USB device {device_id} not connected")
            return b''

        if device_id not in self.device_buffers or len(self.device_buffers[device_id]) == 0:
            # If no data is in buffer, simulate a simple response or empty read
            logger.info(f"[SIM] USB read from {device_id}: no data, returning empty")
            return b''

        # Read up to 'length' bytes from buffer
        data = bytes(self.device_buffers[device_id][:length])
        self.device_buffers[device_id] = self.device_buffers[device_id][len(data):]
        logger.info(f"[SIM] USB data received from {device_id}: {data.hex()}")
        return data
