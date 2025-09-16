// Runtime configuration for EDPMT Frontend
window.EDPMT_CONFIG = {
    // WebSocket server URL
    WS_URL: 'ws://localhost:8086/ws',
    
    // API base URL
    API_BASE_URL: 'http://localhost:8085',
    
    // Debug mode
    DEBUG: true,
    
    // Version
    VERSION: '1.0.0',
    
    // Default theme
    THEME: 'light',
    
    // Features
    FEATURES: {
        VISUAL_PROGRAMMING: true,
        PERIPHERAL_CONTROL: true,
        PROJECT_MANAGEMENT: true
    },
    
    // Default settings
    SETTINGS: {
        AUTO_SAVE: true,
        AUTO_CONNECT: true,
        NOTIFICATIONS: true,
        ANIMATIONS: true
    }
};

// Make config available globally
console.log('EDPMT Runtime Configuration loaded:', window.EDPMT_CONFIG);
