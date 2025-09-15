# EDPMT Visual Programming

🎨 **Drag-and-drop visual programming interface for EDPMT hardware control**

Build hardware automation programs using visual blocks - no coding required!

## Features

- **Drag & Drop Interface**: Build programs by dragging blocks onto the canvas
- **Real-time Execution**: Connect directly to EDPMT server and run programs instantly  
- **Multiple Block Types**: GPIO, I2C, Audio, Control blocks and more
- **Pre-built Templates**: LED blink, sensor monitoring, traffic light, alarm system
- **Code Generation**: View the equivalent Python code for your visual program
- **Save/Load Programs**: Export and import your visual programs as JSON files
- **Variable Tracking**: Monitor variable values during program execution

## Quick Start

1. **Start EDPMT Server**:
   ```bash
   cd /path/to/edpmt
   make server-dev
   ```

2. **Open Visual Programming Interface**:
   ```bash
   # Open in browser
   cd examples/visual-programming
   python3 -m http.server 8080
   # Navigate to http://localhost:8080
   ```

3. **Connect to EDPMT Server**: Click the connection status to configure server URL

4. **Build Your Program**: Drag blocks from the palette to the canvas

5. **Run Your Program**: Click the "Run Program" button

## Block Types

### GPIO Blocks
- **Set GPIO Pin**: Control digital outputs (HIGH/LOW)
- **Read GPIO Pin**: Read digital inputs
- **PWM GPIO Pin**: Generate PWM signals with configurable frequency and duty cycle

### I2C Blocks  
- **Scan I2C Bus**: Discover connected I2C devices
- **Read I2C Device**: Read data from I2C device registers
- **Write I2C Device**: Write data to I2C device registers

### Control Blocks
- **Wait**: Add delays between operations
- **Repeat**: Execute blocks multiple times
- **If Condition**: Conditional execution based on GPIO or I2C state

### Audio Blocks
- **Play Tone**: Generate audio tones with specified frequency and duration
- **Beep Pattern**: Play predefined beep patterns (single, double, triple, SOS)

## Templates

### LED Blink
Classic blinking LED example - toggles GPIO pin with delays

### Sensor Monitor  
Read I2C sensor data and provide audio feedback

### Traffic Light
3-phase traffic light sequence with red, yellow, green LEDs

### Alarm System
Motion detection with audio alarm and visual indicator

## Example Projects

### Smart Garden Monitor
```
1. Read soil moisture sensor (I2C)
2. If moisture low:
   - Turn on water pump (GPIO)
   - Play warning tone
   - Wait 5 seconds
   - Turn off pump
3. Wait 1 minute
4. Repeat
```

### Temperature Alert System
```
1. Scan I2C bus for temperature sensor
2. Read temperature value
3. If temperature > 30°C:
   - Flash warning LED rapidly
   - Play SOS beep pattern
4. Else:
   - Turn on normal status LED
5. Wait 10 seconds
6. Repeat
```

### Door Bell System
```
1. Read door button state (GPIO)
2. If button pressed:
   - Play door bell melody
   - Turn on entrance light
   - Send notification (future feature)
   - Wait 2 seconds
   - Turn off light
3. Wait 0.1 seconds
4. Repeat
```

## Advanced Features

### Variable System
- Automatically stores results from read operations
- View all variables in the Variables tab
- Use variables in conditional blocks

### Code Generation
- See equivalent Python code in the Generated Code tab
- Learn programming concepts through visual blocks
- Export code for further development

### Program Persistence
- Save programs as JSON files
- Load and modify existing programs
- Share programs with others

## Tips & Best Practices

1. **Start Simple**: Begin with basic LED control before complex I2C operations
2. **Use Templates**: Modify existing templates instead of building from scratch
3. **Test Incrementally**: Run small parts of your program first
4. **Monitor Variables**: Check the Variables tab to debug program logic
5. **Add Delays**: Include wait blocks to prevent overwhelming the hardware

## Troubleshooting

### Connection Issues
- Ensure EDPMT server is running on correct port
- Check server URL includes correct protocol (wss:// for HTTPS)
- Verify firewall settings allow WebSocket connections

### Block Execution Errors
- Check input values are within valid ranges
- Ensure I2C devices are properly connected
- Verify GPIO pin numbers match your hardware setup

### Performance Issues
- Add delays between rapid operations
- Limit loop iterations for testing
- Use smaller data transfer sizes for I2C operations

## Browser Compatibility

- Chrome/Chromium: Full support
- Firefox: Full support  
- Safari: Full support
- Edge: Full support

## Development

To extend the visual programming interface:

1. Add new block types in `visual-programming.js`
2. Update CSS styles for new block colors
3. Add execution logic in `executeBlock()` method
4. Create templates using new blocks

## Contributing

Contributions welcome! Areas for improvement:
- Additional block types (SPI, UART, etc.)
- More sophisticated control structures
- Visual debugging features
- Mobile-responsive design
- Block validation and error checking
