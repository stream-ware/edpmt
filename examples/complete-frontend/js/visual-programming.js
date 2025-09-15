/**
 * Visual Programming Module - Drag-and-drop block programming interface
 * Handles block palette, canvas operations, and project management
 */

class VisualProgramming {
    constructor(edpmtClient, canvas, palette) {
        this.edpmtClient = edpmtClient;
        this.canvas = canvas;
        this.palette = palette;
        
        this.blocks = new Map();
        this.connections = new Map();
        this.selectedBlock = null;
        this.dragState = {
            isDragging: false,
            dragElement: null,
            offset: { x: 0, y: 0 }
        };
        
        this.blockTypes = this.initializeBlockTypes();
        this.init();
    }

    init() {
        this.setupCanvas();
        this.setupPalette();
        this.setupEventListeners();
        this.loadTemplates();
    }

    initializeBlockTypes() {
        return {
            'gpio-output': {
                name: 'GPIO Output',
                icon: 'fas fa-lightbulb',
                color: '#ef4444',
                inputs: ['trigger'],
                outputs: ['complete'],
                params: {
                    pin: { type: 'number', default: 18, min: 0, max: 40 },
                    value: { type: 'select', options: ['0', '1'], default: '1' },
                    duration: { type: 'number', default: 1000, min: 0 }
                },
                category: 'gpio'
            },
            'gpio-input': {
                name: 'GPIO Input',
                icon: 'fas fa-download',
                color: '#10b981',
                inputs: [],
                outputs: ['value', 'change'],
                params: {
                    pin: { type: 'number', default: 2, min: 0, max: 40 },
                    mode: { type: 'select', options: ['pull-up', 'pull-down', 'floating'], default: 'pull-up' },
                    trigger: { type: 'select', options: ['rising', 'falling', 'both'], default: 'both' }
                },
                category: 'gpio'
            },
            'delay': {
                name: 'Delay',
                icon: 'fas fa-clock',
                color: '#f59e0b',
                inputs: ['trigger'],
                outputs: ['complete'],
                params: {
                    duration: { type: 'number', default: 1000, min: 0 }
                },
                category: 'control'
            },
            'loop': {
                name: 'Loop',
                icon: 'fas fa-redo',
                color: '#8b5cf6',
                inputs: ['trigger'],
                outputs: ['iteration', 'complete'],
                params: {
                    count: { type: 'number', default: 5, min: 1 },
                    infinite: { type: 'checkbox', default: false }
                },
                category: 'control'
            },
            'condition': {
                name: 'Condition',
                icon: 'fas fa-question',
                color: '#06b6d4',
                inputs: ['trigger', 'value'],
                outputs: ['true', 'false'],
                params: {
                    operator: { type: 'select', options: ['==', '!=', '>', '<', '>=', '<='], default: '==' },
                    value: { type: 'text', default: '1' }
                },
                category: 'logic'
            },
            'pwm': {
                name: 'PWM Output',
                icon: 'fas fa-wave-square',
                color: '#ec4899',
                inputs: ['trigger', 'duty'],
                outputs: ['complete'],
                params: {
                    pin: { type: 'number', default: 18, min: 0, max: 40 },
                    frequency: { type: 'number', default: 1000, min: 1 },
                    duty_cycle: { type: 'number', default: 50, min: 0, max: 100 }
                },
                category: 'gpio'
            },
            'i2c-read': {
                name: 'I2C Read',
                icon: 'fas fa-download',
                color: '#14b8a6',
                inputs: ['trigger'],
                outputs: ['data', 'error'],
                params: {
                    address: { type: 'text', default: '0x48' },
                    register: { type: 'text', default: '0x00' },
                    length: { type: 'number', default: 1, min: 1 }
                },
                category: 'i2c'
            },
            'i2c-write': {
                name: 'I2C Write',
                icon: 'fas fa-upload',
                color: '#f97316',
                inputs: ['trigger', 'data'],
                outputs: ['complete', 'error'],
                params: {
                    address: { type: 'text', default: '0x48' },
                    register: { type: 'text', default: '0x00' }
                },
                category: 'i2c'
            },
            'start': {
                name: 'Start',
                icon: 'fas fa-play',
                color: '#22c55e',
                inputs: [],
                outputs: ['trigger'],
                params: {
                    auto_start: { type: 'checkbox', default: true }
                },
                category: 'control'
            },
            'log': {
                name: 'Log Message',
                icon: 'fas fa-file-text',
                color: '#6b7280',
                inputs: ['trigger', 'message'],
                outputs: ['complete'],
                params: {
                    message: { type: 'text', default: 'Debug message' },
                    level: { type: 'select', options: ['debug', 'info', 'warning', 'error'], default: 'info' }
                },
                category: 'debug'
            }
        };
    }

    setupCanvas() {
        // Canvas event listeners
        this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
        this.canvas.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.canvas.addEventListener('drop', (e) => this.handleDrop(e));
        this.canvas.addEventListener('contextmenu', (e) => this.handleContextMenu(e));

        // Make canvas blocks moveable
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
    }

    setupPalette() {
        const categories = ['control', 'gpio', 'i2c', 'spi', 'uart', 'logic', 'debug'];
        
        categories.forEach(category => {
            const panel = document.getElementById(`${category}-panel`);
            if (!panel) return;
            
            const blocks = Object.entries(this.blockTypes)
                .filter(([_, type]) => type.category === category);
            
            panel.innerHTML = blocks.map(([key, type]) => 
                this.createPaletteBlock(key, type)
            ).join('');
        });

        // Make palette blocks draggable
        document.querySelectorAll('.palette-block').forEach(block => {
            block.addEventListener('dragstart', (e) => this.handlePaletteDragStart(e));
        });
    }

    createPaletteBlock(key, type) {
        return `
            <div class="palette-block" draggable="true" data-type="${key}">
                <div class="block-icon" style="color: ${type.color}">
                    <i class="${type.icon}"></i>
                </div>
                <div class="block-info">
                    <div class="block-name">${type.name}</div>
                    <div class="block-description">${this.getBlockDescription(type)}</div>
                </div>
            </div>
        `;
    }

    getBlockDescription(type) {
        const inputCount = type.inputs ? type.inputs.length : 0;
        const outputCount = type.outputs ? type.outputs.length : 0;
        return `${inputCount} inputs, ${outputCount} outputs`;
    }

    setupEventListeners() {
        // Block selection
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Delete' || e.key === 'Backspace') {
                this.deleteSelectedBlock();
            } else if (e.key === 'Escape') {
                this.clearSelection();
            }
        });

        // Connection mode toggle
        document.addEventListener('keydown', (e) => {
            if (e.key === 'c' && e.ctrlKey) {
                e.preventDefault();
                this.toggleConnectionMode();
            }
        });
    }

    handlePaletteDragStart(e) {
        const blockType = e.target.closest('.palette-block').dataset.type;
        e.dataTransfer.setData('application/json', JSON.stringify({
            type: 'palette-block',
            blockType: blockType
        }));
        e.dataTransfer.effectAllowed = 'copy';
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
    }

    handleDrop(e) {
        e.preventDefault();
        
        try {
            const data = JSON.parse(e.dataTransfer.getData('application/json'));
            
            if (data.type === 'palette-block') {
                const rect = this.canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                this.addBlock(data.blockType, x, y);
            }
        } catch (error) {
            console.error('Drop failed:', error);
        }
    }

    addBlock(typeKey, x, y) {
        const type = this.blockTypes[typeKey];
        if (!type) return null;

        const blockId = this.generateId();
        const block = {
            id: blockId,
            type: typeKey,
            typeInfo: type,
            position: { x, y },
            params: this.getDefaultParams(type),
            connections: { inputs: {}, outputs: {} }
        };

        this.blocks.set(blockId, block);
        this.renderBlock(block);
        this.selectBlock(blockId);
        
        return blockId;
    }

    getDefaultParams(type) {
        const params = {};
        if (type.params) {
            Object.entries(type.params).forEach(([key, param]) => {
                params[key] = param.default;
            });
        }
        return params;
    }

    renderBlock(block) {
        // Hide canvas placeholder if this is the first block
        const placeholder = this.canvas.querySelector('.canvas-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }

        const blockElement = document.createElement('div');
        blockElement.className = 'canvas-block';
        blockElement.dataset.blockId = block.id;
        blockElement.style.left = `${block.position.x}px`;
        blockElement.style.top = `${block.position.y}px`;
        
        blockElement.innerHTML = `
            <div class="block-header" style="background-color: ${block.typeInfo.color}">
                <i class="${block.typeInfo.icon}"></i>
                <span class="block-title">${block.typeInfo.name}</span>
                <button class="block-menu-btn" data-action="menu">⋮</button>
            </div>
            <div class="block-body">
                ${this.renderBlockInputs(block)}
                ${this.renderBlockOutputs(block)}
                ${this.renderBlockParams(block)}
            </div>
            <div class="block-resize-handle"></div>
        `;

        // Add event listeners
        blockElement.addEventListener('click', (e) => this.selectBlock(block.id));
        blockElement.addEventListener('dblclick', (e) => this.editBlock(block.id));
        
        // Add to canvas
        this.canvas.appendChild(blockElement);
    }

    renderBlockInputs(block) {
        if (!block.typeInfo.inputs || block.typeInfo.inputs.length === 0) {
            return '';
        }

        return `
            <div class="block-inputs">
                ${block.typeInfo.inputs.map(input => `
                    <div class="block-connector input-connector" data-connector="${input}">
                        <div class="connector-dot"></div>
                        <span class="connector-label">${input}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderBlockOutputs(block) {
        if (!block.typeInfo.outputs || block.typeInfo.outputs.length === 0) {
            return '';
        }

        return `
            <div class="block-outputs">
                ${block.typeInfo.outputs.map(output => `
                    <div class="block-connector output-connector" data-connector="${output}">
                        <span class="connector-label">${output}</span>
                        <div class="connector-dot"></div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderBlockParams(block) {
        if (!block.typeInfo.params || Object.keys(block.typeInfo.params).length === 0) {
            return '';
        }

        return `
            <div class="block-params">
                ${Object.entries(block.typeInfo.params).map(([key, param]) => `
                    <div class="param-row">
                        <label class="param-label">${key}:</label>
                        ${this.renderParamInput(key, param, block.params[key])}
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderParamInput(key, param, value) {
        switch (param.type) {
            case 'number':
                return `<input type="number" class="param-input" data-param="${key}" value="${value}" min="${param.min || ''}" max="${param.max || ''}">`;
            
            case 'text':
                return `<input type="text" class="param-input" data-param="${key}" value="${value}">`;
            
            case 'select':
                return `
                    <select class="param-input" data-param="${key}">
                        ${param.options.map(option => 
                            `<option value="${option}" ${option === value ? 'selected' : ''}>${option}</option>`
                        ).join('')}
                    </select>
                `;
            
            case 'checkbox':
                return `<input type="checkbox" class="param-input" data-param="${key}" ${value ? 'checked' : ''}>`;
            
            default:
                return `<input type="text" class="param-input" data-param="${key}" value="${value}">`;
        }
    }

    selectBlock(blockId) {
        // Clear previous selection
        this.clearSelection();
        
        // Select new block
        this.selectedBlock = blockId;
        const blockElement = document.querySelector(`[data-block-id="${blockId}"]`);
        if (blockElement) {
            blockElement.classList.add('selected');
        }
    }

    clearSelection() {
        if (this.selectedBlock) {
            const blockElement = document.querySelector(`[data-block-id="${this.selectedBlock}"]`);
            if (blockElement) {
                blockElement.classList.remove('selected');
            }
            this.selectedBlock = null;
        }
    }

    deleteSelectedBlock() {
        if (this.selectedBlock) {
            this.deleteBlock(this.selectedBlock);
        }
    }

    deleteBlock(blockId) {
        // Remove connections
        this.removeBlockConnections(blockId);
        
        // Remove from DOM
        const blockElement = document.querySelector(`[data-block-id="${blockId}"]`);
        if (blockElement) {
            blockElement.remove();
        }
        
        // Remove from blocks map
        this.blocks.delete(blockId);
        
        // Clear selection if this was selected
        if (this.selectedBlock === blockId) {
            this.selectedBlock = null;
        }

        // Show placeholder if no blocks left
        if (this.blocks.size === 0) {
            const placeholder = this.canvas.querySelector('.canvas-placeholder');
            if (placeholder) {
                placeholder.style.display = 'block';
            }
        }
    }

    editBlock(blockId) {
        const block = this.blocks.get(blockId);
        if (!block) return;

        // Open block editor modal with block data
        window.edpmtApp.blockEditor.openEditor(block);
    }

    // Mouse handling for block movement
    handleMouseDown(e) {
        const blockElement = e.target.closest('.canvas-block');
        if (!blockElement || e.target.closest('.block-connector')) return;

        this.dragState.isDragging = true;
        this.dragState.dragElement = blockElement;
        
        const rect = blockElement.getBoundingClientRect();
        this.dragState.offset = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };

        blockElement.style.zIndex = '1000';
        e.preventDefault();
    }

    handleMouseMove(e) {
        if (!this.dragState.isDragging || !this.dragState.dragElement) return;

        const canvasRect = this.canvas.getBoundingClientRect();
        const x = e.clientX - canvasRect.left - this.dragState.offset.x;
        const y = e.clientY - canvasRect.top - this.dragState.offset.y;

        this.dragState.dragElement.style.left = `${Math.max(0, x)}px`;
        this.dragState.dragElement.style.top = `${Math.max(0, y)}px`;

        // Update block position in data
        const blockId = this.dragState.dragElement.dataset.blockId;
        const block = this.blocks.get(blockId);
        if (block) {
            block.position.x = Math.max(0, x);
            block.position.y = Math.max(0, y);
        }
    }

    handleMouseUp(e) {
        if (this.dragState.isDragging && this.dragState.dragElement) {
            this.dragState.dragElement.style.zIndex = '';
        }

        this.dragState.isDragging = false;
        this.dragState.dragElement = null;
    }

    handleCanvasClick(e) {
        if (e.target === this.canvas) {
            this.clearSelection();
        }
    }

    handleContextMenu(e) {
        e.preventDefault();
        
        const blockElement = e.target.closest('.canvas-block');
        if (blockElement) {
            const blockId = blockElement.dataset.blockId;
            this.showBlockContextMenu(blockId, e.clientX, e.clientY);
        }
    }

    showBlockContextMenu(blockId, x, y) {
        // Create context menu
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.style.left = `${x}px`;
        menu.style.top = `${y}px`;
        menu.innerHTML = `
            <div class="context-menu-item" data-action="edit">Edit Block</div>
            <div class="context-menu-item" data-action="duplicate">Duplicate</div>
            <div class="context-menu-item" data-action="delete">Delete</div>
        `;

        // Add event listeners
        menu.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            this.handleContextMenuAction(blockId, action);
            menu.remove();
        });

        // Add to page
        document.body.appendChild(menu);

        // Remove on outside click
        setTimeout(() => {
            document.addEventListener('click', () => menu.remove(), { once: true });
        }, 0);
    }

    handleContextMenuAction(blockId, action) {
        switch (action) {
            case 'edit':
                this.editBlock(blockId);
                break;
            case 'duplicate':
                this.duplicateBlock(blockId);
                break;
            case 'delete':
                this.deleteBlock(blockId);
                break;
        }
    }

    duplicateBlock(blockId) {
        const originalBlock = this.blocks.get(blockId);
        if (!originalBlock) return;

        const newX = originalBlock.position.x + 20;
        const newY = originalBlock.position.y + 20;
        
        const newBlockId = this.addBlock(originalBlock.type, newX, newY);
        
        // Copy parameters
        const newBlock = this.blocks.get(newBlockId);
        if (newBlock) {
            newBlock.params = { ...originalBlock.params };
            // Re-render to show copied params
            this.updateBlockElement(newBlockId);
        }
    }

    updateBlockElement(blockId) {
        const blockElement = document.querySelector(`[data-block-id="${blockId}"]`);
        const block = this.blocks.get(blockId);
        
        if (blockElement && block) {
            // Update parameter values in DOM
            blockElement.querySelectorAll('.param-input').forEach(input => {
                const paramKey = input.dataset.param;
                const value = block.params[paramKey];
                
                if (input.type === 'checkbox') {
                    input.checked = value;
                } else {
                    input.value = value;
                }
            });
        }
    }

    removeBlockConnections(blockId) {
        // Remove all connections involving this block
        const connectionsToRemove = [];
        
        this.connections.forEach((connection, connectionId) => {
            if (connection.from.blockId === blockId || connection.to.blockId === blockId) {
                connectionsToRemove.push(connectionId);
            }
        });

        connectionsToRemove.forEach(connectionId => {
            this.connections.delete(connectionId);
        });

        // Remove visual connection lines
        this.renderConnections();
    }

    renderConnections() {
        // Remove existing connection lines
        this.canvas.querySelectorAll('.connection-line').forEach(line => line.remove());

        // Render all connections
        this.connections.forEach(connection => {
            this.renderConnection(connection);
        });
    }

    renderConnection(connection) {
        // This would render SVG lines between connected blocks
        // Implementation would depend on specific visual requirements
    }

    // Project serialization
    exportProject() {
        const blocks = Array.from(this.blocks.values()).map(block => ({
            id: block.id,
            type: block.type,
            position: block.position,
            params: block.params
        }));

        const connections = Array.from(this.connections.values());

        return {
            blocks: blocks,
            connections: connections,
            metadata: {
                version: '1.0',
                created: new Date().toISOString(),
                name: document.getElementById('project-name')?.value || 'Untitled Project'
            }
        };
    }

    importProject(projectData) {
        // Clear current project
        this.clearCanvas();
        
        // Import blocks
        projectData.blocks.forEach(blockData => {
            const blockId = this.addBlock(blockData.type, blockData.position.x, blockData.position.y);
            const block = this.blocks.get(blockId);
            
            if (block) {
                block.id = blockData.id; // Preserve original ID
                block.params = blockData.params;
                this.blocks.delete(blockId);
                this.blocks.set(blockData.id, block);
                
                // Update DOM element
                const element = document.querySelector(`[data-block-id="${blockId}"]`);
                if (element) {
                    element.dataset.blockId = blockData.id;
                    this.updateBlockElement(blockData.id);
                }
            }
        });

        // Import connections
        if (projectData.connections) {
            projectData.connections.forEach(connection => {
                this.connections.set(connection.id, connection);
            });
            this.renderConnections();
        }
    }

    clearCanvas() {
        // Remove all blocks
        this.canvas.querySelectorAll('.canvas-block').forEach(block => block.remove());
        
        // Clear data
        this.blocks.clear();
        this.connections.clear();
        this.selectedBlock = null;
        
        // Show placeholder
        const placeholder = this.canvas.querySelector('.canvas-placeholder');
        if (placeholder) {
            placeholder.style.display = 'block';
        }
    }

    loadTemplates() {
        // Load predefined project templates
        const templates = [
            {
                name: 'LED Blink',
                description: 'Simple LED blinking pattern',
                blocks: [
                    { type: 'start', position: { x: 50, y: 50 } },
                    { type: 'loop', position: { x: 200, y: 50 }, params: { count: 10 } },
                    { type: 'gpio-output', position: { x: 350, y: 50 }, params: { pin: 18, value: '1' } },
                    { type: 'delay', position: { x: 500, y: 50 }, params: { duration: 500 } },
                    { type: 'gpio-output', position: { x: 650, y: 50 }, params: { pin: 18, value: '0' } },
                    { type: 'delay', position: { x: 800, y: 50 }, params: { duration: 500 } }
                ]
            },
            {
                name: 'Button Monitor',
                description: 'Monitor button presses and control LED',
                blocks: [
                    { type: 'start', position: { x: 50, y: 50 } },
                    { type: 'gpio-input', position: { x: 200, y: 50 }, params: { pin: 2, mode: 'pull-up' } },
                    { type: 'condition', position: { x: 350, y: 50 }, params: { operator: '==', value: '0' } },
                    { type: 'gpio-output', position: { x: 500, y: 30 }, params: { pin: 18, value: '1' } },
                    { type: 'gpio-output', position: { x: 500, y: 90 }, params: { pin: 18, value: '0' } }
                ]
            }
        ];

        // Update templates panel
        const templatesPanel = document.getElementById('templates-panel');
        if (templatesPanel) {
            templatesPanel.innerHTML = templates.map(template => `
                <div class="template-item" data-template="${template.name}">
                    <div class="template-name">${template.name}</div>
                    <div class="template-description">${template.description}</div>
                </div>
            `).join('');

            // Add click handlers
            templatesPanel.querySelectorAll('.template-item').forEach(item => {
                item.addEventListener('click', () => {
                    const templateName = item.dataset.template;
                    const template = templates.find(t => t.name === templateName);
                    if (template) {
                        this.loadTemplate(template);
                    }
                });
            });
        }
    }

    loadTemplate(template) {
        this.clearCanvas();
        
        // Add blocks from template
        template.blocks.forEach((blockData, index) => {
            setTimeout(() => {
                const blockId = this.addBlock(blockData.type, blockData.position.x, blockData.position.y);
                const block = this.blocks.get(blockId);
                
                if (block && blockData.params) {
                    block.params = { ...block.params, ...blockData.params };
                    this.updateBlockElement(blockId);
                }
            }, index * 100); // Stagger creation for visual effect
        });
    }

    generateId() {
        return 'block_' + Math.random().toString(36).substr(2, 9);
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VisualProgramming;
} else if (typeof window !== 'undefined') {
    window.VisualProgramming = VisualProgramming;
}
