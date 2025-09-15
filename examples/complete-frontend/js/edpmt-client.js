/**
 * EDPMT Client - WebSocket and HTTP client for EDPMT backend communication
 * Handles real-time communication with EDPMT server for peripheral control
 */

class EDPMTClient {
    constructor(wsUrl = 'ws://localhost:8085', httpUrl = 'http://localhost:8085') {
        this.wsUrl = wsUrl;
        this.httpUrl = httpUrl;
        this.ws = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 2000;
        this.statusCallbacks = [];
        this.commandCallbacks = new Map();
        this.messageId = 0;
        
        this.init();
    }

    async init() {
        await this.connect();
        this.setupHeartbeat();
    }

    async connect() {
        try {
            console.log('🔌 Connecting to EDPMT backend:', this.wsUrl);
            
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => {
                console.log('✅ Connected to EDPMT backend');
                this.connected = true;
                this.reconnectAttempts = 0;
                this.emit('connection', { status: 'connected' });
                this.requestInitialStatus();
            };
            
            this.ws.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };
            
            this.ws.onclose = () => {
                console.log('❌ Disconnected from EDPMT backend');
                this.connected = false;
                this.emit('connection', { status: 'disconnected' });
                this.handleReconnection();
            };
            
            this.ws.onerror = (error) => {
                console.error('🚨 WebSocket error:', error);
                this.emit('error', { error: error.message });
            };
            
        } catch (error) {
            console.error('❌ Failed to connect to EDPMT backend:', error);
            this.handleReconnection();
        }
    }

    handleMessage(message) {
        const { type, id, data, error } = message;
        
        if (id && this.commandCallbacks.has(id)) {
            const callback = this.commandCallbacks.get(id);
            this.commandCallbacks.delete(id);
            
            if (error) {
                callback.reject(new Error(error));
            } else {
                callback.resolve(data);
            }
            return;
        }
        
        switch (type) {
            case 'status_update':
                this.emit('status', data);
                break;
            case 'peripheral_event':
                this.emit('peripheral_event', data);
                break;
            case 'execution_log':
                this.emit('log', data);
                break;
            case 'hardware_change':
                this.emit('hardware_change', data);
                break;
            default:
                console.log('📨 Received message:', message);
        }
    }

    handleReconnection() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectInterval * this.reconnectAttempts);
        } else {
            console.error('💥 Max reconnection attempts reached');
            this.emit('connection_failed');
        }
    }

    setupHeartbeat() {
        setInterval(() => {
            if (this.connected && this.ws.readyState === WebSocket.OPEN) {
                this.send({ type: 'ping' });
            }
        }, 30000); // Send ping every 30 seconds
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
            return true;
        }
        return false;
    }

    async execute(action, params = {}, timeout = 10000) {
        return new Promise((resolve, reject) => {
            if (!this.connected) {
                reject(new Error('Not connected to EDPMT backend'));
                return;
            }

            const id = `cmd_${this.messageId++}`;
            
            const timeoutId = setTimeout(() => {
                this.commandCallbacks.delete(id);
                reject(new Error('Command timeout'));
            }, timeout);

            this.commandCallbacks.set(id, {
                resolve: (data) => {
                    clearTimeout(timeoutId);
                    resolve(data);
                },
                reject: (error) => {
                    clearTimeout(timeoutId);
                    reject(error);
                }
            });

            const message = {
                type: 'command',
                id: id,
                action: action,
                params: params,
                timestamp: Date.now()
            };

            if (!this.send(message)) {
                this.commandCallbacks.delete(id);
                clearTimeout(timeoutId);
                reject(new Error('Failed to send command'));
            }
        });
    }

    // GPIO Operations
    async setGPIO(pin, value) {
        return this.execute('gpio-set', { pin, value });
    }

    async readGPIO(pin) {
        return this.execute('gpio-get', { pin });
    }

    async setPWM(pin, dutyCycle, frequency = 1000) {
        return this.execute('gpio-pwm', { pin, duty_cycle: dutyCycle, frequency });
    }

    async configurePin(pin, mode, pull = 'none') {
        return this.execute('gpio-config', { pin, mode, pull });
    }

    // I2C Operations
    async scanI2C(bus = 1) {
        return this.execute('i2c-scan', { bus });
    }

    async readI2C(address, register = null, length = 1, bus = 1) {
        return this.execute('i2c-read', { address, register, length, bus });
    }

    async writeI2C(address, data, register = null, bus = 1) {
        return this.execute('i2c-write', { address, data, register, bus });
    }

    // SPI Operations
    async transferSPI(data, bus = 0, device = 0) {
        return this.execute('spi-transfer', { data, bus, device });
    }

    // UART Operations
    async writeUART(data, port = '/dev/ttyS0') {
        return this.execute('uart-write', { data, port });
    }

    async readUART(length = 1, port = '/dev/ttyS0') {
        return this.execute('uart-read', { length, port });
    }

    // Visual Programming Operations
    async executeProject(projectData) {
        return this.execute('execute-project', { project: projectData });
    }

    async stopExecution() {
        return this.execute('stop-execution');
    }

    async saveProject(name, projectData) {
        return this.execute('save-project', { name, project: projectData });
    }

    async loadProject(name) {
        return this.execute('load-project', { name });
    }

    async listProjects() {
        return this.execute('list-projects');
    }

    // System Operations
    async getStatus() {
        return this.execute('get-status');
    }

    async getSystemInfo() {
        return this.execute('get-system-info');
    }

    async emergencyStop() {
        return this.execute('emergency-stop');
    }

    async resetHardware() {
        return this.execute('reset-hardware');
    }

    // HTTP fallback methods
    async httpRequest(method, endpoint, data = null) {
        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(`${this.httpUrl}${endpoint}`, options);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('HTTP request failed:', error);
            throw error;
        }
    }

    async httpExecute(action, params = {}) {
        return this.httpRequest('POST', '/api/execute', { action, params });
    }

    async httpGetStatus() {
        return this.httpRequest('GET', '/api/status');
    }

    // Event handling
    on(event, callback) {
        if (!this.statusCallbacks[event]) {
            this.statusCallbacks[event] = [];
        }
        this.statusCallbacks[event].push(callback);
    }

    off(event, callback) {
        if (this.statusCallbacks[event]) {
            this.statusCallbacks[event] = this.statusCallbacks[event].filter(cb => cb !== callback);
        }
    }

    emit(event, data = null) {
        if (this.statusCallbacks[event]) {
            this.statusCallbacks[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Event callback error:', error);
                }
            });
        }
    }

    requestInitialStatus() {
        // Request initial status updates
        this.send({ type: 'subscribe', events: ['status_update', 'peripheral_event', 'execution_log'] });
        this.getStatus().catch(console.error);
        this.getSystemInfo().catch(console.error);
    }

    // Utility methods
    isConnected() {
        return this.connected && this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    getConnectionStatus() {
        if (!this.ws) return 'Not initialized';
        
        switch (this.ws.readyState) {
            case WebSocket.CONNECTING: return 'Connecting';
            case WebSocket.OPEN: return 'Connected';
            case WebSocket.CLOSING: return 'Closing';
            case WebSocket.CLOSED: return 'Disconnected';
            default: return 'Unknown';
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
    }

    // Quick command helpers
    async blinkLED(pin, times = 5, interval = 500) {
        try {
            for (let i = 0; i < times; i++) {
                await this.setGPIO(pin, 1);
                await this.delay(interval);
                await this.setGPIO(pin, 0);
                await this.delay(interval);
            }
        } catch (error) {
            console.error('LED blink failed:', error);
            throw error;
        }
    }

    async sweepPins(pins, interval = 100) {
        try {
            for (const pin of pins) {
                await this.setGPIO(pin, 1);
                await this.delay(interval);
                await this.setGPIO(pin, 0);
            }
        } catch (error) {
            console.error('Pin sweep failed:', error);
            throw error;
        }
    }

    async setAllPinsLow(pins) {
        try {
            const promises = pins.map(pin => this.setGPIO(pin, 0));
            await Promise.all(promises);
        } catch (error) {
            console.error('Set all pins low failed:', error);
            throw error;
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Export for both module and global use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EDPMTClient;
} else if (typeof window !== 'undefined') {
    window.EDPMTClient = EDPMTClient;
}
