# PC Hardware Simulation Examples

These examples demonstrate EDPMT's hardware simulation capabilities 
on PC/laptop environments without real hardware. 
All examples use EDPMT's built-in simulators that provide realistic hardware behavior
for development and testing.

## Features

- **Cross-Platform**: Works on Windows, macOS, and Linux
- **No Hardware Required**: Uses EDPMT's built-in simulators
- **Realistic Behavior**: Simulators provide authentic hardware responses
- **Educational**: Perfect for learning hardware communication protocols

## Examples

### 1. I2C Sensor Simulation
- **BME280 Temperature/Pressure Sensor**: Complete sensor simulation with realistic data
- **EEPROM Memory**: I2C memory device simulation with read/write operations
- **Device Discovery**: I2C bus scanning and device enumeration

### 2. SPI Communication
- **MAX31855 Thermocouple**: SPI temperature sensor with cold junction compensation
- **MCP3008 ADC**: 8-channel analog-to-digital converter simulation
- **SPI Flash Memory**: Flash memory device with read/write/erase operations

### 3. GPIO Control
- **LED Matrix**: 8x8 LED matrix control with patterns
- **Button Input**: Digital input with debouncing and interrupts
- **PWM Servo Control**: Servo motor positioning with smooth movement

### 4. UART Communication
- **GPS Module**: NMEA sentence parsing and location simulation
- **Serial Terminal**: Bidirectional serial communication example
- **Sensor Data Logger**: UART data collection and storage

## Requirements

- Python 3.8+
- EDPMT package installed
- No additional hardware dependencies

## Quick Start

```bash
# Install EDPMT
pip install edpmt

# Run I2C sensor example
cd examples/pc-simulation
python i2c_sensor_simulation.py

# Run SPI communication example  
python spi_communication.py

# Run GPIO control example
python gpio_led_matrix.py

# Run UART communication example
python uart_gps_simulation.py
```

All examples work entirely in simulation mode and provide realistic hardware behavior
for development and learning.
