"""
EDPMT Hardware Interface Factory
================================
This module provides a factory for creating hardware interfaces based on
configuration or runtime detection. It supports both real hardware and
simulators as fallbacks.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

# Import interfaces and implementations
try:
    from .interfaces import GPIOInterface, I2CInterface, SPIInterface, UARTInterface, USBInterface, I2SInterface
except ImportError:
    # Forward compatibility or placeholder if interfaces are not yet available
    GPIOInterface = I2CInterface = SPIInterface = UARTInterface = USBInterface = I2SInterface = object

try:
    from .gpio_rpi import RPiGPIO
except ImportError:
    RPiGPIO = None

try:
    from .gpio_simulator import SimulatedGPIO
except ImportError:
    SimulatedGPIO = None

try:
    from .i2c_smbus import SMBusI2C
except ImportError:
    SMBusI2C = None

try:
    from .i2c_simulator import SimulatedI2C
except ImportError:
    SimulatedI2C = None

try:
    from .spi_spidev import SpidevSPI
except ImportError:
    SpidevSPI = None

try:
    from .spi_simulator import SimulatedSPI
except ImportError:
    SimulatedSPI = None

try:
    from .uart_serial import SerialUART
except ImportError:
    SerialUART = None

try:
    from .uart_simulator import SimulatedUART
except ImportError:
    SimulatedUART = None

try:
    from .usb_pyusb import PyUSB
except ImportError:
    PyUSB = None

try:
    from .usb_simulator import SimulatedUSB
except ImportError:
    SimulatedUSB = None

try:
    from .i2s_pyaudio import PyAudioI2S
except ImportError:
    PyAudioI2S = None

try:
    from .i2s_simulator import SimulatedI2S
except ImportError:
    SimulatedI2S = None

logger = logging.getLogger(__name__)


class HardwareInterfaceFactory:
    """Factory class for creating hardware interfaces with fallback to simulators."""

    @staticmethod
    async def create_gpio(use_simulators: bool = False, config: Optional[Dict[str, Any]] = None) -> GPIOInterface:
        """Create a GPIO interface, falling back to simulator if real hardware fails or is requested."""
        if use_simulators or RPiGPIO is None:
            logging.info("Using simulated GPIO interface as requested or real GPIO not available")
            if SimulatedGPIO is None:
                raise RuntimeError("Simulated GPIO interface not available")
            return SimulatedGPIO(config or {})
        try:
            gpio = RPiGPIO(config or {})
            await gpio.initialize()
            return gpio
        except Exception as e:
            logging.warning(f"Failed to initialize real GPIO: {e}")
            logging.info("Falling back to simulated GPIO interface")
            if SimulatedGPIO is None:
                raise RuntimeError("Simulated GPIO interface not available")
            return SimulatedGPIO(config or {})

    @staticmethod
    async def create_i2c(use_simulators: bool = False, config: Optional[Dict[str, Any]] = None) -> I2CInterface:
        """Create an I2C interface, falling back to simulator if real hardware fails or is requested."""
        if use_simulators or SMBusI2C is None:
            logging.info("Using simulated I2C interface as requested or real I2C not available")
            if SimulatedI2C is None:
                raise RuntimeError("Simulated I2C interface not available")
            return SimulatedI2C(config or {})
        try:
            i2c = SMBusI2C(config or {})
            await i2c.initialize()
            return i2c
        except Exception as e:
            logging.warning(f"Failed to initialize real I2C: {e}")
            logging.info("Falling back to simulated I2C interface")
            if SimulatedI2C is None:
                raise RuntimeError("Simulated I2C interface not available")
            return SimulatedI2C(config or {})

    @staticmethod
    async def create_spi(use_simulators: bool = False, config: Optional[Dict[str, Any]] = None) -> SPIInterface:
        """Create an SPI interface, falling back to simulator if real hardware fails or is requested."""
        if use_simulators or SimulatedSPI is None:
            logging.info("Using simulated SPI interface as requested or real SPI not available")
            if SimulatedSPI is None:
                logging.warning("Simulated SPI interface not available, using dummy implementation")
                return DummySPI(config or {})
            return SimulatedSPI(config or {})
        try:
            spi = SpidevSPI(config or {})
            await spi.initialize()
            return spi
        except Exception as e:
            logging.warning(f"Failed to initialize real SPI: {e}")
            logging.info("Falling back to simulated SPI interface")
            if SimulatedSPI is None:
                logging.warning("Simulated SPI interface not available, using dummy implementation")
                return DummySPI(config or {})
            return SimulatedSPI(config or {})

    @staticmethod
    async def create_uart(use_simulators: bool = False, config: Optional[Dict[str, Any]] = None) -> UARTInterface:
        """Create a UART interface, falling back to simulator if real hardware fails or is requested."""
        if use_simulators or SerialUART is None:
            logging.info("Using simulated UART interface as requested or real UART not available")
            if SimulatedUART is None:
                logging.warning("Simulated UART interface not available, using dummy implementation")
                return DummyUART(config or {})
            return SimulatedUART(config or {})
        try:
            uart = SerialUART(config or {})
            await uart.initialize()
            return uart
        except Exception as e:
            logging.warning(f"Failed to initialize real UART: {e}")
            logging.info("Falling back to simulated UART interface")
            if SimulatedUART is None:
                logging.warning("Simulated UART interface not available, using dummy implementation")
                return DummyUART(config or {})
            return SimulatedUART(config or {})

    @staticmethod
    async def create_usb(use_simulators: bool = False, config: Optional[Dict[str, Any]] = None) -> USBInterface:
        """Create a USB interface, falling back to simulator if real hardware fails or is requested."""
        if use_simulators or PyUSB is None:
            logging.info("Using simulated USB interface as requested or real USB not available")
            if SimulatedUSB is None:
                logging.warning("Simulated USB interface not available, using dummy implementation")
                return DummyUSB(config or {})
            return SimulatedUSB(config or {})
        try:
            usb = PyUSB(config or {})
            await usb.initialize()
            return usb
        except Exception as e:
            logging.warning(f"Failed to initialize real USB: {e}")
            logging.info("Falling back to simulated USB interface")
            if SimulatedUSB is None:
                logging.warning("Simulated USB interface not available, using dummy implementation")
                return DummyUSB(config or {})
            return SimulatedUSB(config or {})

    @staticmethod
    async def create_i2s(use_simulators: bool = False, config: Optional[Dict[str, Any]] = None) -> I2SInterface:
        """Create an I2S interface, falling back to simulator if real hardware fails or is requested."""
        if use_simulators or PyAudioI2S is None:
            logging.info("Using simulated I2S interface as requested or real I2S not available")
            if SimulatedI2S is None:
                logging.warning("Simulated I2S interface not available, using dummy implementation")
                return DummyI2S(config or {})
            return SimulatedI2S(config or {})
        try:
            i2s = PyAudioI2S(config or {})
            await i2s.initialize()
            return i2s
        except Exception as e:
            logging.warning(f"Failed to initialize real I2S: {e}")
            logging.info("Falling back to simulated I2S interface")
            if SimulatedI2S is None:
                logging.warning("Simulated I2S interface not available, using dummy implementation")
                return DummyI2S(config or {})
            return SimulatedI2S(config or {})

    @staticmethod
    async def create_all_interfaces(use_simulators: bool = False, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create all supported hardware interfaces."""
        config = config or {}
        interfaces = {
            'gpio': await HardwareInterfaceFactory.create_gpio(use_simulators, config),
            'i2c': await HardwareInterfaceFactory.create_i2c(use_simulators, config),
            'spi': await HardwareInterfaceFactory.create_spi(use_simulators, config),
            'uart': await HardwareInterfaceFactory.create_uart(use_simulators, config),
            'usb': await HardwareInterfaceFactory.create_usb(use_simulators, config),
            'i2s': await HardwareInterfaceFactory.create_i2s(use_simulators, config),
        }
        return interfaces


# Dummy implementations for interfaces that are not yet available
class DummySPI(SPIInterface):
    """Dummy SPI interface for when no real or simulated SPI is available."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(name="Dummy SPI", config=config)
        self.logger = logging.getLogger(__name__)
        self.initialized = True
        self.logger.info("Dummy SPI interface created")

    async def initialize(self) -> bool:
        self.logger.info("Initializing dummy SPI interface")
        return True

    async def cleanup(self) -> None:
        self.logger.info("Cleaning up dummy SPI interface")
        self.initialized = False

    async def transfer(self, data: bytes) -> bytes:
        self.logger.info(f"Dummy SPI transfer: {data.hex()}")
        return bytes(len(data))

    async def execute(self, action: str, **params) -> Any:
        if action == "transfer":
            return await self.transfer(params.get("data", b""))
        else:
            raise ValueError(f"Unsupported action: {action}")


class DummyUART(UARTInterface):
    """Dummy UART interface for when no real or simulated UART is available."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(name="Dummy UART", config=config)
        self.logger = logging.getLogger(__name__)
        self.initialized = True
        self.logger.info("Dummy UART interface created")

    async def initialize(self) -> bool:
        self.logger.info("Initializing dummy UART interface")
        return True

    async def cleanup(self) -> None:
        self.logger.info("Cleaning up dummy UART interface")
        self.initialized = False

    async def send(self, data: bytes) -> None:
        self.logger.info(f"Dummy UART send: {data.hex()}")

    async def receive(self, length: int, timeout: float = 1.0) -> bytes:
        self.logger.info(f"Dummy UART receive: {length} bytes")
        return bytes(length)

    async def execute(self, action: str, **params) -> Any:
        if action == "send":
            await self.send(params.get("data", b""))
            return True
        elif action == "receive":
            return await self.receive(params.get("length", 1), params.get("timeout", 1.0))
        else:
            raise ValueError(f"Unsupported action: {action}")


class DummyUSB(USBInterface):
    """Dummy USB interface for when no real or simulated USB is available."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(name="Dummy USB", config=config)
        self.logger = logging.getLogger(__name__)
        self.initialized = True
        self.connected = False
        self.logger.info("Dummy USB interface created")

    async def initialize(self) -> bool:
        self.logger.info("Initializing dummy USB interface")
        return True

    async def cleanup(self) -> None:
        self.logger.info("Cleaning up dummy USB interface")
        self.initialized = False

    async def connect(self, device_id: Optional[str] = None) -> bool:
        self.logger.info(f"Dummy USB connect to {device_id or 'default device'}")
        self.connected = True
        return True

    async def disconnect(self) -> None:
        self.logger.info("Dummy USB disconnect")
        self.connected = False

    async def send(self, data: bytes, endpoint: Optional[int] = None) -> None:
        self.logger.info(f"Dummy USB send: {data.hex()} to endpoint {endpoint or 'default'}")

    async def receive(self, length: int, endpoint: Optional[int] = None, timeout: float = 1.0) -> bytes:
        self.logger.info(f"Dummy USB receive: {length} bytes from endpoint {endpoint or 'default'}")
        return bytes(length)

    async def execute(self, action: str, **params) -> Any:
        if action == "connect":
            return await self.connect(params.get("device_id"))
        elif action == "disconnect":
            await self.disconnect()
            return True
        elif action == "send":
            await self.send(params.get("data", b""), params.get("endpoint"))
            return True
        elif action == "receive":
            return await self.receive(params.get("length", 1), params.get("endpoint"), params.get("timeout", 1.0))
        else:
            raise ValueError(f"Unsupported action: {action}")


class DummyI2S(I2SInterface):
    """Dummy I2S interface for when no real or simulated I2S is available."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(name="Dummy I2S", config=config)
        self.logger = logging.getLogger(__name__)
        self.initialized = True
        self.logger.info("Dummy I2S interface created")

    async def initialize(self) -> bool:
        self.logger.info("Initializing dummy I2S interface")
        return True

    async def cleanup(self) -> None:
        self.logger.info("Cleaning up dummy I2S interface")
        self.initialized = False

    async def play(self, data: bytes) -> None:
        self.logger.info(f"Dummy I2S play: {len(data)} bytes")

    async def record(self, duration: float) -> bytes:
        self.logger.info(f"Dummy I2S record for {duration} seconds")
        return bytes(int(duration * 44100 * 2))  # Simulate 44.1kHz 16-bit audio

    async def execute(self, action: str, **params) -> Any:
        if action == "play":
            await self.play(params.get("data", b""))
            return True
        elif action == "record":
            return await self.record(params.get("duration", 1.0))
        else:
            raise ValueError(f"Unsupported action: {action}")
