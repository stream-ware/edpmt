class VisualProgramming {
    constructor() {
        this.canvas = document.getElementById('canvas');
        this.consoleOutput = document.querySelector('.console-output');
        this.generatedCode = document.querySelector('.generated-code');
        this.connectionStatus = document.getElementById('connection-status');
        this.executionTime = document.getElementById('execution-time');
        
        this.websocket = null;
        this.serverUrl = 'wss://localhost:8888/ws';
        this.blockIdCounter = 0;
        this.variables = {};
        this.programBlocks = [];
        
        this.initializeEventListeners();
        this.connectToServer();
    }

    initializeEventListeners() {
        // Drag and Drop
        this.initializeDragAndDrop();
        
        // Button events
        document.getElementById('runButton').addEventListener('click', () => this.runProgram());
        document.getElementById('clearButton').addEventListener('click', () => this.clearCanvas());
        document.getElementById('saveButton').addEventListener('click', () => this.saveProgram());
        document.getElementById('loadButton').addEventListener('click', () => this.loadProgram());
        
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });
        
        // Template buttons
        document.querySelectorAll('.template-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.loadTemplate(e.target.dataset.template));
        });
        
        // Connection modal
        document.getElementById('connectBtn').addEventListener('click', () => this.connectToServer());
        document.querySelector('.close').addEventListener('click', () => {
            document.getElementById('connectionModal').style.display = 'none';
        });
    }

    initializeDragAndDrop() {
        // Make blocks draggable
        document.querySelectorAll('.block[draggable="true"]').forEach(block => {
            block.addEventListener('dragstart', (e) => this.handleDragStart(e));
        });

        // Canvas drop zone
        this.canvas.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.canvas.addEventListener('drop', (e) => this.handleDrop(e));
    }

    handleDragStart(e) {
        const blockData = {
            type: e.target.dataset.type,
            html: e.target.outerHTML
        };
        e.dataTransfer.setData('text/plain', JSON.stringify(blockData));
        e.target.classList.add('dragging');
    }

    handleDragOver(e) {
        e.preventDefault();
        this.canvas.classList.add('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        this.canvas.classList.remove('drag-over');
        
        try {
            const blockData = JSON.parse(e.dataTransfer.getData('text/plain'));
            this.addBlockToCanvas(blockData);
        } catch (error) {
            console.error('Error parsing dropped data:', error);
        }
    }

    addBlockToCanvas(blockData) {
        const blockId = `block_${this.blockIdCounter++}`;
        const blockElement = document.createElement('div');
        blockElement.className = `canvas-block ${blockData.type}`;
        blockElement.dataset.blockId = blockId;
        blockElement.dataset.type = blockData.type;
        blockElement.innerHTML = blockData.html.replace('<div class="block', '<div class="block-content') + 
            `<button class="delete-btn" onclick="visualProgramming.removeBlock('${blockId}')">×</button>`;
        
        this.canvas.appendChild(blockElement);
        this.updateGeneratedCode();
    }

    removeBlock(blockId) {
        const block = document.querySelector(`[data-block-id="${blockId}"]`);
        if (block) {
            block.remove();
            this.updateGeneratedCode();
        }
    }

    clearCanvas() {
        const blocks = this.canvas.querySelectorAll('.canvas-block');
        blocks.forEach(block => block.remove());
        this.updateGeneratedCode();
        this.log('Canvas cleared');
    }

    async runProgram() {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            this.log('❌ Not connected to EDPMT server');
            return;
        }

        const startTime = Date.now();
        this.log('🚀 Starting program execution...');
        
        const blocks = Array.from(this.canvas.querySelectorAll('.canvas-block'));
        
        for (const block of blocks) {
            await this.executeBlock(block);
        }
        
        const executionTime = Date.now() - startTime;
        this.executionTime.textContent = `Execution: ${executionTime}ms`;
        this.log(`✅ Program completed in ${executionTime}ms`);
    }

    async executeBlock(blockElement) {
        const blockType = blockElement.dataset.type;
        const inputs = this.extractBlockInputs(blockElement);
        
        try {
            switch (blockType) {
                case 'gpio-set':
                    await this.executeCommand('set', 'gpio', {
                        pin: parseInt(inputs.pin),
                        value: parseInt(inputs.value)
                    });
                    break;
                    
                case 'gpio-get':
                    const gpioValue = await this.executeCommand('get', 'gpio', {
                        pin: parseInt(inputs.pin)
                    });
                    this.variables[`gpio_${inputs.pin}`] = gpioValue;
                    break;
                    
                case 'gpio-pwm':
                    await this.executeCommand('pwm', 'gpio', {
                        pin: parseInt(inputs.pin),
                        frequency: parseFloat(inputs.frequency),
                        duty_cycle: parseFloat(inputs.duty)
                    });
                    break;
                    
                case 'i2c-scan':
                    const devices = await this.executeCommand('scan', 'i2c', {});
                    this.variables['i2c_devices'] = devices;
                    break;
                    
                case 'i2c-read':
                    const data = await this.executeCommand('read', 'i2c', {
                        device: parseInt(inputs.device, 16),
                        register: parseInt(inputs.register, 16),
                        length: parseInt(inputs.length)
                    });
                    this.variables[`i2c_${inputs.device}_${inputs.register}`] = data;
                    break;
                    
                case 'i2c-write':
                    await this.executeCommand('write', 'i2c', {
                        device: parseInt(inputs.device, 16),
                        register: parseInt(inputs.register, 16),
                        data: this.hexStringToBytes(inputs.data)
                    });
                    break;
                    
                case 'audio-play':
                    await this.executeCommand('play', 'audio', {
                        frequency: parseFloat(inputs.frequency),
                        duration: parseFloat(inputs.duration)
                    });
                    break;
                    
                case 'delay':
                    await this.delay(parseFloat(inputs.seconds) * 1000);
                    this.log(`⏱️ Waited ${inputs.seconds} seconds`);
                    break;
                    
                case 'repeat':
                    const times = parseInt(inputs.times);
                    const nestedBlocks = blockElement.querySelectorAll('.block-container .canvas-block');
                    for (let i = 0; i < times; i++) {
                        for (const nestedBlock of nestedBlocks) {
                            await this.executeBlock(nestedBlock);
                        }
                    }
                    break;
            }
        } catch (error) {
            this.log(`❌ Error executing ${blockType}: ${error.message}`);
        }
    }

    async executeCommand(action, target, params) {
        return new Promise((resolve, reject) => {
            const message = {
                action,
                target,
                params,
                id: Date.now().toString()
            };
            
            const timeout = setTimeout(() => {
                reject(new Error('Command timeout'));
            }, 5000);
            
            const handler = (event) => {
                const response = JSON.parse(event.data);
                if (response.id === message.id) {
                    clearTimeout(timeout);
                    this.websocket.removeEventListener('message', handler);
                    
                    if (response.success) {
                        this.log(`✅ ${action} ${target}: ${JSON.stringify(response.result)}`);
                        resolve(response.result);
                    } else {
                        this.log(`❌ ${action} ${target}: ${response.error}`);
                        reject(new Error(response.error));
                    }
                }
            };
            
            this.websocket.addEventListener('message', handler);
            this.websocket.send(JSON.stringify(message));
            this.log(`📤 ${action} ${target}: ${JSON.stringify(params)}`);
        });
    }

    extractBlockInputs(blockElement) {
        const inputs = {};
        const inputElements = blockElement.querySelectorAll('input, select');
        
        inputElements.forEach(input => {
            const label = input.previousSibling?.textContent?.trim();
            if (label) {
                const key = label.toLowerCase().replace(':', '').replace(/\s+/g, '_');
                inputs[key] = input.value;
            }
        });
        
        return inputs;
    }

    updateGeneratedCode() {
        const blocks = Array.from(this.canvas.querySelectorAll('.canvas-block'));
        let code = '# Generated EDPMT Program\n\n';
        
        blocks.forEach((block, index) => {
            const blockType = block.dataset.type;
            const inputs = this.extractBlockInputs(block);
            
            code += `# Block ${index + 1}: ${blockType}\n`;
            code += this.generateCodeForBlock(blockType, inputs);
            code += '\n';
        });
        
        this.generatedCode.textContent = code;
    }

    generateCodeForBlock(blockType, inputs) {
        switch (blockType) {
            case 'gpio-set':
                return `await edpmt.execute('set', 'gpio', pin=${inputs.pin}, value=${inputs.value})`;
            case 'gpio-get':
                return `gpio_${inputs.pin} = await edpmt.execute('get', 'gpio', pin=${inputs.pin})`;
            case 'gpio-pwm':
                return `await edpmt.execute('pwm', 'gpio', pin=${inputs.pin}, frequency=${inputs.frequency}, duty_cycle=${inputs.duty})`;
            case 'i2c-scan':
                return `i2c_devices = await edpmt.execute('scan', 'i2c')`;
            case 'i2c-read':
                return `data = await edpmt.execute('read', 'i2c', device=0x${inputs.device}, register=0x${inputs.register}, length=${inputs.length})`;
            case 'i2c-write':
                return `await edpmt.execute('write', 'i2c', device=0x${inputs.device}, register=0x${inputs.register}, data='${inputs.data}')`;
            case 'audio-play':
                return `await edpmt.execute('play', 'audio', frequency=${inputs.frequency}, duration=${inputs.duration})`;
            case 'delay':
                return `await sleep(${inputs.seconds})`;
            case 'repeat':
                return `for i in range(${inputs.times}):\n    # Nested blocks here`;
            default:
                return `# Unknown block type: ${blockType}`;
        }
    }

    loadTemplate(templateName) {
        this.clearCanvas();
        
        const templates = {
            'led-blink': this.createLedBlinkTemplate,
            'sensor-monitor': this.createSensorMonitorTemplate,
            'traffic-light': this.createTrafficLightTemplate,
            'alarm-system': this.createAlarmSystemTemplate
        };
        
        if (templates[templateName]) {
            templates[templateName].call(this);
            this.log(`📋 Loaded template: ${templateName}`);
        }
    }

    createLedBlinkTemplate() {
        // Add repeat block with GPIO set blocks inside
        const blocks = [
            { type: 'repeat', inputs: { times: '10' } },
            { type: 'gpio-set', inputs: { pin: '17', value: '1' } },
            { type: 'delay', inputs: { seconds: '0.5' } },
            { type: 'gpio-set', inputs: { pin: '17', value: '0' } },
            { type: 'delay', inputs: { seconds: '0.5' } }
        ];
        
        this.addBlocksFromTemplate(blocks);
    }

    createSensorMonitorTemplate() {
        const blocks = [
            { type: 'i2c-scan', inputs: {} },
            { type: 'i2c-read', inputs: { device: '76', register: 'D0', length: '1' } },
            { type: 'delay', inputs: { seconds: '1' } },
            { type: 'audio-play', inputs: { frequency: '440', duration: '0.2' } }
        ];
        
        this.addBlocksFromTemplate(blocks);
    }

    createTrafficLightTemplate() {
        const blocks = [
            { type: 'gpio-set', inputs: { pin: '17', value: '1' } }, // Red
            { type: 'delay', inputs: { seconds: '3' } },
            { type: 'gpio-set', inputs: { pin: '17', value: '0' } },
            { type: 'gpio-set', inputs: { pin: '18', value: '1' } }, // Yellow
            { type: 'delay', inputs: { seconds: '1' } },
            { type: 'gpio-set', inputs: { pin: '18', value: '0' } },
            { type: 'gpio-set', inputs: { pin: '19', value: '1' } }, // Green
            { type: 'delay', inputs: { seconds: '3' } },
            { type: 'gpio-set', inputs: { pin: '19', value: '0' } }
        ];
        
        this.addBlocksFromTemplate(blocks);
    }

    createAlarmSystemTemplate() {
        const blocks = [
            { type: 'gpio-get', inputs: { pin: '20' } }, // Motion sensor
            { type: 'if-condition', inputs: { condition: 'gpio-high', pin: '20' } },
            { type: 'audio-beep', inputs: { pattern: 'sos' } },
            { type: 'gpio-set', inputs: { pin: '21', value: '1' } }, // Alarm LED
            { type: 'delay', inputs: { seconds: '5' } },
            { type: 'gpio-set', inputs: { pin: '21', value: '0' } }
        ];
        
        this.addBlocksFromTemplate(blocks);
    }

    addBlocksFromTemplate(blocks) {
        blocks.forEach(blockData => {
            const blockElement = this.createBlockElement(blockData);
            this.canvas.appendChild(blockElement);
        });
        this.updateGeneratedCode();
    }

    createBlockElement(blockData) {
        const blockId = `block_${this.blockIdCounter++}`;
        const blockElement = document.createElement('div');
        blockElement.className = `canvas-block ${blockData.type}`;
        blockElement.dataset.blockId = blockId;
        blockElement.dataset.type = blockData.type;
        
        // Create block content based on type
        let content = `<div class="block-header">${this.getBlockTitle(blockData.type)}</div>`;
        content += '<div class="block-inputs">';
        
        Object.entries(blockData.inputs).forEach(([key, value]) => {
            content += `${key}: <input type="text" value="${value}"> `;
        });
        
        content += '</div>';
        content += `<button class="delete-btn" onclick="visualProgramming.removeBlock('${blockId}')">×</button>`;
        
        blockElement.innerHTML = content;
        return blockElement;
    }

    getBlockTitle(type) {
        const titles = {
            'gpio-set': 'Set GPIO Pin',
            'gpio-get': 'Read GPIO Pin',
            'gpio-pwm': 'PWM GPIO Pin',
            'i2c-scan': 'Scan I2C Bus',
            'i2c-read': 'Read I2C Device',
            'i2c-write': 'Write I2C Device',
            'audio-play': 'Play Tone',
            'audio-beep': 'Beep Pattern',
            'delay': 'Wait',
            'repeat': 'Repeat',
            'if-condition': 'If'
        };
        return titles[type] || type;
    }

    connectToServer() {
        const serverUrlInput = document.getElementById('serverUrl');
        if (serverUrlInput) {
            this.serverUrl = serverUrlInput.value.replace('https://', 'wss://').replace('http://', 'ws://') + '/ws';
        }
        
        try {
            this.websocket = new WebSocket(this.serverUrl);
            
            this.websocket.onopen = () => {
                this.connectionStatus.textContent = 'Connected';
                this.connectionStatus.className = 'status connected';
                this.log('🔌 Connected to EDPMT server');
                document.getElementById('connectionModal').style.display = 'none';
            };
            
            this.websocket.onclose = () => {
                this.connectionStatus.textContent = 'Disconnected';
                this.connectionStatus.className = 'status disconnected';
                this.log('🔌 Disconnected from EDPMT server');
            };
            
            this.websocket.onerror = (error) => {
                this.log(`❌ WebSocket error: ${error.message}`);
                document.getElementById('connectionModal').style.display = 'block';
            };
            
        } catch (error) {
            this.log(`❌ Connection error: ${error.message}`);
            document.getElementById('connectionModal').style.display = 'block';
        }
    }

    switchTab(tabName) {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(tabName).classList.add('active');
        
        if (tabName === 'variables') {
            this.updateVariablesList();
        }
    }

    updateVariablesList() {
        const variablesList = document.querySelector('.variables-list');
        variablesList.innerHTML = '';
        
        Object.entries(this.variables).forEach(([name, value]) => {
            const variableDiv = document.createElement('div');
            variableDiv.innerHTML = `<strong>${name}:</strong> ${JSON.stringify(value)}`;
            variablesList.appendChild(variableDiv);
        });
    }

    saveProgram() {
        const program = {
            blocks: Array.from(this.canvas.querySelectorAll('.canvas-block')).map(block => ({
                type: block.dataset.type,
                inputs: this.extractBlockInputs(block)
            }))
        };
        
        const blob = new Blob([JSON.stringify(program, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'edpmt_program.json';
        a.click();
        URL.revokeObjectURL(url);
        
        this.log('💾 Program saved');
    }

    loadProgram() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    try {
                        const program = JSON.parse(e.target.result);
                        this.clearCanvas();
                        this.addBlocksFromTemplate(program.blocks);
                        this.log('📁 Program loaded');
                    } catch (error) {
                        this.log(`❌ Error loading program: ${error.message}`);
                    }
                };
                reader.readAsText(file);
            }
        };
        input.click();
    }

    hexStringToBytes(hexString) {
        const bytes = [];
        for (let i = 0; i < hexString.length; i += 2) {
            bytes.push(parseInt(hexString.substr(i, 2), 16));
        }
        return bytes;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    log(message) {
        const timestamp = new Date().toLocaleTimeString();
        this.consoleOutput.textContent += `[${timestamp}] ${message}\n`;
        this.consoleOutput.scrollTop = this.consoleOutput.scrollHeight;
    }
}

// Initialize the visual programming interface
const visualProgramming = new VisualProgramming();
