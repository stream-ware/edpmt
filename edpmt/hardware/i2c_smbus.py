import logging
from typing import Dict, Any, List, Optional

try:
    from smbus2 import SMBus
except ImportError:
    SMBus = None

from .interfaces import I2CInterface

class SMBusI2C(I2CInterface):
    """I2C interface using smbus2 library for Raspberry Pi."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(name="SMBus I2C", config=config)
        self.logger = logging.getLogger(__name__)
        self.bus = None
        self.bus_number = self.config.get('bus', 1)  # Default to bus 1 on Raspberry Pi
        self.initialized = False
        if SMBus is None:
            raise RuntimeError("smbus2 library not available")
        self.logger.info("SMBus I2C interface created")

    async def initialize(self) -> bool:
        """Initialize the I2C interface."""
        self.logger.info(f"Initializing SMBus I2C interface on bus {self.bus_number}")
        try:
            self.bus = SMBus(self.bus_number)
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize I2C bus: {e}")
            self.initialized = False
            return False

    async def cleanup(self) -> None:
        """Cleanup I2C resources."""
        self.logger.info("Cleaning up SMBus I2C interface")
        if self.initialized and self.bus is not None:
            try:
                self.bus.close()
            except Exception as e:
                self.logger.warning(f"Error during I2C bus cleanup: {e}")
        self.initialized = False
        self.bus = None

    async def scan(self) -> List[int]:
        """Scan for devices on the I2C bus."""
        if not self.initialized or self.bus is None:
            raise RuntimeError("I2C interface not initialized")
        devices = []
        self.logger.info("Scanning I2C bus for devices")
        try:
            for address in range(128):
                try:
                    self.bus.read_byte(address)
                    devices.append(address)
                except Exception:
                    pass  # No device at this address
        except Exception as e:
            self.logger.error(f"Error during I2C scan: {e}")
            raise
        self.logger.info(f"Found I2C devices at addresses: {[hex(addr) for addr in devices]}")
        return devices

    async def read(self, device_address: int, register: Optional[int] = None, length: int = 1) -> bytes:
        """Read data from an I2C device."""
        if not self.initialized or self.bus is None:
            raise RuntimeError("I2C interface not initialized")
        try:
            if register is not None:
                self.bus.write_byte(device_address, register)
            data = []
            for _ in range(length):
                data.append(self.bus.read_byte(device_address))
            result = bytes(data)
            self.logger.info(f"Read {length} bytes from I2C device at {hex(device_address)}: {result.hex()}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to read from I2C device at {hex(device_address)}: {e}")
            raise

    async def write(self, device_address: int, data: bytes, register: Optional[int] = None) -> None:
        """Write data to an I2C device."""
        if not self.initialized or self.bus is None:
            raise RuntimeError("I2C interface not initialized")
        try:
            if register is not None:
                self.bus.write_byte(device_address, register)
            if len(data) == 1:
                self.bus.write_byte(device_address, data[0])
            else:
                self.bus.write_i2c_block_data(device_address, data[0], list(data[1:]))
            self.logger.info(f"Wrote {len(data)} bytes to I2C device at {hex(device_address)}: {data.hex()}")
        except Exception as e:
            self.logger.error(f"Failed to write to I2C device at {hex(device_address)}: {e}")
            raise

    async def execute(self, action: str, **params) -> Any:
        """Execute a command on the I2C interface."""
        if action == "scan":
            return await self.scan()
        elif action == "read":
            return await self.read(params.get("device", 0), params.get("register"), params.get("length", 1))
        elif action == "write":
            await self.write(params.get("device", 0), params.get("data", b""), params.get("register"))
            return True
        else:
            raise ValueError(f"Unsupported action: {action}")
