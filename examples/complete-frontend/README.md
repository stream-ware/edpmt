# EDPMT Visual Programming & Peripheral Control - Developer Guide

## 🚀 Quick Start

Launch the complete solution with one command:

```bash
make run-complete-frontend
```

This starts both EDPMT backend and the visual programming frontend with real-time peripheral control.

## 📋 Overview

This example demonstrates a complete EDPMT solution with:

- **Real-time Peripheral Control**: Direct GPIO, I2C, SPI, UART control from web interface
- **Visual Programming Interface**: Drag-and-drop block programming with live execution
- **Block Logic Editor**: Edit and save visual programming logic via popup modals
- **Web Page Editor**: Edit and customize the frontend interface directly in browser
- **Live Status Monitor**: Real-time peripheral status, pin states, and protocol activity
- **Predefined Commands**: Quick access to common peripheral operations

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Browser                             │
├─────────────────────────────────────────────────────────────┤
│  Visual Programming Interface  │  Peripheral Control Panel  │
│  ┌─────────────────────────┐   │  ┌─────────────────────────┐ │
│  │ Block Palette           │   │  │ GPIO Status & Control   │ │
│  │ ├─ GPIO Blocks          │   │  │ ├─ Pin States (Live)    │ │
│  │ ├─ I2C Blocks           │   │  │ ├─ Quick Commands       │ │
│  │ ├─ Logic Blocks         │   │  │ └─ Custom Commands      │ │
│  │ └─ Control Blocks       │   │  │                         │ │
│  └─────────────────────────┘   │  │ I2C/SPI/UART Monitor    │ │
│                                 │  │ ├─ Device Scanning      │ │
│  Canvas & Execution             │  │ ├─ Protocol Status      │ │
│  ┌─────────────────────────┐   │  │ └─ Transaction Log      │ │
│  │ Visual Block Program    │   │  └─────────────────────────┘ │
│  │ ├─ Real-time Execution  │   │                             │
│  │ ├─ Block Connections    │   │  Logic & Page Editor        │
│  │ └─ Live Variable Watch  │   │  ┌─────────────────────────┐ │
│  └─────────────────────────┘   │  │ Edit Block Logic (JSON) │ │
└─────────────────────────────────┼─ │ Edit Page Layout (HTML) │ │
                                  │  │ Save Changes            │ │
┌─────────────────────────────────┼─ └─────────────────────────┘ │
│        EDPMT Backend            │                             │
│  ┌─────────────────────────┐   │                             │
│  │ Hardware Abstraction    │   └─────────────────────────────┘
│  │ ├─ GPIO Interface       │              │
│  │ ├─ I2C Interface        │              │ WebSocket/HTTP
│  │ ├─ SPI Interface        │              │ Real-time Communication
│  │ └─ UART Interface       │              │
│  └─────────────────────────┘              │
│                                           │
│  ┌─────────────────────────┐              │
│  │ Visual Programming      │              │
│  │ ├─ Block Execution      │◄─────────────┘
│  │ ├─ State Management     │
│  │ └─ Real-time Updates    │
│  └─────────────────────────┘
└─────────────────────────────────────────────┘
```

## 🛠️ Development Workflow

### 1. Creating Custom Visual Programming Blocks

Create new blocks in `projects/` directory:

```json
{
  "name": "My Custom Project",
  "description": "Custom peripheral control logic",
  "blocks": [
    {
      "id": "custom_block_1",
      "type": "gpio-set",
      "params": {
        "pin": 18,
        "value": 1
      },
      "description": "Turn on LED on GPIO 18"
    }
  ],
  "hardware": ["GPIO Pin 18", "LED", "220Ω Resistor"],
  "connections": {
    "LED": "GPIO Pin 18"
  }
}
```

### 2. Adding New Block Types

Extend `flow-generator.js` with new block types:

```javascript
// Add to blockTypeMap in flow-generator.js
'custom-sensor': { 
  icon: '📡', 
  color: '#9C27B0', 
  name: 'Custom Sensor' 
},
```

### 3. Backend Peripheral Integration

The frontend automatically connects to EDPMT backend:

```javascript
// Automatic backend connection
const edpmtClient = new EDPMTClient('ws://localhost:8085');

// Send commands to peripherals
await edpmtClient.execute('gpio-set', { pin: 18, value: 1 });
await edpmtClient.execute('i2c-scan', {});
```

### 4. Real-time Status Updates

The interface automatically receives real-time updates:

```javascript
// Real-time peripheral status
edpmtClient.onStatusUpdate((status) => {
  updateGPIOStatus(status.gpio);
  updateI2CStatus(status.i2c);
  updateProtocolStatus(status.protocols);
});
```

## 🎛️ Frontend Features

### Visual Programming Interface

- **Block Palette**: Drag-and-drop blocks for GPIO, I2C, SPI, UART operations
- **Canvas**: Visual programming workspace with real-time execution
- **Block Editor**: Popup modal for editing block logic and parameters
- **Project Management**: Save/load visual programming projects

### Peripheral Control Panel

- **GPIO Monitor**: Live pin states, input/output configuration, PWM control
- **Protocol Status**: I2C device scanning, SPI transactions, UART communication
- **Quick Commands**: Predefined peripheral operations (LED blink, sensor read, etc.)
- **Custom Commands**: Direct peripheral command execution

### Live Editing Capabilities

- **Block Logic Editor**: Edit JSON block definitions with live preview
- **Page Layout Editor**: Modify HTML/CSS of the interface
- **Save Functionality**: Persist changes to filesystem via backend
- **Live Reload**: Automatic interface updates after changes

## 🔧 Configuration

### Backend Configuration

Edit `config.json` to customize hardware interfaces:

```json
{
  "hardware_simulators": false,
  "gpio": {
    "pins": [18, 19, 20, 21],
    "default_mode": "output"
  },
  "i2c": {
    "bus": 1,
    "scan_on_startup": true
  },
  "protocols": {
    "spi": { "enabled": true },
    "uart": { "enabled": true, "baudrate": 9600 }
  }
}
```

### Frontend Configuration

Customize interface in `frontend-config.js`:

```javascript
export const CONFIG = {
  edpmtBackend: 'ws://localhost:8085',
  updateInterval: 1000, // Status update frequency (ms)
  enableLiveEditing: true,
  defaultProjects: ['led-blink', 'sensor-monitor'],
  peripheralPanels: ['gpio', 'i2c', 'spi', 'uart']
};
```

## 📡 API Integration

### WebSocket Commands

```javascript
// GPIO Operations
ws.send(JSON.stringify({
  action: 'gpio-set',
  params: { pin: 18, value: 1 }
}));

// I2C Operations  
ws.send(JSON.stringify({
  action: 'i2c-scan',
  params: { bus: 1 }
}));

// Get Real-time Status
ws.send(JSON.stringify({
  action: 'get-status',
  params: { include: ['gpio', 'i2c', 'spi'] }
}));
```

### HTTP REST API

```bash
# Execute peripheral commands
curl -X POST http://localhost:8085/api/execute \
  -H "Content-Type: application/json" \
  -d '{"action": "gpio-set", "params": {"pin": 18, "value": 1}}'

# Get peripheral status
curl http://localhost:8085/api/status

# Save visual programming project
curl -X POST http://localhost:8085/api/projects/save \
  -H "Content-Type: application/json" \
  -d '{"name": "my-project", "blocks": [...]}'
```

## 🔍 Debugging & Monitoring

### Real-time Logs

The interface provides real-time logging:

- **Console Logs**: JavaScript console shows all peripheral operations
- **Network Panel**: Monitor WebSocket/HTTP communication
- **Status Panel**: Live peripheral states and error messages
- **Execution Trace**: Visual programming block execution flow

### Hardware Simulation Mode

For development without hardware:

```bash
make run-complete-frontend-sim
```

This runs with simulated peripherals for safe development.

## 📚 Example Projects

### LED Control Example

```json
{
  "name": "LED Blink Pattern",
  "blocks": [
    {
      "type": "repeat",
      "params": { "times": 10 },
      "children": [
        { "type": "gpio-set", "params": { "pin": 18, "value": 1 } },
        { "type": "delay", "params": { "seconds": 1 } },
        { "type": "gpio-set", "params": { "pin": 18, "value": 0 } },
        { "type": "delay", "params": { "seconds": 1 } }
      ]
    }
  ]
}
```

### I2C Sensor Monitoring

```json
{
  "name": "Temperature Monitor",
  "blocks": [
    {
      "type": "while-loop",
      "params": { "condition": "true" },
      "children": [
        { "type": "i2c-read", "params": { "address": "0x48", "register": "0x00" } },
        { "type": "if-condition", "params": { "condition": "temperature > 30" },
          "children": [
            { "type": "gpio-set", "params": { "pin": 19, "value": 1 } },
            { "type": "audio-beep", "params": { "frequency": 1000, "duration": 500 } }
          ]
        },
        { "type": "delay", "params": { "seconds": 5 } }
      ]
    }
  ]
}
```

## 🚀 Deployment

### Local Development

```bash
# Start development environment
make dev-complete-frontend

# With hardware simulation
make dev-complete-frontend-sim

# Production build
make build-complete-frontend
```

### Production Deployment

```bash
# Build production version
make production-complete-frontend

# Deploy to remote device
make deploy-complete-frontend HOST=pi@192.168.1.100
```

## 🔐 Security Considerations

- **CORS Configuration**: Customize allowed origins in backend
- **Authentication**: Optional JWT token authentication for API access  
- **Command Validation**: All peripheral commands are validated before execution
- **Safe Mode**: Hardware simulation prevents accidental damage during development

## 🐛 Troubleshooting

### Common Issues

1. **Backend Connection Failed**
   - Verify EDPMT backend is running: `make status`
   - Check WebSocket URL in configuration
   - Ensure firewall allows connections

2. **Peripheral Access Denied**
   - Run with appropriate permissions: `sudo make run-complete-frontend`
   - Check hardware interface configuration
   - Verify device connections

3. **Visual Programming Not Loading**
   - Check browser console for JavaScript errors
   - Verify all project JSON files are valid
   - Ensure flow-generator.js is loaded correctly

### Debug Mode

```bash
# Run with enhanced debugging
make debug-complete-frontend
```

This enables:
- Verbose backend logging
- Frontend debug mode
- Hardware simulation logging
- WebSocket traffic monitoring

---

## 📞 Support & Contributing

- **Issues**: Report bugs or request features via GitHub Issues
- **Documentation**: Additional docs in `/docs` directory  
- **Examples**: More examples in `/examples` directory
- **Community**: Join discussions in GitHub Discussions

Happy developing with EDPMT! 🚀
