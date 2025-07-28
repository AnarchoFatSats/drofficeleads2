// Frontend Configuration
const CONFIG = {
    // Production HTTPS Backend URL (AWS Lambda + API Gateway)
    API_BASE_URL: 'https://api.vantagepointcrm.com',
    
    // API Endpoints
    ENDPOINTS: {
        // Authentication
        LOGIN: '/api/v1/auth/login',
        
        // Lead Management
        LEADS: '/api/v1/leads',
        
        // Dashboard
        SUMMARY: '/api/v1/summary', 
        HOT_LEADS: '/api/v1/hot-leads',
        REGIONS: '/api/v1/regions',
        
        // Health Check
        HEALTH: '/health'
    },
    
    // Environment
    ENVIRONMENT: 'production',
    
    // Default credentials for demo
    DEFAULT_CREDENTIALS: {
        username: 'admin',
        password: 'admin123'
    }
};

// Make config available globally
window.CONFIG = CONFIG; 