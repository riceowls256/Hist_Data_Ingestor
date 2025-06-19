 # Operational Procedures Guide
**Hist Data Ingestor - Production-Ready Operations Manual**

---

## Overview

This guide provides comprehensive operational procedures for the Hist Data Ingestor MVP, covering monitoring, troubleshooting, data quality management, and database administration. These procedures enable primary users to operate the system independently with confidence.

**Operational Objectives:**
- Provide systematic monitoring and health checking procedures
- Enable independent troubleshooting and issue resolution
- Establish data quality and integrity validation workflows
- Document database administration and optimization procedures
- Create operational excellence through structured processes

---

## System Monitoring and Health Checking

### **Real-Time System Status Monitoring**

#### **Container Health Monitoring**
```bash
# Verify all containers are running
docker-compose ps

# Expected output:
# Name                              Command              State           Ports
# hist-data-ingestor_app_1         python main.py      Up              
# hist-data-ingestor_timescaledb_1 docker-entrypoint  Up              5432/tcp

# Monitor resource usage in real-time
docker stats

# Check container logs for errors
docker-compose logs --tail=50 app
docker-compose logs --tail=50 timescaledb
```

#### **Application Health Checks**
```bash
# Built-in health check via CLI
python main.py status

# Comprehensive system health assessment
python main.py status --comprehensive

# Database connectivity validation
python main.py status --check-db

# API connectivity validation
python main.py status --check-api
```

**Expected Healthy Status Output:**
```
🟢 System Status: Healthy
📊 Database: Connected (TimescaleDB 2.14.2)
🔗 API: Databento connection valid  
💾 Storage: 15.2GB available
📝 Logs: /app/logs/ (3 files, 2.4MB)
🗂️  Quarantine: /app/dlq/ (empty)

Performance Metrics:
  📈 Average Query Time: 2.3 seconds
  🔄 Last Ingestion: 2024-01-15 14:30:00 (Success)
  ✅ Data Integrity: 99.8% validation success rate
```

### **Database Health and Performance Monitoring**

#### **TimescaleDB Status Checks**
```sql
-- Connect to database for health checks
docker-compose exec timescaledb psql -U postgres -d hist_data_ingestor

-- Check database size and usage
SELECT 
  pg_size_pretty(pg_database_size('hist_data_ingestor')) as database_size,
  pg_size_pretty(pg_total_relation_size('ohlcv_data')) as ohlcv_size,
  pg_size_pretty(pg_total_relation_size('trades_data')) as trades_size,
  pg_size_pretty(pg_total_relation_size('tbbo_data')) as tbbo_size;

-- Verify hypertable health
SELECT 
  hypertable_name,
  hypertable_size,
  number_dimensions,
  num_chunks
FROM timescaledb_information.hypertables;

-- Check recent data ingestion activity
SELECT 
  schemaname,
  tablename,
  n_tup_ins as inserts_today,
  n_tup_upd as updates_today,
  n_tup_del as deletes_today,
  last_autovacuum,
  last_autoanalyze
FROM pg_stat_user_tables 
WHERE schemaname = 'public'
ORDER BY n_tup_ins DESC;
```

#### **Performance Metrics Analysis**
```sql
-- Query performance statistics
SELECT 
  query,
  calls,
  total_time,
  mean_time,
  min_time,
  max_time
FROM pg_stat_statements 
WHERE query LIKE '%FROM ohlcv_data%' 
OR query LIKE '%FROM trades_data%'
ORDER BY total_time DESC
LIMIT 10;

-- Index usage analysis
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_tup_read DESC;
```

---

## Log Analysis and Monitoring

### **Structured Log Analysis Framework**

#### **Log File Locations and Structure**
```bash
# Application logs
/app/logs/hist_data_ingestor.log           # Main application log
/app/logs/pipeline_orchestrator.log       # Pipeline execution logs
/app/logs/databento_adapter.log           # API interaction logs
/app/logs/query_builder.log               # Query performance logs

# Log file analysis
tail -f /app/logs/hist_data_ingestor.log | jq '.'
grep -i error /app/logs/*.log | tail -20
grep -i warning /app/logs/*.log | tail -20
```

#### **Structured Log Analysis Queries**
```bash
# Recent error analysis
jq 'select(.level=="ERROR")' /app/logs/hist_data_ingestor.log | tail -10

# Performance monitoring
jq 'select(.component=="PipelineOrchestrator" and .context.execution_time)' \
   /app/logs/hist_data_ingestor.log | tail -5

# API interaction monitoring
jq 'select(.component=="DatabentoAdapter")' \
   /app/logs/databento_adapter.log | tail -10

# Data validation monitoring
jq 'select(.message | contains("validation"))' \
   /app/logs/hist_data_ingestor.log | tail -10
```

### **Log-Based Performance Monitoring**

#### **Ingestion Performance Analysis**
```bash
# Extract ingestion performance metrics
grep "Pipeline completed" /app/logs/pipeline_orchestrator.log | \
jq '.context | {records_processed, execution_time, processing_rate, memory_peak}'

# API rate limit monitoring
grep "rate_limit" /app/logs/databento_adapter.log | \
jq '.context | {remaining_calls, reset_time, throttle_applied}'

# Memory usage trend analysis
grep "memory_usage" /app/logs/*.log | \
jq '.context.memory_usage' | sort -n | tail -10
```

#### **Query Performance Monitoring**
```bash
# Query execution time analysis
grep "Query executed" /app/logs/query_builder.log | \
jq '.context | {symbol, date_range, execution_time, record_count}'

# Slow query identification (>5 seconds)
jq 'select(.context.execution_time and (.context.execution_time | tonumber) > 5)' \
   /app/logs/query_builder.log

# Query pattern analysis
grep "Query pattern" /app/logs/query_builder.log | \
jq '.context | {schema, symbols_count, date_range_days}' | \
sort | uniq -c | sort -nr
```

---

## Data Quality and Quarantine Management

### **Quarantine Directory Analysis**

#### **Quarantine File Structure**
```bash
# Quarantine directory structure
ls -la dlq/
# Expected structure:
# dlq/
# ├── validation_failures/
# │   ├── 20240115_ohlcv_validation_failures.json
# │   └── 20240115_trades_validation_failures.json
# ├── api_errors/
# │   └── 20240115_databento_api_errors.json
# └── transformation_errors/
#     └── 20240115_transformation_errors.json

# Analyze quarantine file sizes and counts
find dlq/ -name "*.json" -exec wc -l {} \; | \
awk '{total += $1} END {print "Total quarantined records:", total}'
```

#### **Validation Failure Analysis**
```bash
# Recent validation failures
cat dlq/validation_failures/$(date +%Y%m%d)_*_validation_failures.json | \
jq '.validation_failures[] | {schema, symbol, error_type, error_message}' | \
head -10

# Validation failure summary by type
cat dlq/validation_failures/*.json | \
jq -r '.validation_failures[] | .error_type' | \
sort | uniq -c | sort -nr

# Business logic violation analysis
cat dlq/validation_failures/*.json | \
jq '.validation_failures[] | select(.error_type == "BusinessLogicValidation")' | \
jq '.error_message' | sort | uniq -c
```

### **Data Integrity Validation Procedures**

#### **Cross-Schema Data Consistency Checks**
```sql
-- Verify symbol consistency across schemas
SELECT 
  o.symbol,
  COUNT(DISTINCT o.instrument_id) as ohlcv_instruments,
  COUNT(DISTINCT t.instrument_id) as trades_instruments,
  COUNT(DISTINCT b.instrument_id) as tbbo_instruments
FROM ohlcv_data o
LEFT JOIN trades_data t ON o.symbol = t.symbol
LEFT JOIN tbbo_data b ON o.symbol = b.symbol
WHERE o.ts_event >= '2024-01-01'
GROUP BY o.symbol
HAVING COUNT(DISTINCT o.instrument_id) > 1
   OR COUNT(DISTINCT t.instrument_id) > 1
   OR COUNT(DISTINCT b.instrument_id) > 1;

-- Date range consistency validation
SELECT 
  'ohlcv_data' as table_name,
  MIN(ts_event) as earliest_date,
  MAX(ts_event) as latest_date,
  COUNT(*) as record_count
FROM ohlcv_data
UNION ALL
SELECT 
  'trades_data' as table_name,
  MIN(ts_event) as earliest_date,
  MAX(ts_event) as latest_date,
  COUNT(*) as record_count
FROM trades_data;
```

#### **Business Logic Compliance Validation**
```sql
-- OHLCV business logic validation
SELECT 
  symbol,
  ts_event,
  open_price,
  high_price,
  low_price,
  close_price,
  CASE 
    WHEN high_price < low_price THEN 'HIGH_LESS_THAN_LOW'
    WHEN high_price < open_price THEN 'HIGH_LESS_THAN_OPEN'
    WHEN high_price < close_price THEN 'HIGH_LESS_THAN_CLOSE'
    WHEN low_price > open_price THEN 'LOW_GREATER_THAN_OPEN'
    WHEN low_price > close_price THEN 'LOW_GREATER_THAN_CLOSE'
    ELSE 'VALID'
  END as validation_status
FROM ohlcv_data
WHERE ts_event >= CURRENT_DATE - INTERVAL '7 days'
  AND (high_price < low_price 
       OR high_price < open_price 
       OR high_price < close_price
       OR low_price > open_price 
       OR low_price > close_price)
ORDER BY ts_event DESC;

-- Trade data validation
SELECT 
  symbol,
  COUNT(*) as total_trades,
  SUM(CASE WHEN price <= 0 THEN 1 ELSE 0 END) as invalid_prices,
  SUM(CASE WHEN size <= 0 THEN 1 ELSE 0 END) as invalid_sizes,
  SUM(CASE WHEN side NOT IN ('B', 'S') THEN 1 ELSE 0 END) as invalid_sides
FROM trades_data
WHERE ts_event >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY symbol
HAVING SUM(CASE WHEN price <= 0 THEN 1 ELSE 0 END) > 0
    OR SUM(CASE WHEN size <= 0 THEN 1 ELSE 0 END) > 0
    OR SUM(CASE WHEN side NOT IN ('B', 'S') THEN 1 ELSE 0 END) > 0;
```

---

## Troubleshooting Workflows

### **Common Issue Resolution Procedures**

#### **Container and Service Issues**

**Problem**: Container fails to start
```bash
# Diagnosis steps
docker-compose ps
docker-compose logs app
docker-compose logs timescaledb

# Common resolution steps
docker-compose down
docker-compose up -d
docker-compose ps

# If persistent issues
docker system prune -f
docker-compose build --no-cache
docker-compose up -d
```

**Problem**: Database connection failures
```bash
# Check database container status
docker-compose exec timescaledb pg_isready -U postgres

# Test connectivity from application container
docker-compose exec app python -c "
from src.core.config_manager import ConfigManager
from src.storage.timescale_loader import TimescaleLoader
with TimescaleLoader() as loader:
    print('Database connection successful')
"

# Reset database if needed
docker-compose down -v
docker-compose up -d
```

#### **Performance and Resource Issues**

**Problem**: High memory usage
```bash
# Monitor resource usage
docker stats

# Check application memory usage
docker-compose exec app python -c "
import psutil
process = psutil.Process()
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"

# Adjust container resources in docker-compose.yml
# Add memory limits and CPU constraints
```

**Problem**: Slow query performance
```sql
-- Identify slow queries
SELECT 
  query,
  calls,
  total_time,
  mean_time,
  rows
FROM pg_stat_statements 
WHERE mean_time > 5000  -- Queries taking >5 seconds
ORDER BY mean_time DESC;

-- Check for missing indexes
SELECT 
  schemaname,
  tablename,
  attname,
  n_distinct,
  correlation
FROM pg_stats 
WHERE schemaname = 'public' 
  AND n_distinct > 100
ORDER BY n_distinct DESC;

-- Analyze query plans for optimization
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM ohlcv_data 
WHERE instrument_id = 4916 
  AND ts_event >= '2024-01-01'::date 
  AND ts_event < '2024-02-01'::date;
```

#### **Data Quality Issues**

**Problem**: High validation failure rate
```bash
# Analyze validation failures
python main.py quarantine analyze --days 7 --export-summary

# Check recent quarantine activity
ls -la dlq/validation_failures/ | tail -5

# Review validation rules configuration
cat configs/api_specific/databento_config.yaml | grep -A 10 validation_rules

# Test individual schema validation
python main.py validate --schema ohlcv-1d --sample-size 1000
```

**Problem**: Missing or inconsistent data
```sql
-- Check for data gaps
WITH date_series AS (
  SELECT generate_series(
    '2024-01-01'::date,
    CURRENT_DATE,
    '1 day'::interval
  )::date as expected_date
)
SELECT 
  ds.expected_date,
  COUNT(o.ts_event) as records_found
FROM date_series ds
LEFT JOIN ohlcv_data o ON ds.expected_date = o.ts_event::date
GROUP BY ds.expected_date
HAVING COUNT(o.ts_event) = 0
ORDER BY ds.expected_date;

-- Cross-reference with ingestion logs
grep "Pipeline completed" /app/logs/pipeline_orchestrator.log | \
jq 'select(.context.records_processed == 0)'
```

### **API and External Service Issues**

#### **Databento API Connection Problems**
```bash
# Test API connectivity directly
python main.py config test-api databento --verbose

# Check API rate limits
grep "rate_limit" /app/logs/databento_adapter.log | tail -5

# Validate API credentials
python -c "
import os
print('API Key length:', len(os.getenv('DATABENTO_API_KEY', '')))
print('Gateway setting:', os.getenv('DATABENTO_GATEWAY', ''))
"
```

#### **Network and Connectivity Issues**
```bash
# Test external connectivity
docker-compose exec app ping -c 3 hist.databento.com
docker-compose exec app nslookup hist.databento.com

# Check container networking
docker network ls
docker network inspect hist-data-ingestor_default

# Verify port connectivity
docker-compose exec app nc -zv timescaledb 5432
```

---

## Database Administration and Optimization

### **TimescaleDB Structure Exploration**

#### **Hypertable Analysis and Management**
```sql
-- Comprehensive hypertable information
SELECT 
  h.hypertable_name,
  h.hypertable_size,
  h.number_dimensions,
  h.num_chunks,
  c.total_chunks,
  c.data_nodes
FROM timescaledb_information.hypertables h
LEFT JOIN timescaledb_information.chunks c ON h.hypertable_name = c.hypertable_name;

-- Chunk distribution and sizing
SELECT 
  hypertable_name,
  chunk_name,
  range_start,
  range_end,
  pg_size_pretty(total_bytes) as chunk_size,
  row_count
FROM timescaledb_information.chunks 
ORDER BY hypertable_name, range_start DESC;

-- Compression status and savings
SELECT 
  hypertable_name,
  SUM(before_compression_total_bytes) as before_compression,
  SUM(after_compression_total_bytes) as after_compression,
  ROUND(100 * (1 - SUM(after_compression_total_bytes::numeric) / 
                    SUM(before_compression_total_bytes::numeric)), 2) as compression_ratio
FROM timescaledb_information.compressed_chunk_stats
GROUP BY hypertable_name;
```

#### **Index Strategy and Performance**
```sql
-- Index usage statistics
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_tup_read,
  idx_tup_fetch,
  idx_tup_read::float / GREATEST(pg_stat_get_tuples_inserted(c.oid) + 
                                 pg_stat_get_tuples_updated(c.oid), 1) as selectivity
FROM pg_stat_user_indexes psi
JOIN pg_class c ON c.oid = psi.indexrelid
WHERE schemaname = 'public'
ORDER BY idx_tup_read DESC;

-- Identify unused indexes
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
  AND idx_tup_read = 0
  AND idx_tup_fetch = 0;

-- Table and index size analysis
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - 
                 pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### **Database Maintenance Procedures**

#### **Regular Maintenance Tasks**
```sql
-- Vacuum and analyze for optimal performance
VACUUM ANALYZE ohlcv_data;
VACUUM ANALYZE trades_data;
VACUUM ANALYZE tbbo_data;
VACUUM ANALYZE statistics_data;
VACUUM ANALYZE definitions_data;

-- Update table statistics
ANALYZE ohlcv_data;
ANALYZE trades_data;
ANALYZE tbbo_data;

-- Reindex if needed (run during low usage periods)
REINDEX TABLE ohlcv_data;
REINDEX TABLE trades_data;
```

#### **Backup and Recovery Procedures**
```bash
# Database backup
docker-compose exec timescaledb pg_dump -U postgres -d hist_data_ingestor > \
  backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker-compose exec timescaledb pg_dump -U postgres -d hist_data_ingestor | \
  gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Table-specific backup
docker-compose exec timescaledb pg_dump -U postgres -d hist_data_ingestor \
  -t ohlcv_data > ohlcv_backup_$(date +%Y%m%d).sql

# Restore from backup
docker-compose exec -T timescaledb psql -U postgres -d hist_data_ingestor < backup.sql
```

---

## Operational Alerting and Monitoring

### **Automated Health Check Scripts**

#### **System Health Monitor**
```bash
#!/bin/bash
# health_check.sh - Automated system health monitoring

echo "=== Hist Data Ingestor Health Check ==="
echo "Timestamp: $(date)"

# Container status
echo "Container Status:"
docker-compose ps | grep -E "(Up|Exited|Restarting)"

# Disk space check
echo "Disk Space:"
df -h | grep -E "(/$|/var/lib/docker)"

# Database connectivity
echo "Database Connectivity:"
docker-compose exec timescaledb pg_isready -U postgres

# Recent errors
echo "Recent Errors (last 1 hour):"
find /app/logs -name "*.log" -mmin -60 -exec grep -l ERROR {} \; | wc -l

# Memory usage
echo "Memory Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"

echo "=== Health Check Complete ==="
```

#### **Data Quality Monitor**
```bash
#!/bin/bash
# data_quality_check.sh - Automated data quality monitoring

echo "=== Data Quality Check ==="

# Recent quarantine activity
QUARANTINE_COUNT=$(find dlq/ -name "*.json" -mtime -1 | wc -l)
echo "Quarantine files (last 24h): $QUARANTINE_COUNT"

# Validation failure rate
if [ -f "dlq/validation_failures/$(date +%Y%m%d)_validation_failures.json" ]; then
  FAILURE_COUNT=$(jq '.validation_failures | length' \
    dlq/validation_failures/$(date +%Y%m%d)_validation_failures.json)
  echo "Validation failures today: $FAILURE_COUNT"
fi

# Database record counts
echo "Record counts by schema:"
docker-compose exec timescaledb psql -U postgres -d hist_data_ingestor -c "
SELECT 
  'ohlcv_data' as schema, COUNT(*) as records 
FROM ohlcv_data WHERE ts_event >= CURRENT_DATE
UNION ALL
SELECT 
  'trades_data' as schema, COUNT(*) as records 
FROM trades_data WHERE ts_event >= CURRENT_DATE;"

echo "=== Data Quality Check Complete ==="
```

### **Performance Monitoring Dashboard**

#### **Real-Time Performance Metrics**
```bash
#!/bin/bash
# performance_dashboard.sh - Real-time performance monitoring

while true; do
  clear
  echo "=== Hist Data Ingestor Performance Dashboard ==="
  echo "Last updated: $(date)"
  echo ""
  
  # System resources
  echo "SYSTEM RESOURCES:"
  docker stats --no-stream --format \
    "{{.Name}}: CPU {{.CPUPerc}} | Memory {{.MemUsage}} ({{.MemPerc}})"
  echo ""
  
  # Database performance
  echo "DATABASE PERFORMANCE:"
  docker-compose exec timescaledb psql -U postgres -d hist_data_ingestor -t -c "
  SELECT 
    'Active connections: ' || count(*) 
  FROM pg_stat_activity 
  WHERE state = 'active';"
  
  # Recent ingestion activity
  echo "RECENT ACTIVITY:"
  tail -5 /app/logs/pipeline_orchestrator.log | \
    jq -r 'select(.level=="INFO") | "\(.timestamp): \(.message)"'
  
  sleep 30
done
```

---

## Operational Handoff Checklist

### **Daily Operational Tasks**
- [ ] **System Health Check**: Run `python main.py status --comprehensive`
- [ ] **Container Status**: Verify all containers running with `docker-compose ps`
- [ ] **Log Review**: Check for errors in past 24 hours
- [ ] **Quarantine Analysis**: Review any new quarantine files
- [ ] **Disk Space**: Verify adequate storage space available
- [ ] **Database Performance**: Check slow query log for performance issues

### **Weekly Operational Tasks**
- [ ] **Database Maintenance**: Run `VACUUM ANALYZE` on all tables
- [ ] **Log Rotation**: Archive old log files to prevent disk space issues
- [ ] **Performance Review**: Analyze weekly performance trends
- [ ] **Backup Verification**: Ensure database backups are current and valid
- [ ] **API Quota Review**: Monitor Databento API usage and limits
- [ ] **Documentation Updates**: Update operational notes and procedures

### **Monthly Operational Tasks**
- [ ] **Comprehensive Health Review**: Full system performance analysis
- [ ] **Index Optimization**: Review and optimize database indexes
- [ ] **Security Updates**: Update system dependencies and containers
- [ ] **Capacity Planning**: Review storage and compute resource usage
- [ ] **Disaster Recovery Test**: Validate backup and recovery procedures
- [ ] **Operational Procedure Review**: Update documentation and workflows

---

**Document Version**: 1.0  
**Created**: Story 3.5 Implementation  
**Target Audience**: Operations Team, Primary User  
**Usage**: Production Operations and MVP Demonstration