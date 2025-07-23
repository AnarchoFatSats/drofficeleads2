#!/usr/bin/env python3
"""
Production Monitoring & Observability for Cura Genesis CRM
Includes APM, metrics collection, database monitoring, and real-time alerting
"""

import time
import psutil
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import redis
import psycopg2
from sqlalchemy import text
from sqlalchemy.orm import Session

# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("Prometheus client not available - metrics collection disabled")

# ================================
# Metrics Collection
# ================================

class MetricsCollector:
    """Collect application and system metrics"""
    
    def __init__(self):
        if PROMETHEUS_AVAILABLE:
            self.registry = CollectorRegistry()
            
            # Application metrics
            self.request_count = Counter(
                'crm_http_requests_total',
                'Total HTTP requests',
                ['method', 'endpoint', 'status'],
                registry=self.registry
            )
            
            self.request_duration = Histogram(
                'crm_http_request_duration_seconds',
                'HTTP request duration',
                ['method', 'endpoint'],
                registry=self.registry
            )
            
            self.active_connections = Gauge(
                'crm_active_connections',
                'Active database connections',
                registry=self.registry
            )
            
            self.leads_processed = Counter(
                'crm_leads_processed_total',
                'Total leads processed',
                ['status', 'source'],
                registry=self.registry
            )
            
            self.user_sessions = Gauge(
                'crm_active_user_sessions',
                'Active user sessions',
                registry=self.registry
            )
            
            # System metrics
            self.cpu_usage = Gauge(
                'crm_cpu_usage_percent',
                'CPU usage percentage',
                registry=self.registry
            )
            
            self.memory_usage = Gauge(
                'crm_memory_usage_bytes',
                'Memory usage in bytes',
                registry=self.registry
            )
            
            self.database_query_duration = Histogram(
                'crm_database_query_duration_seconds',
                'Database query duration',
                ['operation', 'table'],
                registry=self.registry
            )
    
    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        if PROMETHEUS_AVAILABLE:
            self.request_count.labels(method=method, endpoint=endpoint, status=status).inc()
            self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_lead_processed(self, status: str, source: str):
        """Record lead processing metrics"""
        if PROMETHEUS_AVAILABLE:
            self.leads_processed.labels(status=status, source=source).inc()
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        if PROMETHEUS_AVAILABLE:
            self.cpu_usage.set(psutil.cpu_percent())
            self.memory_usage.set(psutil.virtual_memory().used)
    
    def update_database_connections(self, count: int):
        """Update active database connection count"""
        if PROMETHEUS_AVAILABLE:
            self.active_connections.set(count)
    
    def record_database_query(self, operation: str, table: str, duration: float):
        """Record database query metrics"""
        if PROMETHEUS_AVAILABLE:
            self.database_query_duration.labels(operation=operation, table=table).observe(duration)
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        if PROMETHEUS_AVAILABLE:
            return generate_latest(self.registry)
        return ""

# ================================
# Application Performance Monitoring
# ================================

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: datetime
    endpoint: str
    method: str
    duration: float
    status_code: int
    user_id: Optional[int] = None
    error_message: Optional[str] = None
    query_count: int = 0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0

class APMMonitor:
    """Application Performance Monitor"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.metrics_buffer: List[PerformanceMetric] = []
        self.max_buffer_size = 1000
        self.logger = logging.getLogger(__name__)
    
    def record_request(self, metric: PerformanceMetric):
        """Record a request performance metric"""
        self.metrics_buffer.append(metric)
        
        # Store in Redis for real-time monitoring
        if self.redis_client:
            key = f"apm:request:{int(time.time())}"
            self.redis_client.setex(key, 3600, json.dumps(asdict(metric), default=str))
        
        # Flush buffer if it gets too large
        if len(self.metrics_buffer) >= self.max_buffer_size:
            self.flush_metrics()
        
        # Check for performance anomalies
        self.check_performance_alerts(metric)
    
    def check_performance_alerts(self, metric: PerformanceMetric):
        """Check for performance issues and trigger alerts"""
        alerts = []
        
        # Slow response alert
        if metric.duration > 5.0:
            alerts.append({
                "type": "slow_response",
                "severity": "warning",
                "message": f"Slow response detected: {metric.endpoint} took {metric.duration:.2f}s",
                "metric": metric
            })
        
        # High CPU usage alert
        if metric.cpu_usage > 80.0:
            alerts.append({
                "type": "high_cpu",
                "severity": "warning", 
                "message": f"High CPU usage: {metric.cpu_usage:.1f}%",
                "metric": metric
            })
        
        # High memory usage alert
        if metric.memory_usage > 1024 * 1024 * 1024:  # 1GB
            alerts.append({
                "type": "high_memory",
                "severity": "warning",
                "message": f"High memory usage: {metric.memory_usage / (1024**3):.2f}GB",
                "metric": metric
            })
        
        # Error rate alert
        if metric.status_code >= 500:
            alerts.append({
                "type": "server_error",
                "severity": "critical",
                "message": f"Server error: {metric.status_code} on {metric.endpoint}",
                "metric": metric
            })
        
        for alert in alerts:
            self.trigger_alert(alert)
    
    def trigger_alert(self, alert: Dict[str, Any]):
        """Trigger an alert"""
        self.logger.warning(f"ALERT: {alert['message']}")
        
        # Store alert in Redis
        if self.redis_client:
            alert_key = f"alerts:{alert['type']}:{int(time.time())}"
            self.redis_client.setex(alert_key, 86400, json.dumps(alert, default=str))
    
    def flush_metrics(self):
        """Flush metrics buffer to persistent storage"""
        if not self.metrics_buffer:
            return
        
        # Here you could write to a database, file, or external monitoring service
        self.logger.info(f"Flushing {len(self.metrics_buffer)} metrics to storage")
        
        # Clear buffer
        self.metrics_buffer.clear()
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        if not self.redis_client:
            return {}
        
        cutoff_time = int(time.time()) - (hours * 3600)
        keys = []
        
        # Get all metric keys within time range
        for key in self.redis_client.scan_iter(match="apm:request:*"):
            timestamp = int(key.decode().split(":")[-1])
            if timestamp >= cutoff_time:
                keys.append(key)
        
        if not keys:
            return {"message": "No metrics found"}
        
        # Analyze metrics
        metrics = []
        for key in keys:
            try:
                data = json.loads(self.redis_client.get(key))
                metrics.append(data)
            except (json.JSONDecodeError, TypeError):
                continue
        
        if not metrics:
            return {"message": "No valid metrics found"}
        
        # Calculate summary statistics
        durations = [m["duration"] for m in metrics]
        status_codes = [m["status_code"] for m in metrics]
        
        return {
            "total_requests": len(metrics),
            "avg_response_time": sum(durations) / len(durations),
            "max_response_time": max(durations),
            "min_response_time": min(durations),
            "error_rate": len([s for s in status_codes if s >= 400]) / len(status_codes) * 100,
            "status_code_distribution": {
                "2xx": len([s for s in status_codes if 200 <= s < 300]),
                "3xx": len([s for s in status_codes if 300 <= s < 400]),
                "4xx": len([s for s in status_codes if 400 <= s < 500]),
                "5xx": len([s for s in status_codes if s >= 500]),
            }
        }

# ================================
# Database Monitoring
# ================================

class DatabaseMonitor:
    """Monitor database performance and health"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.logger = logging.getLogger(__name__)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get database connection statistics"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Get connection count
            cursor.execute("""
                SELECT count(*) as total_connections,
                       count(*) FILTER (WHERE state = 'active') as active_connections,
                       count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            
            stats = cursor.fetchone()
            
            # Get database size
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size,
                       pg_database_size(current_database()) as db_size_bytes
            """)
            
            size_stats = cursor.fetchone()
            
            # Get slow queries
            cursor.execute("""
                SELECT query, calls, total_time, mean_time, rows
                FROM pg_stat_statements 
                WHERE mean_time > 100
                ORDER BY mean_time DESC 
                LIMIT 10
            """)
            
            slow_queries = cursor.fetchall()
            
            conn.close()
            
            return {
                "total_connections": stats[0],
                "active_connections": stats[1], 
                "idle_connections": stats[2],
                "database_size": size_stats[0],
                "database_size_bytes": size_stats[1],
                "slow_queries": [
                    {
                        "query": q[0][:100] + "..." if len(q[0]) > 100 else q[0],
                        "calls": q[1],
                        "total_time": q[2],
                        "mean_time": q[3],
                        "rows": q[4]
                    }
                    for q in slow_queries
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}
    
    def get_table_stats(self) -> Dict[str, Any]:
        """Get table-level statistics"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del, 
                       n_live_tup, n_dead_tup, last_vacuum, last_autovacuum
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
            """)
            
            tables = cursor.fetchall()
            conn.close()
            
            return {
                "tables": [
                    {
                        "schema": t[0],
                        "table": t[1], 
                        "inserts": t[2],
                        "updates": t[3],
                        "deletes": t[4],
                        "live_tuples": t[5],
                        "dead_tuples": t[6],
                        "last_vacuum": t[7],
                        "last_autovacuum": t[8]
                    }
                    for t in tables
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get table stats: {e}")
            return {"error": str(e)}

# ================================
# Health Check System
# ================================

class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self, database_url: str, redis_client: Optional[redis.Redis] = None):
        self.database_url = database_url
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            conn.close()
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        if not self.redis_client:
            return {"status": "disabled", "message": "Redis not configured"}
        
        try:
            start_time = time.time()
            self.redis_client.ping()
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = "healthy"
            alerts = []
            
            if cpu_percent > 80:
                status = "warning"
                alerts.append("High CPU usage")
            
            if memory.percent > 80:
                status = "warning" 
                alerts.append("High memory usage")
            
            if disk.percent > 90:
                status = "critical"
                alerts.append("Low disk space")
            
            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "alerts": alerts,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {
            "overall_status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        # Run all checks
        results["checks"]["database"] = await self.check_database_health()
        results["checks"]["redis"] = await self.check_redis_health()
        results["checks"]["system"] = await self.check_system_resources()
        
        # Determine overall status
        statuses = [check["status"] for check in results["checks"].values()]
        
        if "unhealthy" in statuses or "critical" in statuses:
            results["overall_status"] = "unhealthy"
        elif "warning" in statuses:
            results["overall_status"] = "degraded"
        
        return results

# ================================
# Monitoring Dashboard Data
# ================================

class MonitoringDashboard:
    """Provide data for monitoring dashboard"""
    
    def __init__(self, metrics_collector: MetricsCollector, apm_monitor: APMMonitor, 
                 db_monitor: DatabaseMonitor, health_checker: HealthChecker):
        self.metrics = metrics_collector
        self.apm = apm_monitor
        self.db_monitor = db_monitor
        self.health_checker = health_checker
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        return {
            "health": await self.health_checker.comprehensive_health_check(),
            "performance": self.apm.get_performance_summary(hours=1),
            "database": {
                "connections": self.db_monitor.get_connection_stats(),
                "tables": self.db_monitor.get_table_stats()
            },
            "timestamp": datetime.utcnow().isoformat()
        }

# ================================
# Initialize Global Monitoring
# ================================

# Global instances (will be initialized by the main application)
metrics_collector: Optional[MetricsCollector] = None
apm_monitor: Optional[APMMonitor] = None
database_monitor: Optional[DatabaseMonitor] = None
health_checker: Optional[HealthChecker] = None
monitoring_dashboard: Optional[MonitoringDashboard] = None

def initialize_monitoring(database_url: str, redis_client: Optional[redis.Redis] = None):
    """Initialize all monitoring components"""
    global metrics_collector, apm_monitor, database_monitor, health_checker, monitoring_dashboard
    
    metrics_collector = MetricsCollector()
    apm_monitor = APMMonitor(redis_client)
    database_monitor = DatabaseMonitor(database_url)
    health_checker = HealthChecker(database_url, redis_client)
    monitoring_dashboard = MonitoringDashboard(
        metrics_collector, apm_monitor, database_monitor, health_checker
    )
    
    logging.info("🔍 Monitoring system initialized")

# ================================
# Middleware Integration
# ================================

class MonitoringMiddleware:
    """FastAPI middleware for monitoring requests"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        method = scope["method"]
        path = scope["path"]
        
        # Track system resources at request start
        process = psutil.Process()
        start_memory = process.memory_info().rss
        start_cpu_time = process.cpu_times()
        
        status_code = 200
        error_message = None
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            error_message = str(e)
            status_code = 500
            raise
        finally:
            # Calculate metrics
            duration = time.time() - start_time
            end_memory = process.memory_info().rss
            memory_delta = end_memory - start_memory
            
            # Record metrics
            if metrics_collector:
                metrics_collector.record_request(method, path, status_code, duration)
            
            if apm_monitor:
                metric = PerformanceMetric(
                    timestamp=datetime.utcnow(),
                    endpoint=path,
                    method=method,
                    duration=duration,
                    status_code=status_code,
                    error_message=error_message,
                    memory_usage=end_memory,
                    cpu_usage=psutil.cpu_percent()
                )
                apm_monitor.record_request(metric) 