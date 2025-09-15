/**
 * Dynamic Flow Generator Library
 * Generates HTML block flows from JSON project files
 * Author: EDPMT Visual Programming Team
 */

class FlowGenerator {
    constructor() {
        this.blockTypeMap = {
            'gpio-set': { icon: '📍', color: '#4CAF50', name: 'GPIO Set' },
            'gpio-get': { icon: '📊', color: '#17a2b8', name: 'GPIO Read' },
            'gpio-pwm': { icon: '🌀', color: '#ffc107', name: 'GPIO PWM' },
            'i2c-scan': { icon: '🔍', color: '#6f42c1', name: 'I2C Scan' },
            'i2c-read': { icon: '📊', color: '#6610f2', name: 'I2C Read' },
            'i2c-write': { icon: '✍️', color: '#e83e8c', name: 'I2C Write' },
            'delay': { icon: '⏰', color: '#607D8B', name: 'Wait' },
            'repeat': { icon: '🔄', color: '#FF5722', name: 'Repeat' },
            'if-condition': { icon: '❓', color: '#dc3545', name: 'If Condition' },
            'while-loop': { icon: '🔁', color: '#FF9800', name: 'While Loop' },
            'audio-play': { icon: '🎵', color: '#e83e8c', name: 'Play Tone' },
            'audio-beep': { icon: '🔊', color: '#009688', name: 'Beep Pattern' },
            'set-variable': { icon: '💾', color: '#FFC107', name: 'Set Variable' },
            'increment-variable': { icon: '📈', color: '#FFEB3B', name: 'Increment Variable' },
            'get-variable': { icon: '📤', color: '#795548', name: 'Get Variable' }
        };
    }

    /**
     * Load and parse JSON project file
     */
    async loadProject(projectPath) {
        try {
            const response = await fetch(projectPath);
            if (!response.ok) {
                throw new Error(`Failed to load project: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error loading project:', error);
            throw error;
        }
    }

    /**
     * Generate complete HTML page for a project
     */
    async generateProjectPage(projectName, projectPath) {
        const project = await this.loadProject(projectPath);
        
        const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${project.name} - EDPMT Visual Blocks</title>
    <style>
        ${this.getCSS()}
    </style>
</head>
<body>
    <div class="standalone-container">
        <header class="standalone-header">
            <h1>🎨 EDPMT Visual Programming</h1>
            <p>Project Visualization: ${project.name}</p>
        </header>
        <main>
            <div class="project-visualization">
                <div class="project-header">
                    <h2>${project.name}</h2>
                    <p class="project-description">${project.description || ''}</p>
                    <div class="project-meta">
                        <span class="author">👤 ${project.author || 'EDPMT Visual Programming'}</span>
                        <span class="version">📦 ${project.version || 'v1.0'}</span>
                    </div>
                </div>
                
                ${this.generateProjectDashboard(project)}
                
                <div class="block-flow">
                    ${this.generateBlockFlow(project.blocks)}
                </div>

                ${this.generateProjectFooter(project)}
            </div>
        </main>
    </div>
    
    <script>
        ${this.getJavaScript(project)}
    </script>
</body>
</html>`;

        return html;
    }

    /**
     * Generate block flow HTML from JSON blocks
     */
    generateBlockFlow(blocks) {
        if (!blocks || !Array.isArray(blocks)) {
            return '<p>No blocks found in project</p>';
        }

        let html = '';
        
        for (let i = 0; i < blocks.length; i++) {
            const block = blocks[i];
            html += this.generateBlock(block);
            
            // Add connector between blocks (except for last block)
            if (i < blocks.length - 1) {
                html += this.generateConnector();
            }
        }

        return html;
    }

    /**
     * Generate individual block HTML
     */
    generateBlock(block) {
        const blockType = this.blockTypeMap[block.type] || {
            icon: '🔧',
            color: '#6c757d',
            name: block.type
        };

        let html = `
        <div class="block-item" style="border-left-color: ${blockType.color};">
            <div class="block-header" style="background-color: ${blockType.color};">
                <span class="block-icon">${blockType.icon}</span>
                <span class="block-type">${blockType.name}</span>
                <span class="block-id">#${block.id || 'block'}</span>
            </div>
            <div class="block-content">`;

        // Add block inputs/parameters
        if (block.params && Object.keys(block.params).length > 0) {
            html += '<div class="block-inputs">';
            Object.entries(block.params).forEach(([key, value]) => {
                html += `
                <div class="input-item">
                    <span class="input-key">${key}:</span>
                    <span class="input-value">${value}</span>
                </div>`;
            });
            html += '</div>';
        }

        // Add block description
        if (block.description) {
            html += `<div class="block-description">💬 ${block.description}</div>`;
        }

        html += '</div>';

        // Add children blocks if they exist
        if (block.children && block.children.length > 0) {
            html += `
            <div class="block-children">
                <div class="children-label">Contains ${block.children.length} blocks (Click to expand):</div>
                ${this.generateBlockFlow(block.children)}
            </div>`;
        }

        // Add else blocks for conditional statements
        if (block.else && block.else.length > 0) {
            html += `
            <div class="block-children">
                <div class="children-label">Else Actions:</div>
                ${this.generateBlockFlow(block.else)}
            </div>`;
        }

        html += '</div>';
        return html;
    }

    /**
     * Generate connector between blocks
     */
    generateConnector() {
        return `
        <div class="block-connector">
            <div class="connector-line"></div>
            <div class="connector-arrow">▼</div>
        </div>`;
    }

    /**
     * Generate project-specific dashboard/widgets
     */
    generateProjectDashboard(project) {
        // Generate dashboard based on project type or hardware requirements
        if (project.hardware && project.hardware.includes('LED')) {
            return this.generateLEDDashboard();
        } else if (project.hardware && project.hardware.includes('sensor')) {
            return this.generateSensorDashboard();
        } else if (project.hardware && project.hardware.includes('temperature')) {
            return this.generateTemperatureDashboard();
        }
        return '';
    }

    generateLEDDashboard() {
        return `
        <div class="project-dashboard">
            <div class="led-demo">
                <div class="led-indicator" id="led-status">💡</div>
                <p>LED Status: <span id="led-text">OFF</span></p>
            </div>
        </div>`;
    }

    generateSensorDashboard() {
        return `
        <div class="sensor-dashboard">
            <div class="sensor-widget">
                <div class="sensor-value" id="sensor-value">24.5°C</div>
                <div class="sensor-label">Temperature</div>
            </div>
            <div class="sensor-widget">
                <div class="sensor-value" id="humidity-value">65%</div>
                <div class="sensor-label">Humidity</div>
            </div>
        </div>`;
    }

    generateTemperatureDashboard() {
        return `
        <div class="temp-dashboard">
            <div class="temp-widget">
                <div class="temp-display" id="current-temp">24.5°C</div>
                <div class="alert-badge" id="temp-status">NORMAL</div>
            </div>
            <div class="temp-widget">
                <div class="fan-control">
                    <span class="fan-icon" id="fan-icon">🌀</span>
                    <div class="pwm-bar">
                        <div class="pwm-fill" id="pwm-fill" style="width: 30%;"></div>
                    </div>
                    <span id="fan-speed">30%</span>
                </div>
            </div>
        </div>`;
    }

    /**
     * Generate project footer with hardware requirements
     */
    generateProjectFooter(project) {
        let html = `
        <div class="project-footer">
            <div class="hardware-requirements">
                <h4>🔧 Hardware Requirements:</h4>
                <ul>`;

        if (project.hardware) {
            project.hardware.forEach(item => {
                html += `<li>${item}</li>`;
            });
        }

        html += `</ul>
            </div>`;

        if (project.connections) {
            html += `
            <div class="connections">
                <h4>🔌 Connections:</h4>
                <ul>`;
            
            Object.entries(project.connections).forEach(([component, pin]) => {
                html += `<li><strong>${component}:</strong> ${pin}</li>`;
            });

            html += `</ul>
            </div>`;
        }

        if (project.notes) {
            html += `
            <div class="project-notes">
                <h4>📝 Notes:</h4>
                <ul>`;
            
            project.notes.forEach(note => {
                html += `<li>${note}</li>`;
            });

            html += `</ul>
            </div>`;
        }

        html += '</div>';
        return html;
    }

    /**
     * Get CSS styles for generated pages
     */
    getCSS() {
        return `
        body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .standalone-container { max-width: 1200px; margin: 0 auto; background: rgba(255,255,255,0.95); border-radius: 10px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .standalone-header { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #eee; }
        .project-visualization { margin: 20px 0; }
        .project-header { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .block-item { margin: 15px 0; border: 2px solid #ddd; border-radius: 8px; background: white; border-left-width: 5px; transition: all 0.3s ease; }
        .block-item:hover { transform: translateX(5px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .block-header { padding: 15px; color: white; font-weight: bold; display: flex; align-items: center; gap: 10px; }
        .block-content { padding: 15px; }
        .block-inputs { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px; }
        .input-item { background: #f0f0f0; padding: 5px 10px; border-radius: 4px; font-size: 0.9em; }
        .input-key { font-weight: bold; color: #555; }
        .input-value { color: #333; margin-left: 5px; }
        .block-description { font-style: italic; color: #666; margin-top: 10px; }
        .block-children { margin-left: 20px; border-left: 2px dashed #ccc; padding-left: 15px; margin-top: 15px; }
        .children-label { font-weight: bold; color: #555; margin-bottom: 10px; cursor: pointer; }
        .block-connector { text-align: center; margin: 5px 0; }
        .connector-line { width: 2px; height: 20px; background: #ccc; margin: 0 auto; }
        .connector-arrow { color: #ccc; font-size: 12px; }
        .project-footer { margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .project-dashboard, .sensor-dashboard, .temp-dashboard { display: flex; justify-content: center; margin: 20px 0; gap: 20px; flex-wrap: wrap; }
        .sensor-widget, .temp-widget { background: #fff; border-radius: 8px; padding: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); text-align: center; min-width: 120px; }
        .led-demo { text-align: center; padding: 20px; }
        .led-indicator { font-size: 48px; }
        `;
    }

    /**
     * Get JavaScript for interactive elements
     */
    getJavaScript(project) {
        return `
        // Expandable sections
        document.querySelectorAll('.children-label').forEach(label => {
            label.addEventListener('click', function(e) {
                e.stopPropagation();
                const section = this.parentElement;
                section.classList.toggle('collapsed');
                
                const content = Array.from(section.children).slice(1);
                content.forEach(el => {
                    el.style.display = el.style.display === 'none' ? 'block' : 'none';
                });
            });
        });

        // Project-specific animations and interactions
        ${this.getProjectSpecificJS(project)}
        `;
    }

    getProjectSpecificJS(project) {
        if (project.name && project.name.toLowerCase().includes('led')) {
            return `
            let ledOn = false;
            setInterval(() => {
                ledOn = !ledOn;
                const indicator = document.getElementById('led-status');
                const text = document.getElementById('led-text');
                if (indicator && text) {
                    indicator.textContent = ledOn ? '💡' : '⚫';
                    text.textContent = ledOn ? 'ON' : 'OFF';
                }
            }, 1000);
            `;
        } else if (project.name && project.name.toLowerCase().includes('sensor')) {
            return `
            function updateSensorData() {
                const temp = (20 + Math.random() * 15).toFixed(1);
                const humidity = (50 + Math.random() * 30).toFixed(0);
                
                const tempEl = document.getElementById('sensor-value');
                const humidityEl = document.getElementById('humidity-value');
                
                if (tempEl) tempEl.textContent = temp + '°C';
                if (humidityEl) humidityEl.textContent = humidity + '%';
            }
            updateSensorData();
            setInterval(updateSensorData, 2000);
            `;
        }
        return '';
    }
}

// Export for both module and global use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FlowGenerator;
} else if (typeof window !== 'undefined') {
    window.FlowGenerator = FlowGenerator;
}

export default FlowGenerator;
