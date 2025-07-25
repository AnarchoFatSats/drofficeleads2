// Frontend Configuration
const CONFIG = {
    // ECS Backend URL
    API_BASE_URL: 'http://cura-genesis-crm-alb-370496819.us-east-1.elb.amazonaws.com',
    
    // API Endpoints
    ENDPOINTS: {
        LEADS: '/api/v1/leads',
        SUMMARY: '/api/v1/summary', 
        HOT_LEADS: '/api/v1/hot-leads',
        REGIONS: '/api/v1/regions',
        HEALTH: '/health'
    },
    
    // Environment
    ENVIRONMENT: 'production'
};

// Make config available globally
window.CONFIG = CONFIG; 