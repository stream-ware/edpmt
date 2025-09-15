#!/usr/bin/env python3
"""
EDPMT Web UI
Modern, responsive web interface for hardware control and monitoring
"""

def get_web_ui() -> str:
    """Return the complete HTML/CSS/JavaScript web interface"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EDPMT - Transparent Hardware Control</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            font-weight: 300;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.4em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .status.connected {
            background: #d4edda;
            color: #155724;
        }
        
        .status.disconnected {
            background: #f8d7da;
            color: #721c24;
        }
        
        .status.connecting {
            background: #fff3cd;
            color: #856404;
        }
        
        .status::before {
            content: '';
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
        }
        
        .control-group {
            margin: 15px 0;
        }
        
        .control-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #555;
        }
        
        input, select, button, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        button {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button.secondary {
            background: #6c757d;
        }
        
        button.success {
            background: #28a745;
        }
        
        button.warning {
            background: #ffc107;
            color: #212529;
        }
        
        button.danger {
            background: #dc3545;
        }
        
        .button-group {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }
        
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        
        .response-area {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            max-height: 300px;
            overflow-y: auto;
            border: 2px solid #e9ecef;
        }
        
        .log-area {
            background: #1a1a1a;
            color: #00ff00;
            border-radius: 8px;
            padding: 15px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 12px;
            height: 250px;
            overflow-y: auto;
            border: 2px solid #333;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .stat {
            text-align: center;
            padding: 15px;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 10px;
        }
        
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
            display: block;
        }
        
        .stat-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        
        .icon {
            width: 20px;
            height: 20px;
            display: inline-block;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        
        .success {
            color: #155724;
            background: #d4edda;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .quick-actions {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 EDPMT Transparent</h1>
            <p>Simple • Secure • Universal Hardware Control</p>
        </div>
        
        <div class="grid">
            <!-- Connection Status -->
            <div class="card">
                <h2>
                    <span class="icon">🌐</span>
                    Connection
                </h2>
                <div class="control-group">
                    <span class="status" id="status">Checking...</span>
                </div>
                <div class="button-group">
                    <button onclick="connect()">Connect</button>
                    <button onclick="testConnection()" class="secondary">Test</button>
                    <button onclick="disconnect()" class="warning">Disconnect</button>
                </div>
                <div class="stats">
                    <div class="stat">
                        <span class="stat-value" id="uptime">--</span>
                        <div class="stat-label">Uptime</div>
                    </div>
                    <div class="stat">
                        <span class="stat-value" id="messages">--</span>
                        <div class="stat-label">Messages</div>
                    </div>
                </div>
            </div>
            
            <!-- Universal API -->
            <div class="card">
                <h2>
                    <span class="icon">⚡</span>
                    Universal API
                </h2>
                <p style="margin-bottom: 15px; color: #666;">One method for everything: <code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px;">execute(action, target, params)</code></p>
                
                <div class="control-group">
                    <label>Action</label>
                    <select id="action">
                        <option value="set">Set</option>
                        <option value="get">Get</option>
                        <option value="read">Read</option>
                        <option value="write">Write</option>
                        <option value="scan">Scan</option>
                        <option value="play">Play</option>
                        <option value="pwm">PWM</option>
                        <option value="transfer">Transfer</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label>Target</label>
                    <select id="target">
                        <option value="gpio">GPIO</option>
                        <option value="i2c">I2C</option>
                        <option value="spi">SPI</option>
                        <option value="uart">UART</option>
                        <option value="audio">Audio</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label>Parameters (JSON)</label>
                    <textarea id="params" rows="3" placeholder='{"pin": 17, "value": 1}'></textarea>
                </div>
                
                <button onclick="executeCommand()">
                    <span id="execute-btn-text">Execute</span>
                    <div id="execute-loading" class="loading" style="display: none;"></div>
                </button>
            </div>
            
            <!-- Quick Actions -->
            <div class="card">
                <h2>
                    <span class="icon">🚀</span>
                    Quick Actions
                </h2>
                
                <div class="control-group">
                    <label>GPIO Control</label>
                    <div class="quick-actions">
                        <button onclick="quickAction('set', 'gpio', {pin: 17, value: 1})" class="success">GPIO 17 HIGH</button>
                        <button onclick="quickAction('set', 'gpio', {pin: 17, value: 0})" class="danger">GPIO 17 LOW</button>
                        <button onclick="quickAction('get', 'gpio', {pin: 18})">Read GPIO 18</button>
                        <button onclick="quickAction('pwm', 'gpio', {pin: 18, frequency: 1000, duty_cycle: 50})">PWM GPIO 18</button>
                    </div>
                </div>
                
                <div class="control-group">
                    <label>I2C Operations</label>
                    <div class="quick-actions">
                        <button onclick="quickAction('scan', 'i2c', {})">Scan I2C Bus</button>
                        <button onclick="quickAction('read', 'i2c', {device: 0x76, register: 0xD0, length: 1})">Read BME280 ID</button>
                    </div>
                </div>
                
                <div class="control-group">
                    <label>Audio & Misc</label>
                    <div class="quick-actions">
                        <button onclick="quickAction('play', 'audio', {frequency: 440, duration: 0.5})">Play 440Hz</button>
                        <button onclick="quickAction('play', 'audio', {frequency: 880, duration: 0.3})">Play 880Hz</button>
                    </div>
                </div>
            </div>
            
            <!-- System Info -->
            <div class="card">
                <h2>
                    <span class="icon">📊</span>
                    System Information
                </h2>
                <div id="system-info">
                    <div class="stats">
                        <div class="stat">
                            <span class="stat-value" id="transport">--</span>
                            <div class="stat-label">Transport</div>
                        </div>
                        <div class="stat">
                            <span class="stat-value" id="tls-status">--</span>
                            <div class="stat-label">TLS</div>
                        </div>
                        <div class="stat">
                            <span class="stat-value" id="errors">--</span>
                            <div class="stat-label">Errors</div>
                        </div>
                    </div>
                </div>
                <button onclick="getSystemInfo()" class="secondary">Refresh Info</button>
            </div>
        </div>
        
        <!-- Response Area -->
        <div class="card">
            <h2>
                <span class="icon">📤</span>
                Response
            </h2>
            <div class="response-area" id="response">Ready for commands...</div>
        </div>
        
        <!-- System Log -->
        <div class="card">
            <h2>
                <span class="icon">📋</span>
                System Log
            </h2>
            <div class="log-area" id="log"></div>
            <div class="button-group" style="margin-top: 15px;">
                <button onclick="clearLog()" class="secondary">Clear Log</button>
                <button onclick="exportLog()" class="secondary">Export Log</button>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let reconnectInterval = null;
        let messageCount = 0;
        let startTime = Date.now();
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        // Initialize on page load
        window.addEventListener('load', () => {
            log('🚀 EDPMT Web Interface initialized');
            connect();
            testConnection();
            updateSystemInfo();
            setInterval(updateUptime, 1000);
        });
        
        function connect() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                log('Already connected');
                return;
            }
            
            setStatus('connecting', 'Connecting...');
            log('🔌 Attempting WebSocket connection...');
            
            try {
                ws = new WebSocket(wsUrl);
                
                ws.onopen = () => {
                    setStatus('connected', 'Connected');
                    log('✅ WebSocket connected successfully');
                    clearReconnectInterval();
                };
                
                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        handleResponse(data);
                        messageCount++;
                        updateMessageCount();
                    } catch (e) {
                        log(`❌ Invalid message format: ${e.message}`, 'error');
                    }
                };
                
                ws.onerror = (error) => {
                    log('❌ WebSocket error occurred', 'error');
                    setStatus('disconnected', 'Error');
                };
                
                ws.onclose = () => {
                    setStatus('disconnected', 'Disconnected');
                    log('🔌 WebSocket disconnected');
                    scheduleReconnect();
                };
                
            } catch (error) {
                log(`❌ Connection failed: ${error.message}`, 'error');
                setStatus('disconnected', 'Failed');
            }
        }
        
        function disconnect() {
            if (ws) {
                ws.close();
                ws = null;
            }
            clearReconnectInterval();
            setStatus('disconnected', 'Disconnected');
            log('🔌 Manually disconnected');
        }
        
        function scheduleReconnect() {
            clearReconnectInterval();
            reconnectInterval = setInterval(() => {
                log('🔄 Attempting to reconnect...');
                connect();
            }, 5000);
        }
        
        function clearReconnectInterval() {
            if (reconnectInterval) {
                clearInterval(reconnectInterval);
                reconnectInterval = null;
            }
        }
        
        function setStatus(type, text) {
            const statusEl = document.getElementById('status');
            statusEl.className = `status ${type}`;
            statusEl.textContent = text;
        }
        
        function executeCommand() {
            const action = document.getElementById('action').value;
            const target = document.getElementById('target').value;
            let params = {};
            
            try {
                const paramsText = document.getElementById('params').value.trim();
                if (paramsText) {
                    params = JSON.parse(paramsText);
                }
            } catch (e) {
                showError('Invalid JSON parameters');
                return;
            }
            
            setExecuteLoading(true);
            sendCommand(action, target, params);
        }
        
        function quickAction(action, target, params) {
            sendCommand(action, target, params);
        }
        
        function sendCommand(action, target, params) {
            const message = {
                action: action,
                target: target,
                params: params,
                timestamp: Date.now()
            };
            
            log(`📤 Sending: ${action} ${target} ${JSON.stringify(params)}`);
            
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify(message));
            } else {
                // Fallback to HTTP
                fetch('/api/execute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(message)
                })
                .then(r => r.json())
                .then(data => {
                    handleResponse(data);
                    messageCount++;
                    updateMessageCount();
                })
                .catch(err => {
                    log(`❌ HTTP request failed: ${err}`, 'error');
                    showError(`Request failed: ${err.message}`);
                })
                .finally(() => {
                    setExecuteLoading(false);
                });
            }
        }
        
        function handleResponse(data) {
            setExecuteLoading(false);
            
            document.getElementById('response').innerHTML = 
                `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            
            if (data.success) {
                log(`✅ Success: ${JSON.stringify(data.result)}`, 'success');
                showSuccess(`Command executed successfully`);
            } else {
                log(`❌ Error: ${data.error}`, 'error');
                showError(data.error);
            }
        }
        
        function testConnection() {
            log('🔍 Testing connection...');
            fetch('/health')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('response').innerHTML = 
                        `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                    log('✅ Health check successful', 'success');
                    updateSystemInfo(data);
                })
                .catch(err => {
                    log(`❌ Health check failed: ${err}`, 'error');
                    showError(`Health check failed: ${err.message}`);
                });
        }
        
        function getSystemInfo() {
            testConnection();
        }
        
        function updateSystemInfo(data) {
            if (data) {
                document.getElementById('transport').textContent = data.transport || '--';
                document.getElementById('tls-status').textContent = data.tls ? '✅' : '❌';
                document.getElementById('errors').textContent = data.stats?.errors || '0';
            }
        }
        
        function updateUptime() {
            const uptime = Math.floor((Date.now() - startTime) / 1000);
            const hours = Math.floor(uptime / 3600);
            const minutes = Math.floor((uptime % 3600) / 60);
            const seconds = uptime % 60;
            
            document.getElementById('uptime').textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
        
        function updateMessageCount() {
            document.getElementById('messages').textContent = messageCount;
        }
        
        function setExecuteLoading(loading) {
            const btnText = document.getElementById('execute-btn-text');
            const loadingEl = document.getElementById('execute-loading');
            
            if (loading) {
                btnText.style.display = 'none';
                loadingEl.style.display = 'inline-block';
            } else {
                btnText.style.display = 'inline';
                loadingEl.style.display = 'none';
            }
        }
        
        function log(message, level = 'info') {
            const logDiv = document.getElementById('log');
            const entry = document.createElement('div');
            const timestamp = new Date().toLocaleTimeString();
            
            entry.innerHTML = `<span style="color: #888;">[${timestamp}]</span> ${message}`;
            
            if (level === 'error') entry.style.color = '#ff6b6b';
            if (level === 'success') entry.style.color = '#51cf66';
            if (level === 'warning') entry.style.color = '#ffd43b';
            
            logDiv.appendChild(entry);
            logDiv.scrollTop = logDiv.scrollHeight;
            
            // Keep only last 100 entries
            while (logDiv.children.length > 100) {
                logDiv.removeChild(logDiv.firstChild);
            }
        }
        
        function clearLog() {
            document.getElementById('log').innerHTML = '';
            log('📋 Log cleared');
        }
        
        function exportLog() {
            const logContent = document.getElementById('log').textContent;
            const blob = new Blob([logContent], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `edpmt-log-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            log('📁 Log exported to file');
        }
        
        function showError(message) {
            showNotification(message, 'error');
        }
        
        function showSuccess(message) {
            showNotification(message, 'success');
        }
        
        function showNotification(message, type) {
            // Create notification element
            const notification = document.createElement('div');
            notification.className = type;
            notification.textContent = message;
            notification.style.position = 'fixed';
            notification.style.top = '20px';
            notification.style.right = '20px';
            notification.style.zIndex = '10000';
            notification.style.padding = '15px 20px';
            notification.style.borderRadius = '8px';
            notification.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
            notification.style.maxWidth = '300px';
            
            document.body.appendChild(notification);
            
            // Auto remove after 3 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 3000);
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'Enter':
                        e.preventDefault();
                        executeCommand();
                        break;
                    case 'r':
                        e.preventDefault();
                        connect();
                        break;
                    case 'l':
                        e.preventDefault();
                        clearLog();
                        break;
                }
            }
        });
        
        // Add tooltips for keyboard shortcuts
        document.addEventListener('DOMContentLoaded', () => {
            const executeBtn = document.querySelector('button[onclick="executeCommand()"]');
            if (executeBtn) {
                executeBtn.title = 'Execute Command (Ctrl+Enter)';
            }
        });
    </script>
</body>
</html>'''
