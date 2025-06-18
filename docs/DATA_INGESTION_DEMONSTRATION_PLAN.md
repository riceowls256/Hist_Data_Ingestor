# Data Ingestion Demonstration Plan
**Hist Data Ingestor - Comprehensive Data Pipeline Showcase**

---

## Overview

This document details the complete data ingestion demonstration plan for the Hist Data Ingestor MVP, covering all Databento schemas with realistic data volumes, performance benchmarks, and success validation criteria.

**Ingestion Objectives:**
- Demonstrate complete pipeline from API to database storage
- Validate all 5 Databento schemas (OHLCV, Trades, TBBO, Statistics, Definitions)
- Showcase error handling and data quality validation
- Verify NFR performance targets (<2-4 hours for 1 year daily data)
- Demonstrate operational monitoring and logging capabilities

---

## Schema Coverage and Data Targets

### **Primary Target Symbols (MVP Compliant)**
Based on PRD Section 5 technical assumptions for MVP data focus:

1. **CL.c.0** - Crude Oil Futures (WTI)
2. **ES.c.0** - E-mini S&P 500 Futures  
3. **NG.c.0** - Natural Gas Futures
4. **HO.c.0** - Heating Oil Futures
5. **RB.c.0** - RBOB Gasoline Futures

**Rationale**: These symbols represent the core MVP requirements from PRD and provide diverse energy/equity coverage for comprehensive testing.

### **Schema-Specific Demonstration Targets**

#### **Schema 1: OHLCV-1D (Daily Bars)**
```yaml
# Demonstration Parameters
symbols: [CL.c.0, ES.c.0, NG.c.0]
date_range: 2024-01-01 to 2024-01-15 (15 days)
expected_records: ~45 records (3 symbols × 15 days)
target_duration: <30 seconds
data_volume: Minimal (high-level aggregated data)
```

**CLI Command Example:**
```bash
python main.py ingest \
  --api databento \
  --schema ohlcv-1d \
  --symbols "CL.c.0,ES.c.0,NG.c.0" \
  --start-date 2024-01-01 \
  --end-date 2024-01-15 \
  --job-name "demo_ohlcv_daily" \
  --verbose
```

**Success Criteria:**
- All 45 records ingested successfully (100% success rate)
- Validation success rate >99% (meet NFR 3 target)
- Execution time <30 seconds
- Proper OHLC business logic validation (High ≥ Low, High ≥ Open/Close)

#### **Schema 2: Trades (High-Volume Transaction Data)**
```yaml
# Demonstration Parameters  
symbols: [ES.c.0]  # Single symbol for manageable volume
date_range: 2024-01-10 (1 day only)
expected_records: 300,000-500,000 records
target_duration: <180 seconds (3 minutes)
data_volume: High (tick-level trade data)
```

**CLI Command Example:**
```bash
python main.py ingest \
  --api databento \
  --schema trades \
  --symbols ES.c.0 \
  --start-date 2024-01-10 \
  --end-date 2024-01-10 \
  --job-name "demo_trades_high_volume" \
  --batch-size 5000 \
  --show-progress
```

**Success Criteria:**
- Handle 300,000+ records successfully
- Processing rate >1,500 records/second
- Memory usage remains <2GB throughout ingestion
- Validation rate >99.5% despite high volume

#### **Schema 3: TBBO (Top of Book Bid/Offer)**
```yaml
# Demonstration Parameters
symbols: [ES.c.0, CL.c.0]
date_range: 2024-01-10 (1 day)
expected_records: 200,000-400,000 records
target_duration: <150 seconds
data_volume: High (frequent quote updates)
```

**CLI Command Example:**
```bash
python main.py ingest \
  --api databento \
  --schema tbbo \
  --symbols "ES.c.0,CL.c.0" \
  --start-date 2024-01-10 \
  --end-date 2024-01-10 \
  --job-name "demo_tbbo_quotes" \
  --memory-limit 1500MB
```

**Success Criteria:**
- Bid/ask spread validation successful (bid ≤ ask)
- Quote timestamp ordering maintained
- Memory efficiency with large quote streams
- Cross-symbol processing consistency

#### **Schema 4: Statistics (Market Statistics)**
```yaml
# Demonstration Parameters
symbols: [ES.c.0, CL.c.0, NG.c.0]
date_range: 2024-01-01 to 2024-01-31 (31 days)
expected_records: 150-300 records (varies by stat type)
target_duration: <45 seconds
data_volume: Low (aggregated market statistics)
```

**CLI Command Example:**
```bash
python main.py ingest \
  --api databento \
  --schema statistics \
  --symbols "ES.c.0,CL.c.0,NG.c.0" \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --job-name "demo_statistics_monthly"
```

**Success Criteria:**
- All CME statistics types successfully ingested
- Stat type validation (opening price, settlement, volume, etc.)
- Proper statistical value formatting and precision
- Cross-symbol statistical consistency

#### **Schema 5: Definitions (Instrument Metadata)**
```yaml
# Demonstration Parameters
symbols: All available (no symbol filter - schema limitation)
date_range: 2024-01-01 to 2024-01-31
expected_records: 15,000-50,000 records (filtered post-ingestion)
target_duration: <300 seconds (5 minutes)
data_volume: Medium (instrument specification data)
```

**CLI Command Example:**
```bash
python main.py ingest \
  --api databento \
  --schema definition \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --job-name "demo_definitions_monthly" \
  --filter-post-ingestion
```

**Success Criteria:**
- Complete instrument metadata retrieved
- Symbol format validation and standardization
- Contract specification accuracy (tick sizes, multipliers)
- Expiration date and trading hour validation

---

## Performance Benchmark Framework

### **Individual Schema Performance Targets**

| Schema | Volume | Target Duration | Success Rate | Memory Limit |
|--------|--------|----------------|--------------|--------------|
| OHLCV-1D | 45 records | <30 seconds | >99% | <100MB |
| Trades | 400K records | <180 seconds | >99% | <2GB |
| TBBO | 300K records | <150 seconds | >99% | <1.5GB |
| Statistics | 200 records | <45 seconds | >99% | <100MB |
| Definitions | 25K records | <300 seconds | >99% | <500MB |

### **Comprehensive Performance Demonstration**
```yaml
# Full pipeline stress test
total_expected_duration: <900 seconds (15 minutes)
total_expected_records: 700,000+ records
memory_peak_target: <2.5GB
overall_success_rate: >99%
```

### **Resource Utilization Monitoring**
```bash
# Resource monitoring during demonstration
docker stats --no-stream hist-data-ingestor_app_1
docker stats --no-stream hist-data-ingestor_timescaledb_1

# Database performance monitoring
SELECT 
  schemaname, 
  tablename, 
  n_tup_ins as inserts,
  n_tup_upd as updates,
  n_tup_del as deletes
FROM pg_stat_user_tables 
WHERE schemaname = 'public';
```

---

## Error Handling and Data Quality Demonstration

### **Intentional Error Scenarios**

#### **Invalid Symbol Testing**
```bash
# Test graceful handling of invalid symbols
python main.py ingest \
  --schema ohlcv-1d \
  --symbols "INVALID.SYMBOL,ES.c.0" \
  --start-date 2024-01-10 \
  --end-date 2024-01-12
```

**Expected Behavior:**
- Clear error message for invalid symbol
- Processing continues for valid symbols
- Quarantine logging for failed symbol resolution
- No pipeline crash or data corruption

#### **API Rate Limit Simulation**
```bash
# Test retry mechanism with small batches
python main.py ingest \
  --schema trades \
  --symbols ES.c.0 \
  --start-date 2024-01-01 \
  --end-date 2024-01-15 \
  --batch-size 100 \
  --api-rate-limit-demo
```

**Expected Behavior:**
- Automatic retry with exponential backoff
- Rate limit detection and graceful throttling
- Progress preservation across retry attempts
- Comprehensive logging of API interactions

#### **Data Validation Failure Testing**
```bash
# Simulate validation failures for demonstration
python main.py ingest \
  --schema ohlcv-1d \
  --symbols ES.c.0 \
  --start-date 2024-01-10 \
  --end-date 2024-01-12 \
  --inject-validation-errors 5  # Development flag
```

**Expected Behavior:**
- Failed records moved to quarantine
- Detailed validation error logging
- Processing continues for valid records
- Quarantine analysis capabilities demonstrated

### **Data Quality Validation Framework**

#### **Business Logic Validation**
```python
# OHLCV Business Rules (demonstrated via logs)
- High price ≥ Low price ≥ 0
- High price ≥ Open price, Close price
- Volume ≥ 0
- Timestamp ordering and timezone correctness

# Trade Data Validation  
- Price > 0
- Size > 0
- Side validation ('B' or 'S')
- Timestamp microsecond precision

# TBBO Validation
- Bid price ≤ Ask price
- Bid price, Ask price > 0
- Quote timestamp ordering
- Bid/Ask size ≥ 0
```

#### **Quarantine Analysis Demonstration**
```bash
# Show quarantine file structure and analysis
ls -la dlq/
python main.py quarantine analyze --schema all --days 1
python main.py quarantine summary --export-csv
```

**Expected Quarantine Output:**
```json
{
  "validation_failures": [
    {
      "timestamp": "2024-01-15T10:30:15Z",
      "schema": "ohlcv-1d", 
      "symbol": "ES.c.0",
      "error_type": "BusinessLogicValidation",
      "error_message": "High price (4750.25) less than low price (4751.00)",
      "original_record": { "raw_data": "..." },
      "validation_context": { "rule": "high_gte_low" }
    }
  ]
}
```

---

## Real-Time Monitoring and Logging Demonstration

### **Structured Logging Showcase**
```bash
# Monitor logs in real-time during ingestion
docker-compose logs -f app | grep -E "(INFO|WARN|ERROR)"

# Analyze log structure and content
tail -100 logs/hist_data_ingestor.log | jq '.'
```

**Expected Log Output Structure:**
```json
{
  "timestamp": "2024-01-15T10:30:15.123456Z",
  "level": "INFO",
  "component": "DatabentoAdapter",
  "message": "Ingestion progress update",
  "context": {
    "schema": "trades",
    "symbol": "ES.c.0", 
    "records_processed": 45000,
    "processing_rate": "1547 records/sec",
    "memory_usage": "234MB",
    "elapsed_time": "29.1s"
  }
}
```

### **Performance Metrics Collection**
```bash
# Real-time performance dashboard (simulated)
python main.py dashboard --live --schema trades --duration 300s

# Export performance metrics for analysis
python main.py metrics export --format json --file demo_metrics.json
```

**Expected Metrics Output:**
```json
{
  "ingestion_session": {
    "session_id": "demo_trades_20240115_103015",
    "start_time": "2024-01-15T10:30:15Z",
    "end_time": "2024-01-15T10:33:42Z",
    "total_duration": "00:03:27",
    "schemas_processed": ["trades"],
    "symbols_processed": ["ES.c.0"],
    "performance": {
      "records_ingested": 387420,
      "records_per_second": 1867,
      "peak_memory_mb": 1840,
      "api_calls": 78,
      "validation_success_rate": 0.9987,
      "quarantine_count": 5
    }
  }
}
```

---

## Database Integration and Validation

### **TimescaleDB Performance Optimization**
```sql
-- Demonstrate hypertable structure
SELECT * FROM timescaledb_information.hypertables;

-- Show partitioning strategy
SELECT 
  schemaname,
  tablename,
  chunk_schema,
  chunk_name,
  range_start,
  range_end
FROM timescaledb_information.chunks 
WHERE hypertable_name = 'trades_data'
ORDER BY range_start DESC
LIMIT 10;

-- Validate indexing strategy
SELECT 
  schemaname, 
  tablename, 
  indexname, 
  indexdef 
FROM pg_indexes 
WHERE tablename IN ('ohlcv_data', 'trades_data', 'tbbo_data', 'statistics_data', 'definitions_data');
```

### **Data Integrity Cross-Validation**
```sql
-- Verify record counts match ingestion logs
SELECT 
  'ohlcv_data' as table_name,
  COUNT(*) as record_count,
  MIN(ts_event) as earliest_date,
  MAX(ts_event) as latest_date
FROM ohlcv_data
UNION ALL
SELECT 
  'trades_data' as table_name,
  COUNT(*) as record_count,
  MIN(ts_event) as earliest_date,
  MAX(ts_event) as latest_date  
FROM trades_data;

-- Validate business logic compliance
SELECT 
  COUNT(*) as total_records,
  SUM(CASE WHEN high_price >= low_price THEN 1 ELSE 0 END) as valid_high_low,
  SUM(CASE WHEN high_price >= open_price THEN 1 ELSE 0 END) as valid_high_open,
  SUM(CASE WHEN volume >= 0 THEN 1 ELSE 0 END) as valid_volume
FROM ohlcv_data;
```

---

## CLI Command Sequence for Live Demonstration

### **Phase 1: Basic Schema Ingestion (30 minutes)**
```bash
# 1. OHLCV Daily (Quick Success Validation)
python main.py ingest \
  --schema ohlcv-1d \
  --symbols "ES.c.0,CL.c.0" \
  --start-date 2024-01-10 \
  --end-date 2024-01-15 \
  --job-name "demo_phase1_ohlcv"

# 2. Statistics (CME Data Validation)  
python main.py ingest \
  --schema statistics \
  --symbols "ES.c.0,CL.c.0" \
  --start-date 2024-01-01 \
  --end-date 2024-01-15 \
  --job-name "demo_phase1_statistics"
```

### **Phase 2: High-Volume Schema Testing (45 minutes)**
```bash
# 3. Trades (Performance Validation)
python main.py ingest \
  --schema trades \
  --symbols ES.c.0 \
  --start-date 2024-01-10 \
  --end-date 2024-01-10 \
  --job-name "demo_phase2_trades_performance" \
  --show-progress

# 4. TBBO (Quote Data Processing)
python main.py ingest \
  --schema tbbo \
  --symbols ES.c.0 \
  --start-date 2024-01-10 \
  --end-date 2024-01-10 \
  --job-name "demo_phase2_tbbo" \
  --memory-limit 1500MB
```

### **Phase 3: Comprehensive Schema Coverage (15 minutes)**
```bash
# 5. Definitions (Metadata Completion)
python main.py ingest \
  --schema definition \
  --start-date 2024-01-01 \
  --end-date 2024-01-15 \
  --job-name "demo_phase3_definitions"
```

---

## Success Validation and Metrics

### **Quantitative Success Criteria**

**Technical Performance Targets:**
- [ ] Total ingestion time <15 minutes (900 seconds)
- [ ] Individual schema performance targets achieved (see table above)
- [ ] Memory usage remains <2.5GB peak across all ingestion
- [ ] Processing rate >1,000 records/second for high-volume schemas

**Data Quality Targets:**
- [ ] Overall validation success rate >99%
- [ ] Zero data corruption or loss incidents
- [ ] Quarantine rate <1% as per NFR 3 requirements
- [ ] Business logic validation 100% compliant

**Operational Excellence Targets:**
- [ ] Zero pipeline crashes or unrecoverable errors
- [ ] Complete error logging and quarantine functionality
- [ ] Real-time progress tracking and user feedback
- [ ] Comprehensive monitoring and observability

### **Qualitative Success Criteria**

**User Experience Validation:**
- [ ] CLI provides clear progress feedback and timing
- [ ] Error messages are actionable and helpful
- [ ] Resource usage is transparent and controlled
- [ ] Documentation matches actual behavior

**System Integration Validation:**
- [ ] Configuration system works seamlessly
- [ ] Database integration performs as designed
- [ ] API integration handles rate limits gracefully
- [ ] Logging provides operational visibility

---

## Risk Mitigation and Contingency Plans

### **API Rate Limit Management**
- **Primary Strategy**: Use conservative date ranges (1-15 days max)
- **Monitoring**: Real-time rate limit tracking and automatic throttling
- **Fallback**: Pre-cached sample data available if limits exceeded
- **Documentation**: Clear rate limit information for operational teams

### **Memory and Resource Management**
- **Primary Strategy**: Configurable batch sizes and memory limits
- **Monitoring**: Real-time memory usage tracking with alerts
- **Fallback**: Automatic batch size reduction if memory thresholds approached
- **Documentation**: Resource requirement guidelines for production

### **Data Volume Management**
- **Primary Strategy**: Representative but manageable data volumes
- **Monitoring**: Record count estimation and processing rate calculation  
- **Fallback**: Ability to terminate long-running ingestion jobs gracefully
- **Documentation**: Scaling guidelines for production data volumes

---

**Document Version**: 1.0  
**Created**: Story 3.5 Implementation  
**Target Audience**: Technical Team, Primary User  
**Usage**: MVP Demonstration Phase 2 