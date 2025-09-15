"""
EDPMT USB Hardware Interface using pyusb
========================================
This module provides a concrete implementation of the USB hardware interface
using the pyusb library for real USB communication.
"""

import logging
from typing import Dict, List, Optional

try:
    import usb.core
    import usb.util
except ImportError:
    usb = None
else:
    usb = type('usb', (), {'core': usb.core, 'util': usb.util})

from .interfaces import USBHardwareInterface

logger = logging.getLogger(__name__)


class PyUSBInterface(USBHardwareInterface):
    """USB Hardware Interface implementation using pyusb."""

    def __init__(self, name: str = "PyUSB-USB", config: Optional[Dict] = None):
        super().__init__(name, config)
        self.usb = usb
        self.connected_devices = {}

    async def initialize(self) -> bool:
        """Initialize the USB interface using pyusb."""
        if self.usb is None:
            logger.error("pyusb library not available")
            return False

        try:
            logger.info("USB interface initialized")
            self.is_initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize USB: {e}")
            self.is_initialized = False
            return False

    async def cleanup(self) -> None:
        """Clean up USB resources."""
        if self.is_initialized:
            for device_id, device in list(self.connected_devices.items()):
                try:
                    self.usb.util.dispose_resources(device)
                    logger.info(f"USB device {device_id} disconnected")
                except Exception as e:
                    logger.warning(f"Error disconnecting USB device {device_id}: {e}")
            self.connected_devices.clear()
            logger.info("USB interface cleaned up")
            self.is_initialized = False

    async def list_devices(self) -> List[Dict[str, Any]]:
        """List connected USB devices."""
        if not self.is_initialized:
            logger.error("USB interface not initialized")
            return []

        try:
            devices = self.usb.core.find(find_all=True)
            device_list = []
            for dev in devices:
                try:
                    device_info = {
                        'id': f"{dev.idVendor:04x}:{dev.idProduct:04x}",
                        'vendor_id': dev.idVendor,
                        'product_id': dev.idProduct,
                        'manufacturer': usb.util.get_string(dev, dev.iManufacturer) or "Unknown",
                        'product': usb.util.get_string(dev, dev.iProduct) or "Unknown",
                        'serial': usb.util.get_string(dev, dev.iSerialNumber) or "N/A"
                    }
                    device_list.append(device_info)
                except Exception as e:
                    logger.warning(f"Error getting info for USB device: {e}")
                    continue
            logger.debug(f"Found {len(device_list)} USB devices")
            return device_list
        except Exception as e:
            logger.error(f"Error listing USB devices: {e}")
            return []

    async def connect(self, device_id: str) -> bool:
        """Connect to a specific USB device."""
        if not self.is_initialized:
            logger.error("USB interface not initialized")
            return False

        if device_id in self.connected_devices:
            logger.info(f"USB device {device_id} already connected")
            return True

        try:
            # Parse vendor_id and product_id from device_id (format: "vendor:product")
            vendor_id, product_id = map(lambda x: int(x, 16), device_id.split(':'))
            dev = self.usb.core.find(idVendor=vendor_id, idProduct=product_id)
            if dev is None:
                logger.error(f"USB device {device_id} not found")
                return False

            # Set configuration
            dev.set_configuration()
            self.connected_devices[device_id] = dev
            logger.info(f"Connected to USB device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to USB device {device_id}: {e}")
            return False

    async def disconnect(self, device_id: str) -> bool:
        """Disconnect from a specific USB device."""
        if not self.is_initialized:
            logger.error("USB interface not initialized")
            return False

        if device_id not in self.connected_devices:
            logger.warning(f"USB device {device_id} not connected")
            return False

        try:
            dev = self.connected_devices.pop(device_id)
            self.usb.util.dispose_resources(dev)
            logger.info(f"Disconnected from USB device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from USB device {device_id}: {e}")
            return False

    async def send_data(self, device_id: str, data: bytes) -> bool:
        """Send data to a USB device."""
        if not self.is_initialized:
            logger.error("USB interface not initialized")
            return False

        if device_id not in self.connected_devices:
            logger.error(f"USB device {device_id} not connected")
            return False

        try:
            dev = self.connected_devices[device_id]
            # Find the first OUT endpoint
            cfg = dev.get_active_configuration()
            intf = cfg[(0, 0)]
            ep_out = self.usb.util.find_descriptor(intf, custom_match=lambda e: self.usb.util.endpoint_direction(e.bEndpointAddress) == self.usb.util.ENDPOINT_OUT)
            if ep_out is None:
                logger.error(f"No OUT endpoint found for USB device {device_id}")
                return False

            ep_out.write(data)
            logger.debug(f"USB data sent to {device_id}: {data.hex()}")
            return True
        except Exception as e:
            logger.error(f"Error sending data to USB device {device_id}: {e}")
            return False

    async def receive_data(self, device_id: str, length: int = 1024, timeout: float = 1.0) -> bytes:
        """Receive data from a USB device."""
        if not self.is_initialized:
            logger.error("USB interface not initialized")
            return b''

        if device_id not in self.connected_devices:
            logger.error(f"USB device {device_id} not connected")
            return b''

        try:
            dev = self.connected_devices[device_id]
            # Find the first IN endpoint
            cfg = dev.get_active_configuration()
            intf = cfg[(0, 0)]
            ep_in = self.usb.util.find_descriptor(intf, custom_match=lambda e: self.usb.util.endpoint_direction(e.bEndpointAddress) == self.usb.util.ENDPOINT_IN)
            if ep_in is None:
                logger.error(f"No IN endpoint found for USB device {device_id}")
                return b''

            data = ep_in.read(length, timeout=int(timeout * 1000))
            result = bytes(data)
            logger.debug(f"USB data received from {device_id}: {result.hex()}")
            return result
        except Exception as e:
            logger.error(f"Error receiving data from USB device {device_id}: {e}")
            return b''

    def is_supported(self) -> bool:
        """Check if pyusb is supported on the current platform."""
        return self.usb is not None
