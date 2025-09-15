/**
 * Page Editor Component - Handles popup modal for editing HTML/CSS/JS
 * Supports live preview and file save functionality
 */

class PageEditor {
    constructor(edpmtClient) {
        this.edpmtClient = edpmtClient;
        this.isOpen = false;
        this.currentContent = {
            html: '',
            css: '',
            js: ''
        };
        this.originalContent = null;
        
        this.modal = document.getElementById('page-editor-modal');
        this.htmlEditor = document.getElementById('html-editor-textarea');
        this.cssEditor = document.getElementById('css-editor-textarea');
        this.jsEditor = document.getElementById('js-editor-textarea');
        this.previewFrame = document.getElementById('preview-iframe');
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAutoSave();
    }

    setupEventListeners() {
        // Modal controls
        document.getElementById('close-page-editor').addEventListener('click', () => {
            this.closeEditor();
        });

        document.getElementById('cancel-page-edit').addEventListener('click', () => {
            this.cancelEdit();
        });

        // Save buttons
        document.getElementById('save-page-edit').addEventListener('click', () => {
            this.savePage();
        });

        document.getElementById('apply-page-edit').addEventListener('click', () => {
            this.applyChanges();
        });

        // Tab switching
        document.querySelectorAll('#page-editor-modal .editor-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.switchTab(btn.dataset.tab);
            });
        });

        // Live editing
        [this.htmlEditor, this.cssEditor, this.jsEditor].forEach(editor => {
            editor.addEventListener('input', () => {
                this.updatePreview();
                this.markAsModified();
            });
        });

        // File operations
        document.getElementById('new-page-btn')?.addEventListener('click', () => {
            this.newPage();
        });

        document.getElementById('load-page-btn')?.addEventListener('click', () => {
            this.loadPage();
        });

        document.getElementById('export-page-btn')?.addEventListener('click', () => {
            this.exportPage();
        });

        // Preview controls
        document.getElementById('refresh-preview-btn')?.addEventListener('click', () => {
            this.refreshPreview();
        });

        document.getElementById('open-preview-btn')?.addEventListener('click', () => {
            this.openPreviewInNewTab();
        });

        // Code formatting
        document.getElementById('format-html-btn')?.addEventListener('click', () => {
            this.formatCode('html');
        });

        document.getElementById('format-css-btn')?.addEventListener('click', () => {
            this.formatCode('css');
        });

        document.getElementById('format-js-btn')?.addEventListener('click', () => {
            this.formatCode('js');
        });
    }

    setupAutoSave() {
        // Auto-save every 30 seconds
        setInterval(() => {
            if (this.isOpen && this.hasUnsavedChanges()) {
                this.autoSave();
            }
        }, 30000);
    }

    openEditor(content = null) {
        this.isOpen = true;
        
        if (content) {
            this.currentContent = { ...content };
        } else {
            // Load current page content
            this.loadCurrentPageContent();
        }
        
        this.originalContent = JSON.parse(JSON.stringify(this.currentContent));
        
        this.populateEditors();
        this.modal.classList.add('active');
        this.switchTab('html-editor');
        this.updatePreview();
    }

    closeEditor() {
        this.modal.classList.remove('active');
        this.isOpen = false;
        this.currentContent = { html: '', css: '', js: '' };
        this.originalContent = null;
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

    savePage() {
        this.collectEditorContent();
        
        // Apply to current page
        this.applyToCurrentPage();
        
        // Save to server if available
        this.saveToServer();
        
        this.closeEditor();
        this.addLogEntry('success', 'Page saved successfully');
    }

    applyChanges() {
        this.collectEditorContent();
        this.updatePreview();
        this.markAsModified();
    }

    loadCurrentPageContent() {
        // Extract current page HTML, CSS, and JS
        const htmlContent = document.documentElement.outerHTML;
        
        // Extract inline CSS
        const styleElements = document.querySelectorAll('style');
        const cssContent = Array.from(styleElements)
            .map(style => style.textContent)
            .join('\n\n');
        
        // Extract inline JS
        const scriptElements = document.querySelectorAll('script:not([src])');
        const jsContent = Array.from(scriptElements)
            .map(script => script.textContent)
            .join('\n\n');
        
        this.currentContent = {
            html: this.formatHTML(htmlContent),
            css: cssContent,
            js: jsContent
        };
    }

    populateEditors() {
        this.htmlEditor.value = this.currentContent.html;
        this.cssEditor.value = this.currentContent.css;
        this.jsEditor.value = this.currentContent.js;
    }

    collectEditorContent() {
        this.currentContent.html = this.htmlEditor.value;
        this.currentContent.css = this.cssEditor.value;
        this.currentContent.js = this.jsEditor.value;
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

        // Focus the appropriate editor
        const editors = {
            'html-editor': this.htmlEditor,
            'css-editor': this.cssEditor,
            'js-editor': this.jsEditor
        };
        
        if (editors[tabName]) {
            setTimeout(() => editors[tabName].focus(), 100);
        }
    }

    updatePreview() {
        this.collectEditorContent();
        
        const previewContent = this.generatePreviewHTML();
        
        // Update iframe
        if (this.previewFrame) {
            const doc = this.previewFrame.contentDocument || this.previewFrame.contentWindow.document;
            doc.open();
            doc.write(previewContent);
            doc.close();
        }
    }

    generatePreviewHTML() {
        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Preview</title>
    <style>
        ${this.currentContent.css}
    </style>
</head>
<body>
    ${this.currentContent.html}
    <script>
        try {
            ${this.currentContent.js}
        } catch (error) {
            console.error('Preview JavaScript Error:', error);
        }
    </script>
</body>
</html>
        `;
    }

    refreshPreview() {
        this.updatePreview();
        this.addLogEntry('info', 'Preview refreshed');
    }

    openPreviewInNewTab() {
        const previewContent = this.generatePreviewHTML();
        const blob = new Blob([previewContent], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
    }

    applyToCurrentPage() {
        try {
            // Apply CSS changes
            this.applyCSSChanges();
            
            // Apply HTML changes (limited to safe areas)
            this.applyHTMLChanges();
            
            // Apply JS changes (with caution)
            this.applyJSChanges();
            
        } catch (error) {
            console.error('Error applying changes:', error);
            this.addLogEntry('error', `Failed to apply changes: ${error.message}`);
        }
    }

    applyCSSChanges() {
        // Remove existing dynamic styles
        document.querySelectorAll('style[data-page-editor]').forEach(el => el.remove());
        
        // Add new styles
        if (this.currentContent.css.trim()) {
            const styleElement = document.createElement('style');
            styleElement.dataset.pageEditor = 'true';
            styleElement.textContent = this.currentContent.css;
            document.head.appendChild(styleElement);
        }
    }

    applyHTMLChanges() {
        // For safety, only allow changes to specific container elements
        const safeContainers = [
            '#main-content',
            '#custom-content',
            '.editable-content'
        ];
        
        safeContainers.forEach(selector => {
            const container = document.querySelector(selector);
            if (container) {
                // Extract content for this container from HTML
                const parser = new DOMParser();
                const doc = parser.parseFromString(this.currentContent.html, 'text/html');
                const newContent = doc.querySelector(selector);
                
                if (newContent) {
                    container.innerHTML = newContent.innerHTML;
                }
            }
        });
    }

    applyJSChanges() {
        // Remove existing dynamic scripts
        document.querySelectorAll('script[data-page-editor]').forEach(el => el.remove());
        
        // Add new script (with safety checks)
        if (this.currentContent.js.trim()) {
            try {
                const scriptElement = document.createElement('script');
                scriptElement.dataset.pageEditor = 'true';
                scriptElement.textContent = this.currentContent.js;
                document.head.appendChild(scriptElement);
            } catch (error) {
                console.error('JavaScript execution error:', error);
                this.addLogEntry('error', 'JavaScript execution failed');
            }
        }
    }

    formatCode(type) {
        try {
            switch (type) {
                case 'html':
                    this.htmlEditor.value = this.formatHTML(this.htmlEditor.value);
                    break;
                case 'css':
                    this.cssEditor.value = this.formatCSS(this.cssEditor.value);
                    break;
                case 'js':
                    this.jsEditor.value = this.formatJS(this.jsEditor.value);
                    break;
            }
            this.updatePreview();
            this.addLogEntry('info', `${type.toUpperCase()} formatted`);
        } catch (error) {
            this.addLogEntry('error', `Failed to format ${type.toUpperCase()}`);
        }
    }

    formatHTML(html) {
        // Basic HTML formatting
        return html
            .replace(/></g, '>\n<')
            .replace(/^\s+|\s+$/g, '')
            .split('\n')
            .map((line, index, array) => {
                const trimmed = line.trim();
                if (!trimmed) return '';
                
                // Calculate indentation
                let indent = 0;
                for (let i = 0; i < index; i++) {
                    const prevLine = array[i].trim();
                    if (prevLine.match(/<[^\/][^>]*[^\/]>$/)) indent++;
                    if (prevLine.match(/<\/[^>]*>$/)) indent--;
                }
                
                return '  '.repeat(Math.max(0, indent)) + trimmed;
            })
            .join('\n');
    }

    formatCSS(css) {
        // Basic CSS formatting
        return css
            .replace(/\s*{\s*/g, ' {\n  ')
            .replace(/;\s*/g, ';\n  ')
            .replace(/\s*}\s*/g, '\n}\n\n')
            .replace(/,\s*/g, ',\n')
            .trim();
    }

    formatJS(js) {
        // Basic JS formatting (very simple)
        return js
            .replace(/;\s*/g, ';\n')
            .replace(/{\s*/g, ' {\n  ')
            .replace(/}\s*/g, '\n}\n')
            .trim();
    }

    newPage() {
        if (this.hasUnsavedChanges()) {
            if (!confirm('You have unsaved changes. Create new page anyway?')) {
                return;
            }
        }

        this.currentContent = {
            html: `<div class="container">
    <h1>New Page</h1>
    <p>Start editing your page content here.</p>
</div>`,
            css: `.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    font-family: Arial, sans-serif;
}

h1 {
    color: #333;
    border-bottom: 2px solid #007bff;
    padding-bottom: 10px;
}`,
            js: `// Add your JavaScript code here
console.log('Page loaded');`
        };

        this.populateEditors();
        this.updatePreview();
        this.originalContent = JSON.parse(JSON.stringify(this.currentContent));
    }

    loadPage() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.html,.htm';
        
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.parseHTMLFile(e.target.result);
                };
                reader.readAsText(file);
            }
        };
        
        input.click();
    }

    parseHTMLFile(htmlContent) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlContent, 'text/html');
        
        // Extract CSS
        const styles = Array.from(doc.querySelectorAll('style'))
            .map(style => style.textContent)
            .join('\n\n');
        
        // Extract JS
        const scripts = Array.from(doc.querySelectorAll('script:not([src])'))
            .map(script => script.textContent)
            .join('\n\n');
        
        // Extract HTML (body content)
        const bodyContent = doc.body ? doc.body.innerHTML : htmlContent;
        
        this.currentContent = {
            html: bodyContent,
            css: styles,
            js: scripts
        };
        
        this.populateEditors();
        this.updatePreview();
        this.originalContent = JSON.parse(JSON.stringify(this.currentContent));
        
        this.addLogEntry('success', 'Page loaded from file');
    }

    exportPage() {
        const fullHTML = this.generatePreviewHTML();
        const blob = new Blob([fullHTML], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'page.html';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.addLogEntry('success', 'Page exported as HTML file');
    }

    async saveToServer() {
        if (!this.edpmtClient || !this.edpmtClient.isConnected()) {
            this.addLogEntry('warning', 'Not connected to server - changes saved locally only');
            return;
        }

        try {
            const pageData = {
                html: this.currentContent.html,
                css: this.currentContent.css,
                js: this.currentContent.js,
                timestamp: Date.now()
            };

            await this.edpmtClient.execute('save-page', pageData);
            this.addLogEntry('success', 'Page saved to server');
        } catch (error) {
            console.error('Failed to save to server:', error);
            this.addLogEntry('error', 'Failed to save to server');
        }
    }

    autoSave() {
        if (!this.isOpen) return;
        
        this.collectEditorContent();
        localStorage.setItem('edpmt-page-autosave', JSON.stringify({
            content: this.currentContent,
            timestamp: Date.now()
        }));
        
        this.addLogEntry('info', 'Auto-saved locally');
    }

    loadAutoSave() {
        const autoSave = localStorage.getItem('edpmt-page-autosave');
        if (autoSave) {
            try {
                const data = JSON.parse(autoSave);
                const age = Date.now() - data.timestamp;
                
                // Only load if less than 24 hours old
                if (age < 24 * 60 * 60 * 1000) {
                    if (confirm('Auto-saved content found. Do you want to restore it?')) {
                        this.currentContent = data.content;
                        this.populateEditors();
                        this.updatePreview();
                        this.addLogEntry('info', 'Auto-saved content restored');
                    }
                }
            } catch (error) {
                console.error('Failed to load auto-save:', error);
            }
        }
    }

    hasUnsavedChanges() {
        if (!this.originalContent) return false;
        
        this.collectEditorContent();
        return JSON.stringify(this.currentContent) !== JSON.stringify(this.originalContent);
    }

    markAsModified() {
        // Visual indication of unsaved changes
        const saveBtn = document.getElementById('save-page-edit');
        if (saveBtn) {
            saveBtn.textContent = 'Save *';
            saveBtn.classList.add('modified');
        }
    }

    addLogEntry(level, message) {
        if (window.edpmtApp) {
            window.edpmtApp.addLogEntry(level, message);
        }
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PageEditor;
} else if (typeof window !== 'undefined') {
    window.PageEditor = PageEditor;
}
