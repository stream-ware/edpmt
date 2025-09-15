"""
EDPMT GPIO Hardware Interface Simulator
=======================================
This module provides a simulated implementation of the GPIO hardware interface
for testing and development purposes when real hardware is not available.
"""

import logging
from typing import Dict, Any

from .interfaces import GPIOInterface

class SimulatedGPIO(GPIOInterface):
    """Simulated GPIO interface for testing without real hardware."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(name="Simulated GPIO", config=config)
        self.logger = logging.getLogger(__name__)
        self.pins = {}  # Simulated pin states
        self.modes = {}  # Simulated pin modes
        self.initialized = True
        self.logger.info("Simulated GPIO interface created")

    async def initialize(self) -> bool:
        """Initialize the simulated GPIO interface."""
        self.logger.info("Initializing simulated GPIO interface")
        self.initialized = True
        return True

    async def cleanup(self) -> None:
        """Cleanup resources (none needed for simulator)."""
        self.logger.info("Cleaning up simulated GPIO interface")
        self.initialized = False

    async def set_pin(self, pin: int, value: bool) -> None:
        """Set the value of a simulated GPIO pin."""
        if pin not in self.modes:
            self.modes[pin] = "output"
        if self.modes[pin] != "output":
            raise ValueError(f"Pin {pin} is not configured as output")
        self.pins[pin] = value
        self.logger.info(f"Set simulated GPIO pin {pin} to {value}")

    async def get_pin(self, pin: int) -> bool:
        """Get the value of a simulated GPIO pin."""
        if pin not in self.modes:
            self.modes[pin] = "input"
        value = self.pins.get(pin, False)
        self.logger.info(f"Read simulated GPIO pin {pin} as {value}")
        return value

    async def configure_pin(self, pin: int, mode: str) -> None:
        """Configure the mode of a simulated GPIO pin (input/output)."""
        if mode not in ["input", "output"]:
            raise ValueError(f"Invalid mode {mode}. Use 'input' or 'output'")
        self.modes[pin] = mode
        self.logger.info(f"Configured simulated GPIO pin {pin} as {mode}")

    async def execute(self, action: str, **params) -> Any:
        """Execute a command on the simulated GPIO interface."""
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
