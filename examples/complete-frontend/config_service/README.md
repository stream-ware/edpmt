# EDPMT Configuration Service

This service provides a REST API for managing the EDPMT frontend configuration. It reads from and writes to the `.env` file in the project root.

## Features

- RESTful API for configuration management
- Real-time configuration updates
- Environment variable validation
- CORS enabled for frontend access

## API Endpoints

### GET /api/config

Get the current configuration.

**Response:**
```json
{
  "BACKEND_WS_URL": "ws://localhost:8085/ws",
  "BACKEND_HTTP_URL": "http://localhost:8085",
  "UPDATE_INTERVAL": 1000,
  "ENABLE_LOGGING": true,
  "HARDWARE_MODE": "simulator"
}
```

### PUT /api/config

Update the configuration.

**Request Body:**
```json
{
  "BACKEND_WS_URL": "ws://new-host:8085/ws",
  "BACKEND_HTTP_URL": "http://new-host:8085",
  "UPDATE_INTERVAL": 2000,
  "ENABLE_LOGGING": false,
  "HARDWARE_MODE": "real"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Configuration updated successfully"
}
```

## Environment Variables

The service reads from the `.env` file in the project root. The following variables are supported:

- `BACKEND_WS_URL`: WebSocket URL for the backend
- `BACKEND_HTTP_URL`: HTTP URL for the backend
- `UPDATE_INTERVAL`: Update interval in milliseconds
- `ENABLE_LOGGING`: Enable/disable debug logging (true/false)
- `HARDWARE_MODE`: Hardware mode ('simulator' or 'real')
- `API_HOST`: Host to bind the API server to (default: 0.0.0.0)
- `API_PORT`: Port to run the API server on (default: 8000)
- `DEBUG`: Enable debug mode (true/false)

## Development

1. Install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Start the service:
   ```bash
   # Using the Makefile (recommended)
   make config-service-start

   # Or manually
   python main.py
   ```

The service will be available at `http://localhost:8000` by default.

## Integration with Frontend

The frontend automatically uses this service for configuration management. The service is started and stopped automatically with the main application when using the provided Makefile commands.
