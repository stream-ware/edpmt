/**
 * EDPMT Complete Frontend - Main Application Controller
 * Coordinates all frontend components and manages application state
 */

class EDPMTApp {
    constructor() {
        this.edpmtClient = new EDPMTClient();
        this.currentProject = null;
        
        // Initialize the application
        this.initialize();
    }
    
    async initialize() {
        console.log('🚀 Initializing EDPMT Complete Frontend...');
        
        // Initialize UI components
        this.initializeUI();
        
        // Load initial data
        try {
            await this.loadInitialData();
        } catch (error) {
            console.error('❌ Failed to load initial data:', error);
            this.addLogEntry('error', `Failed to load initial data: ${error.message}`);
        }
        
        console.log('✅ EDPMT Complete Frontend initialized successfully!');
    }
    
    initializeUI() {
        // Initialize UI components and event listeners
        this.initializeProjectUI();
        this.initializeHardwareUI();
        this.initializeEventListeners();
    }
    
    initializeProjectUI() {
        // Project management UI initialization
        document.getElementById('new-project-btn')?.addEventListener('click', () => this.newProject());
        document.getElementById('save-project-btn')?.addEventListener('click', () => this.saveProject());
        document.getElementById('load-project-btn')?.addEventListener('click', () => this.showProjectList());
        
        // Project list modal
        this.projectListModal = new bootstrap.Modal(document.getElementById('projectListModal'));
    }
    
    initializeHardwareUI() {
        // Hardware control UI initialization
        // Add your hardware control UI initialization code here
    }
    
    initializeEventListeners() {
        // Global event listeners
        this.edpmtClient.on('connect', () => {
            this.addLogEntry('success', 'Connected to EDPMT backend');
        });
        
        this.edpmtClient.on('disconnect', () => {
            this.addLogEntry('warning', 'Disconnected from EDPMT backend');
        });
        
        this.edpmtClient.on('error', (error) => {
            console.error('EDPMT client error:', error);
            this.addLogEntry('error', `Connection error: ${error.message}`);
        });
        
        this.edpmtClient.on('system_info', (data) => {
            this.updateSystemInfo(data);
        });
    }
    
    async loadInitialData() {
        // Load system info
        try {
            const systemInfo = await this.edpmtClient.getSystemInfo();
            this.updateSystemInfo(systemInfo);
            
            // Load projects list
            await this.loadProjects();
        } catch (error) {
            console.error('Failed to load initial data:', error);
            throw error;
        }
    }
    
    updateSystemInfo(systemInfo) {
        // Update UI with system information
        const systemInfoEl = document.getElementById('system-info');
        if (systemInfoEl) {
            systemInfoEl.textContent = JSON.stringify(systemInfo, null, 2);
        }
    }
    
    addLogEntry(type, message) {
        const logContainer = document.getElementById('log-container');
        if (!logContainer) return;
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        logEntry.innerHTML = `
            <span class="log-timestamp">${new Date().toISOString()}</span>
            <span class="log-message">${message}</span>
        `;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
    
    // Project management methods
    async newProject() {
        this.currentProject = {
            name: 'New Project',
            description: '',
            blocks: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };
        
        this.updateProjectUI();
        this.addLogEntry('info', 'Created new project');
    }
    
    async saveProject() {
        if (!this.currentProject) {
            this.addLogEntry('warning', 'No project to save');
            return;
        }
        
        try {
            const projectName = prompt('Enter project name:', this.currentProject.name || 'My Project');
            if (!projectName) return;
            
            this.currentProject.name = projectName;
            this.currentProject.updatedAt = new Date().toISOString();
            
            // Save project to the server
            const response = await fetch('/api/save-project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: this.currentProject.name,
                    project: this.currentProject
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to save project');
            }
            
            const result = await response.json();
            this.addLogEntry('success', `Project '${projectName}' saved successfully`);
            
            // Reload projects list
            await this.loadProjects();
            
            return result;
        } catch (error) {
            console.error('Failed to save project:', error);
            this.addLogEntry('error', `Failed to save project: ${error.message}`);
            throw error;
        }
    }
    
    async loadProjects() {
        try {
            const response = await fetch('/api/projects');
            if (!response.ok) {
                throw new Error('Failed to load projects');
            }
            
            const data = await response.json();
            this.updateProjectList(data.projects || []);
            return data.projects || [];
        } catch (error) {
            console.error('Failed to load projects:', error);
            this.addLogEntry('error', 'Failed to load projects');
            throw error;
        }
    }
    
    async loadProject(projectName) {
        try {
            const response = await fetch('/api/load-project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: projectName })
            });
            
            if (!response.ok) {
                throw new Error('Failed to load project');
            }
            
            this.currentProject = await response.json();
            this.updateProjectUI();
            this.addLogEntry('success', `Project '${projectName}' loaded`);
            
            return this.currentProject;
        } catch (error) {
            console.error(`Failed to load project '${projectName}':`, error);
            this.addLogEntry('error', `Failed to load project: ${error.message}`);
            throw error;
        }
    }
    
    updateProjectList(projects) {
        const projectList = document.getElementById('project-list');
        if (!projectList) return;
        
        projectList.innerHTML = '';
        
        if (projects.length === 0) {
            projectList.innerHTML = '<div class="text-muted text-center p-3">No projects found</div>';
            return;
        }
        
        projects.forEach(project => {
            const projectEl = document.createElement('div');
            projectEl.className = 'list-group-item list-group-item-action';
            projectEl.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">${project.name}</h5>
                    <small>${new Date(project.updatedAt || project.createdAt).toLocaleDateString()}</small>
                </div>
                <p class="mb-1">${project.description || 'No description'}</p>
                <small>Click to open</small>
            `;
            
            projectEl.addEventListener('click', () => {
                this.loadProject(project.name)
                    .then(() => {
                        this.projectListModal.hide();
                    })
                    .catch(console.error);
            });
            
            projectList.appendChild(projectEl);
        });
    }
    
    showProjectList() {
        this.loadProjects().then(() => {
            this.projectListModal.show();
        }).catch(console.error);
    }
    
    updateProjectUI() {
        if (!this.currentProject) return;
        
        // Update project info in the UI
        const projectNameEl = document.getElementById('project-name');
        if (projectNameEl) {
            projectNameEl.textContent = this.currentProject.name;
        }
        
        // Update other UI elements based on the current project
        // Add your UI update logic here
    }
    
    // Hardware control methods
    async executeProject() {
        if (!this.currentProject) {
            this.addLogEntry('warning', 'No project to execute');
            return;
        }
        
        try {
            this.addLogEntry('info', 'Executing project...');
            const result = await this.edpmtClient.executeProject(this.currentProject);
            this.addLogEntry('success', 'Project execution started');
            return result;
        } catch (error) {
            console.error('Failed to execute project:', error);
            this.addLogEntry('error', `Failed to execute project: ${error.message}`);
            throw error;
        }
    }
    
    async stopExecution() {
        try {
            this.addLogEntry('info', 'Stopping execution...');
            const result = await this.edpmtClient.stopExecution();
            this.addLogEntry('success', 'Execution stopped');
            return result;
        } catch (error) {
            console.error('Failed to stop execution:', error);
            this.addLogEntry('error', `Failed to stop execution: ${error.message}`);
            throw error;
        }
    }
}

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the application
    window.app = new EDPMTApp();
    
    // Expose the client for debugging
    window.edpmtClient = window.app.edpmtClient;
});
