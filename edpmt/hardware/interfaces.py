"""
EDPMT Hardware Interface Abstraction Layer
==========================================
This module defines the abstract base classes and interfaces for hardware
abstraction in EDPMT. It allows for pluggable hardware implementations that
can be initialized at runtime, making EDPMT hardware-agnostic.
"""

from abc import ABC, abstractmethod
import asyncio
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HardwareInterface(ABC):
    """Abstract base class for all hardware interfaces in EDPMT."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.is_initialized = False

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the hardware interface.

        Returns:
            bool: True if initialization is successful, False otherwise.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources used by the hardware interface."""
        pass

    @abstractmethod
    async def execute(self, action: str, **params) -> Any:
        """Execute a specific action on the hardware.

        Args:
            action (str): The action to perform (e.g., 'set', 'get', 'read', 'write').
            **params: Additional parameters for the action.

        Returns:
            Any: The result of the action.
        """
        pass

    def is_supported(self) -> bool:
        """Check if the hardware interface is supported on the current platform.

        Returns:
            bool: True if supported, False otherwise.
        """
        return True


class GPIOHardwareInterface(HardwareInterface):
    """Abstract interface for GPIO hardware operations."""

    @abstractmethod
    async def set_pin(self, pin: int, value: int) -> bool:
        """Set a GPIO pin to a specific value.

        Args:
            pin (int): The GPIO pin number.
            value (int): The value to set (0 for LOW, 1 for HIGH).

        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    @abstractmethod
    async def get_pin(self, pin: int) -> int:
        """Read the value of a GPIO pin.

        Args:
            pin (int): The GPIO pin number.

        Returns:
            int: The value of the pin (0 or 1).
        """
        pass

    @abstractmethod
    async def pwm(self, pin: int, frequency: float, duty_cycle: float) -> bool:
        """Set PWM on a GPIO pin.

        Args:
            pin (int): The GPIO pin number.
            frequency (float): The frequency in Hz.
            duty_cycle (float): The duty cycle percentage (0-100).

        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    async def execute(self, action: str, **params) -> Any:
        """Execute GPIO-specific actions."""
        if action == 'set':
            return await self.set_pin(params.get('pin', 0), params.get('value', 0))
        elif action == 'get':
            return await self.get_pin(params.get('pin', 0))
        elif action == 'pwm':
            return await self.pwm(params.get('pin', 0), params.get('frequency', 0.0), params.get('duty_cycle', 0.0))
        else:
            raise ValueError(f"Unsupported GPIO action: {action}")


class I2CHardwareInterface(HardwareInterface):
    """Abstract interface for I2C hardware operations."""

    @abstractmethod
    async def scan(self, bus: int = 1) -> List[int]:
        """Scan the I2C bus for connected devices.

        Args:
            bus (int): The I2C bus number (default is 1).

        Returns:
            List[int]: List of device addresses found on the bus.
        """
        pass

    @abstractmethod
    async def read(self, device: int, register: int, length: int = 1, bus: int = 1) -> bytes:
        """Read data from an I2C device.

        Args:
            device (int): The I2C device address.
            register (int): The register to read from.
            length (int): Number of bytes to read (default is 1).
            bus (int): The I2C bus number (default is 1).

        Returns:
            bytes: Data read from the device.
        """
        pass

    @abstractmethod
    async def write(self, device: int, data: bytes, bus: int = 1) -> bool:
        """Write data to an I2C device.

        Args:
            device (int): The I2C device address.
            data (bytes): Data to write.
            bus (int): The I2C bus number (default is 1).

        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    async def execute(self, action: str, **params) -> Any:
        """Execute I2C-specific actions."""
        if action == 'scan':
            return await self.scan(params.get('bus', 1))
        elif action == 'read':
            return await self.read(params.get('device', 0), params.get('register', 0), params.get('length', 1), params.get('bus', 1))
        elif action == 'write':
            return await self.write(params.get('device', 0), params.get('data', b''), params.get('bus', 1))
        else:
            raise ValueError(f"Unsupported I2C action: {action}")


class SPIHardwareInterface(HardwareInterface):
    """Abstract interface for SPI hardware operations."""

    @abstractmethod
    async def transfer(self, data: bytes, bus: int = 0, device: int = 0) -> bytes:
        """Transfer data over SPI.

        Args:
            data (bytes): Data to send.
            bus (int): The SPI bus number (default is 0).
            device (int): The SPI device number (default is 0).

        Returns:
            bytes: Data received from the device.
        """
        pass

    @abstractmethod
    async def configure(self, bus: int = 0, device: int = 0, mode: int = 0, speed: int = 1000000) -> bool:
        """Configure SPI settings.

        Args:
            bus (int): The SPI bus number (default is 0).
            device (int): The SPI device number (default is 0).
            mode (int): SPI mode (0-3, default is 0).
            speed (int): SPI speed in Hz (default is 1MHz).

        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    async def execute(self, action: str, **params) -> Any:
        """Execute SPI-specific actions."""
        if action == 'transfer':
            return await self.transfer(params.get('data', b''), params.get('bus', 0), params.get('device', 0))
        elif action == 'configure':
            return await self.configure(params.get('bus', 0), params.get('device', 0), params.get('mode', 0), params.get('speed', 1000000))
        else:
            raise ValueError(f"Unsupported SPI action: {action}")


class UARTHardwareInterface(HardwareInterface):
    """Abstract interface for UART hardware operations."""

    @abstractmethod
    async def write(self, port: str, data: bytes, baudrate: int = 9600) -> bool:
        """Write data to a UART port.

        Args:
            port (str): The UART port (e.g., '/dev/ttyS0').
            data (bytes): Data to write.
            baudrate (int): Baud rate (default is 9600).

        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    @abstractmethod
    async def read(self, port: str, length: int = 1024, baudrate: int = 9600, timeout: float = 1.0) -> bytes:
        """Read data from a UART port.

        Args:
            port (str): The UART port (e.g., '/dev/ttyS0').
            length (int): Maximum number of bytes to read (default is 1024).
            baudrate (int): Baud rate (default is 9600).
            timeout (float): Read timeout in seconds (default is 1.0).

        Returns:
            bytes: Data read from the port.
        """
        pass

    async def execute(self, action: str, **params) -> Any:
        """Execute UART-specific actions."""
        if action == 'write':
            return await self.write(params.get('port', ''), params.get('data', b''), params.get('baudrate', 9600))
        elif action == 'read':
            return await self.read(params.get('port', ''), params.get('length', 1024), params.get('baudrate', 9600), params.get('timeout', 1.0))
        else:
            raise ValueError(f"Unsupported UART action: {action}")


class USBHardwareInterface(HardwareInterface):
    """Abstract interface for USB hardware operations."""

    @abstractmethod
    async def list_devices(self) -> List[Dict[str, Any]]:
        """List connected USB devices.

        Returns:
            List[Dict[str, Any]]: List of dictionaries containing device information.
        """
        pass

    @abstractmethod
    async def connect(self, device_id: str) -> bool:
        """Connect to a specific USB device.

        Args:
            device_id (str): The ID or serial number of the device.

        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    @abstractmethod
    async def disconnect(self, device_id: str) -> bool:
        """Disconnect from a specific USB device.

        Args:
            device_id (str): The ID or serial number of the device.

        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    @abstractmethod
    async def send_data(self, device_id: str, data: bytes) -> bool:
        """Send data to a USB device.

        Args:
            device_id (str): The ID or serial number of the device.
            data (bytes): Data to send.

        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    @abstractmethod
    async def receive_data(self, device_id: str, length: int = 1024, timeout: float = 1.0) -> bytes:
        """Receive data from a USB device.

        Args:
            device_id (str): The ID or serial number of the device.
            length (int): Maximum number of bytes to read (default is 1024).
            timeout (float): Read timeout in seconds (default is 1.0).

        Returns:
            bytes: Data received from the device.
        """
        pass

    async def execute(self, action: str, **params) -> Any:
        """Execute USB-specific actions."""
        if action == 'list':
            return await self.list_devices()
        elif action == 'connect':
            return await self.connect(params.get('device_id', ''))
        elif action == 'disconnect':
            return await self.disconnect(params.get('device_id', ''))
        elif action == 'send':
            return await self.send_data(params.get('device_id', ''), params.get('data', b''))
        elif action == 'receive':
            return await self.receive_data(params.get('device_id', ''), params.get('length', 1024), params.get('timeout', 1.0))
        else:
            raise ValueError(f"Unsupported USB action: {action}")


class I2SHardwareInterface(HardwareInterface):
    """Abstract interface for I2S (Inter-IC Sound) hardware operations."""

    @abstractmethod
    async def configure(self, sample_rate: int = 44100, bits_per_sample: int = 16, channels: int = 2) -> bool:
        """Configure I2S settings.

        Args:
            sample_rate (int): Sample rate in Hz (default is 44100).
            bits_per_sample (int): Bits per sample (default is 16).
            channels (int): Number of channels (default is 2 for stereo).

        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    @abstractmethod
    async def play(self, data: bytes) -> bool:
        """Play audio data over I2S.

        Args:
            data (bytes): Audio data to play.

        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    @abstractmethod
    async def record(self, duration: float) -> bytes:
        """Record audio data from I2S.

        Args:
            duration (float): Duration to record in seconds.

        Returns:
            bytes: Recorded audio data.
        """
        pass

    async def execute(self, action: str, **params) -> Any:
        """Execute I2S-specific actions."""
        if action == 'configure':
            return await self.configure(params.get('sample_rate', 44100), params.get('bits_per_sample', 16), params.get('channels', 2))
        elif action == 'play':
            return await self.play(params.get('data', b''))
        elif action == 'record':
            return await self.record(params.get('duration', 1.0))
        else:
            raise ValueError(f"Unsupported I2S action: {action}")
