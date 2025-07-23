# 🚀 Cura Genesis CRM - Production Deployment Guide

## Overview

This guide covers the complete process for deploying the Cura Genesis CRM system to production.

## ✅ Production Readiness Status

### 🟢 COMPLETED
- ✅ **Server Stability**: Fixed port conflicts and crashes
- ✅ **Database Schema**: All migrations applied, missing columns added
- ✅ **Circular Imports**: Fixed enum import issues
- ✅ **Security Headers**: Added CSP, HSTS, X-Frame-Options, etc.
- ✅ **Rate Limiting**: 100 requests/minute per IP
- ✅ **Error Handling**: Comprehensive error middleware with request IDs
- ✅ **Logging**: Structured logging with request tracing
- ✅ **Health Checks**: Full system health endpoint
- ✅ **Configuration**: Production config template created

### 🟡 REQUIRED FOR PRODUCTION
- 🔑 **Change Secret Keys**: Update SECRET_KEY and JWT_SECRET_KEY
- 🗄️ **Production Database**: Configure external PostgreSQL
- 📧 **Email Configuration**: Set up SMTP for notifications  
- 🔒 **SSL/TLS**: Configure HTTPS certificates
- 🔥 **Firewall**: Configure security rules

### ✅ MONITORING & OBSERVABILITY READY
- 📊 **Prometheus Metrics**: Application and system metrics collection
- 🔍 **APM Monitoring**: Request tracking with performance alerts
- 🗄️ **Database Monitoring**: Connection stats and slow query detection
- 🚨 **Real-time Alerting**: Automated alert system for critical issues
- 📈 **Performance Dashboards**: Comprehensive monitoring endpoints
- 🏥 **Health Checks**: Multi-level system health monitoring

## 🛠️ Pre-Deployment Requirements

### System Requirements
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Amazon Linux 2
- **Python**: 3.9+
- **Database**: PostgreSQL 12+
- **Cache**: Redis 6+
- **Memory**: Minimum 2GB RAM (4GB+ recommended)
- **Storage**: 20GB+ available space

### Dependencies
```bash
# Install system dependencies
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server nginx
sudo apt install python3-pip python3-venv supervisor
```

## 🔧 Deployment Steps

### 1. Server Setup

```bash
# Create application user
sudo useradd -m -s /bin/bash crmuser
sudo usermod -aG sudo crmuser

# Create application directory
sudo mkdir -p /opt/cura-genesis-crm
sudo chown crmuser:crmuser /opt/cura-genesis-crm
```

### 2. Database Setup

```bash
# Create production database
sudo -u postgres createdb cura_genesis_crm_prod
sudo -u postgres createuser crmuser
sudo -u postgres psql -c "ALTER USER crmuser WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cura_genesis_crm_prod TO crmuser;"
```

### 3. Application Deployment

```bash
# Switch to application user
sudo su - crmuser
cd /opt/cura-genesis-crm

# Clone repository
git clone [your-repo-url] .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python migrate_percentile_system.py
python migrate_team_hierarchy.py
```

### 4. Environment Configuration

Create `/opt/cura-genesis-crm/.env`:

```bash
# Copy production template
cp production_config.py .env.production

# Generate secure keys
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))" >> .env
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))" >> .env

# Configure database
echo "DATABASE_URL=postgresql://crmuser:secure_password@localhost:5432/cura_genesis_crm_prod" >> .env

# Configure Redis
echo "REDIS_URL=redis://localhost:6379/0" >> .env
```

### 5. Nginx Configuration

Create `/etc/nginx/sites-available/cura-genesis-crm`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
    
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files (if serving directly)
    location /static/ {
        alias /opt/cura-genesis-crm/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/cura-genesis-crm /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 📊 Monitoring & Observability Setup

The CRM includes comprehensive monitoring with Prometheus metrics, APM, and real-time alerting.

### Monitoring Endpoints

- **`/metrics`** - Prometheus metrics endpoint
- **`/api/v1/monitoring/health`** - Comprehensive health check
- **`/api/v1/monitoring/performance`** - Performance metrics
- **`/api/v1/monitoring/database`** - Database performance
- **`/api/v1/monitoring/dashboard`** - Complete monitoring dashboard
- **`/api/v1/monitoring/alerts`** - Recent system alerts

### Install Monitoring Dependencies

```bash
pip install prometheus-client psutil
```

### Prometheus Setup

1. **Install Prometheus**:
```bash
# Download and install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*
```

2. **Configure Prometheus** (use `monitoring_config.yaml`):
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'crm-app'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/metrics'
```

3. **Start Prometheus**:
```bash
./prometheus --config.file=crm_prometheus.yml
```

### Grafana Dashboard Setup

1. **Install Grafana**:
```bash
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
sudo apt-get update
sudo apt-get install grafana
```

2. **Start Grafana**:
```bash
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

3. **Access Grafana**: http://localhost:3000 (admin/admin)

4. **Import CRM Dashboard**:
   - Add Prometheus data source: http://localhost:9090
   - Import dashboard from `monitoring_config.yaml`

### Database Monitoring

Enable PostgreSQL statistics:
```sql
-- Enable pg_stat_statements for slow query monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Add to postgresql.conf:
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
```

### Alerting Setup

1. **Install Alertmanager**:
```bash
wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
tar xvfz alertmanager-*.tar.gz
cd alertmanager-*
```

2. **Configure alerts** (from `monitoring_config.yaml`):
```yaml
route:
  receiver: 'email-alerts'
receivers:
  - name: 'email-alerts'
    email_configs:
      - to: 'admin@curagenesis.com'
        subject: '[ALERT] CRM System Alert'
```

### Production Monitoring Checklist

- ✅ **Metrics Collection**: Prometheus scraping `/metrics`
- ✅ **Performance Monitoring**: APM tracking all requests
- ✅ **Database Monitoring**: Connection and query tracking
- ✅ **System Monitoring**: CPU, memory, disk usage
- ✅ **Error Tracking**: Automatic error detection and alerting
- ✅ **Health Checks**: Multi-component health monitoring
- ✅ **Real-time Dashboards**: Grafana visualization
- ✅ **Alert Configuration**: Email/SMS notifications

### Testing Monitoring

Test the monitoring system:
```bash
# Check metrics endpoint
curl http://localhost:8001/metrics

# Test comprehensive health check
curl http://localhost:8001/api/v1/monitoring/health

# View performance metrics
curl http://localhost:8001/api/v1/monitoring/performance

# Trigger test alert
curl -X POST http://localhost:8001/api/v1/monitoring/test-alert
```

### 6. Process Management with Supervisor

Create `/etc/supervisor/conf.d/cura-genesis-crm.conf`:

```ini
[program:cura-genesis-crm]
command=/opt/cura-genesis-crm/venv/bin/python crm_main.py
directory=/opt/cura-genesis-crm
user=crmuser
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/cura-genesis-crm.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PYTHONPATH="/opt/cura-genesis-crm"
```

Start the service:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start cura-genesis-crm
```

### 7. SSL Certificate Setup

Using Let's Encrypt:
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### 8. Monitoring Setup

#### Log Rotation
Create `/etc/logrotate.d/cura-genesis-crm`:
```
/var/log/cura-genesis-crm.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 crmuser crmuser
    postrotate
        supervisorctl restart cura-genesis-crm
    endscript
}
```

#### Health Check Script
Create `/opt/cura-genesis-crm/health_check.sh`:
```bash
#!/bin/bash
HEALTH_URL="https://yourdomain.com/health"
EXPECTED_STATUS="healthy"

response=$(curl -s "$HEALTH_URL" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ "$response" != "$EXPECTED_STATUS" ]; then
    echo "Health check failed: $response"
    # Send alert (email, Slack, etc.)
    exit 1
fi

echo "Health check passed"
exit 0
```

### 9. Backup Configuration

Create backup script `/opt/cura-genesis-crm/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/crm"
DB_NAME="cura_genesis_crm_prod"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Database backup
pg_dump "$DB_NAME" | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Application backup
tar -czf "$BACKUP_DIR/app_backup_$DATE.tar.gz" /opt/cura-genesis-crm --exclude=venv --exclude=__pycache__

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /opt/cura-genesis-crm/backup.sh >> /var/log/backup.log 2>&1
```

## 🔒 Security Hardening

### Firewall Configuration
```bash
# UFW setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Database Security
```bash
# PostgreSQL hardening
sudo nano /etc/postgresql/12/main/postgresql.conf
# Set: listen_addresses = 'localhost'
# Set: ssl = on

sudo nano /etc/postgresql/12/main/pg_hba.conf
# Use md5 authentication method
```

### Application Security
```bash
# Set secure file permissions
sudo chown -R crmuser:crmuser /opt/cura-genesis-crm
sudo chmod -R 750 /opt/cura-genesis-crm
sudo chmod 600 /opt/cura-genesis-crm/.env
```

## 📊 Monitoring & Alerts

### System Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Set up disk space monitoring
echo '#!/bin/bash
df -h | awk '"'"'$5 > 80 {print "Disk usage high: " $0}'"'"' | mail -s "Disk Alert" admin@yourdomain.com' > /opt/cura-genesis-crm/disk_check.sh

# Add to crontab (check every hour)
0 * * * * /opt/cura-genesis-crm/disk_check.sh
```

### Application Metrics
The CRM includes built-in health checks and metrics:
- **Health endpoint**: `GET /health`
- **Metrics endpoint**: `GET /metrics` (if enabled)
- **Real-time dashboard**: WebSocket monitoring

## 🧪 Testing Production Deployment

### Pre-Go-Live Tests
```bash
# 1. Health check
curl https://yourdomain.com/health

# 2. Authentication test
curl -X POST https://yourdomain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 3. API endpoints test
curl https://yourdomain.com/api/v1/leads?limit=1

# 4. WebSocket test (use browser developer tools)
# Connect to: wss://yourdomain.com/ws/1

# 5. Load test (optional)
# Install: pip install locust
# Run: locust -f load_test.py --host=https://yourdomain.com
```

### Performance Validation
- Response time < 500ms for API calls
- Database queries < 100ms average
- Memory usage < 80% of available
- CPU usage < 70% under normal load

## 🚨 Troubleshooting

### Common Issues
1. **502 Bad Gateway**: Check if application is running (`sudo supervisorctl status`)
2. **Database connection errors**: Verify PostgreSQL service and credentials
3. **Redis connection errors**: Check Redis service (`sudo systemctl status redis`)
4. **Permission errors**: Verify file ownership and permissions

### Log Locations
- Application logs: `/var/log/cura-genesis-crm.log`
- Nginx logs: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- PostgreSQL logs: `/var/log/postgresql/postgresql-12-main.log`
- Redis logs: `/var/log/redis/redis-server.log`

### Emergency Procedures
```bash
# Restart all services
sudo supervisorctl restart cura-genesis-crm
sudo systemctl restart nginx
sudo systemctl restart postgresql
sudo systemctl restart redis

# View live logs
sudo tail -f /var/log/cura-genesis-crm.log

# Check system resources
htop
df -h
free -m
```

## 📞 Support & Maintenance

### Regular Maintenance Tasks
- **Weekly**: Review logs and performance metrics
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Full backup test and recovery drill
- **Yearly**: Security audit and penetration testing

### Contact Information
- **Technical Support**: tech@yourdomain.com
- **Emergency Contact**: emergency@yourdomain.com
- **Documentation**: https://docs.yourdomain.com

---

## 🎉 Go-Live Checklist

Before switching to production:

- [ ] All security configurations applied
- [ ] SSL certificates installed and tested
- [ ] Database backups working
- [ ] Monitoring and alerts configured
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Documentation updated
- [ ] Team trained on production procedures
- [ ] Rollback plan prepared
- [ ] Go-live communication sent

**Congratulations! Your Cura Genesis CRM is ready for production! 🚀** 