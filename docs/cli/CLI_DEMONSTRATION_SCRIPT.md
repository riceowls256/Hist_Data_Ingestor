# CLI Demonstration Script
**Hist Data Ingestor - Complete Command Line Interface Showcase**

---

## Overview

This script provides a comprehensive demonstration of the Hist Data Ingestor CLI interface, showcasing all commands, output formats, error handling, and user experience features. The demonstration validates NFR 6 (Usability) requirements and provides hands-on knowledge transfer.

**CLI Components Demonstrated:**
- All CLI commands (ingest, query, status, version)
- Multiple query scenarios and output formats
- Error handling and user guidance features
- Progress indicators and feedback systems
- Help system and documentation integration

---

## Phase 1: CLI Foundation and Help System (15 minutes)

### **1.1 CLI Access and Version Verification (5 minutes)**

#### **Basic CLI Access**
```bash
# Enter application container
docker-compose exec app bash

# Verify CLI accessibility
cd /app
python main.py --help

# Version information
python main.py version
```

**Expected Output:**
```
Hist Data Ingestor CLI v0.1.0-mvp
Python Version: 3.11.x
Docker Environment: Active
Database Status: Connected
```

#### **Command Structure Overview**
```bash
# Display main command help
python main.py --help

# Command-specific help
python main.py ingest --help
python main.py query --help
python main.py status --help
```

**Expected Features:**
- Rich-formatted help text with colors and structure
- Clear command descriptions and parameter explanations
- Practical usage examples for each command
- Parameter validation and type information

### **1.2 Status Command Demonstration (5 minutes)**

#### **System Health Checking**
```bash
# Basic status check
python main.py status

# Detailed status with verbose output
python main.py status --verbose

# Database connectivity validation
python main.py status --check-db
```

**Expected Output Example:**
```
🟢 System Status: Healthy
📊 Database: Connected (TimescaleDB 2.14.2)
🔗 API: Databento connection valid
💾 Storage: 15.2GB available
📝 Logs: /app/logs/ (3 files, 2.4MB)
🗂️  Quarantine: /app/dlq/ (empty)

Recent Activity:
  ✅ Last ingestion: 2024-01-15 14:30:00 (Success)
  🔍 Available symbols: 12 loaded
  📈 Data range: 2024-01-01 to 2024-01-15

Configuration Status:
  ✅ System config: Valid
  ✅ API config: Valid  
  ✅ Environment: All variables loaded
```

### **1.3 Help System and Documentation Integration (5 minutes)**

#### **Comprehensive Help Demonstration**
```bash
# Rich help formatting
python main.py query --help

# Parameter validation help
python main.py query --symbols INVALID_SYMBOL --help-symbols

# Examples and tips
python main.py ingest --examples
```

**Expected Features:**
- Color-coded help text with Rich formatting
- Detailed parameter descriptions with examples
- Common usage patterns and best practices
- Error prevention guidance and tips

---

## Phase 2: Data Ingestion CLI Commands (25 minutes)

### **2.1 Basic Ingestion Commands (10 minutes)**

#### **Single Schema Ingestion**
```bash
# OHLCV daily data ingestion
python main.py ingest \
  --api databento \
  --schema ohlcv-1d \
  --symbols ES.c.0 \
  --start-date 2024-01-10 \
  --end-date 2024-01-12 \
  --verbose

# Monitor progress with real-time feedback
```

**Expected Output Features:**
- Rich progress bar with percentage completion
- Real-time timing information and ETA
- Record count and processing rate updates
- Color-coded status messages (success, warning, error)

#### **Multiple Symbol Ingestion**
```bash
# Multiple symbols with different input formats
python main.py ingest \
  --api databento \
  --schema trades \
  --symbols "ES.c.0,CL.c.0" \
  --start-date 2024-01-10 \
  --end-date 2024-01-10 \
  --batch-size 1000
```

### **2.2 Advanced Ingestion Features (10 minutes)**

#### **Job Configuration and Resume Functionality**
```bash
# Create and execute named job
python main.py ingest \
  --job-name demo_comprehensive \
  --config configs/api_specific/databento_config.yaml \
  --symbols ES.c.0,CL.c.0,NG.c.0 \
  --schema ohlcv-1d \
  --start-date 2024-01-01 \
  --end-date 2024-01-03

# Resume interrupted job (demonstration of resilience)
python main.py ingest --resume demo_comprehensive
```

#### **Performance and Resource Monitoring**
```bash
# Ingestion with performance metrics
python main.py ingest \
  --api databento \
  --schema statistics \
  --symbols ES.c.0 \
  --start-date 2024-01-01 \
  --end-date 2024-01-15 \
  --show-metrics \
  --memory-limit 2GB
```

**Expected Metrics Output:**
```
📊 Ingestion Performance Metrics:
   Records Processed: 1,247
   Processing Rate: 156 records/second
   Memory Usage: 234MB / 2GB limit
   API Calls: 12 (rate limit: 8 remaining)
   Validation Success: 99.2% (1,237/1,247)
   Storage Time: 2.3 seconds
   Total Duration: 8.7 seconds
```

### **2.3 Error Handling and Recovery (5 minutes)**

#### **Invalid Parameter Handling**
```bash
# Invalid date format
python main.py ingest \
  --schema ohlcv-1d \
  --symbols ES.c.0 \
  --start-date "invalid-date" \
  --end-date 2024-01-10
```

**Expected Error Response:**
```
❌ Error: Invalid date format 'invalid-date'
💡 Expected format: YYYY-MM-DD (e.g., 2024-01-15)
📖 Use --help for parameter documentation
```

#### **API Error Simulation and Recovery**
```bash
# Intentional API error (invalid symbol)
python main.py ingest \
  --schema ohlcv-1d \
  --symbols NONEXISTENT.SYMBOL \
  --start-date 2024-01-10 \
  --end-date 2024-01-10
```

**Expected Recovery Response:**
```
⚠️  Warning: Symbol resolution failed for 'NONEXISTENT.SYMBOL'
🔍 Available symbols (sample):
   • ES.c.0 (E-mini S&P 500)
   • CL.c.0 (Crude Oil)
   • NG.c.0 (Natural Gas)
💡 Use 'python main.py query --list-symbols' for complete list
```

---

## Phase 3: Query Commands and Data Retrieval (25 minutes)

### **3.1 Basic Query Operations (10 minutes)**

#### **Single Symbol Queries**
```bash
# Basic OHLCV query with table output
python main.py query \
  --schema ohlcv-1d \
  --symbols ES.c.0 \
  --start-date 2024-01-10 \
  --end-date 2024-01-12

# Query with performance timing
python main.py query \
  --schema trades \
  --symbols ES.c.0 \
  --start-date 2024-01-10 \
  --end-date 2024-01-10 \
  --limit 1000 \
  --show-timing
```

**Expected Table Output:**
```
📊 Query Results: OHLCV Daily Data (ES.c.0)
┌─────────────┬────────────┬───────────┬───────────┬───────────┬───────────┬─────────────┐
│ Date        │ Symbol     │ Open      │ High      │ Low       │ Close     │ Volume      │
├─────────────┼────────────┼───────────┼───────────┼───────────┼───────────┼─────────────┤
│ 2024-01-10  │ ES.c.0     │ 4,742.25  │ 4,756.00  │ 4,739.50  │ 4,752.75  │ 2,847,392   │
│ 2024-01-11  │ ES.c.0     │ 4,752.75  │ 4,768.25  │ 4,745.00  │ 4,763.50  │ 2,923,154   │
│ 2024-01-12  │ ES.c.0     │ 4,763.50  │ 4,771.25  │ 4,757.75  │ 4,768.00  │ 2,756,889   │
└─────────────┴────────────┴───────────┴───────────┴───────────┴───────────┴─────────────┘

⏱️  Query executed in 1.24 seconds
📈 3 records retrieved
```

#### **Multiple Output Formats**
```bash
# CSV output format
python main.py query \
  --schema ohlcv-1d \
  --symbols ES.c.0 \
  --start-date 2024-01-10 \
  --end-date 2024-01-12 \
  --output-format csv

# JSON output format  
python main.py query \
  --schema statistics \
  --symbols ES.c.0 \
  --start-date 2024-01-01 \
  --end-date 2024-01-15 \
  --output-format json \
  --pretty
```

### **3.2 Advanced Query Scenarios (10 minutes)**

#### **Multiple Symbol Queries**
```bash
# Multiple symbols with performance comparison
python main.py query \
  --schema ohlcv-1d \
  --symbols "ES.c.0,CL.c.0,NG.c.0" \
  --start-date 2024-01-08 \
  --end-date 2024-01-12 \
  --output-format table \
  --sort-by date,symbol

# Cross-schema data correlation
python main.py query \
  --schema tbbo \
  --symbols ES.c.0 \
  --start-date 2024-01-10 \
  --end-date 2024-01-10 \
  --limit 100 \
  --show-bid-ask-spread
```

#### **Large Dataset Handling**
```bash
# Large result set with pagination
python main.py query \
  --schema trades \
  --symbols ES.c.0 \
  --start-date 2024-01-10 \
  --end-date 2024-01-10 \
  --limit 10000 \
  --offset 0 \
  --show-progress

# Aggregated queries for performance
python main.py query \
  --schema trades \
  --symbols ES.c.0 \
  --start-date 2024-01-10 \
  --end-date 2024-01-10 \
  --aggregate daily \
  --metrics "count,volume_sum,price_avg"
```

### **3.3 File Output and Data Export (5 minutes)**

#### **File Export Capabilities**
```bash
# Export to CSV file
python main.py query \
  --schema ohlcv-1d \
  --symbols "ES.c.0,CL.c.0" \
  --start-date 2024-01-01 \
  --end-date 2024-01-15 \
  --output-format csv \
  --output-file "demo_export.csv"

# Export to JSON with metadata
python main.py query \
  --schema statistics \
  --symbols ES.c.0 \
  --start-date 2024-01-01 \
  --end-date 2024-01-15 \
  --output-format json \
  --output-file "demo_stats.json" \
  --include-metadata
```

**Expected File Output Confirmation:**
```
✅ Query completed successfully
📁 Output written to: demo_export.csv
📊 Records exported: 45
💾 File size: 2.4KB
🔍 Preview available: Use --preview flag to display first 5 rows
```

---

## Phase 4: User Experience and Error Handling (10 minutes)

### **4.1 Progress Indicators and Feedback (5 minutes)**

#### **Real-time Progress Tracking**
```bash
# Large query with progress indication
python main.py query \
  --schema trades \
  --symbols ES.c.0 \
  --start-date 2024-01-01 \
  --end-date 2024-01-15 \
  --show-progress \
  --verbose

# Ingestion with detailed progress
python main.py ingest \
  --schema ohlcv-1d \
  --symbols "ES.c.0,CL.c.0,NG.c.0" \
  --start-date 2024-01-01 \
  --end-date 2024-01-10 \
  --progress-style detailed
```

**Expected Progress Display:**
```
🔄 Processing Query...
[████████████████████████████████████████] 100%
📊 Records Found: 156,847
⏱️  Elapsed: 00:03:42 | ETA: 00:00:00
💾 Memory Usage: 145MB | Rate: 704 records/sec

Status Updates:
  ✅ Database connection established
  🔍 Symbol resolution: ES.c.0 → instrument_id 4916
  📈 Date range validation: 15 days
  🚀 Query execution: 3.7 seconds
  🎯 Results formatting: 0.2 seconds
```

### **4.2 Error Scenarios and User Guidance (5 minutes)**

#### **Comprehensive Error Handling**
```bash
# Database connectivity error simulation
python main.py query \
  --schema ohlcv-1d \
  --symbols ES.c.0 \
  --start-date 2024-01-10 \
  --end-date 2024-01-12
# (with database temporarily stopped)
```

**Expected Error Response:**
```
❌ Error: Database connection failed
🔧 Troubleshooting Steps:
   1. Verify database container is running: docker-compose ps
   2. Check database logs: docker-compose logs timescaledb
   3. Validate connection settings in .env file
   4. Try status command: python main.py status --check-db

📞 Need help? Refer to troubleshooting guide:
   docs/troubleshooting.md#database-connection-issues
```

#### **Parameter Validation and Suggestions**
```bash
# Date range validation error
python main.py query \
  --schema ohlcv-1d \
  --symbols ES.c.0 \
  --start-date 2024-01-15 \
  --end-date 2024-01-10  # End before start
```

**Expected Validation Response:**
```
❌ Error: Invalid date range
🗓️  Start Date: 2024-01-15
🗓️  End Date: 2024-01-10

💡 Issue: End date must be after start date
✅ Suggested fix: --start-date 2024-01-10 --end-date 2024-01-15

📖 Date Range Guidelines:
   • Use YYYY-MM-DD format
   • Maximum range: 1 year for OHLCV, 30 days for trades
   • Ensure data availability in selected range
```

---

## Phase 5: Advanced Features and Integration (15 minutes)

### **5.1 Symbol Discovery and Management (5 minutes)**

#### **Available Symbols Query**
```bash
# List all available symbols
python main.py query --list-symbols

# Search symbols by pattern
python main.py query --search-symbols "*ES*"

# Symbol information lookup
python main.py query --symbol-info ES.c.0
```

**Expected Symbol Information:**
```
🔍 Symbol Information: ES.c.0

📊 Basic Details:
   Name: E-mini S&P 500 Futures (Continuous Contract)
   Exchange: CME Globex
   Asset Class: Equity Index Futures
   Currency: USD
   Tick Size: 0.25 points ($12.50)

📈 Available Data:
   Schemas: OHLCV, Trades, TBBO, Statistics, Definitions
   Date Range: 2020-01-01 to 2024-01-15
   Record Count: 1,247,892 (all schemas)
   Last Update: 2024-01-15 09:30:00

🎯 Performance Stats:
   Average Query Time: 2.3 seconds (1 month OHLCV)
   Data Quality: 99.8% validation success rate
```

### **5.2 Configuration and System Integration (5 minutes)**

#### **Configuration Validation and Testing**
```bash
# Validate system configuration
python main.py config validate

# Test API connectivity
python main.py config test-api databento

# Display current configuration (sanitized)
python main.py config show --mask-credentials
```

#### **Log and Quarantine Analysis**
```bash
# Review recent logs
python main.py logs --tail 100 --level INFO

# Analyze quarantine files
python main.py quarantine analyze --days 7

# System health comprehensive check
python main.py status --comprehensive --export-report
```

### **5.3 Performance Benchmarking and Optimization (5 minutes)**

#### **Performance Testing Commands**
```bash
# Query performance benchmark
python main.py benchmark query \
  --schema ohlcv-1d \
  --symbols ES.c.0 \
  --duration 30-days \
  --iterations 5

# Ingestion performance test
python main.py benchmark ingest \
  --schema trades \
  --symbols ES.c.0 \
  --duration 1-day \
  --measure-memory \
  --target-rate 1000-records-per-sec
```

**Expected Benchmark Output:**
```
🏁 Performance Benchmark Results

Query Performance:
  Schema: OHLCV-1D | Symbol: ES.c.0 | Duration: 30 days
  
  Execution Times (5 iterations):
    Avg: 3.24 seconds | Min: 2.87s | Max: 3.91s
    Std Dev: 0.42s | 95th Percentile: 3.78s
  
  🎯 NFR Target: <5.0 seconds ✅ PASSED
  
  Records Retrieved: 30 records (30 days)
  Throughput: 9.3 records/second
  Memory Peak: 45MB
  
  Performance Grade: A (Excellent)
  Recommendation: Current performance exceeds targets
```

---

## CLI Command Reference Summary

### **Core Commands**
```bash
# Essential operations
python main.py version          # Version information
python main.py status           # System health check
python main.py config validate  # Configuration validation

# Data operations
python main.py ingest           # Data ingestion
python main.py query            # Data retrieval
python main.py logs             # Log analysis
python main.py quarantine       # Error analysis

# Utilities
python main.py benchmark        # Performance testing
python main.py config           # Configuration management
python main.py --help           # Comprehensive help
```

### **Common Parameter Patterns**
```bash
# Standard query pattern
--schema <schema_name> --symbols <symbol_list> --start-date <YYYY-MM-DD> --end-date <YYYY-MM-DD>

# Output control
--output-format <table|csv|json> --output-file <filename> --limit <number>

# Performance and debugging
--verbose --show-timing --show-progress --show-metrics

# Error handling and help
--help --examples --validate-only --dry-run
```

---

## Success Criteria Validation

### **User Experience Validation**
- [ ] Intuitive command structure with clear help documentation
- [ ] Rich-formatted output with colors and progress indicators
- [ ] Comprehensive error handling with actionable guidance
- [ ] Performance feedback and timing information
- [ ] Multiple output formats for different use cases

### **Functional Validation**
- [ ] All CLI commands execute successfully
- [ ] Query performance meets NFR targets (<5 seconds)
- [ ] Error scenarios handled gracefully
- [ ] File output capabilities functional
- [ ] Real-time progress tracking operational

### **Knowledge Transfer Validation**
- [ ] Primary user can execute all demonstrated commands independently
- [ ] Error scenarios provide clear troubleshooting guidance
- [ ] Help system enables self-service learning
- [ ] Performance benchmarking provides operational insight

---

**Document Version**: 1.0  
**Created**: Story 3.5 Implementation  
**Target Audience**: Primary User, Demonstration Attendees  
**Usage**: MVP Demonstration Phase 3 