/**
 * EDPMT Complete Frontend - Main Application Controller
 * Coordinates all frontend components and manages application state
 */

class EDPMTApp {
    constructor() {
        this.edpmtClient = null;
        this.visualProgramming = null;
        this.peripheralControl = null;
        this.blockEditor = null;
        this.pageEditor = null;
        
        this.currentProject = null;
        this.executionState = 'stopped';
        this.config = {
            backendUrl: 'ws://localhost:8086',
            httpUrl: 'http://localhost:8085',
            updateInterval: 1000,
            enableLogging: true,
            hardwareMode: 'real'
        };
        
        this.init();
    }

    async init() {
        console.log('🚀 Initializing EDPMT Complete Frontend...');
        
        // Load configuration
        this.loadConfig();
        
        // Initialize components
        this.initializeUI();
        this.initializeEventListeners();
        
        // Connect to backend
        await this.connectToBackend();
        
        // Initialize subsystems
        this.initializeVisualProgramming();
        this.initializePeripheralControl();
        this.initializeEditors();
        
        // Load initial data
        await this.loadInitialData();
        
        console.log('✅ EDPMT Complete Frontend initialized successfully!');
    }

    loadConfig() {
        const savedConfig = localStorage.getItem('edpmt-config');
        if (savedConfig) {
            this.config = { ...this.config, ...JSON.parse(savedConfig) };
        }
        
        // Update UI with config
        document.getElementById('backend-url').value = this.config.backendUrl;
        document.getElementById('update-interval').value = this.config.updateInterval;
        document.getElementById('hardware-mode').value = this.config.hardwareMode;
        document.getElementById('enable-logging').checked = this.config.enableLogging;
    }

    saveConfig() {
        localStorage.setItem('edpmt-config', JSON.stringify(this.config));
    }

    initializeUI() {
        // Set up tab switching
        this.setupTabs();
        
        // Set up modal handling
        this.setupModals();
        
        // Set up drag and drop
        this.setupDragAndDrop();
        
        // Initialize status indicators
        this.updateConnectionStatus('Disconnected');
        this.updateHardwareStatus('Unknown');
    }

    setupTabs() {
        // Palette tabs
        document.querySelectorAll('.palette-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                this.switchPaletteTab(tab);
            });
        });

        // Control tabs
        document.querySelectorAll('.control-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                this.switchControlTab(tab);
            });
        });

        // Editor tabs
        document.querySelectorAll('.editor-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                this.switchEditorTab(btn.closest('.modal').id, tab);
            });
        });
    }

    switchPaletteTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.palette-tabs .tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update tab panels
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.toggle('active', panel.id === `${tabName}-panel`);
        });
    }

    switchControlTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.control-tabs .tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update control panels
        document.querySelectorAll('.control-panel').forEach(panel => {
            panel.classList.toggle('active', panel.id === tabName);
        });
    }

    switchEditorTab(modalId, tabName) {
        const modal = document.getElementById(modalId);
        
        // Update tab buttons
        modal.querySelectorAll('.editor-tabs .tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update tab panels
        modal.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.toggle('active', panel.id === tabName);
        });
    }

    setupModals() {
        // Modal close buttons
        document.querySelectorAll('[data-modal]').forEach(btn => {
            btn.addEventListener('click', () => {
                const modalId = btn.dataset.modal;
                this.closeModal(modalId);
            });
        });

        // Close modal on backdrop click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }

    setupDragAndDrop() {
        // Make blocks draggable
        document.querySelectorAll('.block[draggable="true"]').forEach(block => {
            block.addEventListener('dragstart', (e) => this.handleDragStart(e));
        });

        // Canvas drop zone
        const canvas = document.getElementById('programming-canvas');
        canvas.addEventListener('dragover', (e) => this.handleDragOver(e));
        canvas.addEventListener('drop', (e) => this.handleDrop(e));
    }

    initializeEventListeners() {
        // Navigation buttons
        document.getElementById('settings-btn').addEventListener('click', () => {
            this.openModal('settings-modal');
        });

        document.getElementById('help-btn').addEventListener('click', () => {
            this.showHelp();
        });

        // Project controls
        document.getElementById('new-project-btn').addEventListener('click', () => {
            this.newProject();
        });

        document.getElementById('save-project-btn').addEventListener('click', () => {
            this.saveProject();
        });

        document.getElementById('load-project-btn').addEventListener('click', () => {
            this.loadProjectDialog();
        });

        // Execution controls
        document.getElementById('run-project-btn').addEventListener('click', () => {
            this.runProject();
        });

        document.getElementById('stop-project-btn').addEventListener('click', () => {
            this.stopProject();
        });

        document.getElementById('clear-canvas-btn').addEventListener('click', () => {
            this.clearCanvas();
        });

        document.getElementById('edit-page-btn').addEventListener('click', () => {
            this.openPageEditor();
        });

        // Peripheral controls
        document.getElementById('refresh-status-btn').addEventListener('click', () => {
            this.refreshPeripheralStatus();
        });

        document.getElementById('emergency-stop-btn').addEventListener('click', () => {
            this.emergencyStop();
        });

        // Log controls
        document.getElementById('clear-log-btn').addEventListener('click', () => {
            this.clearLog();
        });

        // Settings
        document.getElementById('save-settings-btn').addEventListener('click', () => {
            this.saveSettings();
        });

        // Quick commands
        document.querySelectorAll('.cmd-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const command = btn.dataset.command;
                this.executeQuickCommand(command);
            });
        });

        // Custom GPIO command
        document.getElementById('execute-gpio-cmd').addEventListener('click', () => {
            this.executeCustomGPIOCommand();
        });

        // I2C scan
        document.getElementById('i2c-scan-btn').addEventListener('click', () => {
            this.scanI2C();
        });

        // Project name changes
        document.getElementById('project-name').addEventListener('input', (e) => {
            this.updateProjectStatus('Modified');
        });
    }

    async connectToBackend() {
        try {
            this.updateConnectionStatus('Connecting...');
            
            this.edpmtClient = new EDPMTClient(this.config.backendUrl, this.config.httpUrl);
            
            // Set up event listeners
            this.edpmtClient.on('connection', (data) => {
                this.updateConnectionStatus(data.status === 'connected' ? 'Connected' : 'Disconnected');
            });

            this.edpmtClient.on('status', (data) => {
                this.updatePeripheralStatus(data);
            });

            this.edpmtClient.on('log', (data) => {
                this.addLogEntry(data.level, data.message);
            });

            this.edpmtClient.on('error', (data) => {
                this.addLogEntry('error', data.error);
            });

            this.edpmtClient.on('hardware_change', (data) => {
                this.updateHardwareStatus(data.mode);
            });

        } catch (error) {
            console.error('❌ Failed to connect to backend:', error);
            this.updateConnectionStatus('Failed');
            this.addLogEntry('error', `Backend connection failed: ${error.message}`);
        }
    }

    initializeVisualProgramming() {
        // Initialize visual programming functionality
        this.visualProgramming = {
            blocks: [],
            connections: [],
            canvas: document.getElementById('programming-canvas')
        };
    }

    initializePeripheralControl() {
        // Initialize peripheral control
        this.setupGPIOGrid();
        this.startStatusUpdates();
    }

    initializeEditors() {
        // Initialize block and page editors
        this.blockEditor = {
            currentBlock: null,
            isOpen: false
        };

        this.pageEditor = {
            currentContent: null,
            isOpen: false
        };
    }

    async loadInitialData() {
        try {
            // Load available projects
            await this.loadProjects();
            
            // Get initial peripheral status
            await this.refreshPeripheralStatus();
            
        } catch (error) {
            console.error('❌ Failed to load initial data:', error);
            this.addLogEntry('error', 'Failed to load initial data');
        }
    }

    // Project Management
    newProject() {
        this.currentProject = {
            name: 'New Project',
            description: '',
            blocks: [],
            hardware: [],
            connections: {}
        };
        
        document.getElementById('project-name').value = this.currentProject.name;
        this.clearCanvas();
        this.updateProjectStatus('New');
        this.addLogEntry('info', 'New project created');
    }

    async saveProject() {
        if (!this.currentProject) {
            this.addLogEntry('warning', 'No project to save');
            return;
        }

        try {
            const projectName = document.getElementById('project-name').value;
            this.currentProject.name = projectName;
            this.currentProject.blocks = this.getCanvasBlocks();

            await this.edpmtClient.saveProject(projectName, this.currentProject);
            this.updateProjectStatus('Saved');
            this.addLogEntry('success', `Project '${projectName}' saved successfully`);
        } catch (error) {
            console.error('❌ Failed to save project:', error);
            this.addLogEntry('error', `Failed to save project: ${error.message}`);
        }
    }

    async loadProjects() {
        try {
            const result = await this.edpmtClient.listProjects();
            const projects = Array.isArray(result) ? result : (result?.projects || []);
            const listEl = document.getElementById('project-list');
            if (listEl) {
                listEl.innerHTML = projects.map(p => `
                    <div class="project-item" data-name="${(p.name || p.filename || '').replace(/"/g, '&quot;')}">
                        <div class="project-name">${p.name || p.filename || 'Unnamed Project'}</div>
                        <div class="project-desc">${p.description || ''}</div>
                    </div>
                `).join('');
                listEl.querySelectorAll('.project-item').forEach(item => {
                    item.addEventListener('click', () => {
                        const name = item.dataset.name;
                        if (!name) return;
                        this.edpmtClient.loadProject(name)
                            .then(project => {
                                this.currentProject = project;
                                const nameEl = document.getElementById('project-name');
                                if (nameEl) nameEl.value = project?.name || name;
                                this.clearCanvas();
                                this.addLogEntry('success', `Project '${name}' loaded`);
                            })
                            .catch(err => {
                                console.error('Load project failed:', err);
                                this.addLogEntry('error', `Failed to load project '${name}': ${err.message}`);
                            });
                    });
                });
            }
        } catch (error) {
            console.error('❌ Failed to load projects:', error);
            this.addLogEntry('error', 'Failed to load projects');
        }
    }

    // Execution Control
    async runProject() {
        if (!this.currentProject) {
            this.addLogEntry('warning', 'No project to run');
            return;
        }

        try {
            this.executionState = 'running';
            this.updateExecutionButtons();
            
            this.currentProject.blocks = this.getCanvasBlocks();
            await this.edpmtClient.executeProject(this.currentProject);
            
            this.addLogEntry('success', 'Project execution started');
        } catch (error) {
            console.error('❌ Failed to run project:', error);
            this.executionState = 'stopped';
            this.updateExecutionButtons();
            this.addLogEntry('error', `Execution failed: ${error.message}`);
        }
    }

    async stopProject() {
        try {
            await this.edpmtClient.stopExecution();
            this.executionState = 'stopped';
            this.updateExecutionButtons();
            this.addLogEntry('info', 'Project execution stopped');
        } catch (error) {
            console.error('❌ Failed to stop project:', error);
            this.addLogEntry('error', `Failed to stop execution: ${error.message}`);
        }
    }

    // Peripheral Control
    setupGPIOGrid() {
        const gpioGrid = document.getElementById('gpio-grid');
        const pins = [2, 3, 4, 17, 27, 22, 10, 9, 11, 5, 6, 13, 19, 26, 14, 15, 18, 23, 24, 25, 8, 7, 1, 12, 16, 20, 21];
        
        gpioGrid.innerHTML = '';
        
        pins.forEach(pin => {
            const pinElement = document.createElement('div');
            pinElement.className = 'gpio-pin';
            pinElement.dataset.pin = pin;
            pinElement.innerHTML = `
                <div>Pin ${pin}</div>
                <div class="pin-status">OFF</div>
            `;
            
            pinElement.addEventListener('click', () => {
                this.toggleGPIOPin(pin);
            });
            
            gpioGrid.appendChild(pinElement);
        });
    }

    async toggleGPIOPin(pin) {
        try {
            const pinElement = document.querySelector(`[data-pin="${pin}"]`);
            const isActive = pinElement.classList.contains('active');
            
            const newValue = isActive ? 0 : 1;
            await this.edpmtClient.setGPIO(pin, newValue);
            
            pinElement.classList.toggle('active', !isActive);
            pinElement.querySelector('.pin-status').textContent = newValue ? 'ON' : 'OFF';
            
            this.addLogEntry('info', `GPIO Pin ${pin} set to ${newValue ? 'HIGH' : 'LOW'}`);
        } catch (error) {
            console.error('❌ Failed to toggle GPIO pin:', error);
            this.addLogEntry('error', `Failed to toggle GPIO pin ${pin}: ${error.message}`);
        }
    }

    async executeQuickCommand(command) {
        try {
            switch (command) {
                case 'led-blink':
                    await this.edpmtClient.blinkLED(18, 5, 500);
                    this.addLogEntry('success', 'LED blink command executed');
                    break;
                    
                case 'all-pins-low':
                    const pins = [18, 19, 20, 21];
                    await this.edpmtClient.setAllPinsLow(pins);
                    this.addLogEntry('success', 'All pins set to LOW');
                    break;
                    
                case 'pin-sweep':
                    const sweepPins = [18, 19, 20, 21];
                    await this.edpmtClient.sweepPins(sweepPins, 200);
                    this.addLogEntry('success', 'Pin sweep completed');
                    break;
                    
                default:
                    this.addLogEntry('warning', `Unknown command: ${command}`);
            }
        } catch (error) {
            console.error('❌ Quick command failed:', error);
            this.addLogEntry('error', `Quick command failed: ${error.message}`);
        }
    }

    async executeCustomGPIOCommand() {
        const action = document.getElementById('gpio-action').value;
        const pin = parseInt(document.getElementById('gpio-pin').value);
        const value = parseInt(document.getElementById('gpio-value').value);

        if (isNaN(pin) || pin < 0 || pin > 40) {
            this.addLogEntry('error', 'Invalid pin number');
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
                    
                case 'pwm':
                    if (isNaN(value) || value < 0 || value > 100) {
                        this.addLogEntry('error', 'PWM duty cycle must be 0-100');
                        return;
                    }
                    await this.edpmtClient.setPWM(pin, value);
                    this.addLogEntry('success', `GPIO Pin ${pin} PWM set to ${value}%`);
                    break;
            }
        } catch (error) {
            console.error('❌ Custom GPIO command failed:', error);
            this.addLogEntry('error', `GPIO command failed: ${error.message}`);
        }
    }

    async scanI2C() {
        try {
            const devices = await this.edpmtClient.scanI2C();
            this.updateI2CDevices(devices);
            this.addLogEntry('success', `I2C scan completed. Found ${devices.length} devices`);
        } catch (error) {
            console.error('❌ I2C scan failed:', error);
            this.addLogEntry('error', `I2C scan failed: ${error.message}`);
        }
    }

    // UI Update Methods
    updateConnectionStatus(status) {
        document.getElementById('connection-status').textContent = status;
        const indicator = document.getElementById('backend-status').querySelector('.fas');
        indicator.style.color = status === 'Connected' ? '#10b981' : '#ef4444';
    }

    updateHardwareStatus(mode) {
        document.getElementById('hardware-mode').textContent = mode;
    }

    updateProjectStatus(status) {
        document.getElementById('project-status').textContent = status;
    }

    updateExecutionButtons() {
        const runBtn = document.getElementById('run-project-btn');
        const stopBtn = document.getElementById('stop-project-btn');
        
        if (this.executionState === 'running') {
            runBtn.disabled = true;
            stopBtn.disabled = false;
        } else {
            runBtn.disabled = false;
            stopBtn.disabled = true;
        }
    }

    addLogEntry(level, message) {
        const logContent = document.getElementById('log-content');
        const timestamp = new Date().toLocaleTimeString();
        
        const entry = document.createElement('div');
        entry.className = `log-entry ${level}`;
        entry.innerHTML = `
            <span class="timestamp">${timestamp}</span>
            <span class="message">${message}</span>
        `;
        
        logContent.appendChild(entry);
        logContent.scrollTop = logContent.scrollHeight;
    }

    clearLog() {
        document.getElementById('log-content').innerHTML = '';
        this.addLogEntry('info', 'Log cleared');
    }

    // Modal Management
    openModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    }

    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
    }

    // Utility Methods
    startStatusUpdates() {
        setInterval(async () => {
            if (this.edpmtClient && this.edpmtClient.isConnected()) {
                try {
                    await this.refreshPeripheralStatus();
                } catch (error) {
                    console.error('Status update failed:', error);
                }
            }
        }, this.config.updateInterval);
    }

    async refreshPeripheralStatus() {
        try {
            const status = await this.edpmtClient.getStatus();
            this.updatePeripheralStatus(status);
        } catch (error) {
            console.error('❌ Failed to refresh status:', error);
        }
    }

    updatePeripheralStatus(status) {
        // Update GPIO pin states
        if (status.gpio) {
            Object.entries(status.gpio).forEach(([pin, state]) => {
                const pinElement = document.querySelector(`[data-pin="${pin}"]`);
                if (pinElement) {
                    pinElement.classList.toggle('active', state.value === 1);
                    pinElement.querySelector('.pin-status').textContent = state.value ? 'ON' : 'OFF';
                }
            });
        }

        // Update protocol status
        if (status.i2c) {
            document.getElementById('i2c-status').textContent = status.i2c.active ? 'Active' : 'Inactive';
        }

        if (status.spi) {
            document.getElementById('spi-status').textContent = status.spi.ready ? 'Ready' : 'Not Ready';
        }

        if (status.uart) {
            document.getElementById('uart-status').textContent = `${status.uart.baudrate} baud`;
        }
    }

    updateI2CDevices(devices) {
        const deviceList = document.getElementById('i2c-devices');
        deviceList.innerHTML = devices.map(device => 
            `<div class="device-item">0x${device.address.toString(16).padStart(2, '0')}</div>`
        ).join('');
    }

    // Drag and Drop Implementation
    handleDragStart(e) {
        const blockData = {
            type: e.target.dataset.type,
            html: e.target.outerHTML
        };
        e.dataTransfer.setData('application/json', JSON.stringify(blockData));
    }

    handleDragOver(e) {
        e.preventDefault();
    }

    handleDrop(e) {
        e.preventDefault();
        try {
            const blockData = JSON.parse(e.dataTransfer.getData('application/json'));
            this.addBlockToCanvas(blockData, e.offsetX, e.offsetY);
        } catch (error) {
            console.error('Drop failed:', error);
        }
    }

    addBlockToCanvas(blockData, x, y) {
        const canvas = document.getElementById('programming-canvas');
        const placeholder = canvas.querySelector('.canvas-placeholder');
        if (placeholder) placeholder.style.display = 'none';

        const blockElement = document.createElement('div');
        blockElement.className = 'canvas-block';
        blockElement.style.left = `${x}px`;
        blockElement.style.top = `${y}px`;
        blockElement.innerHTML = `
            ${blockData.html}
            <button class="delete-btn" onclick="this.parentElement.remove()">×</button>
        `;

        canvas.appendChild(blockElement);
        this.updateProjectStatus('Modified');
    }

    getCanvasBlocks() {
        const blocks = [];
        document.querySelectorAll('.canvas-block').forEach(block => {
            // Extract block data from DOM element
            // This would be more sophisticated in a real implementation
            blocks.push({
                type: block.querySelector('.block').dataset.type,
                position: {
                    x: parseInt(block.style.left),
                    y: parseInt(block.style.top)
                }
            });
        });
        return blocks;
    }

    clearCanvas() {
        const canvas = document.getElementById('programming-canvas');
        canvas.querySelectorAll('.canvas-block').forEach(block => block.remove());
        const placeholder = canvas.querySelector('.canvas-placeholder');
        if (placeholder) placeholder.style.display = 'block';
        this.updateProjectStatus('Modified');
    }

    // Settings Management
    saveSettings() {
        this.config.backendUrl = document.getElementById('backend-url').value;
        this.config.updateInterval = parseInt(document.getElementById('update-interval').value);
        this.config.hardwareMode = document.getElementById('hardware-mode').value;
        this.config.enableLogging = document.getElementById('enable-logging').checked;
        
        this.saveConfig();
        this.closeModal('settings-modal');
        this.addLogEntry('success', 'Settings saved');
    }

    async emergencyStop() {
        try {
            await this.edpmtClient.emergencyStop();
            this.executionState = 'stopped';
            this.updateExecutionButtons();
            this.addLogEntry('warning', 'Emergency stop activated');
        } catch (error) {
            console.error('❌ Emergency stop failed:', error);
            this.addLogEntry('error', 'Emergency stop failed');
        }
    }

    showHelp() {
        window.open('README.md', '_blank');
    }

    openPageEditor() {
        this.openModal('page-editor-modal');
        // Load current page content into editor
        document.getElementById('html-editor-textarea').value = document.documentElement.outerHTML;
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.edpmtApp = new EDPMTApp();
});
