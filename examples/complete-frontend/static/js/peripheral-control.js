/**
 * Peripheral Control Component - Handles real-time peripheral monitoring and control
 * Integrates with EDPMT client for GPIO, I2C, SPI, UART operations
 */

class PeripheralControl {
    constructor(edpmtClient) {
        this.edpmtClient = edpmtClient;
        this.statusUpdateInterval = null;
        this.isMonitoring = false;
        
        this.peripheralStates = {
            gpio: {},
            i2c: { devices: [], status: 'inactive' },
            spi: { status: 'inactive' },
            uart: { status: 'inactive', baudrate: 9600 }
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.startMonitoring();
    }

    setupEventListeners() {
        // GPIO Controls
        document.getElementById('gpio-grid')?.addEventListener('click', (e) => {
            if (e.target.closest('.gpio-pin')) {
                const pin = parseInt(e.target.closest('.gpio-pin').dataset.pin);
                this.toggleGPIOPin(pin);
            }
        });

        // Custom GPIO Command
        document.getElementById('execute-gpio-cmd')?.addEventListener('click', () => {
            this.executeCustomGPIOCommand();
        });

        // Quick Commands
        document.querySelectorAll('.cmd-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const command = btn.dataset.command;
                this.executeQuickCommand(command);
            });
        });

        // I2C Controls
        document.getElementById('i2c-scan-btn')?.addEventListener('click', () => {
            this.scanI2C();
        });

        document.getElementById('i2c-read-btn')?.addEventListener('click', () => {
            this.readI2C();
        });

        document.getElementById('i2c-write-btn')?.addEventListener('click', () => {
            this.writeI2C();
        });

        // SPI Controls
        document.getElementById('spi-transfer-btn')?.addEventListener('click', () => {
            this.transferSPI();
        });

        // UART Controls
        document.getElementById('uart-send-btn')?.addEventListener('click', () => {
            this.sendUART();
        });

        document.getElementById('uart-read-btn')?.addEventListener('click', () => {
            this.readUART();
        });

        // Emergency Stop
        document.getElementById('emergency-stop-btn')?.addEventListener('click', () => {
            this.emergencyStop();
        });

        // Refresh Status
        document.getElementById('refresh-status-btn')?.addEventListener('click', () => {
            this.refreshStatus();
        });

        // EDPMT Client Events
        if (this.edpmtClient) {
            this.edpmtClient.on('status', (data) => {
                this.updatePeripheralStatus(data);
            });

            this.edpmtClient.on('peripheral_event', (data) => {
                this.handlePeripheralEvent(data);
            });
        }
    }

    startMonitoring() {
        if (this.isMonitoring) return;
        
        this.isMonitoring = true;
        this.statusUpdateInterval = setInterval(() => {
            this.refreshStatus();
        }, 2000); // Update every 2 seconds

        this.addLogEntry('info', 'Peripheral monitoring started');
    }

    stopMonitoring() {
        if (!this.isMonitoring) return;
        
        this.isMonitoring = false;
        if (this.statusUpdateInterval) {
            clearInterval(this.statusUpdateInterval);
            this.statusUpdateInterval = null;
        }

        this.addLogEntry('info', 'Peripheral monitoring stopped');
    }

    async refreshStatus() {
        if (!this.edpmtClient || !this.edpmtClient.isConnected()) {
            return;
        }

        try {
            const status = await this.edpmtClient.getStatus();
            this.updatePeripheralStatus(status);
        } catch (error) {
            console.error('Status refresh failed:', error);
        }
    }

    updatePeripheralStatus(status) {
        // Update GPIO status
        if (status.gpio) {
            this.updateGPIOStatus(status.gpio);
        }

        // Update I2C status
        if (status.i2c) {
            this.updateI2CStatus(status.i2c);
        }

        // Update SPI status
        if (status.spi) {
            this.updateSPIStatus(status.spi);
        }

        // Update UART status
        if (status.uart) {
            this.updateUARTStatus(status.uart);
        }

        // Store current states
        this.peripheralStates = { ...this.peripheralStates, ...status };
    }

    updateGPIOStatus(gpioStatus) {
        const gpioGrid = document.getElementById('gpio-grid');
        if (!gpioGrid) return;

        Object.entries(gpioStatus).forEach(([pin, state]) => {
            const pinElement = gpioGrid.querySelector(`[data-pin="${pin}"]`);
            if (pinElement) {
                pinElement.classList.toggle('active', state.value === 1);
                pinElement.classList.toggle('input', state.mode === 'input');
                pinElement.classList.toggle('output', state.mode === 'output');
                
                const statusEl = pinElement.querySelector('.pin-status');
                if (statusEl) {
                    statusEl.textContent = state.value ? 'HIGH' : 'LOW';
                }

                const modeEl = pinElement.querySelector('.pin-mode');
                if (modeEl) {
                    modeEl.textContent = state.mode || 'unknown';
                }
            }
        });
    }

    updateI2CStatus(i2cStatus) {
        const statusEl = document.getElementById('i2c-status');
        if (statusEl) {
            statusEl.textContent = i2cStatus.active ? 'Active' : 'Inactive';
        }

        if (i2cStatus.devices) {
            this.updateI2CDevices(i2cStatus.devices);
        }
    }

    updateSPIStatus(spiStatus) {
        const statusEl = document.getElementById('spi-status');
        if (statusEl) {
            statusEl.textContent = spiStatus.ready ? 'Ready' : 'Not Ready';
        }

        const speedEl = document.getElementById('spi-speed');
        if (speedEl && spiStatus.speed) {
            speedEl.textContent = `${spiStatus.speed} Hz`;
        }
    }

    updateUARTStatus(uartStatus) {
        const statusEl = document.getElementById('uart-status');
        if (statusEl) {
            statusEl.textContent = `${uartStatus.baudrate || 9600} baud`;
        }

        const portEl = document.getElementById('uart-port-status');
        if (portEl) {
            portEl.textContent = uartStatus.port || '/dev/ttyS0';
        }
    }

    updateI2CDevices(devices) {
        const deviceList = document.getElementById('i2c-devices');
        if (!deviceList) return;

        deviceList.innerHTML = devices.map(device => `
            <div class="device-item" data-address="0x${device.address.toString(16).padStart(2, '0')}">
                <span class="device-address">0x${device.address.toString(16).padStart(2, '0')}</span>
                <span class="device-name">${device.name || 'Unknown Device'}</span>
                <button class="btn small" onclick="peripheralControl.selectI2CDevice('0x${device.address.toString(16).padStart(2, '0')}')">
                    Select
                </button>
            </div>
        `).join('');
    }

    async toggleGPIOPin(pin) {
        try {
            const currentState = this.peripheralStates.gpio?.[pin]?.value || 0;
            const newValue = currentState ? 0 : 1;
            
            await this.edpmtClient.setGPIO(pin, newValue);
            this.addLogEntry('success', `GPIO Pin ${pin} set to ${newValue ? 'HIGH' : 'LOW'}`);
            
            // Update UI immediately
            this.updateSingleGPIOPin(pin, newValue);
            
        } catch (error) {
            console.error('GPIO toggle failed:', error);
            this.addLogEntry('error', `Failed to toggle GPIO pin ${pin}: ${error.message}`);
        }
    }

    updateSingleGPIOPin(pin, value) {
        const pinElement = document.querySelector(`[data-pin="${pin}"]`);
        if (pinElement) {
            pinElement.classList.toggle('active', value === 1);
            const statusEl = pinElement.querySelector('.pin-status');
            if (statusEl) {
                statusEl.textContent = value ? 'HIGH' : 'LOW';
            }
        }
    }

    async executeCustomGPIOCommand() {
        const action = document.getElementById('gpio-action')?.value;
        const pin = parseInt(document.getElementById('gpio-pin')?.value);
        const value = parseInt(document.getElementById('gpio-value')?.value);

        if (isNaN(pin) || pin < 0 || pin > 40) {
            this.addLogEntry('error', 'Invalid pin number (0-40)');
            return;
        }

        try {
            switch (action) {
                case 'set':
                    if (isNaN(value) || (value !== 0 && value !== 1)) {
                        this.addLogEntry('error', 'Value must be 0 or 1 for set operation');
                        return;
                    }
                    await this.edpmtClient.setGPIO(pin, value);
                    this.addLogEntry('success', `GPIO Pin ${pin} set to ${value}`);
                    break;
                    
                case 'get':
                    const result = await this.edpmtClient.readGPIO(pin);
                    this.addLogEntry('info', `GPIO Pin ${pin} value: ${result.value}`);
                    break;
                    
                case 'config':
                    const mode = document.getElementById('gpio-mode')?.value || 'output';
                    const pull = document.getElementById('gpio-pull')?.value || 'none';
                    await this.edpmtClient.configurePin(pin, mode, pull);
                    this.addLogEntry('success', `GPIO Pin ${pin} configured as ${mode} with ${pull} pull`);
                    break;
                    
                case 'pwm':
                    if (isNaN(value) || value < 0 || value > 100) {
                        this.addLogEntry('error', 'PWM duty cycle must be 0-100');
                        return;
                    }
                    const frequency = parseInt(document.getElementById('gpio-frequency')?.value) || 1000;
                    await this.edpmtClient.setPWM(pin, value, frequency);
                    this.addLogEntry('success', `GPIO Pin ${pin} PWM set to ${value}% @ ${frequency}Hz`);
                    break;
                    
                default:
                    this.addLogEntry('error', 'Unknown GPIO action');
            }
        } catch (error) {
            console.error('GPIO command failed:', error);
            this.addLogEntry('error', `GPIO command failed: ${error.message}`);
        }
    }

    async executeQuickCommand(command) {
        try {
            switch (command) {
                case 'led-blink':
                    const pin = 18;
                    await this.edpmtClient.blinkLED(pin, 5, 500);
                    this.addLogEntry('success', `LED blink on pin ${pin} completed`);
                    break;
                    
                case 'all-pins-low':
                    const pins = [18, 19, 20, 21];
                    await this.edpmtClient.setAllPinsLow(pins);
                    this.addLogEntry('success', 'All configured pins set to LOW');
                    break;
                    
                case 'pin-sweep':
                    const sweepPins = [18, 19, 20, 21];
                    await this.edpmtClient.sweepPins(sweepPins, 200);
                    this.addLogEntry('success', 'Pin sweep completed');
                    break;
                    
                case 'gpio-reset':
                    await this.edpmtClient.execute('gpio-reset');
                    this.addLogEntry('success', 'GPIO reset completed');
                    break;
                    
                default:
                    this.addLogEntry('warning', `Unknown quick command: ${command}`);
            }
        } catch (error) {
            console.error('Quick command failed:', error);
            this.addLogEntry('error', `Quick command '${command}' failed: ${error.message}`);
        }
    }

    async scanI2C() {
        try {
            const bus = parseInt(document.getElementById('i2c-bus')?.value) || 1;
            const devices = await this.edpmtClient.scanI2C(bus);
            
            this.updateI2CDevices(devices);
            this.addLogEntry('success', `I2C scan on bus ${bus} found ${devices.length} devices`);
            
        } catch (error) {
            console.error('I2C scan failed:', error);
            this.addLogEntry('error', `I2C scan failed: ${error.message}`);
        }
    }

    async readI2C() {
        const address = document.getElementById('i2c-address')?.value;
        const register = document.getElementById('i2c-register')?.value;
        const length = parseInt(document.getElementById('i2c-length')?.value) || 1;
        const bus = parseInt(document.getElementById('i2c-bus')?.value) || 1;

        if (!address) {
            this.addLogEntry('error', 'I2C address is required');
            return;
        }

        try {
            const addressNum = parseInt(address, 16);
            const registerNum = register ? parseInt(register, 16) : null;
            
            const result = await this.edpmtClient.readI2C(addressNum, registerNum, length, bus);
            
            const dataStr = result.data.map(b => `0x${b.toString(16).padStart(2, '0')}`).join(' ');
            this.addLogEntry('success', `I2C Read from ${address}: ${dataStr}`);
            
        } catch (error) {
            console.error('I2C read failed:', error);
            this.addLogEntry('error', `I2C read failed: ${error.message}`);
        }
    }

    async writeI2C() {
        const address = document.getElementById('i2c-address')?.value;
        const register = document.getElementById('i2c-register')?.value;
        const data = document.getElementById('i2c-data')?.value;
        const bus = parseInt(document.getElementById('i2c-bus')?.value) || 1;

        if (!address || !data) {
            this.addLogEntry('error', 'I2C address and data are required');
            return;
        }

        try {
            const addressNum = parseInt(address, 16);
            const registerNum = register ? parseInt(register, 16) : null;
            const dataBytes = data.split(' ').map(b => parseInt(b, 16));
            
            await this.edpmtClient.writeI2C(addressNum, dataBytes, registerNum, bus);
            this.addLogEntry('success', `I2C Write to ${address}: ${data}`);
            
        } catch (error) {
            console.error('I2C write failed:', error);
            this.addLogEntry('error', `I2C write failed: ${error.message}`);
        }
    }

    async transferSPI() {
        const data = document.getElementById('spi-data')?.value;
        const bus = parseInt(document.getElementById('spi-bus')?.value) || 0;
        const device = parseInt(document.getElementById('spi-device')?.value) || 0;

        if (!data) {
            this.addLogEntry('error', 'SPI data is required');
            return;
        }

        try {
            const dataBytes = data.split(' ').map(b => parseInt(b, 16));
            const result = await this.edpmtClient.transferSPI(dataBytes, bus, device);
            
            const resultStr = result.data.map(b => `0x${b.toString(16).padStart(2, '0')}`).join(' ');
            this.addLogEntry('success', `SPI Transfer result: ${resultStr}`);
            
        } catch (error) {
            console.error('SPI transfer failed:', error);
            this.addLogEntry('error', `SPI transfer failed: ${error.message}`);
        }
    }

    async sendUART() {
        const data = document.getElementById('uart-data')?.value;
        const port = document.getElementById('uart-port')?.value || '/dev/ttyS0';

        if (!data) {
            this.addLogEntry('error', 'UART data is required');
            return;
        }

        try {
            await this.edpmtClient.writeUART(data, port);
            this.addLogEntry('success', `UART sent to ${port}: ${data}`);
            
        } catch (error) {
            console.error('UART send failed:', error);
            this.addLogEntry('error', `UART send failed: ${error.message}`);
        }
    }

    async readUART() {
        const length = parseInt(document.getElementById('uart-length')?.value) || 1;
        const port = document.getElementById('uart-port')?.value || '/dev/ttyS0';

        try {
            const result = await this.edpmtClient.readUART(length, port);
            this.addLogEntry('success', `UART read from ${port}: ${result.data}`);
            
        } catch (error) {
            console.error('UART read failed:', error);
            this.addLogEntry('error', `UART read failed: ${error.message}`);
        }
    }

    async emergencyStop() {
        try {
            await this.edpmtClient.emergencyStop();
            this.addLogEntry('warning', 'Emergency stop activated - all peripherals stopped');
            
            // Update UI to reflect stopped state
            this.updateAllPeripheralsOff();
            
        } catch (error) {
            console.error('Emergency stop failed:', error);
            this.addLogEntry('error', 'Emergency stop failed');
        }
    }

    updateAllPeripheralsOff() {
        // Set all GPIO pins to LOW in UI
        document.querySelectorAll('.gpio-pin').forEach(pinEl => {
            pinEl.classList.remove('active');
            const statusEl = pinEl.querySelector('.pin-status');
            if (statusEl) {
                statusEl.textContent = 'LOW';
            }
        });

        // Reset peripheral states
        this.peripheralStates.gpio = {};
    }

    selectI2CDevice(address) {
        document.getElementById('i2c-address').value = address;
        this.addLogEntry('info', `Selected I2C device: ${address}`);
    }

    handlePeripheralEvent(eventData) {
        switch (eventData.type) {
            case 'gpio_change':
                this.updateSingleGPIOPin(eventData.pin, eventData.value);
                this.addLogEntry('info', `GPIO Pin ${eventData.pin} changed to ${eventData.value ? 'HIGH' : 'LOW'}`);
                break;
                
            case 'i2c_device_detected':
                this.addLogEntry('info', `I2C device detected: 0x${eventData.address.toString(16)}`);
                break;
                
            case 'peripheral_error':
                this.addLogEntry('error', `Peripheral error: ${eventData.message}`);
                break;
                
            default:
                console.log('Unknown peripheral event:', eventData);
        }
    }

    // Utility methods
    addLogEntry(level, message) {
        if (window.edpmtApp) {
            window.edpmtApp.addLogEntry(level, message);
        } else {
            console.log(`[${level.toUpperCase()}] ${message}`);
        }
    }

    getPeripheralStates() {
        return this.peripheralStates;
    }

    setUpdateInterval(interval) {
        if (this.statusUpdateInterval) {
            clearInterval(this.statusUpdateInterval);
        }
        
        this.statusUpdateInterval = setInterval(() => {
            this.refreshStatus();
        }, interval);
    }

    exportPeripheralConfig() {
        const config = {
            gpio: this.peripheralStates.gpio,
            settings: {
                updateInterval: 2000,
                autoRefresh: this.isMonitoring
            },
            timestamp: Date.now()
        };

        const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'peripheral-config.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.addLogEntry('success', 'Peripheral configuration exported');
    }

    importPeripheralConfig(configData) {
        try {
            if (configData.gpio) {
                this.peripheralStates.gpio = configData.gpio;
                this.updateGPIOStatus(configData.gpio);
            }
            
            if (configData.settings) {
                if (configData.settings.updateInterval) {
                    this.setUpdateInterval(configData.settings.updateInterval);
                }
            }
            
            this.addLogEntry('success', 'Peripheral configuration imported');
        } catch (error) {
            console.error('Config import failed:', error);
            this.addLogEntry('error', 'Failed to import configuration');
        }
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PeripheralControl;
} else if (typeof window !== 'undefined') {
    window.PeripheralControl = PeripheralControl;
}
