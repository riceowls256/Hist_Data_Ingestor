# Production Deployment Guide

This guide provides comprehensive instructions for deploying the Historical Data Ingestor in production environments.

## Quick Start for Production

### Prerequisites

- Docker and Docker Compose
- 16GB+ RAM (32GB recommended for large datasets)  
- 500GB+ SSD storage (1TB+ recommended)
- Linux/macOS production environment
- Valid Databento API subscription

### Minimal Production Deployment

```bash
# 1. Clone and setup
git clone <repository_url>
cd hist_data_ingestor

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Deploy
docker-compose up --build -d

# 4. Verify
python main.py status
```

## Detailed Production Setup

### 1. System Requirements

#### Hardware Requirements

**Minimum Configuration**:
- CPU: 4 cores
- RAM: 16GB
- Storage: 500GB SSD
- Network: 100Mbps dedicated bandwidth

**Recommended Configuration**:
- CPU: 8+ cores
- RAM: 32GB+
- Storage: 1TB+ NVMe SSD
- Network: 1Gbps dedicated bandwidth

**Large-Scale Configuration**:
- CPU: 16+ cores
- RAM: 64GB+
- Storage: 2TB+ NVMe SSD (RAID 10)
- Network: 10Gbps dedicated bandwidth

#### Software Requirements

- **Operating System**: Ubuntu 20.04+ LTS, CentOS 8+, or macOS 11+
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Python**: Version 3.11+ (for direct CLI usage)
- **Network**: Outbound HTTPS access to Databento APIs

### 2. Environment Configuration

#### Production Environment Variables

Create `/etc/hist-data-ingestor/.env`:

```bash
# === CORE CONFIGURATION ===
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# === DATABENTO API ===
DATABENTO_API_KEY=your_production_api_key_here
DATABENTO_TIMEOUT=300
DATABENTO_RETRY_ATTEMPTS=3

# === TIMESCALE DATABASE ===
TIMESCALEDB_HOST=timescaledb
TIMESCALEDB_PORT=5432
TIMESCALEDB_DBNAME=hist_data_prod
TIMESCALEDB_USER=postgres
TIMESCALEDB_PASSWORD=your_secure_password_here

# === PERFORMANCE TUNING ===
BATCH_SIZE=1000
MAX_WORKERS=4
MEMORY_LIMIT=8GB
DISK_CACHE_SIZE=10GB

# === MONITORING ===
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30

# === SECURITY ===
ALLOWED_HOSTS=your-domain.com,localhost
API_RATE_LIMIT=1000
MAX_REQUEST_SIZE=100MB
```

#### Docker Compose Production Configuration

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: hist-data-ingestor-prod
    restart: unless-stopped
    environment:
      - ENV_FILE=/app/.env
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./dlq:/app/dlq
      - /etc/hist-data-ingestor/.env:/app/.env
    depends_on:
      - timescaledb
    networks:
      - hist-data-network
    healthcheck:
      test: ["CMD", "python", "main.py", "status"]
      interval: 30s
      timeout: 10s
      retries: 3

  timescaledb:
    image: timescale/timescaledb:latest-pg15
    container_name: hist-data-timescaledb-prod
    restart: unless-stopped
    environment:
      POSTGRES_DB: hist_data_prod
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${TIMESCALEDB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
    volumes:
      - timescaledb_data:/var/lib/postgresql/data
      - ./backup:/backup
    ports:
      - "5432:5432"
    networks:
      - hist-data-network
    command: ["postgres", "-c", "shared_preload_libraries=timescaledb", "-c", "max_connections=200", "-c", "shared_buffers=1GB", "-c", "effective_cache_size=3GB"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d hist_data_prod"]
      interval: 30s
      timeout: 10s
      retries: 5

  nginx:
    image: nginx:alpine
    container_name: hist-data-nginx-prod
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - hist-data-network

volumes:
  timescaledb_data:
    driver: local

networks:
  hist-data-network:
    driver: bridge
```

### 3. Security Configuration

#### Database Security

1. **Strong Password Policy**:
   ```bash
   # Generate secure password
   openssl rand -base64 32
   ```

2. **Network Security**:
   ```sql
   -- Create read-only user for reporting
   CREATE USER hist_reader WITH PASSWORD 'secure_reader_password';
   GRANT CONNECT ON DATABASE hist_data_prod TO hist_reader;
   GRANT USAGE ON SCHEMA public TO hist_reader;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO hist_reader;
   ```

3. **SSL/TLS Configuration**:
   ```bash
   # Enable SSL in PostgreSQL
   sudo openssl req -new -x509 -days 365 -nodes -text -out server.crt -keyout server.key -subj "/CN=hist-data-db"
   sudo chown postgres:postgres server.crt server.key
   sudo chmod 400 server.key
   ```

#### API Key Management

```bash
# Store API key securely
sudo mkdir -p /etc/hist-data-ingestor/secrets
echo "your_api_key_here" | sudo tee /etc/hist-data-ingestor/secrets/databento_api_key
sudo chmod 600 /etc/hist-data-ingestor/secrets/databento_api_key
sudo chown root:root /etc/hist-data-ingestor/secrets/databento_api_key
```

#### Firewall Configuration

```bash
# Ubuntu/Debian UFW
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 5432/tcp  # PostgreSQL (if external access needed)
sudo ufw enable

# CentOS/RHEL firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload
```

### 4. Performance Optimization

#### Database Tuning

TimescaleDB Production Configuration (`postgresql.conf`):

```ini
# === MEMORY SETTINGS ===
shared_buffers = 8GB                    # 25% of total RAM
effective_cache_size = 24GB             # 75% of total RAM
work_mem = 256MB                        # For complex queries
maintenance_work_mem = 2GB              # For maintenance operations

# === CHECKPOINT SETTINGS ===
checkpoint_completion_target = 0.9
checkpoint_timeout = 15min
max_wal_size = 4GB
min_wal_size = 1GB

# === CONNECTION SETTINGS ===
max_connections = 200
shared_preload_libraries = 'timescaledb'

# === LOGGING ===
log_statement = 'mod'                   # Log modifications
log_duration = on
log_min_duration_statement = 5000       # Log slow queries (5s+)

# === TIMESCALEDB SETTINGS ===
timescaledb.max_background_workers = 8
timescaledb.telemetry_level = off
```

#### Application Performance Tuning

Environment Variables for Production:

```bash
# === PROCESSING OPTIMIZATION ===
BATCH_SIZE=2000                         # Larger batches for throughput
MAX_WORKERS=8                           # Increase for multi-core systems
CHUNK_SIZE=50000                        # Larger chunks for bulk operations

# === MEMORY MANAGEMENT ===
MEMORY_LIMIT=16GB                       # Set appropriate memory limit
PANDAS_MEMORY_LIMIT=8GB                 # Limit pandas memory usage
CACHE_SIZE=4GB                          # Enable result caching

# === NETWORK OPTIMIZATION ===
CONNECTION_POOL_SIZE=20                 # Database connection pool
HTTP_TIMEOUT=300                        # 5-minute HTTP timeout
RETRY_BACKOFF_MAX=60                    # Max retry delay
```

#### Monitoring Configuration

```bash
# === METRICS AND MONITORING ===
ENABLE_PROMETHEUS_METRICS=true
PROMETHEUS_PORT=9090
GRAFANA_ENABLED=true
GRAFANA_PORT=3000

# === ALERTING ===
ALERT_ON_FAILURES=true
ALERT_EMAIL=admin@yourcompany.com
SLACK_WEBHOOK_URL=your_slack_webhook_url

# === LOGGING ===
LOG_FORMAT=json
LOG_LEVEL=INFO
LOG_ROTATION=daily
LOG_RETENTION_DAYS=30
```

### 5. Deployment Process

#### Automated Deployment Script

Create `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Starting production deployment..."

# 1. Environment validation
echo "📋 Validating environment..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# 2. Backup existing data
echo "💾 Creating backup..."
docker-compose exec timescaledb pg_dump -U postgres hist_data_prod > backup/backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Pull latest code
echo "📦 Updating codebase..."
git pull origin main

# 4. Build and deploy
echo "🔨 Building and deploying..."
docker-compose -f docker-compose.prod.yml up --build -d

# 5. Wait for services
echo "⏳ Waiting for services to start..."
sleep 30

# 6. Run health checks
echo "🔍 Running health checks..."
python main.py status

# 7. Run smoke tests
echo "🧪 Running smoke tests..."
python main.py ingest --api databento --dataset GLBX.MDP3 --schema definitions --symbols ES.FUT --stype-in parent --start-date 2024-04-15 --end-date 2024-04-16 --force

echo "✅ Deployment completed successfully!"
```

#### Rolling Update Process

```bash
# 1. Deploy new version alongside old
docker-compose -f docker-compose.prod.yml up --build -d --scale app=2

# 2. Health check new instance
curl -f http://localhost:8080/health || exit 1

# 3. Stop old instance
docker stop hist-data-ingestor-prod-old

# 4. Remove old container
docker rm hist-data-ingestor-prod-old
```

### 6. Monitoring and Alerting

#### Health Check Endpoints

```python
# Add to main.py or create health_check.py
@app.route('/health')
def health_check():
    try:
        # Database connectivity
        with get_db_connection() as conn:
            cursor.execute("SELECT 1")
        
        # API connectivity
        test_databento_connection()
        
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500

@app.route('/metrics')
def metrics():
    return {
        "records_processed": get_total_records(),
        "uptime": get_uptime(),
        "database_size": get_database_size(),
        "active_connections": get_active_connections()
    }
```

#### Monitoring with Docker

```yaml
# Add to docker-compose.prod.yml
  prometheus:
    image: prom/prometheus:latest
    container_name: hist-data-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:latest
    container_name: hist-data-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
```

### 7. Backup and Recovery

#### Automated Backup Script

Create `backup.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/backup/$(date +%Y/%m/%d)"
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
echo "🗄️ Backing up database..."
docker-compose exec -T timescaledb pg_dump -U postgres -Fc hist_data_prod > "$BACKUP_DIR/database_$(date +%H%M%S).dump"

# Configuration backup
echo "⚙️ Backing up configuration..."
tar -czf "$BACKUP_DIR/config_$(date +%H%M%S).tar.gz" .env docker-compose.prod.yml nginx/

# Data directory backup
echo "📁 Backing up data directory..."
tar -czf "$BACKUP_DIR/data_$(date +%H%M%S).tar.gz" data/ logs/ dlq/

# Cleanup old backups
echo "🧹 Cleaning up old backups..."
find /backup -type f -mtime +$RETENTION_DAYS -delete

echo "✅ Backup completed: $BACKUP_DIR"
```

#### Recovery Procedures

```bash
# 1. Stop services
docker-compose -f docker-compose.prod.yml down

# 2. Restore database
docker-compose up -d timescaledb
sleep 30
cat backup/database_backup.dump | docker-compose exec -T timescaledb pg_restore -U postgres -d hist_data_prod

# 3. Restore configuration
tar -xzf backup/config_backup.tar.gz

# 4. Restart services
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify recovery
python main.py status
```

### 8. Performance Benchmarks

#### Expected Performance Metrics

**Definitions Schema (Production Ready)**:
- Processing Speed: 3,000+ records/second
- API Response Time: < 2 seconds for parent symbols
- Memory Usage: < 2GB for typical workloads
- Storage Efficiency: ~1KB per definition record

**OHLCV Data**:
- Processing Speed: 1,000+ records/second
- Batch Size: 1,000-5,000 records optimal
- Memory Usage: < 4GB for monthly data
- Storage Efficiency: ~100 bytes per OHLCV record

**High-Frequency Data (Trades/TBBO)**:
- Processing Speed: 500+ records/second
- Recommended Range: 1-3 days maximum
- Memory Usage: Monitor closely, can exceed 8GB
- Storage Efficiency: ~50 bytes per trade record

#### Performance Testing

```bash
# Benchmark definitions schema
time python main.py ingest --api databento --dataset GLBX.MDP3 --schema definitions --symbols ES.FUT,CL.FUT --stype-in parent --start-date 2024-04-15 --end-date 2024-05-05

# Benchmark OHLCV processing
time python main.py ingest --api databento --dataset GLBX.MDP3 --schema ohlcv-1d --symbols ES.c.0,CL.c.0 --start-date 2024-04-01 --end-date 2024-04-30

# Database performance test
docker-compose exec timescaledb psql -U postgres -d hist_data_prod -c "
SELECT 
  count(*) as total_records,
  pg_size_pretty(pg_total_relation_size('definitions_data')) as table_size,
  pg_size_pretty(pg_database_size('hist_data_prod')) as db_size
FROM definitions_data;"
```

### 9. Troubleshooting Production Issues

#### Common Production Issues

1. **High Memory Usage**:
   ```bash
   # Monitor memory usage
   docker stats
   
   # Adjust batch sizes
   export BATCH_SIZE=500
   export PANDAS_MEMORY_LIMIT=4GB
   ```

2. **Database Connection Issues**:
   ```bash
   # Check connection pool
   docker-compose exec timescaledb psql -U postgres -d hist_data_prod -c "
   SELECT state, count(*) 
   FROM pg_stat_activity 
   WHERE datname='hist_data_prod' 
   GROUP BY state;"
   ```

3. **API Rate Limiting**:
   ```bash
   # Implement exponential backoff
   export RETRY_BACKOFF_MULTIPLIER=2.0
   export MAX_RETRY_DELAY=300
   ```

#### Emergency Procedures

```bash
# Emergency stop
docker-compose -f docker-compose.prod.yml down

# Quick restart
docker-compose -f docker-compose.prod.yml up -d

# Database emergency recovery
docker-compose exec timescaledb pg_ctl restart -D /var/lib/postgresql/data

# Clear cache and restart
docker system prune -f
docker-compose -f docker-compose.prod.yml up --build -d
```

### 10. Maintenance Procedures

#### Daily Maintenance

```bash
# Automated via cron
0 2 * * * /opt/hist-data-ingestor/backup.sh
0 3 * * * /opt/hist-data-ingestor/cleanup.sh
0 4 * * * docker system prune -f
```

#### Weekly Maintenance

```bash
# Database maintenance
docker-compose exec timescaledb psql -U postgres -d hist_data_prod -c "
VACUUM ANALYZE;
REINDEX DATABASE hist_data_prod;
"

# Update dependencies
docker-compose pull
docker-compose -f docker-compose.prod.yml up --build -d
```

#### Monthly Maintenance

```bash
# Database statistics update
docker-compose exec timescaledb psql -U postgres -d hist_data_prod -c "
ANALYZE;
SELECT compress_chunk(chunk_name) 
FROM timescaledb_information.chunks 
WHERE table_name IN ('ohlcv_data', 'definitions_data')
AND chunk_name NOT IN (SELECT chunk_name FROM timescaledb_information.compressed_chunks);
"

# Security updates
apt update && apt upgrade -y
docker system prune -af
```

---

**Production Readiness**: This deployment guide supports the fully production-ready definitions schema with excellent performance and comprehensive monitoring capabilities.

**Last Updated**: 2025-06-19  
**Version**: Production Release  
**Support**: See TROUBLESHOOTING.md for detailed issue resolution