# Historical Data Ingestor - Troubleshooting Guide

This comprehensive guide helps diagnose and resolve common issues with the Historical Data Ingestor system.

## Quick Diagnostics

### System Health Check

Run these commands to quickly assess system status:

```bash
# Check application status
python main.py status

# Check Docker services
docker-compose ps

# Check database connectivity
docker-compose exec timescaledb psql -U postgres -d hist_data -c "SELECT 1;"

# Check recent logs
docker-compose logs -f --tail=50
```

### Environment Validation

```bash
# Verify environment variables
echo $DATABENTO_API_KEY
echo $TIMESCALEDB_HOST
echo $TIMESCALEDB_PASSWORD

# Test API connectivity
python -c "import databento; print('Databento library available')"
```

## Common Error Categories

### 1. API and Authentication Errors

#### Error: "API key not found"
**Symptoms**: Authentication failures, 401 errors
**Solutions**:
1. Check `.env` file contains `DATABENTO_API_KEY=your_key_here`
2. Verify API key is valid: [Databento Dashboard](https://databento.com)
3. Ensure no extra spaces or quotes in environment variable
4. Restart application after changing environment variables

#### Error: "Dataset not found" or "403 Forbidden"
**Symptoms**: Access denied to specific datasets
**Solutions**:
1. Verify your Databento subscription includes the requested dataset
2. Check dataset name spelling (e.g., `GLBX.MDP3`, `XNAS.ITCH`)
3. Confirm date range is within your subscription coverage
4. Contact Databento support for subscription verification

#### Error: "Rate limit exceeded"
**Symptoms**: 429 HTTP errors, request throttling
**Solutions**:
1. Reduce concurrent requests
2. Use smaller date ranges
3. Add delays between requests
4. Check Databento rate limits for your plan

### 2. Date Range and Symbol Issues

#### Error: "Start date must be different from end date"
**Symptoms**: Databento API rejects equal start/end dates
**Solutions**:
1. Always use at least 1-day ranges: `--start-date 2024-01-01 --end-date 2024-01-02`
2. For testing, use: `--start-date 2024-04-15 --end-date 2024-04-17`
3. For production definitions: use 2-3 week ranges

#### Error: "No data returned" or empty results
**Symptoms**: API call succeeds but returns zero records
**Solutions**:
1. **Definitions Schema**: Use wider date ranges (2-3 weeks)
2. **OHLCV Data**: Verify symbols are active during date range
3. **High-frequency data**: Check market hours and trading days
4. Use different symbol types: `continuous`, `parent`, `native`

#### Error: "Invalid symbols for stype_in"
**Symptoms**: CLI validation rejects symbol format
**Solutions**:
1. **Continuous**: Use format like `ES.c.0`, `CL.c.0`
2. **Parent**: Use format like `ES.FUT`, `CL.FUT`  
3. **Native**: Use format like `AAPL`, `SPY`
4. **ALL_SYMBOLS**: Now works with any stype_in (fixed)

### 3. Database and Storage Issues

#### Error: "Database connection error"
**Symptoms**: Cannot connect to TimescaleDB
**Solutions**:
1. **Check Database Status**:
   ```bash
   docker-compose ps timescaledb
   docker-compose logs timescaledb
   ```

2. **Restart Database**:
   ```bash
   docker-compose restart timescaledb
   # Wait 30 seconds for startup
   docker-compose exec timescaledb pg_isready
   ```

3. **Verify Configuration**:
   ```bash
   # Check environment variables
   grep TIMESCALE .env
   
   # Test manual connection
   docker-compose exec timescaledb psql -U postgres -d hist_data
   ```

4. **Reset Database** (if needed):
   ```bash
   docker-compose down
   docker volume rm hist_data_ingestor_timescaledb_data
   docker-compose up --build -d
   ```

#### Error: "Table does not exist"
**Symptoms**: SQL errors about missing tables
**Solutions**:
1. **Create Tables**:
   ```bash
   # Run schema creation
   python main.py status
   
   # Or force recreation
   docker-compose up --build
   ```

2. **Check Table Existence**:
   ```bash
   docker-compose exec timescaledb psql -U postgres -d hist_data -c "\dt"
   ```

#### Error: "Constraint violation" or "Check constraint failed"
**Symptoms**: Database rejects records due to constraint violations
**Solutions**:
1. **For Definitions Schema**: These are now automatically fixed
2. **For Other Schemas**: Check data integrity and field mappings
3. **Report Issue**: If persists, this indicates a data quality problem

### 4. Performance and Memory Issues

#### Error: "Out of memory" or slow processing
**Symptoms**: System becomes unresponsive, high memory usage
**Solutions**:
1. **Reduce Batch Size**:
   - Use shorter date ranges (1-7 days)
   - Process fewer symbols at once
   - Use `--limit` parameter for queries

2. **Monitor Resources**:
   ```bash
   # Check memory usage
   docker stats
   
   # Monitor disk space
   df -h
   
   # Check database size
   docker-compose exec timescaledb psql -U postgres -d hist_data -c "
   SELECT 
     schemaname,
     tablename,
     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
   FROM pg_tables 
   WHERE schemaname = 'public' 
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
   ```

3. **Optimize Database**:
   ```bash
   # Enable compression (if not already enabled)
   docker-compose exec timescaledb psql -U postgres -d hist_data -c "
   SELECT compress_chunk(chunk_name) 
   FROM timescaledb_information.chunks 
   WHERE table_name = 'ohlcv_data' 
   AND chunk_name NOT IN (SELECT chunk_name FROM timescaledb_information.compressed_chunks);"
   ```

#### Error: "Timeout" or "Request took too long"
**Symptoms**: Operations timeout before completion
**Solutions**:
1. **Reduce Scope**:
   - Shorter date ranges
   - Fewer symbols
   - Use specific symbols instead of ALL_SYMBOLS

2. **Adjust Timeouts**:
   ```python
   # In configuration files, increase timeout values
   timeout: 300  # 5 minutes instead of default
   ```

3. **Use Incremental Processing**:
   ```bash
   # Process in smaller chunks
   python main.py ingest --api databento --schema ohlcv-1d --symbols ES.c.0 --start-date 2024-01-01 --end-date 2024-01-07
   python main.py ingest --api databento --schema ohlcv-1d --symbols ES.c.0 --start-date 2024-01-08 --end-date 2024-01-14
   ```

### 5. Data Quality and Validation Issues

#### Error: "Validation failed" or "Schema validation error"
**Symptoms**: Data doesn't match expected format
**Solutions**:
1. **Check Data Source**:
   - Verify dataset and schema combination is valid
   - Test with known working symbols (ES.c.0, CL.c.0)

2. **Review Field Mappings**:
   - Check transformation configuration files
   - Verify Pydantic model definitions

3. **Enable Debug Logging**:
   ```bash
   # Run with verbose logging
   python main.py ingest --verbose --api databento --schema definitions --symbols ES.FUT --start-date 2024-04-15 --end-date 2024-04-17
   ```

#### Error: "NUL character" or "String literal cannot contain NUL"
**Symptoms**: PostgreSQL rejects data with embedded null characters
**Solutions**:
1. **For Definitions Schema**: This is now automatically fixed
2. **For Other Schemas**: Report this as it should be handled automatically
3. **Manual Cleanup** (if needed):
   ```python
   # Data is automatically sanitized before storage
   # No manual action required
   ```

## Schema-Specific Guidance

### Definitions Schema (Production Ready)

**Optimal Configuration**:
```bash
python main.py ingest \
  --api databento \
  --dataset GLBX.MDP3 \
  --schema definitions \
  --symbols ES.FUT,CL.FUT \
  --stype-in parent \
  --start-date 2024-04-15 \
  --end-date 2024-05-05
```

**Performance Expectations**:
- 3,000+ records/second processing speed
- 2-10 seconds for typical parent symbol queries
- Zero validation errors on real-world data

**Common Issues**:
- ✅ All major issues resolved
- Use 2-3 week date ranges for best coverage
- ALL_SYMBOLS works with any stype_in

### OHLCV Schema

**Optimal Configuration**:
```bash
python main.py ingest \
  --api databento \
  --dataset GLBX.MDP3 \
  --schema ohlcv-1d \
  --symbols ES.c.0,CL.c.0 \
  --start-date 2024-04-15 \
  --end-date 2024-04-22
```

**Performance Expectations**:
- 1,000+ records/second for daily data
- 1 week to 1 month optimal range
- Fast processing for continuous symbols

### High-Frequency Data (Trades, TBBO)

**Optimal Configuration**:
```bash
python main.py ingest \
  --api databento \
  --dataset GLBX.MDP3 \
  --schema trades \
  --symbols ES.c.0 \
  --start-date 2024-04-15 \
  --end-date 2024-04-16
```

**Performance Expectations**:
- Very high volume data
- Use 1-3 day ranges maximum
- Monitor memory usage closely

## Monitoring and Logging

### Enable Debug Logging

```bash
# Set environment variable for verbose logging
export LOG_LEVEL=DEBUG

# Or run with verbose flag
python main.py ingest --verbose [other args]
```

### Monitor System Performance

```bash
# Real-time resource monitoring
docker stats

# Database performance
docker-compose exec timescaledb psql -U postgres -d hist_data -c "
SELECT 
  schemaname,
  tablename,
  n_tup_ins as inserts,
  n_tup_upd as updates,
  n_tup_del as deletes
FROM pg_stat_user_tables 
ORDER BY n_tup_ins DESC;"

# Check recent ingestion jobs
python main.py query --symbols ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --limit 10
```

### Log File Locations

```bash
# Application logs (if file logging enabled)
tail -f logs/application.log

# Docker container logs
docker-compose logs -f

# Database logs
docker-compose logs timescaledb
```

## Getting Help

### Self-Service Resources

1. **Check Recent Changes**: Review `CLAUDE.md` for latest updates
2. **API Documentation**: [Databento Docs](https://docs.databento.com)
3. **TimescaleDB Guide**: [TimescaleDB Documentation](https://docs.timescale.com)

### Reporting Issues

When reporting issues, include:

1. **System Information**:
   ```bash
   python main.py version
   docker-compose version
   python --version
   ```

2. **Error Details**:
   - Full error message
   - Command that caused the error
   - Relevant log output

3. **Environment Context**:
   - Operating system
   - Available memory/disk space
   - Network configuration

4. **Reproduction Steps**:
   - Minimal command to reproduce
   - Expected vs actual behavior
   - Workarounds attempted

### Emergency Recovery

If the system becomes completely unresponsive:

```bash
# Stop all services
docker-compose down

# Clean up resources
docker system prune -f

# Restart fresh
docker-compose up --build -d

# Wait for services to start
sleep 30

# Test basic functionality
python main.py status
```

---

**Last Updated**: 2025-06-19  
**Version**: Production Release  
**Status**: Definitions schema fully production-ready