# Production Deployment Checklist

## Issues Fixed

### 1. EnvironmentAdapter AttributeError: 'is_windows'
**Issue**: `EnvironmentAdapter` initialization order caused AttributeError when accessing `is_windows`
**Root Cause**: The `_detect_color_support()` method was called before `self.is_windows` was initialized
**Fix**: Reordered initialization in `src/cli/config_manager.py` to set `self.is_windows` first
**Status**: ✅ FIXED

### 2. Symbol Type Validation
**Issue**: Users could specify invalid symbol/stype_in combinations (e.g., NG.FUT with stype_in='continuous')
**Fix**: Added `validate_symbol_stype_combination()` function with helpful error messages
**Status**: ✅ IMPLEMENTED

### 3. Exception Handling
**Issue**: `typer.Exit` exceptions were being logged as errors
**Fix**: Added specific handling for `typer.Exit` to re-raise without logging
**Status**: ✅ FIXED

## Symbol Format Guide

### Continuous Contracts (stype_in='continuous')
- Format: `[ROOT].[ROLL_RULE].[RANK]`
- Examples: `ES.c.0`, `NG.c.0`, `CL.c.1`
- Use for: Time series data with continuous contract rolls

### Parent Symbols (stype_in='parent')
- Format: `[ROOT].[PRODUCT_TYPE]`
- Examples: `ES.FUT`, `NG.FUT`, `CL.OPT`
- Use for: Fetching all contracts under a product family
- Note: Especially efficient for definition schemas

### Native Symbols (stype_in='native')
- Format: `[SYMBOL]`
- Examples: `SPY`, `AAPL`, `MSFT`
- Use for: Equity symbols and ETFs

## Pre-Deployment Testing

### 1. Environment Detection
```bash
python main.py config environment
```
- Verify platform detection works correctly
- Check terminal capabilities are detected
- Ensure color/unicode support is accurate

### 2. Symbol Validation Tests
```bash
# Should fail with helpful error
python main.py ingest --api databento --dataset GLBX.MDP3 --schema ohlcv-1d \
    --symbols NG.FUT --stype-in continuous --start-date 2024-01-01 --end-date 2024-01-01 --dry-run

# Should succeed
python main.py ingest --api databento --dataset GLBX.MDP3 --schema ohlcv-1d \
    --symbols NG.c.0 --stype-in continuous --start-date 2024-01-01 --end-date 2024-01-01 --dry-run

# Should succeed
python main.py ingest --api databento --dataset GLBX.MDP3 --schema ohlcv-1d \
    --symbols NG.FUT --stype-in parent --start-date 2024-01-01 --end-date 2024-01-01 --dry-run
```

### 3. Run Comprehensive Test Suite
```bash
python test_cli_production.py
```

**Expected Results:**
- Total Tests: 26 (1 test commented out for invalid API)
- All tests should pass
- No timeouts expected
- Symbol validation should work correctly for all formats

### 4. Performance Tests
- Test with large symbol lists (50+ symbols)
- Test with large date ranges (but respect 365-day limit)
- Monitor memory usage during ingestion

## Production Configuration

### Environment Variables
```bash
# Required
export DATABENTO_API_KEY="your-api-key"
export TIMESCALEDB_USER="your-db-user"
export TIMESCALEDB_PASSWORD="your-db-password"
export TIMESCALEDB_HOST="your-db-host"
export TIMESCALEDB_PORT="5432"
export TIMESCALEDB_DBNAME="your-db-name"

# Optional CLI Configuration
export HDI_PROGRESS_STYLE="advanced"  # or simple, compact, minimal
export HDI_SHOW_ETA="true"
export HDI_COLORS="true"
export HDI_MAX_RETRIES="3"
```

### Database Setup
1. Ensure TimescaleDB extension is installed
2. Create required schemas and tables
3. Set up appropriate indexes
4. Configure connection pooling for production load

### Logging Configuration
- Ensure log directory exists: `mkdir -p logs`
- Configure log rotation to prevent disk space issues
- Set appropriate log levels for production

### Error Handling
- Monitor `dlq/` directory for quarantined records
- Set up alerts for pipeline failures
- Implement retry logic for transient API failures

## Monitoring

### Key Metrics to Track
1. **Pipeline Performance**
   - Records per second
   - API response times
   - Database write times
   - Memory usage

2. **Data Quality**
   - Validation failure rate
   - Records quarantined
   - Schema mismatches

3. **System Health**
   - API rate limits
   - Database connection pool
   - Disk space (logs and DLQ)

### Alerting Thresholds
- Pipeline failure rate > 5%
- Validation failure rate > 1%
- API response time > 5 seconds
- Database write time > 1 second
- DLQ size > 1GB

## Rollback Plan

1. Keep previous version available
2. Document database schema changes
3. Test rollback procedure in staging
4. Have manual intervention procedures ready

## Post-Deployment Verification

1. **Smoke Tests**
   ```bash
   # Basic health check
   python main.py status
   
   # Test small ingestion
   python main.py ingest --api databento --job ohlcv_1d --dry-run
   
   # Test query functionality
   python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-01
   ```

2. **Monitor First 24 Hours**
   - Check error logs every hour
   - Monitor DLQ directory
   - Verify data quality in database
   - Check API usage and rate limits

3. **Performance Baseline**
   - Record typical ingestion speeds
   - Document memory usage patterns
   - Note API response times
   - Track database query performance

## Known Issues

1. **trade_count Field Type Coercion**
   - Warning during OHLCV ingestion about int64 coercion
   - Records still stored successfully
   - Consider updating schema validation rules

2. **Date Range Limits**
   - Maximum 365 days per ingestion request
   - Users must split larger ranges manually
   - Consider implementing automatic date chunking

## Support Contacts

- Technical Issues: [Create issue on GitHub]
- API Issues: Databento support
- Database Issues: DBA team
- Emergency: On-call engineer