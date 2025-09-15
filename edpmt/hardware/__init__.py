# __init__.py for edpmt.hardware package

# This file marks the directory as a Python package
# Import key modules to make them accessible from edpmt.hardware
try:
    from .factory import HardwareInterfaceFactory
except ImportError:
    pass  # Factory might not be available yet

try:
    from .interfaces import GPIOInterface, I2CInterface, SPIInterface, UARTInterface, USBInterface, I2SInterface
except ImportError:
    pass  # Interfaces might not be available yet

try:
    from .gpio_simulator import SimulatedGPIO
except ImportError:
    pass  # SimulatedGPIO might not be available yet

__all__ = ['HardwareInterfaceFactory', 'GPIOInterface', 'I2CInterface', 'SPIInterface', 'UARTInterface', 'USBInterface', 'I2SInterface', 'SimulatedGPIO']
