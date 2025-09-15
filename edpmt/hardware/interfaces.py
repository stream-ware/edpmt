"""
EDPMT Hardware Interface Abstraction Layer
==========================================
This module defines the abstract base classes and interfaces for hardware
abstraction in EDPMT. It allows for pluggable hardware implementations that
can be initialized at runtime, making EDPMT hardware-agnostic.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class HardwareInterface(ABC):
    """Abstract base class for all hardware interfaces."""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.initialized = False

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the hardware interface."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources used by the hardware interface."""
        pass

    @abstractmethod
    async def execute(self, action: str, **params) -> Any:
        """Execute a command on the hardware."""
        pass


class GPIOInterface(HardwareInterface):
    """Abstract base class for GPIO interfaces."""

    @abstractmethod
    async def set_pin(self, pin: int, value: bool) -> None:
        """Set the value of a GPIO pin."""
        pass

    @abstractmethod
    async def get_pin(self, pin: int) -> bool:
        """Get the value of a GPIO pin."""
        pass

    @abstractmethod
    async def configure_pin(self, pin: int, mode: str) -> None:
        """Configure the mode of a GPIO pin (input/output)."""
        pass


class I2CInterface(HardwareInterface):
    """Abstract base class for I2C interfaces."""

    @abstractmethod
    async def scan(self) -> List[int]:
        """Scan for devices on the I2C bus."""
        pass

    @abstractmethod
    async def read(self, device_address: int, register: Optional[int] = None, length: int = 1) -> bytes:
        """Read data from an I2C device."""
        pass

    @abstractmethod
    async def write(self, device_address: int, data: bytes, register: Optional[int] = None) -> None:
        """Write data to an I2C device."""
        pass


class SPIInterface(HardwareInterface):
    """Abstract base class for SPI interfaces."""

    @abstractmethod
    async def transfer(self, data: bytes) -> bytes:
        """Perform an SPI transfer."""
        pass


class UARTInterface(HardwareInterface):
    """Abstract base class for UART interfaces."""

    @abstractmethod
    async def send(self, data: bytes) -> None:
        """Send data over UART."""
        pass

    @abstractmethod
    async def receive(self, length: int, timeout: float = 1.0) -> bytes:
        """Receive data over UART."""
        pass


class USBInterface(HardwareInterface):
    """Abstract base class for USB interfaces."""

    @abstractmethod
    async def connect(self, device_id: Optional[str] = None) -> bool:
        """Connect to a USB device."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from a USB device."""
        pass

    @abstractmethod
    async def send(self, data: bytes, endpoint: Optional[int] = None) -> None:
        """Send data to a USB device."""
        pass

    @abstractmethod
    async def receive(self, length: int, endpoint: Optional[int] = None, timeout: float = 1.0) -> bytes:
        """Receive data from a USB device."""
        pass


class I2SInterface(HardwareInterface):
    """Abstract base class for I2S interfaces."""

    @abstractmethod
    async def play(self, data: bytes) -> None:
        """Play audio data over I2S."""
        pass

    @abstractmethod
    async def record(self, duration: float) -> bytes:
        """Record audio data over I2S."""
        pass
