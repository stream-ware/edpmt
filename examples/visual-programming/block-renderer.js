// Visual Block Renderer - Converts JSON projects to visual block diagrams
class BlockRenderer {
    constructor() {
        this.blockColors = {
            'gpio-set': '#4CAF50',
            'gpio-read': '#2196F3', 
            'gpio-pwm': '#FF9800',
            'i2c-scan': '#9C27B0',
            'i2c-read': '#673AB7',
            'i2c-write': '#3F51B5',
            'wait': '#607D8B',
            'repeat': '#FF5722',
            'if': '#E91E63',
            'while': '#795548',
            'play-tone': '#00BCD4',
            'beep-pattern': '#009688',
            'set-variable': '#FFC107',
            'get-variable': '#FFEB3B'
        };
        
        this.blockIcons = {
            'gpio-set': '📍',
            'gpio-read': '📥',
            'gpio-pwm': '📶',
            'i2c-scan': '🔍',
            'i2c-read': '📖',
            'i2c-write': '✏️',
            'wait': '⏰',
            'repeat': '🔄',
            'if': '❓',
            'while': '🔁',
            'play-tone': '🎵',
            'beep-pattern': '🔊',
            'set-variable': '💾',
            'get-variable': '📂'
        };
    }

    // Render project as visual blocks
    renderProject(project, containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Container not found:', containerId);
            return;
        }

        container.innerHTML = this.generateProjectHTML(project);
        this.addInteractivity(container);
    }

    // Generate HTML for entire project
    generateProjectHTML(project) {
        let html = `
            <div class="project-visualization">
                <div class="project-header">
                    <h2>${project.name}</h2>
                    <p class="project-description">${project.description}</p>
                    <div class="project-meta">
                        <span class="author">👤 ${project.author || 'Unknown'}</span>
                        <span class="version">📦 v${project.version || '1.0'}</span>
                    </div>
                </div>
                <div class="block-flow">
        `;

        if (project.blocks && Array.isArray(project.blocks)) {
            html += this.renderBlockSequence(project.blocks, 0);
        } else {
            html += '<p class="no-blocks">No blocks defined in this project.</p>';
        }

        html += `
                </div>
                ${this.generateProjectFooter(project)}
            </div>
        `;

        return html;
    }

    // Render sequence of blocks
    renderBlockSequence(blocks, indentLevel = 0) {
        let html = '';
        
        blocks.forEach((block, index) => {
            html += this.renderSingleBlock(block, indentLevel);
            
            // Add connector line if not last block
            if (index < blocks.length - 1) {
                html += this.renderConnector(indentLevel);
            }
        });
        
        return html;
    }

    // Render single block
    renderSingleBlock(block, indentLevel = 0) {
        const color = this.blockColors[block.type] || '#757575';
        const icon = this.blockIcons[block.type] || '📦';
        const indent = indentLevel * 30;
        
        let html = `
            <div class="block-item" style="margin-left: ${indent}px; border-left-color: ${color};">
                <div class="block-header" style="background-color: ${color};">
                    <span class="block-icon">${icon}</span>
                    <span class="block-type">${this.formatBlockType(block.type)}</span>
                    <span class="block-id">#${block.id}</span>
                </div>
                <div class="block-content">
                    ${this.renderBlockInputs(block)}
                    ${this.renderBlockDescription(block)}
                </div>
        `;

        // Handle nested blocks (children)
        if (block.children && Array.isArray(block.children)) {
            html += `
                <div class="block-children">
                    <div class="children-label">Contains ${block.children.length} blocks:</div>
                    ${this.renderBlockSequence(block.children, indentLevel + 1)}
                </div>
            `;
        }

        // Handle else blocks for if statements
        if (block.else_children && Array.isArray(block.else_children)) {
            html += `
                <div class="block-else">
                    <div class="else-label">Else:</div>
                    ${this.renderBlockSequence(block.else_children, indentLevel + 1)}
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    // Render block inputs
    renderBlockInputs(block) {
        if (!block.inputs || Object.keys(block.inputs).length === 0) {
            return '<div class="block-inputs">No parameters</div>';
        }

        let html = '<div class="block-inputs">';
        Object.entries(block.inputs).forEach(([key, value]) => {
            html += `<div class="input-item">
                <span class="input-key">${key}:</span>
                <span class="input-value">${value}</span>
            </div>`;
        });
        html += '</div>';
        
        return html;
    }

    // Render block description
    renderBlockDescription(block) {
        if (!block.description) return '';
        
        return `<div class="block-description">💬 ${block.description}</div>`;
    }

    // Render connector line between blocks
    renderConnector(indentLevel = 0) {
        const indent = indentLevel * 30;
        return `<div class="block-connector" style="margin-left: ${indent + 10}px;">
            <div class="connector-line"></div>
            <div class="connector-arrow">▼</div>
        </div>`;
    }

    // Format block type for display
    formatBlockType(type) {
        return type.split('-').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    // Generate project footer with metadata
    generateProjectFooter(project) {
        let html = '<div class="project-footer">';
        
        if (project.hardware_requirements) {
            html += `
                <div class="hardware-requirements">
                    <h4>🔧 Hardware Requirements:</h4>
                    <ul>
                        ${project.hardware_requirements.map(req => `<li>${req}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (project.connections) {
            html += `
                <div class="connections">
                    <h4>🔌 Connections:</h4>
                    <ul>
                        ${Object.entries(project.connections).map(([name, connection]) => 
                            `<li><strong>${name}:</strong> ${connection}</li>`
                        ).join('')}
                    </ul>
                </div>
            `;
        }

        if (project.notes) {
            html += `
                <div class="project-notes">
                    <h4>📝 Notes:</h4>
                    <ul>
                        ${project.notes.map(note => `<li>${note}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    // Add interactivity to rendered blocks
    addInteractivity(container) {
        // Add click handlers for blocks
        container.querySelectorAll('.block-item').forEach(block => {
            block.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleBlockDetails(block);
            });
        });

        // Add expand/collapse functionality
        container.querySelectorAll('.block-children, .block-else').forEach(section => {
            const label = section.querySelector('.children-label, .else-label');
            if (label) {
                label.style.cursor = 'pointer';
                label.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleSection(section);
                });
            }
        });
    }

    // Toggle block details visibility
    toggleBlockDetails(blockElement) {
        blockElement.classList.toggle('expanded');
        
        const content = blockElement.querySelector('.block-content');
        if (content) {
            content.style.display = content.style.display === 'none' ? 'block' : 'none';
        }
    }

    // Toggle section (children/else) visibility
    toggleSection(sectionElement) {
        sectionElement.classList.toggle('collapsed');
        
        const content = sectionElement.children;
        for (let i = 1; i < content.length; i++) {
            const element = content[i];
            element.style.display = element.style.display === 'none' ? 'block' : 'none';
        }
    }

    // Create standalone HTML page for project
    generateStandaloneHTML(project) {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${project.name} - EDPMT Visual Blocks</title>
    <style>
        ${this.getEmbeddedCSS()}
    </style>
</head>
<body>
    <div class="standalone-container">
        <header class="standalone-header">
            <h1>🎨 EDPMT Visual Programming</h1>
            <p>Project Visualization: ${project.name}</p>
        </header>
        <main id="project-container">
            ${this.generateProjectHTML(project)}
        </main>
    </div>
    <script>
        ${this.getEmbeddedJS()}
    </script>
</body>
</html>`;
    }

    // Get embedded CSS for standalone pages
    getEmbeddedCSS() {
        return `
        body { 
            font-family: 'Segoe UI', sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .standalone-container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: rgba(255,255,255,0.95);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .standalone-header { 
            text-align: center; 
            margin-bottom: 30px; 
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        .standalone-header h1 { 
            color: #333; 
            margin-bottom: 10px; 
        }
        .project-visualization { 
            margin: 20px 0; 
        }
        .project-header { 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            margin-bottom: 20px; 
        }
        .project-header h2 { 
            color: #333; 
            margin-bottom: 10px; 
        }
        .project-description { 
            color: #666; 
            margin-bottom: 15px; 
            font-size: 1.1em;
        }
        .project-meta { 
            display: flex; 
            gap: 20px; 
            font-size: 0.9em; 
            color: #777;
        }
        .block-flow { 
            padding: 20px 0; 
        }
        .block-item { 
            margin: 10px 0; 
            border: 2px solid #ddd; 
            border-radius: 8px; 
            background: white; 
            border-left-width: 5px;
            transition: all 0.3s ease;
        }
        .block-item:hover { 
            transform: translateX(5px); 
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .block-header { 
            padding: 15px; 
            color: white; 
            font-weight: bold; 
            display: flex; 
            align-items: center; 
            gap: 10px;
        }
        .block-content { 
            padding: 15px; 
        }
        .block-inputs { 
            display: flex; 
            flex-wrap: wrap; 
            gap: 10px; 
            margin-bottom: 10px;
        }
        .input-item { 
            background: #f0f0f0; 
            padding: 5px 10px; 
            border-radius: 4px; 
            font-size: 0.9em;
        }
        .input-key { 
            font-weight: bold; 
            color: #555;
        }
        .input-value { 
            color: #333; 
            margin-left: 5px;
        }
        .block-description { 
            font-style: italic; 
            color: #666; 
            margin-top: 10px;
        }
        .block-children, .block-else { 
            margin-left: 20px; 
            border-left: 2px dashed #ccc; 
            padding-left: 15px; 
            margin-top: 15px;
        }
        .children-label, .else-label { 
            font-weight: bold; 
            color: #555; 
            margin-bottom: 10px; 
            cursor: pointer;
            user-select: none;
        }
        .children-label:hover, .else-label:hover { 
            color: #333; 
        }
        .block-connector { 
            text-align: center; 
            margin: 5px 0; 
        }
        .connector-line { 
            width: 2px; 
            height: 20px; 
            background: #ccc; 
            margin: 0 auto; 
        }
        .connector-arrow { 
            color: #ccc; 
            font-size: 12px; 
        }
        .project-footer { 
            margin-top: 30px; 
            padding: 20px; 
            background: #f8f9fa; 
            border-radius: 8px;
        }
        .project-footer h4 { 
            margin-bottom: 10px; 
            color: #333;
        }
        .project-footer ul { 
            margin: 10px 0; 
            padding-left: 20px;
        }
        .project-footer li { 
            margin: 5px 0; 
            color: #555;
        }
        .hardware-requirements, .connections, .project-notes { 
            margin-bottom: 20px; 
        }
        .no-blocks { 
            text-align: center; 
            color: #999; 
            font-style: italic; 
            padding: 40px;
        }
        `;
    }

    // Get embedded JavaScript for standalone pages
    getEmbeddedJS() {
        return `
        // Add basic interactivity
        document.querySelectorAll('.block-item').forEach(block => {
            block.addEventListener('click', function(e) {
                e.stopPropagation();
                this.classList.toggle('expanded');
            });
        });
        
        document.querySelectorAll('.children-label, .else-label').forEach(label => {
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
        `;
    }
}

// Initialize block renderer when DOM is ready
window.addEventListener('DOMContentLoaded', () => {
    window.blockRenderer = new BlockRenderer();
});
