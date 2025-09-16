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

# EDPMT Complete Frontend

A complete frontend solution for the EDPMT (Embedded Device Programming and Management Tool) that provides a visual programming interface and peripheral control.

## Project Structure

```
complete-frontend/
├── config_service/      # Configuration service (optional)
├── frontend/           # Frontend server (static files and API)
│   ├── __init__.py
│   ├── server.py       # Main frontend server
│   └── requirements.txt
├── websocket/          # WebSocket server (hardware communication)
│   ├── __init__.py
│   ├── server.py       # WebSocket server implementation
│   └── requirements.txt
├── js/                 # Frontend JavaScript files
│   ├── edpmt-client.js # WebSocket client
│   ├── main.js         # Main application logic
│   ├── block-editor.js # Block editor implementation
│   └── page-editor.js  # Page editor implementation
├── logs/               # Log files directory
├── projects/           # Project files directory
├── scripts/            # Utility scripts
├── .env                # Environment variables
├── .gitignore
├── Makefile            # Build and run commands
├── index.html          # Main HTML file
├── requirements.txt    # Global requirements
└── server.py          # Legacy server (kept for reference)
```

## Prerequisites

- Python 3.8+
- Node.js 14+ (for frontend development)
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd edpmt/examples/complete-frontend
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies for both services:
   ```bash
   make install
   ```
   
   Or install them separately:
   ```bash
   # Install frontend dependencies
   cd frontend
   pip install -r requirements.txt
   cd ..
   
   # Install WebSocket server dependencies
   cd websocket
   pip install -r requirements.txt
   cd ..
   ```

4. Create a `.env` file (if not already created):
   ```bash
   cp .env.example .env
   ```

## Configuration

Edit the `.env` file to configure the application:

```env
# Server Ports
FRONTEND_PORT=8085
WEBSOCKET_PORT=8086

# Debug Settings
DEBUG=true
LOG_LEVEL=INFO

# Hardware Settings
USE_HARDWARE_SIMULATORS=true

# Paths (relative to project root)
LOG_DIR=logs
PROJECTS_DIR=projects
STATIC_DIR=.
```

## Running the Application

### Development Mode

To start both the frontend and WebSocket servers in development mode:

```bash
make dev
```

This will:
1. Start the frontend server on port 8085
2. Start the WebSocket server on port 8086
3. Open the application in your default browser
4. Tail the logs from both servers

### Production Mode

For production, you might want to run the servers separately using a process manager like `pm2` or `systemd`.

Start the frontend server:
```bash
cd frontend
python server.py
```

In a separate terminal, start the WebSocket server:
```bash
cd websocket
python server.py
```

## Available Make Commands

- `make install` - Install all dependencies
- `make dev` - Start both servers in development mode
- `make start-frontend` - Start only the frontend server
- `make start-websocket` - Start only the WebSocket server
- `make stop` - Stop all running servers
- `make clean` - Clean up temporary files
- `make test` - Run tests
- `make lint` - Run linters
- `make format` - Format code

## API Endpoints

### Frontend Server (Port 8085 by default)

- `GET /` - Main application
- `GET /api/projects` - List all projects
- `POST /api/save-project` - Save a project
- `POST /api/load-project` - Load a project

### WebSocket Server (Port 8086 by default)

- `ws://localhost:8086/ws` - WebSocket endpoint
- `GET /api/status` - Server status
- `POST /api/execute` - Execute a command

## Project Structure Details

### Frontend Server (`frontend/server.py`)

- Serves static files (HTML, CSS, JS)
- Handles project management (save/load)
- Provides a REST API for the frontend

### WebSocket Server (`websocket/server.py`)

- Handles WebSocket connections
- Manages hardware communication
- Broadcasts system information
- Processes commands from the frontend

### JavaScript Client (`js/edpmt-client.js`)

- Manages WebSocket connection
- Provides a clean API for sending commands
- Handles reconnection and error handling
- Emits events for state changes

## Development

### Adding New Features

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and test them:
   ```bash
   make dev
   ```

3. Run tests and linters:
   ```bash
   make test
   make lint
   ```

4. Commit your changes with a descriptive message:
   ```bash
   git add .
   git commit -m "Add feature: your feature description"
   ```

5. Push your branch and create a pull request

### Debugging

- Check the logs in the terminal where you ran `make dev`
- Browser developer tools (F12) for frontend debugging
- Use `console.log()` or `debugger` statements in JavaScript
- Check the browser's network tab for API requests

## License

[Your License Here]

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

For support, please open an issue in the repository or contact the maintainers.
