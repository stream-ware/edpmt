"""
EDPMT GPIO Hardware Interface for Raspberry Pi
==============================================
This module provides a concrete implementation of the GPIO hardware interface
using the RPi.GPIO library for Raspberry Pi hardware.
"""

import logging
from typing import Dict, Optional

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

from .interfaces import GPIOHardwareInterface

logger = logging.getLogger(__name__)


class RPiGPIOInterface(GPIOHardwareInterface):
    """GPIO Hardware Interface implementation for Raspberry Pi using RPi.GPIO."""

    def __init__(self, name: str = "RPi-GPIO", config: Optional[Dict] = None):
        super().__init__(name, config)
        self.gpio = GPIO
        self.pwm_objects: Dict[int, Any] = {}

    async def initialize(self) -> bool:
        """Initialize the GPIO interface using RPi.GPIO."""
        if self.gpio is None:
            logger.error("RPi.GPIO library not available")
            return False

        try:
            self.gpio.setmode(self.gpio.BCM)
            self.gpio.setwarnings(False)
            self.is_initialized = True
            logger.info("RPi.GPIO interface initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize RPi.GPIO: {e}")
            self.is_initialized = False
            return False

    async def cleanup(self) -> None:
        """Clean up GPIO resources."""
        if self.is_initialized and self.gpio:
            # Stop any PWM objects
            for pin, pwm in self.pwm_objects.items():
                try:
                    pwm.stop()
                except Exception as e:
                    logger.warning(f"Error stopping PWM on pin {pin}: {e}")
            self.pwm_objects.clear()

            try:
                self.gpio.cleanup()
                logger.info("RPi.GPIO resources cleaned up")
            except Exception as e:
                logger.warning(f"Error during GPIO cleanup: {e}")
            finally:
                self.is_initialized = False

    async def set_pin(self, pin: int, value: int) -> bool:
        """Set a GPIO pin to a specific value."""
        if not self.is_initialized:
            logger.error("GPIO interface not initialized")
            return False

        try:
            # Setup pin as output if not already
            if pin not in self.pwm_objects:
                self.gpio.setup(pin, self.gpio.OUT)
            self.gpio.output(pin, value)
            logger.debug(f"GPIO pin {pin} set to {value}")
            return True
        except Exception as e:
            logger.error(f"Error setting GPIO pin {pin} to {value}: {e}")
            return False

    async def get_pin(self, pin: int) -> int:
        """Read the value of a GPIO pin."""
        if not self.is_initialized:
            logger.error("GPIO interface not initialized")
            return 0

        try:
            # Setup pin as input if not already
            self.gpio.setup(pin, self.gpio.IN)
            value = self.gpio.input(pin)
            logger.debug(f"GPIO pin {pin} read: {value}")
            return value
        except Exception as e:
            logger.error(f"Error reading GPIO pin {pin}: {e}")
            return 0

    async def pwm(self, pin: int, frequency: float, duty_cycle: float) -> bool:
        """Set PWM on a GPIO pin."""
        if not self.is_initialized:
            logger.error("GPIO interface not initialized")
            return False

        try:
            # Setup pin as output if not already
            self.gpio.setup(pin, self.gpio.OUT)

            # If PWM already exists for this pin, stop it
            if pin in self.pwm_objects:
                self.pwm_objects[pin].stop()
                del self.pwm_objects[pin]

            # Create new PWM object
            pwm = self.gpio.PWM(pin, frequency)
            pwm.start(duty_cycle)
            self.pwm_objects[pin] = pwm

            logger.debug(f"PWM set on GPIO pin {pin}: {frequency}Hz at {duty_cycle}% duty cycle")
            return True
        except Exception as e:
            logger.error(f"Error setting PWM on GPIO pin {pin}: {e}")
            return False

    def is_supported(self) -> bool:
        """Check if RPi.GPIO is supported on the current platform."""
        return self.gpio is not None
