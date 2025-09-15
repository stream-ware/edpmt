// Project Loader - Dynamically loads projects and templates
class ProjectLoader {
    constructor() {
        this.projects = [];
        this.templates = [];
        this.loadedProjects = new Map();
        this.loadedTemplates = new Map();
    }

    // Initialize project loader
    async init() {
        await this.loadProjectList();
        await this.loadTemplateList();
        this.renderProjectList();
        this.renderTemplateList();
        this.setupEventListeners();
    }

    // Load project list from projects folder
    async loadProjectList() {
        const projectFiles = [
            'all-blocks-demo.json',
            'led-blink.json', 
            'sensor-monitor.json',
            'traffic-light.json',
            'alarm-system.json',
            'doorbell.json',
            'temperature-alert.json',
            'smart-garden.json',
            'security-system.json',
            'iot-weather-station.json'
        ];

        for (const file of projectFiles) {
            try {
                const response = await fetch(`projects/${file}`);
                if (response.ok) {
                    const project = await response.json();
                    project.filename = file;
                    this.projects.push(project);
                    this.loadedProjects.set(file, project);
                }
            } catch (error) {
                console.warn(`Could not load project: ${file}`, error);
            }
        }
    }

    // Load template list from templates folder  
    async loadTemplateList() {
        const templateFiles = [
            'basic-led.json',
            'sensor-read.json'
        ];

        for (const file of templateFiles) {
            try {
                const response = await fetch(`templates/${file}`);
                if (response.ok) {
                    const template = await response.json();
                    template.filename = file;
                    this.templates.push(template);
                    this.loadedTemplates.set(file, template);
                }
            } catch (error) {
                console.warn(`Could not load template: ${file}`, error);
            }
        }
    }

    // Render project list in sidebar
    renderProjectList() {
        const projectsTab = document.getElementById('projects-tab');
        if (!projectsTab) return;

        let html = `
            <h3>📁 Available Projects</h3>
            <div class="project-list">
        `;

        this.projects.forEach(project => {
            const icon = this.getProjectIcon(project.name);
            html += `
                <button class="project-btn" data-project="${project.filename}" data-type="project">
                    ${icon} ${project.name}
                </button>
            `;
        });

        html += `
            </div>
            <div class="project-controls">
                <button id="saveProjectBtn" class="btn btn-secondary">💾 Save Project</button>
                <button id="loadProjectBtn" class="btn btn-secondary">📂 Load Project</button>
                <input type="file" id="loadProjectFile" accept=".json" style="display: none;">
            </div>
        `;

        projectsTab.innerHTML = html;
    }

    // Render template list (you can add a templates tab or section)
    renderTemplateList() {
        // Add templates to blocks tab or create separate templates section
        const blocksTab = document.getElementById('blocks-tab');
        if (!blocksTab) return;

        let templatesHtml = `
            <h3>📋 Quick Templates</h3>
            <div class="template-list">
        `;

        this.templates.forEach(template => {
            templatesHtml += `
                <button class="template-btn" data-template="${template.filename}" data-type="template">
                    🏗️ ${template.name}
                </button>
            `;
        });

        templatesHtml += '</div>';
        
        // Add templates section to blocks tab
        blocksTab.insertAdjacentHTML('beforeend', templatesHtml);
    }

    // Get appropriate icon for project
    getProjectIcon(projectName) {
        const iconMap = {
            'All Blocks Demo': '🎯',
            'LED Blink': '💡',
            'Sensor Monitor': '📊', 
            'Traffic Light Controller': '🚦',
            'Alarm System': '🚨',
            'Smart Doorbell System': '🔔',
            'Temperature Alert System': '🌡️',
            'Smart Garden Monitor': '🌱',
            'Security System': '🔒',
            'IoT Weather Station': '🌤️'
        };
        return iconMap[projectName] || '📄';
    }

    // Setup event listeners for project/template loading
    setupEventListeners() {
        // Project buttons
        document.addEventListener('click', async (e) => {
            if (e.target.matches('[data-project]')) {
                const filename = e.target.dataset.project;
                await this.loadProject(filename);
            }
            
            if (e.target.matches('[data-template]')) {
                const filename = e.target.dataset.template;
                await this.loadTemplate(filename);
            }
        });

        // File input for custom project loading
        const loadProjectFile = document.getElementById('loadProjectFile');
        if (loadProjectFile) {
            loadProjectFile.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    this.loadProjectFromFile(file);
                }
            });
        }

        // Load project button
        const loadProjectBtn = document.getElementById('loadProjectBtn');
        if (loadProjectBtn) {
            loadProjectBtn.addEventListener('click', () => {
                loadProjectFile?.click();
            });
        }

        // Save project button
        const saveProjectBtn = document.getElementById('saveProjectBtn');
        if (saveProjectBtn) {
            saveProjectBtn.addEventListener('click', () => {
                this.saveCurrentProject();
            });
        }
    }

    // Load project and render on canvas
    async loadProject(filename) {
        const project = this.loadedProjects.get(filename);
        if (!project) {
            console.error('Project not found:', filename);
            return;
        }

        console.log('Loading project:', project.name);
        
        // Clear canvas first
        if (window.visualProgramming) {
            window.visualProgramming.clearCanvas();
            window.visualProgramming.renderProjectBlocks(project);
        } else {
            console.warn('Visual programming instance not available');
        }
    }

    // Load template and render on canvas
    async loadTemplate(filename) {
        const template = this.loadedTemplates.get(filename);
        if (!template) {
            console.error('Template not found:', filename);
            return;
        }

        console.log('Loading template:', template.name);
        
        if (window.visualProgramming) {
            window.visualProgramming.renderProjectBlocks(template);
        } else {
            console.warn('Visual programming instance not available');
        }
    }

    // Load project from uploaded file
    async loadProjectFromFile(file) {
        try {
            const text = await file.text();
            const project = JSON.parse(text);
            
            console.log('Loading project from file:', project.name);
            
            if (window.visualProgramming) {
                window.visualProgramming.clearCanvas();
                window.visualProgramming.renderProjectBlocks(project);
            }
        } catch (error) {
            console.error('Error loading project file:', error);
            alert('Error loading project file. Please check the format.');
        }
    }

    // Save current project
    saveCurrentProject() {
        if (!window.visualProgramming) {
            alert('Visual programming not available');
            return;
        }

        const currentBlocks = window.visualProgramming.getCurrentBlocks();
        const project = {
            name: "Custom Project",
            description: "User created project",
            author: "User",
            version: "1.0",
            blocks: currentBlocks,
            timestamp: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(project, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'my-project.json';
        a.click();
        URL.revokeObjectURL(url);
    }

    // Get project by filename
    getProject(filename) {
        return this.loadedProjects.get(filename);
    }

    // Get template by filename
    getTemplate(filename) {
        return this.loadedTemplates.get(filename);
    }
}

// Initialize project loader when DOM is ready
window.addEventListener('DOMContentLoaded', () => {
    window.projectLoader = new ProjectLoader();
    // Small delay to ensure other components are initialized
    setTimeout(() => {
        window.projectLoader.init();
    }, 500);
});
