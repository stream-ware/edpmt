/**
 * Script to generate all dynamic view HTML files from JSON projects
 * This creates clean dynamic versions that load JSON and render with FlowGenerator
 */

import FlowGenerator from './flow-generator.js';
import fs from 'fs';
import path from 'path';

const projects = [
    'traffic-light',
    'sensor-monitor', 
    'alarm-system',
    'doorbell',
    'temperature-alert',
    'all-blocks-demo'
];

function generateDynamicHTML(projectName) {
    const emojis = {
        'traffic-light': '🚦',
        'sensor-monitor': '📊', 
        'alarm-system': '🚨',
        'doorbell': '🔔',
        'temperature-alert': '🌡️',
        'all-blocks-demo': '🎛️'
    };

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${projectName.charAt(0).toUpperCase() + projectName.slice(1).replace('-', ' ')} - EDPMT Visual Blocks (Dynamic)</title>
    <style>
        body { 
            font-family: 'Segoe UI', sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        #loading {
            text-align: center;
            padding: 50px;
            font-size: 18px;
            color: white;
        }
        #error {
            text-align: center;
            padding: 30px;
            background: rgba(255,255,255,0.9);
            border-radius: 8px;
            margin: 20px auto;
            max-width: 600px;
            color: #d32f2f;
        }
    </style>
</head>
<body>
    <div id="loading">${emojis[projectName] || '⚡'} Loading ${projectName.replace('-', ' ')} project dynamically from JSON...</div>
    <div id="error" style="display: none;"></div>
    <div id="dynamic-content"></div>
    
    <script type="module">
        import FlowGenerator from '../flow-generator.js';
        
        async function loadAndRenderProject() {
            try {
                console.log('🔧 Initializing FlowGenerator...');
                const generator = new FlowGenerator();
                
                console.log('📂 Loading ${projectName} project from JSON...');
                const html = await generator.generateProjectPage('${projectName}', '../projects/${projectName}.json');
                
                // Hide loading and show content
                document.getElementById('loading').style.display = 'none';
                document.body.innerHTML = html;
                
                console.log('✅ ${projectName} project loaded and rendered dynamically from JSON!');
            } catch (error) {
                console.error('❌ Error loading project:', error);
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').style.display = 'block';
                document.getElementById('error').innerHTML = \`
                    <h2>❌ Error Loading Project</h2>
                    <p><strong>Could not load ${projectName}.json:</strong> \${error.message}</p>
                    <p>Make sure the project file exists at: <code>../projects/${projectName}.json</code></p>
                    <p>Also check that <code>flow-generator.js</code> is properly loaded.</p>
                    <details>
                        <summary>Technical Details</summary>
                        <pre>\${error.stack}</pre>
                    </details>
                \`;
            }
        }
        
        // Load when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', loadAndRenderProject);
        } else {
            loadAndRenderProject();
        }
    </script>
</body>
</html>`;
}

// Generate all dynamic view files
projects.forEach(projectName => {
    const html = generateDynamicHTML(projectName);
    const filePath = `./view/${projectName}.html`;
    
    fs.writeFileSync(filePath, html);
    console.log(`✅ Generated dynamic ${projectName}.html`);
});

console.log('🎉 All view files converted to dynamic JSON-based generation!');
