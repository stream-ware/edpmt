"""
EDPMT GPIO Hardware Interface Simulator
=======================================
This module provides a simulated implementation of the GPIO hardware interface
for testing and development purposes when real hardware is not available.
"""

import logging
import random
from typing import Dict, Optional

from .interfaces import GPIOHardwareInterface

logger = logging.getLogger(__name__)


class SimulatedGPIOInterface(GPIOHardwareInterface):
    """Simulated GPIO Hardware Interface for testing without real hardware."""

    def __init__(self, name: str = "Simulated-GPIO", config: Optional[Dict] = None):
        super().__init__(name, config)
        self.pins: Dict[int, int] = {}
        self.pwm_pins: Dict[int, Dict[str, float]] = {}

    async def initialize(self) -> bool:
        """Initialize the simulated GPIO interface."""
        self.pins.clear()
        self.pwm_pins.clear()
        self.is_initialized = True
        logger.info("GPIO simulator initialized")
        return True

    async def cleanup(self) -> None:
        """Clean up simulated GPIO resources."""
        self.pins.clear()
        self.pwm_pins.clear()
        self.is_initialized = False
        logger.info("GPIO simulator cleaned up")

    async def set_pin(self, pin: int, value: int) -> bool:
        """Simulate setting a GPIO pin to a specific value."""
        if not self.is_initialized:
            logger.error("GPIO simulator not initialized")
            return False

        self.pins[pin] = value
        logger.info(f"[SIM] GPIO pin {pin} set to {value}")
        return True

    async def get_pin(self, pin: int) -> int:
        """Simulate reading the value of a GPIO pin."""
        if not self.is_initialized:
            logger.error("GPIO simulator not initialized")
            return 0

        # Return stored value or random for unset pins
        value = self.pins.get(pin, random.randint(0, 1))
        logger.info(f"[SIM] GPIO pin {pin} read: {value}")
        return value

    async def pwm(self, pin: int, frequency: float, duty_cycle: float) -> bool:
        """Simulate setting PWM on a GPIO pin."""
        if not self.is_initialized:
            logger.error("GPIO simulator not initialized")
            return False

        self.pwm_pins[pin] = {'frequency': frequency, 'duty_cycle': duty_cycle}
        logger.info(f"[SIM] PWM on GPIO pin {pin}: {frequency}Hz at {duty_cycle}% duty cycle")
        return True
