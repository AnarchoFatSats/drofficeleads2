#!/usr/bin/env python3
"""
Production Configuration for Cura Genesis CRM
Template for production deployment settings
"""

import os
from typing import List

class ProductionConfig:
    """Production environment configuration"""
    
    # ================================
    # Application Settings
    # ================================
    APP_NAME: str = "Cura Genesis CRM"
    DEBUG: bool = False
    TESTING: bool = False
    VERSION: str = "1.0.0"
    
    # Security Keys (CHANGE THESE!)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_THIS_TO_A_SECURE_RANDOM_STRING_IN_PRODUCTION")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "CHANGE_THIS_TO_A_DIFFERENT_SECURE_RANDOM_STRING")
    
    # ================================
    # Database Configuration
    # ================================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://username:password@localhost:5432/cura_genesis_crm_prod"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # ================================
    # Redis Configuration
    # ================================
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_POOL_SIZE: int = 10
    REDIS_TIMEOUT: int = 5
    
    # ================================
    # Security Settings
    # ================================
    ALLOWED_HOSTS: List[str] = [
        "yourdomain.com",
        "*.yourdomain.com",
        "localhost",  # Remove in production
        "127.0.0.1"   # Remove in production
    ]
    
    CORS_ORIGINS: List[str] = [
        "https://yourdomain.com",
        "https://app.yourdomain.com",
        "https://crm.yourdomain.com"
    ]
    
    # Session & Cookie Security
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "strict"
    CSRF_COOKIE_SECURE: bool = True
    
    # ================================
    # Authentication Settings
    # ================================
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_SPECIAL: bool = True
    ENABLE_TWO_FACTOR_AUTH: bool = False
    
    # ================================
    # Rate Limiting
    # ================================
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    RATE_LIMIT_STORAGE: str = "redis"
    
    # ================================
    # Email Configuration
    # ================================
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.youremailprovider.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@yourdomain.com")
    
    # ================================
    # Logging Configuration
    # ================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "logs/crm.log"
    LOG_MAX_SIZE: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # ================================
    # File Upload Settings
    # ================================
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_PATH: str = "/var/uploads/crm"
    ALLOWED_FILE_TYPES: List[str] = [".csv", ".xlsx", ".pdf", ".doc", ".docx"]
    
    # ================================
    # Performance Settings
    # ================================
    ENABLE_GZIP: bool = True
    CACHE_TIMEOUT: int = 300  # 5 minutes
    STATIC_FILE_CACHE: int = 86400  # 1 day
    
    # ================================
    # Feature Flags
    # ================================
    ENABLE_REGISTRATION: bool = False
    ENABLE_FORGOT_PASSWORD: bool = True
    ENABLE_EMAIL_VERIFICATION: bool = True
    ENABLE_API_DOCS: bool = False  # Disable in production
    ENABLE_METRICS_ENDPOINT: bool = True
    ENABLE_HEALTH_CHECKS: bool = True
    
    # ================================
    # Monitoring & Analytics
    # ================================
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    ENABLE_SENTRY: bool = bool(SENTRY_DSN)
    
    # Metrics
    PROMETHEUS_ENABLED: bool = True
    METRICS_PATH: str = "/metrics"
    
    # ================================
    # Backup Configuration
    # ================================
    BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE: str = "0 2 * * *"  # Daily at 2 AM
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_PATH: str = "/var/backups/crm"
    
    # ================================
    # External API Configuration
    # ================================
    # Twilio (for SMS notifications)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    ENABLE_SMS: bool = bool(TWILIO_ACCOUNT_SID)
    
    # SendGrid (for email)
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    ENABLE_SENDGRID: bool = bool(SENDGRID_API_KEY)
    
    # ================================
    # Deployment Information
    # ================================
    ENVIRONMENT: str = "production"
    DEPLOYMENT_DATE: str = os.getenv("DEPLOYMENT_DATE", "")
    COMMIT_HASH: str = os.getenv("COMMIT_HASH", "")
    BUILD_NUMBER: str = os.getenv("BUILD_NUMBER", "")
    
    # ================================
    # Health Check Configuration
    # ================================
    HEALTH_CHECK_TIMEOUT: int = 5
    DATABASE_HEALTH_CHECK: bool = True
    REDIS_HEALTH_CHECK: bool = True
    EXTERNAL_API_HEALTH_CHECK: bool = False
    
    # ================================
    # SSL/TLS Configuration
    # ================================
    FORCE_HTTPS: bool = True
    HSTS_MAX_AGE: int = 31536000  # 1 year
    HSTS_INCLUDE_SUBDOMAINS: bool = True
    HSTS_PRELOAD: bool = True


# ================================
# Configuration Validation
# ================================

def validate_production_config():
    """Validate production configuration and warn about insecure settings"""
    issues = []
    
    config = ProductionConfig()
    
    # Check for default secret keys
    if config.SECRET_KEY == "CHANGE_THIS_TO_A_SECURE_RANDOM_STRING_IN_PRODUCTION":
        issues.append("🚨 SECRET_KEY is using default value - CHANGE THIS!")
    
    if config.JWT_SECRET_KEY == "CHANGE_THIS_TO_A_DIFFERENT_SECURE_RANDOM_STRING":
        issues.append("🚨 JWT_SECRET_KEY is using default value - CHANGE THIS!")
    
    # Check database URL
    if "localhost" in config.DATABASE_URL and config.ENVIRONMENT == "production":
        issues.append("⚠️ Database URL uses localhost in production")
    
    # Check CORS origins
    if "*" in str(config.CORS_ORIGINS):
        issues.append("⚠️ CORS allows all origins - restrict for production")
    
    # Check debug mode
    if config.DEBUG:
        issues.append("⚠️ DEBUG mode is enabled in production")
    
    # Check HTTPS enforcement
    if not config.FORCE_HTTPS:
        issues.append("⚠️ HTTPS is not enforced")
    
    # Check if docs are enabled
    if config.ENABLE_API_DOCS:
        issues.append("⚠️ API documentation is enabled in production")
    
    return issues


def print_production_checklist():
    """Print production deployment checklist"""
    print("🚀 PRODUCTION DEPLOYMENT CHECKLIST")
    print("=" * 50)
    
    checklist = [
        "✅ Change SECRET_KEY and JWT_SECRET_KEY",
        "✅ Configure production database URL",
        "✅ Set up Redis for caching",
        "✅ Configure SMTP for email notifications",
        "✅ Set up SSL/TLS certificates",
        "✅ Configure reverse proxy (nginx/Apache)",
        "✅ Set up log rotation",
        "✅ Configure automated backups",
        "✅ Set up monitoring (Sentry, Prometheus)",
        "✅ Configure rate limiting",
        "✅ Test all API endpoints",
        "✅ Run security audit",
        "✅ Set up CI/CD pipeline",
        "✅ Configure domain and DNS",
        "✅ Set up firewall rules"
    ]
    
    for item in checklist:
        print(f"  {item}")
    
    print("\n🔍 CONFIGURATION ISSUES:")
    issues = validate_production_config()
    if issues:
        for issue in issues:
            print(f"  {issue}")
    else:
        print("  ✅ No configuration issues found!")


if __name__ == "__main__":
    print_production_checklist() 