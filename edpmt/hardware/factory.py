"""
EDPMT Hardware Interface Factory
================================
This module provides a factory for creating hardware interfaces based on
configuration or runtime detection. It supports both real hardware and
simulators as fallbacks.
"""

import asyncio
import logging
from typing import Dict, Optional, Type

from .interfaces import (
    HardwareInterface,
    GPIOHardwareInterface,
    I2CHardwareInterface,
    SPIHardwareInterface,
    UARTHardwareInterface,
    USBHardwareInterface,
    I2SHardwareInterface
)

# Import concrete implementations (to be created)
try:
    from .gpio_rpi import RPiGPIOInterface
except ImportError:
    RPiGPIOInterface = None
try:
    from .gpio_simulator import SimulatedGPIOInterface
except ImportError:
    SimulatedGPIOInterface = None
try:
    from .i2c_smbus import SMBusI2CInterface
except ImportError:
    SMBusI2CInterface = None
try:
    from .i2c_simulator import SimulatedI2CInterface
except ImportError:
    SimulatedI2CInterface = None
try:
    from .spi_spidev import SpidevSPIInterface
except ImportError:
    SpidevSPIInterface = None
try:
    from .spi_simulator import SimulatedSPIInterface
except ImportError:
    SimulatedSPIInterface = None
try:
    from .uart_serial import SerialUARTInterface
except ImportError:
    SerialUARTInterface = None
try:
    from .uart_simulator import SimulatedUARTInterface
except ImportError:
    SimulatedUARTInterface = None
try:
    from .usb_pyusb import PyUSBInterface
except ImportError:
    PyUSBInterface = None
try:
    from .usb_simulator import SimulatedUSBInterface
except ImportError:
    SimulatedUSBInterface = None
try:
    from .i2s_pyaudio import PyAudioI2SInterface
except ImportError:
    PyAudioI2SInterface = None
try:
    from .i2s_simulator import SimulatedI2SInterface
except ImportError:
    SimulatedI2SInterface = None

logger = logging.getLogger(__name__)


class HardwareInterfaceFactory:
    """Factory class for creating hardware interfaces with fallback to simulators."""

    # Mapping of hardware type to real and simulator classes
    INTERFACE_MAPPING: Dict[str, Type[HardwareInterface]] = {
        'gpio': RPiGPIOInterface,
        'i2c': SMBusI2CInterface,
        'spi': SpidevSPIInterface,
        'uart': SerialUARTInterface,
        'usb': PyUSBInterface,
        'i2s': PyAudioI2SInterface
    }

    SIMULATOR_MAPPING: Dict[str, Type[HardwareInterface]] = {
        'gpio': SimulatedGPIOInterface,
        'i2c': SimulatedI2CInterface,
        'spi': SimulatedSPIInterface,
        'uart': SimulatedUARTInterface,
        'usb': SimulatedUSBInterface,
        'i2s': SimulatedI2SInterface
    }

    @staticmethod
    async def create_interface(interface_type: str, use_simulator: bool = False, config: Optional[Dict] = None) -> Optional[HardwareInterface]:
        """Create a hardware interface of the specified type.

        Args:
            interface_type (str): Type of hardware interface ('gpio', 'i2c', 'spi', 'uart', 'usb', 'i2s').
            use_simulator (bool): If True, use simulator even if real hardware is available.
            config (Optional[Dict]): Configuration dictionary for the interface.

        Returns:
            Optional[HardwareInterface]: Initialized hardware interface or None if creation fails.
        """
        if interface_type not in HardwareInterfaceFactory.INTERFACE_MAPPING:
            logger.error(f"Unknown hardware interface type: {interface_type}")
            return None

        if use_simulator:
            simulator_cls = HardwareInterfaceFactory.SIMULATOR_MAPPING.get(interface_type)
            if simulator_cls:
                try:
                    simulator = simulator_cls(name=f"Simulated-{interface_type.upper()}", config=config)
                    await simulator.initialize()
                    logger.info(f"Using simulator for {interface_type.upper()}")
                    return simulator
                except Exception as e:
                    logger.error(f"Failed to initialize simulator for {interface_type}: {e}")
                    return None
            else:
                logger.error(f"No simulator available for {interface_type}")
                return None

        # Try real hardware first
        real_cls = HardwareInterfaceFactory.INTERFACE_MAPPING.get(interface_type)
        if real_cls:
            try:
                interface = real_cls(name=f"Real-{interface_type.upper()}", config=config)
                if await interface.initialize():
                    logger.info(f"Using real hardware for {interface_type.upper()}")
                    return interface
                else:
                    logger.warning(f"Failed to initialize real {interface_type.upper()} hardware")
            except Exception as e:
                logger.warning(f"Real hardware {interface_type.upper()} unavailable: {e}")

        # Fallback to simulator if real hardware fails
        simulator_cls = HardwareInterfaceFactory.SIMULATOR_MAPPING.get(interface_type)
        if simulator_cls:
            try:
                simulator = simulator_cls(name=f"Simulated-{interface_type.upper()}", config=config)
                await simulator.initialize()
                logger.info(f"Falling back to simulator for {interface_type.upper()}")
                return simulator
            except Exception as e:
                logger.error(f"Failed to initialize simulator for {interface_type}: {e}")
                return None
        else:
            logger.error(f"No simulator available for {interface_type} as fallback")
            return None

    @staticmethod
    async def create_all_interfaces(use_simulators: bool = False, config: Optional[Dict] = None) -> Dict[str, HardwareInterface]:
        """Create all available hardware interfaces.

        Args:
            use_simulators (bool): If True, use simulators for all interfaces.
            config (Optional[Dict]): Configuration dictionary for interfaces.

        Returns:
            Dict[str, HardwareInterface]: Dictionary mapping interface type to initialized interface.
        """
        interfaces = {}
        tasks = []

        for interface_type in HardwareInterfaceFactory.INTERFACE_MAPPING.keys():
            tasks.append(HardwareInterfaceFactory.create_interface(interface_type, use_simulators, config))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for interface_type, result in zip(HardwareInterfaceFactory.INTERFACE_MAPPING.keys(), results):
            if isinstance(result, HardwareInterface):
                interfaces[interface_type] = result
            else:
                logger.warning(f"Failed to create interface for {interface_type}")

        return interfaces
