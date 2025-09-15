#!/usr/bin/env python3
"""
EDPMT (Electronic Device Protocol Management - Transparent)
Simple, Secure, Universal Hardware Communication Library

Copyright 2024 Stream-Ware Team
Licensed under the Apache License, Version 2.0

This package provides a transparent, zero-configuration solution for hardware communication
across different protocols (GPIO, I2C, SPI, UART) with automatic TLS encryption and
universal API access.

Key Features:
- Single universal execute() method for all operations
- Automatic transport protocol selection (Local IPC, Network TLS, WebSocket Secure)
- Zero configuration required - auto-detection of everything
- Full TLS encryption with auto-generated certificates
- Hardware abstraction layer with simulators for development
- Docker support with privilege escalation for hardware access
- Web-based control panel with real-time monitoring
- Cross-platform support (Linux, Windows, macOS)
"""

__version__ = "1.0.1"
__author__ = "Tom Sapletta"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2025 Tom Sapletta"

# Import main classes for easy access
from .transparent import (
    EDPMTransparent,
    EDPMClient,
    Message,
    TransportType,
)

from .hardware import (
    GPIOInterface,
    I2CInterface,
    SPIInterface,
    UARTInterface,
    GPIOSimulator,
    I2CSimulator,
    SPISimulator,
    UARTSimulator,
)

from .utils import (
    ensure_dependencies,
    generate_certificates,
    detect_hardware_platform,
)

# Main entry points
__all__ = [
    # Core classes
    "EDPMTransparent",
    "EDPMClient",
    "Message",
    "TransportType",
    
    # Hardware interfaces
    "GPIOInterface",
    "I2CInterface", 
    "SPIInterface",
    "UARTInterface",
    
    # Simulators for development
    "GPIOSimulator",
    "I2CSimulator",
    "SPISimulator", 
    "UARTSimulator",
    
    # Utilities
    "ensure_dependencies",
    "generate_certificates",
    "detect_hardware_platform",
]

# Package metadata
__pkg_info__ = {
    "name": "edpmt",
    "version": __version__,
    "description": "EDPM Transparent - Simple, Secure, Universal Hardware Communication",
    "author": __author__,
    "license": __license__,
    "url": "https://github.com/stream-ware/edpmt",
    "keywords": ["hardware", "gpio", "i2c", "spi", "uart", "raspberry-pi", "iot", "embedded", "automation"],
}
