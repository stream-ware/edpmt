// UI Testing Module for EDPMT Visual Programming
class UITestSuite {
    constructor(visualProgramming) {
        this.vp = visualProgramming;
        this.testResults = [];
        this.testsPassed = 0;
        this.testsFailed = 0;
    }

    // Run all UI tests
    async runAllTests() {
        console.log('🧪 Starting EDPMT Visual Programming UI Test Suite...');
        this.testResults = [];
        this.testsPassed = 0;
        this.testsFailed = 0;

        // Test categories
        await this.testBasicUI();
        await this.testBlockCreation();
        await this.testDragAndDrop();
        await this.testProjectLoading();
        await this.testVariableSystem();
        await this.testCodeGeneration();
        await this.testConnectionHandling();
        await this.testAllBlockTypes();

        return this.generateTestReport();
    }

    // Test basic UI functionality
    async testBasicUI() {
        this.addTestCategory('Basic UI Tests');
        
        // Test tab switching
        this.testTabSwitching();
        
        // Test button states
        this.testButtonStates();
        
        // Test modal functionality
        this.testModalFunctionality();
        
        // Test canvas interaction
        this.testCanvasInteraction();
    }

    testTabSwitching() {
        try {
            const tabs = ['blocks', 'projects', 'variables', 'code', 'logs'];
            let allTabsWork = true;
            
            tabs.forEach(tabName => {
                const tabBtn = document.querySelector(`[data-tab="${tabName}"]`);
                const tabContent = document.getElementById(`${tabName}-tab`);
                
                if (!tabBtn || !tabContent) {
                    allTabsWork = false;
                    return;
                }
                
                // Simulate click
                tabBtn.click();
                
                // Check if tab becomes active
                if (!tabContent.classList.contains('active')) {
                    allTabsWork = false;
                }
            });
            
            this.addTestResult('Tab Switching', allTabsWork, allTabsWork ? 'All tabs switch correctly' : 'Some tabs failed to switch');
        } catch (error) {
            this.addTestResult('Tab Switching', false, `Error: ${error.message}`);
        }
    }

    testButtonStates() {
        try {
            const buttons = {
                'connectBtn': 'Connect button exists',
                'runBtn': 'Run button exists', 
                'stopBtn': 'Stop button exists',
                'clearBtn': 'Clear button exists',
                'testBtn': 'Test button exists'
            };
            
            let allButtonsExist = true;
            const buttonResults = [];
            
            Object.entries(buttons).forEach(([id, description]) => {
                const button = document.getElementById(id);
                if (!button) {
                    allButtonsExist = false;
                    buttonResults.push(`Missing: ${description}`);
                } else {
                    buttonResults.push(`✓ ${description}`);
                }
            });
            
            this.addTestResult('Button States', allButtonsExist, buttonResults.join(', '));
        } catch (error) {
            this.addTestResult('Button States', false, `Error: ${error.message}`);
        }
    }

    testModalFunctionality() {
        try {
            const connectionModal = document.getElementById('connectionModal');
            const testModal = document.getElementById('testModal');
            
            let modalTestPassed = true;
            const issues = [];
            
            if (!connectionModal) {
                modalTestPassed = false;
                issues.push('Connection modal missing');
            }
            
            if (!testModal) {
                modalTestPassed = false;
                issues.push('Test modal missing');
            }
            
            this.addTestResult('Modal Functionality', modalTestPassed, modalTestPassed ? 'All modals present' : issues.join(', '));
        } catch (error) {
            this.addTestResult('Modal Functionality', false, `Error: ${error.message}`);
        }
    }

    testCanvasInteraction() {
        try {
            const canvas = document.getElementById('canvas');
            let canvasTestPassed = true;
            const issues = [];
            
            if (!canvas) {
                canvasTestPassed = false;
                issues.push('Canvas element missing');
            } else {
                // Test canvas drag and drop setup
                const dropHandler = canvas.ondrop;
                const dragOverHandler = canvas.ondragover;
                
                if (!dropHandler && !dragOverHandler) {
                    issues.push('Drag and drop not properly configured');
                }
            }
            
            this.addTestResult('Canvas Interaction', canvasTestPassed, canvasTestPassed ? 'Canvas ready for interaction' : issues.join(', '));
        } catch (error) {
            this.addTestResult('Canvas Interaction', false, `Error: ${error.message}`);
        }
    }

    // Test block creation and management
    async testBlockCreation() {
        this.addTestCategory('Block Creation Tests');
        
        const blockTypes = [
            'gpio-set', 'gpio-read', 'gpio-pwm',
            'i2c-scan', 'i2c-read', 'i2c-write',
            'wait', 'repeat', 'if', 'while',
            'play-tone', 'beep-pattern',
            'set-variable', 'get-variable'
        ];
        
        blockTypes.forEach(blockType => {
            this.testBlockTypeExists(blockType);
        });
    }

    testBlockTypeExists(blockType) {
        try {
            const blockElement = document.querySelector(`[data-type="${blockType}"]`);
            const exists = blockElement !== null;
            
            if (exists) {
                // Test if block is draggable
                const isDraggable = blockElement.getAttribute('draggable') === 'true';
                this.addTestResult(`Block: ${blockType}`, exists && isDraggable, 
                    exists && isDraggable ? 'Block exists and is draggable' : 'Block not properly configured');
            } else {
                this.addTestResult(`Block: ${blockType}`, false, 'Block element not found');
            }
        } catch (error) {
            this.addTestResult(`Block: ${blockType}`, false, `Error: ${error.message}`);
        }
    }

    // Test drag and drop functionality
    async testDragAndDrop() {
        this.addTestCategory('Drag and Drop Tests');
        
        try {
            // Test that blocks have drag event listeners
            const draggableBlocks = document.querySelectorAll('.block[draggable="true"]');
            const hasBlocks = draggableBlocks.length > 0;
            
            let allHaveDragStart = true;
            draggableBlocks.forEach(block => {
                // Check if drag start event is attached (this is a simplified check)
                if (!block.ondragstart && !block.getAttribute('data-drag-configured')) {
                    allHaveDragStart = false;
                }
            });
            
            this.addTestResult('Draggable Blocks', hasBlocks, 
                hasBlocks ? `${draggableBlocks.length} blocks are draggable` : 'No draggable blocks found');
            
            this.addTestResult('Drag Event Handlers', allHaveDragStart, 
                allHaveDragStart ? 'Drag handlers configured' : 'Some blocks missing drag handlers');
                
        } catch (error) {
            this.addTestResult('Drag and Drop', false, `Error: ${error.message}`);
        }
    }

    // Test project loading functionality
    async testProjectLoading() {
        this.addTestCategory('Project Loading Tests');
        
        const expectedProjects = [
            'all-blocks-demo', 'led-blink', 'sensor-monitor', 
            'traffic-light', 'alarm-system', 'doorbell'
        ];
        
        expectedProjects.forEach(project => {
            this.testProjectButtonExists(project);
        });
    }

    testProjectButtonExists(projectName) {
        try {
            const projectBtn = document.querySelector(`[data-project="${projectName}"]`);
            const exists = projectBtn !== null;
            
            this.addTestResult(`Project: ${projectName}`, exists, 
                exists ? 'Project button exists' : 'Project button not found');
        } catch (error) {
            this.addTestResult(`Project: ${projectName}`, false, `Error: ${error.message}`);
        }
    }

    // Test variable system
    async testVariableSystem() {
        this.addTestCategory('Variable System Tests');
        
        try {
            const variablesList = document.getElementById('variablesList');
            const exists = variablesList !== null;
            
            this.addTestResult('Variables Display', exists, 
                exists ? 'Variables list element exists' : 'Variables list missing');
        } catch (error) {
            this.addTestResult('Variables Display', false, `Error: ${error.message}`);
        }
    }

    // Test code generation
    async testCodeGeneration() {
        this.addTestCategory('Code Generation Tests');
        
        try {
            const generatedCode = document.getElementById('generatedCode');
            const exists = generatedCode !== null;
            
            this.addTestResult('Code Display', exists, 
                exists ? 'Generated code element exists' : 'Generated code element missing');
        } catch (error) {
            this.addTestResult('Code Display', false, `Error: ${error.message}`);
        }
    }

    // Test connection handling
    async testConnectionHandling() {
        this.addTestCategory('Connection Tests');
        
        try {
            const connectionStatus = document.getElementById('connectionStatus');
            const statusIndicator = document.getElementById('statusIndicator');
            const statusText = document.getElementById('statusText');
            
            const allElementsExist = connectionStatus && statusIndicator && statusText;
            
            this.addTestResult('Connection UI Elements', allElementsExist, 
                allElementsExist ? 'All connection UI elements present' : 'Some connection UI elements missing');
        } catch (error) {
            this.addTestResult('Connection UI Elements', false, `Error: ${error.message}`);
        }
    }

    // Test all block types comprehensively
    async testAllBlockTypes() {
        this.addTestCategory('Comprehensive Block Tests');
        
        const blockCategories = {
            'GPIO Blocks': ['gpio-set', 'gpio-read', 'gpio-pwm'],
            'I2C Blocks': ['i2c-scan', 'i2c-read', 'i2c-write'],
            'Control Blocks': ['wait', 'repeat', 'if', 'while'],
            'Audio Blocks': ['play-tone', 'beep-pattern'],
            'Variable Blocks': ['set-variable', 'get-variable']
        };
        
        Object.entries(blockCategories).forEach(([category, blocks]) => {
            const allBlocksExist = blocks.every(blockType => {
                return document.querySelector(`[data-type="${blockType}"]`) !== null;
            });
            
            this.addTestResult(`${category} Complete`, allBlocksExist, 
                allBlocksExist ? `All ${blocks.length} blocks in category exist` : 'Some blocks missing');
        });
    }

    // Utility methods for test management
    addTestCategory(categoryName) {
        this.testResults.push({
            type: 'category',
            name: categoryName,
            timestamp: new Date().toISOString()
        });
    }

    addTestResult(testName, passed, details) {
        this.testResults.push({
            type: 'test',
            name: testName,
            passed: passed,
            details: details,
            timestamp: new Date().toISOString()
        });
        
        if (passed) {
            this.testsPassed++;
        } else {
            this.testsFailed++;
        }
    }

    generateTestReport() {
        const totalTests = this.testsPassed + this.testsFailed;
        const passRate = totalTests > 0 ? ((this.testsPassed / totalTests) * 100).toFixed(1) : 0;
        
        const report = {
            summary: {
                total: totalTests,
                passed: this.testsPassed,
                failed: this.testsFailed,
                passRate: passRate,
                timestamp: new Date().toISOString()
            },
            results: this.testResults
        };
        
        console.log('🧪 Test Summary:', report.summary);
        return report;
    }

    // Display test results in the UI
    displayTestResults(report) {
        const testModal = document.getElementById('testModal');
        const testResults = document.getElementById('testResults');
        
        if (!testModal || !testResults) {
            console.error('Test results modal not found');
            return;
        }
        
        let html = `
            <div class="test-summary">
                <h4>📊 Test Summary</h4>
                <div class="test-stats">
                    <span class="stat passed">✅ Passed: ${report.summary.passed}</span>
                    <span class="stat failed">❌ Failed: ${report.summary.failed}</span>
                    <span class="stat rate">📈 Pass Rate: ${report.summary.passRate}%</span>
                </div>
            </div>
            <div class="test-details">
        `;
        
        let currentCategory = null;
        report.results.forEach(result => {
            if (result.type === 'category') {
                if (currentCategory) html += '</div>';
                html += `<div class="test-category">
                    <h5>📁 ${result.name}</h5>
                    <div class="category-tests">`;
                currentCategory = result.name;
            } else {
                const icon = result.passed ? '✅' : '❌';
                const className = result.passed ? 'test-passed' : 'test-failed';
                html += `<div class="test-item ${className}">
                    <span class="test-icon">${icon}</span>
                    <span class="test-name">${result.name}</span>
                    <span class="test-details">${result.details}</span>
                </div>`;
            }
        });
        
        if (currentCategory) html += '</div>';
        html += '</div></div>';
        
        testResults.innerHTML = html;
        testModal.style.display = 'block';
    }
}

// Initialize UI testing when the page loads
window.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for the main visual programming to initialize
    setTimeout(() => {
        if (typeof visualProgramming !== 'undefined') {
            window.uiTestSuite = new UITestSuite(visualProgramming);
            console.log('🧪 UI Test Suite initialized');
        } else {
            console.warn('⚠️ Visual Programming not found - UI tests may not work properly');
            window.uiTestSuite = new UITestSuite(null);
        }
    }, 1000);
});
