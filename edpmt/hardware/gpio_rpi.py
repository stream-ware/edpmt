"""
EDPMT GPIO Hardware Interface for Raspberry Pi
==============================================
This module provides a concrete implementation of the GPIO hardware interface
using the RPi.GPIO library for Raspberry Pi hardware.
"""

import logging
from typing import Dict, Any

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

from .interfaces import GPIOInterface

logger = logging.getLogger(__name__)


class RPiGPIO(GPIOInterface):
    """GPIO interface for Raspberry Pi using RPi.GPIO library."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(name="Raspberry Pi GPIO", config=config)
        self.logger = logging.getLogger(__name__)
        self.initialized = False
        if GPIO is None:
            raise RuntimeError("RPi.GPIO library not available")
        self.logger.info("Raspberry Pi GPIO interface created")

    async def initialize(self) -> bool:
        """Initialize the Raspberry Pi GPIO interface."""
        self.logger.info("Initializing Raspberry Pi GPIO interface")
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(self.config.get('warnings', False))
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize GPIO: {e}")
            self.initialized = False
            return False

    async def cleanup(self) -> None:
        """Cleanup GPIO resources."""
        self.logger.info("Cleaning up Raspberry Pi GPIO interface")
        if self.initialized:
            try:
                GPIO.cleanup()
            except Exception as e:
                self.logger.warning(f"Error during GPIO cleanup: {e}")
        self.initialized = False

    async def set_pin(self, pin: int, value: bool) -> None:
        """Set the value of a GPIO pin."""
        if not self.initialized:
            raise RuntimeError("GPIO interface not initialized")
        try:
            GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)
            self.logger.info(f"Set GPIO pin {pin} to {value}")
        except Exception as e:
            self.logger.error(f"Failed to set GPIO pin {pin}: {e}")
            raise

    async def get_pin(self, pin: int) -> bool:
        """Get the value of a GPIO pin."""
        if not self.initialized:
            raise RuntimeError("GPIO interface not initialized")
        try:
            value = GPIO.input(pin) == GPIO.HIGH
            self.logger.info(f"Read GPIO pin {pin} as {value}")
            return value
        except Exception as e:
            self.logger.error(f"Failed to read GPIO pin {pin}: {e}")
            raise

    async def configure_pin(self, pin: int, mode: str) -> None:
        """Configure the mode of a GPIO pin (input/output)."""
        if not self.initialized:
            raise RuntimeError("GPIO interface not initialized")
        try:
            if mode == "input":
                GPIO.setup(pin, GPIO.IN)
            elif mode == "output":
                GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
            else:
                raise ValueError(f"Invalid mode {mode}. Use 'input' or 'output'")
            self.logger.info(f"Configured GPIO pin {pin} as {mode}")
        except Exception as e:
            self.logger.error(f"Failed to configure GPIO pin {pin}: {e}")
            raise

    async def execute(self, action: str, **params) -> Any:
        """Execute a command on the GPIO interface."""
        if action == "set":
            await self.set_pin(params.get("pin", 0), params.get("value", False))
            return True
        elif action == "get":
            return await self.get_pin(params.get("pin", 0))
        elif action == "configure":
            await self.configure_pin(params.get("pin", 0), params.get("mode", "output"))
            return True
        else:
            raise ValueError(f"Unsupported action: {action}")
