/**
 * Block Editor Component - Handles popup modal for editing block properties
 * Supports both visual parameter editing and raw JSON editing
 */

class BlockEditor {
    constructor(edpmtClient) {
        this.edpmtClient = edpmtClient;
        this.currentBlock = null;
        this.isOpen = false;
        this.originalData = null;
        
        this.modal = document.getElementById('block-editor-modal');
        this.visualEditor = document.getElementById('visual-editor');
        this.jsonEditor = document.getElementById('json-editor');
        this.jsonTextarea = document.getElementById('json-editor-textarea');
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupValidation();
    }

    setupEventListeners() {
        // Modal close buttons
        document.getElementById('close-block-editor').addEventListener('click', () => {
            this.closeEditor();
        });

        document.getElementById('cancel-block-edit').addEventListener('click', () => {
            this.cancelEdit();
        });

        // Save buttons
        document.getElementById('save-block-edit').addEventListener('click', () => {
            this.saveBlock();
        });

        document.getElementById('apply-block-edit').addEventListener('click', () => {
            this.applyChanges();
        });

        // Tab switching
        document.querySelectorAll('#block-editor-modal .editor-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.switchTab(btn.dataset.tab);
            });
        });

        // JSON validation and formatting
        document.getElementById('format-json-btn').addEventListener('click', () => {
            this.formatJSON();
        });

        document.getElementById('validate-json-btn').addEventListener('click', () => {
            this.validateJSON();
        });

        // Live parameter updates
        this.visualEditor.addEventListener('input', (e) => {
            if (e.target.classList.contains('param-input')) {
                this.updateParameter(e.target);
            }
        });

        // Block type changes
        document.getElementById('block-type-select')?.addEventListener('change', (e) => {
            this.changeBlockType(e.target.value);
        });

        // Advanced options
        document.getElementById('reset-block-btn')?.addEventListener('click', () => {
            this.resetBlock();
        });

        document.getElementById('duplicate-block-btn')?.addEventListener('click', () => {
            this.duplicateBlock();
        });

        document.getElementById('delete-block-btn')?.addEventListener('click', () => {
            this.deleteBlock();
        });
    }

    setupValidation() {
        // Set up real-time validation for parameters
        this.validationRules = {
            pin: {
                type: 'number',
                min: 0,
                max: 40,
                message: 'Pin must be between 0 and 40'
            },
            frequency: {
                type: 'number',
                min: 1,
                max: 100000,
                message: 'Frequency must be between 1 and 100000 Hz'
            },
            duty_cycle: {
                type: 'number',
                min: 0,
                max: 100,
                message: 'Duty cycle must be between 0 and 100%'
            },
            address: {
                type: 'hex',
                pattern: /^0x[0-9A-Fa-f]{2}$/,
                message: 'Address must be in hex format (e.g., 0x48)'
            }
        };
    }

    openEditor(block) {
        if (!block) return;

        this.currentBlock = block;
        this.originalData = JSON.parse(JSON.stringify(block)); // Deep copy
        this.isOpen = true;

        this.populateEditor();
        this.modal.classList.add('active');
        this.switchTab('visual-editor');
    }

    closeEditor() {
        this.modal.classList.remove('active');
        this.currentBlock = null;
        this.originalData = null;
        this.isOpen = false;
        this.clearValidationMessages();
    }

    cancelEdit() {
        if (this.hasUnsavedChanges()) {
            if (confirm('You have unsaved changes. Are you sure you want to cancel?')) {
                this.closeEditor();
            }
        } else {
            this.closeEditor();
        }
    }

    saveBlock() {
        if (!this.validateCurrentBlock()) {
            return;
        }

        // Apply changes to the original block
        this.applyChanges();
        
        // Update the visual block in the canvas
        this.updateCanvasBlock();
        
        // Close editor
        this.closeEditor();
        
        // Log the change
        this.addLogEntry('success', `Block "${this.currentBlock.typeInfo.name}" updated successfully`);
    }

    applyChanges() {
        if (!this.currentBlock) return;

        const currentTab = this.getCurrentTab();
        
        if (currentTab === 'visual-editor') {
            this.applyVisualChanges();
        } else if (currentTab === 'json-editor') {
            this.applyJSONChanges();
        }
    }

    applyVisualChanges() {
        // Collect all parameter values from visual editor
        const paramInputs = this.visualEditor.querySelectorAll('.param-input');
        const newParams = {};

        paramInputs.forEach(input => {
            const paramKey = input.dataset.param;
            let value;

            switch (input.type) {
                case 'number':
                    value = parseFloat(input.value) || 0;
                    break;
                case 'checkbox':
                    value = input.checked;
                    break;
                default:
                    value = input.value;
            }

            newParams[paramKey] = value;
        });

        // Update block parameters
        this.currentBlock.params = newParams;

        // Update block info if changed
        const blockName = document.getElementById('block-name-input')?.value;
        if (blockName && blockName !== this.currentBlock.typeInfo.name) {
            this.currentBlock.customName = blockName;
        }

        // Update JSON editor to reflect changes
        this.syncJSONEditor();
    }

    applyJSONChanges() {
        try {
            const jsonData = JSON.parse(this.jsonTextarea.value);
            
            // Validate the JSON structure
            if (!this.validateJSONStructure(jsonData)) {
                return;
            }

            // Apply JSON changes to current block
            Object.assign(this.currentBlock, jsonData);
            
            // Update visual editor to reflect changes
            this.syncVisualEditor();
            
        } catch (error) {
            this.showValidationError('json-error', `Invalid JSON: ${error.message}`);
        }
    }

    populateEditor() {
        if (!this.currentBlock) return;

        // Populate block header info
        document.getElementById('block-editor-title').textContent = 
            `Edit ${this.currentBlock.typeInfo.name}`;
        
        document.getElementById('block-name-input').value = 
            this.currentBlock.customName || this.currentBlock.typeInfo.name;

        // Populate visual editor
        this.populateVisualEditor();
        
        // Populate JSON editor
        this.populateJSONEditor();
    }

    populateVisualEditor() {
        const block = this.currentBlock;
        
        // Clear existing content
        const paramContainer = this.visualEditor.querySelector('.param-container');
        paramContainer.innerHTML = '';

        // Add block type info
        const typeInfo = document.createElement('div');
        typeInfo.className = 'block-type-info';
        typeInfo.innerHTML = `
            <div class="info-row">
                <label>Block Type:</label>
                <span class="block-type-badge" style="background-color: ${block.typeInfo.color}">
                    <i class="${block.typeInfo.icon}"></i>
                    ${block.typeInfo.name}
                </span>
            </div>
            <div class="info-row">
                <label>Block ID:</label>
                <span class="block-id">${block.id}</span>
            </div>
        `;
        paramContainer.appendChild(typeInfo);

        // Add parameters
        if (block.typeInfo.params) {
            const paramsSection = document.createElement('div');
            paramsSection.className = 'params-section';
            paramsSection.innerHTML = '<h3>Parameters</h3>';

            Object.entries(block.typeInfo.params).forEach(([key, paramDef]) => {
                const paramRow = this.createParameterRow(key, paramDef, block.params[key]);
                paramsSection.appendChild(paramRow);
            });

            paramContainer.appendChild(paramsSection);
        }

        // Add connections info
        this.addConnectionsInfo(paramContainer);

        // Add position info
        this.addPositionInfo(paramContainer);
    }

    createParameterRow(key, paramDef, currentValue) {
        const row = document.createElement('div');
        row.className = 'param-row';

        const label = document.createElement('label');
        label.className = 'param-label';
        label.textContent = this.formatParameterName(key);
        
        const inputContainer = document.createElement('div');
        inputContainer.className = 'param-input-container';

        const input = this.createParameterInput(key, paramDef, currentValue);
        inputContainer.appendChild(input);

        // Add validation message container
        const validation = document.createElement('div');
        validation.className = 'param-validation';
        validation.id = `validation-${key}`;
        inputContainer.appendChild(validation);

        // Add help text if available
        if (paramDef.help) {
            const help = document.createElement('div');
            help.className = 'param-help';
            help.textContent = paramDef.help;
            inputContainer.appendChild(help);
        }

        row.appendChild(label);
        row.appendChild(inputContainer);

        return row;
    }

    createParameterInput(key, paramDef, currentValue) {
        let input;

        switch (paramDef.type) {
            case 'number':
                input = document.createElement('input');
                input.type = 'number';
                input.value = currentValue;
                input.min = paramDef.min || '';
                input.max = paramDef.max || '';
                input.step = paramDef.step || 'any';
                break;

            case 'text':
                input = document.createElement('input');
                input.type = 'text';
                input.value = currentValue;
                input.placeholder = paramDef.placeholder || '';
                break;

            case 'select':
                input = document.createElement('select');
                paramDef.options.forEach(option => {
                    const optionElement = document.createElement('option');
                    optionElement.value = option;
                    optionElement.textContent = option;
                    optionElement.selected = option === currentValue;
                    input.appendChild(optionElement);
                });
                break;

            case 'checkbox':
                input = document.createElement('input');
                input.type = 'checkbox';
                input.checked = currentValue;
                break;

            case 'range':
                input = document.createElement('input');
                input.type = 'range';
                input.value = currentValue;
                input.min = paramDef.min || 0;
                input.max = paramDef.max || 100;
                input.step = paramDef.step || 1;
                
                // Add value display
                const valueDisplay = document.createElement('span');
                valueDisplay.className = 'range-value';
                valueDisplay.textContent = currentValue;
                
                input.addEventListener('input', () => {
                    valueDisplay.textContent = input.value;
                });
                
                const container = document.createElement('div');
                container.className = 'range-container';
                container.appendChild(input);
                container.appendChild(valueDisplay);
                return container;

            default:
                input = document.createElement('input');
                input.type = 'text';
                input.value = currentValue;
        }

        input.className = 'param-input';
        input.dataset.param = key;
        
        // Add validation
        input.addEventListener('blur', () => this.validateParameter(key, input));
        input.addEventListener('input', () => this.clearParameterValidation(key));

        return input;
    }

    addConnectionsInfo(container) {
        const block = this.currentBlock;
        const connectionsSection = document.createElement('div');
        connectionsSection.className = 'connections-section';
        connectionsSection.innerHTML = '<h3>Connections</h3>';

        // Input connections
        if (block.typeInfo.inputs && block.typeInfo.inputs.length > 0) {
            const inputsDiv = document.createElement('div');
            inputsDiv.className = 'connections-group';
            inputsDiv.innerHTML = `
                <h4>Inputs</h4>
                ${block.typeInfo.inputs.map(input => `
                    <div class="connection-item">
                        <span class="connection-name">${input}</span>
                        <span class="connection-status">Not connected</span>
                    </div>
                `).join('')}
            `;
            connectionsSection.appendChild(inputsDiv);
        }

        // Output connections
        if (block.typeInfo.outputs && block.typeInfo.outputs.length > 0) {
            const outputsDiv = document.createElement('div');
            outputsDiv.className = 'connections-group';
            outputsDiv.innerHTML = `
                <h4>Outputs</h4>
                ${block.typeInfo.outputs.map(output => `
                    <div class="connection-item">
                        <span class="connection-name">${output}</span>
                        <span class="connection-status">Not connected</span>
                    </div>
                `).join('')}
            `;
            connectionsSection.appendChild(outputsDiv);
        }

        container.appendChild(connectionsSection);
    }

    addPositionInfo(container) {
        const block = this.currentBlock;
        const positionSection = document.createElement('div');
        positionSection.className = 'position-section';
        positionSection.innerHTML = `
            <h3>Position</h3>
            <div class="position-inputs">
                <div class="param-row">
                    <label>X:</label>
                    <input type="number" id="block-x-pos" value="${block.position.x}" min="0">
                </div>
                <div class="param-row">
                    <label>Y:</label>
                    <input type="number" id="block-y-pos" value="${block.position.y}" min="0">
                </div>
            </div>
        `;

        // Add position update listeners
        positionSection.addEventListener('input', (e) => {
            if (e.target.id === 'block-x-pos' || e.target.id === 'block-y-pos') {
                this.updateBlockPosition();
            }
        });

        container.appendChild(positionSection);
    }

    populateJSONEditor() {
        if (!this.currentBlock) return;

        const blockData = {
            id: this.currentBlock.id,
            type: this.currentBlock.type,
            position: this.currentBlock.position,
            params: this.currentBlock.params,
            customName: this.currentBlock.customName
        };

        this.jsonTextarea.value = JSON.stringify(blockData, null, 2);
    }

    switchTab(tabName) {
        // Update tab buttons
        this.modal.querySelectorAll('.editor-tabs .tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update tab panels
        this.modal.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.toggle('active', panel.id === tabName);
        });

        // Sync editors when switching tabs
        if (tabName === 'json-editor') {
            this.syncJSONEditor();
        } else if (tabName === 'visual-editor') {
            this.syncVisualEditor();
        }
    }

    syncJSONEditor() {
        if (this.currentBlock) {
            this.populateJSONEditor();
        }
    }

    syncVisualEditor() {
        if (this.currentBlock) {
            // Update visual editor inputs to match current block data
            const paramInputs = this.visualEditor.querySelectorAll('.param-input');
            
            paramInputs.forEach(input => {
                const paramKey = input.dataset.param;
                const value = this.currentBlock.params[paramKey];
                
                if (input.type === 'checkbox') {
                    input.checked = value;
                } else {
                    input.value = value;
                }
            });
        }
    }

    getCurrentTab() {
        const activeTab = this.modal.querySelector('.editor-tabs .tab-btn.active');
        return activeTab ? activeTab.dataset.tab : 'visual-editor';
    }

    validateCurrentBlock() {
        const currentTab = this.getCurrentTab();
        
        if (currentTab === 'visual-editor') {
            return this.validateVisualEditor();
        } else if (currentTab === 'json-editor') {
            return this.validateJSONEditor();
        }
        
        return true;
    }

    validateVisualEditor() {
        let isValid = true;
        const paramInputs = this.visualEditor.querySelectorAll('.param-input');
        
        paramInputs.forEach(input => {
            const paramKey = input.dataset.param;
            if (!this.validateParameter(paramKey, input)) {
                isValid = false;
            }
        });

        return isValid;
    }

    validateJSONEditor() {
        try {
            const jsonData = JSON.parse(this.jsonTextarea.value);
            
            if (!this.validateJSONStructure(jsonData)) {
                return false;
            }
            
            this.clearValidationError('json-error');
            return true;
            
        } catch (error) {
            this.showValidationError('json-error', `Invalid JSON: ${error.message}`);
            return false;
        }
    }

    validateParameter(paramKey, input) {
        const rule = this.validationRules[paramKey];
        if (!rule) return true;

        const value = input.type === 'checkbox' ? input.checked : input.value;
        
        // Type validation
        if (rule.type === 'number') {
            const numValue = parseFloat(value);
            if (isNaN(numValue)) {
                this.showParameterError(paramKey, 'Must be a valid number');
                return false;
            }
            
            if (rule.min !== undefined && numValue < rule.min) {
                this.showParameterError(paramKey, `Must be at least ${rule.min}`);
                return false;
            }
            
            if (rule.max !== undefined && numValue > rule.max) {
                this.showParameterError(paramKey, `Must be at most ${rule.max}`);
                return false;
            }
        }
        
        // Pattern validation
        if (rule.pattern && !rule.pattern.test(value)) {
            this.showParameterError(paramKey, rule.message);
            return false;
        }

        this.clearParameterValidation(paramKey);
        return true;
    }

    validateJSONStructure(jsonData) {
        const requiredFields = ['id', 'type', 'position', 'params'];
        
        for (const field of requiredFields) {
            if (!(field in jsonData)) {
                this.showValidationError('json-error', `Missing required field: ${field}`);
                return false;
            }
        }

        if (typeof jsonData.position !== 'object' || 
            !('x' in jsonData.position) || !('y' in jsonData.position)) {
            this.showValidationError('json-error', 'Position must have x and y coordinates');
            return false;
        }

        return true;
    }

    showParameterError(paramKey, message) {
        const validationEl = document.getElementById(`validation-${paramKey}`);
        if (validationEl) {
            validationEl.textContent = message;
            validationEl.className = 'param-validation error';
        }
    }

    clearParameterValidation(paramKey) {
        const validationEl = document.getElementById(`validation-${paramKey}`);
        if (validationEl) {
            validationEl.textContent = '';
            validationEl.className = 'param-validation';
        }
    }

    showValidationError(elementId, message) {
        const errorEl = document.getElementById(elementId);
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.className = 'validation-error';
        }
    }

    clearValidationError(elementId) {
        const errorEl = document.getElementById(elementId);
        if (errorEl) {
            errorEl.textContent = '';
            errorEl.className = '';
        }
    }

    clearValidationMessages() {
        this.modal.querySelectorAll('.param-validation, .validation-error').forEach(el => {
            el.textContent = '';
            el.className = el.className.replace(/error|validation-error/, '').trim();
        });
    }

    formatJSON() {
        try {
            const jsonData = JSON.parse(this.jsonTextarea.value);
            this.jsonTextarea.value = JSON.stringify(jsonData, null, 2);
            this.clearValidationError('json-error');
        } catch (error) {
            this.showValidationError('json-error', `Cannot format invalid JSON: ${error.message}`);
        }
    }

    validateJSON() {
        this.validateJSONEditor();
    }

    updateParameter(input) {
        const paramKey = input.dataset.param;
        let value;

        switch (input.type) {
            case 'number':
                value = parseFloat(input.value) || 0;
                break;
            case 'checkbox':
                value = input.checked;
                break;
            default:
                value = input.value;
        }

        if (this.currentBlock) {
            this.currentBlock.params[paramKey] = value;
        }
    }

    updateBlockPosition() {
        const xInput = document.getElementById('block-x-pos');
        const yInput = document.getElementById('block-y-pos');
        
        if (this.currentBlock && xInput && yInput) {
            this.currentBlock.position.x = parseInt(xInput.value) || 0;
            this.currentBlock.position.y = parseInt(yInput.value) || 0;
            
            // Update canvas block position
            this.updateCanvasBlockPosition();
        }
    }

    updateCanvasBlock() {
        if (!this.currentBlock) return;

        const blockElement = document.querySelector(`[data-block-id="${this.currentBlock.id}"]`);
        if (blockElement) {
            // Update parameter displays
            const paramInputs = blockElement.querySelectorAll('.param-input');
            paramInputs.forEach(input => {
                const paramKey = input.dataset.param;
                const value = this.currentBlock.params[paramKey];
                
                if (input.type === 'checkbox') {
                    input.checked = value;
                } else {
                    input.value = value;
                }
            });
        }
    }

    updateCanvasBlockPosition() {
        if (!this.currentBlock) return;

        const blockElement = document.querySelector(`[data-block-id="${this.currentBlock.id}"]`);
        if (blockElement) {
            blockElement.style.left = `${this.currentBlock.position.x}px`;
            blockElement.style.top = `${this.currentBlock.position.y}px`;
        }
    }

    hasUnsavedChanges() {
        if (!this.currentBlock || !this.originalData) return false;
        
        return JSON.stringify(this.currentBlock) !== JSON.stringify(this.originalData);
    }

    resetBlock() {
        if (confirm('Reset block to default values?')) {
            // Reset parameters to defaults
            Object.entries(this.currentBlock.typeInfo.params || {}).forEach(([key, paramDef]) => {
                this.currentBlock.params[key] = paramDef.default;
            });
            
            // Refresh editors
            this.populateVisualEditor();
            this.populateJSONEditor();
            
            // Update canvas
            this.updateCanvasBlock();
        }
    }

    duplicateBlock() {
        if (this.currentBlock && window.edpmtApp && window.edpmtApp.visualProgramming) {
            const vp = window.edpmtApp.visualProgramming;
            vp.duplicateBlock(this.currentBlock.id);
            this.closeEditor();
        }
    }

    deleteBlock() {
        if (confirm('Delete this block? This cannot be undone.')) {
            if (this.currentBlock && window.edpmtApp && window.edpmtApp.visualProgramming) {
                const vp = window.edpmtApp.visualProgramming;
                vp.deleteBlock(this.currentBlock.id);
                this.closeEditor();
            }
        }
    }

    formatParameterName(key) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    addLogEntry(level, message) {
        if (window.edpmtApp) {
            window.edpmtApp.addLogEntry(level, message);
        }
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BlockEditor;
} else if (typeof window !== 'undefined') {
    window.BlockEditor = BlockEditor;
}
