# MVP Verification Test Suite

This directory contains the comprehensive MVP verification test suite that validates whether the historical data ingestor MVP meets all success metrics defined in the PRD.

## Overview

The verification suite tests against the following Non-Functional Requirements (NFRs):

- **NFR 2**: Operational Stability - 95% of scheduled ingestion runs complete without manual intervention
- **NFR 3**: Data Integrity - <1% of processed records fail critical validation checks  
- **NFR 4.1**: Initial Bulk Ingestion - 1 year daily data for 5 symbols within 2-4 hours
- **NFR 4.2**: Querying Interface - 1 month daily data for single symbol in <5 seconds

## Test Components

### 1. Data Availability Test (`data_availability_test.py`)

**Purpose**: Validates AC1 - Confirms data presence for MVP target symbols from Databento

**What it tests**:
- Data availability for MVP symbols (CL, SPY/ES, NG, HO, RB) 
- Coverage across key schemas (ohlcv-1d, trades, tbbo, statistics, definitions)
- Minimum 30 days of recent data
- Data continuity and recency checks

**Success criteria**: All MVP symbols have data with >90% continuity for last 30 days

### 2. Performance Benchmark Test (`performance_benchmark_test.py`)

**Purpose**: Validates AC2 - Tests CLI query performance against <5 second target

**What it tests**:
- Query response times using actual CLI commands
- Multiple test scenarios (single symbol, multiple symbols, different time ranges)
- 80% of queries must meet <5 second target
- Performance statistics and trends

**Success criteria**: 80% of benchmark queries complete in <5 seconds

### 3. Data Integrity Analysis (`data_integrity_analysis.py`)

**Purpose**: Validates AC3 - Calculates data integrity rates against <1% failure target

**What it tests**:
- Application log analysis for success/failure patterns
- Quarantine/DLQ file analysis for failed records
- Database-level data validation and consistency
- Integrity trend analysis over time

**Success criteria**: <1% of processed records fail validation checks

### 4. Master Verification Runner (`master_verification_runner.py`)

**Purpose**: Validates AC5 - Orchestrates all tests and generates comprehensive reports

**What it provides**:
- Unified test execution framework
- Cross-test analysis and insights
- Executive summary generation
- MVP readiness scoring and recommendations

## Quick Start

### Running All Tests

From the project root directory:

```bash
# Run complete verification suite
python run_mvp_verification.py

# Run with detailed output
python run_mvp_verification.py --verbose
```

### Running Individual Tests

```bash
# Data availability only
python run_mvp_verification.py --test data_availability

# Performance benchmarks only  
python run_mvp_verification.py --test performance_benchmark

# Data integrity analysis only
python run_mvp_verification.py --test data_integrity
```

### Viewing Previous Results

```bash
# Generate report from last test run
python run_mvp_verification.py --report-only

# Detailed report from last run
python run_mvp_verification.py --report-only --verbose
```

## Prerequisites

### Database Requirements

- TimescaleDB instance running and accessible
- Environment variables configured:
  ```bash
  export TIMESCALEDB_HOST=localhost
  export TIMESCALEDB_PORT=5432
  export TIMESCALEDB_DB=hist_data_ingestor
  export TIMESCALEDB_USER=postgres
  export TIMESCALEDB_PASSWORD=your_password
  ```

### Data Requirements

- MVP target symbols ingested: CL.c.0, SPY, ES.c.0, NG.c.0, HO.c.0, RB.c.0
- Minimum 30 days of recent data
- CLI query functionality operational (Story 3.2)

### Dependencies

All required dependencies are included in the main project `requirements.txt`:

- sqlalchemy>=2.0.0
- structlog>=23.0.0  
- pandas>=2.0.0
- pydantic>=2.5.0

## Understanding Test Results

### Test Status Values

- **PASS**: All criteria met, no issues
- **WARNING**: Minor issues or close to thresholds  
- **FAIL**: Critical criteria not met
- **ERROR**: Test execution failed

### MVP Readiness Determination

The MVP is considered ready when:

1. **Data Availability**: PASS status (all symbols present with good continuity)
2. **Performance**: PASS status (>80% of queries meet <5s target)  
3. **Data Integrity**: PASS status (<1% validation failure rate)
4. **Overall Score**: ≥80% (B grade or better)

### Results Files

Test results are saved to the `logs/` directory:

- `mvp_verification_results_YYYYMMDD_HHMMSS.json` - Individual test results
- `mvp_analysis_YYYYMMDD_HHMMSS.json` - Comprehensive analysis
- `mvp_comprehensive_verification_YYYYMMDD_HHMMSS.json` - Full report

## Troubleshooting

### Common Issues

**Database Connection Errors**
```
Error: Failed to create database engine
```
- Verify TimescaleDB is running
- Check environment variables
- Confirm network connectivity

**No Data Found**
```
Test Status: FAIL - Missing symbols: [...]
```
- Run data ingestion for missing symbols
- Check Databento API connectivity
- Verify symbol naming conventions

**Performance Test Failures**  
```
Query timed out after 30 seconds
```
- Check database indexes on security_symbol and event_timestamp
- Verify TimescaleDB hypertable configuration
- Consider query optimization

**CLI Command Failures**
```
CLI command failed: No module named 'main'
```
- Ensure running from project root directory
- Verify CLI dependencies installed
- Check Python path configuration

### Debug Mode

For detailed debugging, run with verbose output:

```bash
python run_mvp_verification.py --verbose
```

This provides:
- Detailed execution logs
- SQL query traces
- Performance metrics
- Error stack traces

### Manual Test Execution

For debugging individual components:

```python
from tests.integration.mvp_verification.data_availability_test import DataAvailabilityTest

# Run single test with detailed output
test = DataAvailabilityTest()
result = test.run_test()
print(test.generate_detailed_report(result))
```

## Integration with CI/CD

### Exit Codes

The verification runner uses standard exit codes:
- `0`: Success (MVP ready)
- `1`: Failure (MVP not ready or execution error)

### CI/CD Integration Example

```yaml
# GitHub Actions example
- name: Run MVP Verification
  run: |
    python run_mvp_verification.py
    if [ $? -eq 0 ]; then
      echo "MVP verification passed"
    else
      echo "MVP verification failed" 
      exit 1
    fi
```

### Automated Monitoring

For ongoing monitoring, consider:

```bash
# Daily verification check
0 6 * * * cd /path/to/project && python run_mvp_verification.py >> logs/daily_verification.log 2>&1
```

## Extending the Test Suite

### Adding New Tests

1. Create test class inheriting from base structure:

```python
from .verification_utils import VerificationUtils, MVPVerificationResult

class NewTest:
    def __init__(self):
        self.utils = VerificationUtils()
    
    def run_test(self) -> MVPVerificationResult:
        # Implement test logic
        pass
```

2. Add to `master_verification_runner.py`:

```python
from .new_test import NewTest

# In __init__ method:
self.tests['new_test'] = NewTest()
```

3. Update CLI runner and documentation

### Custom Metrics

Add custom metrics to `verification_utils.py`:

```python
def custom_metric_check(self, criteria):
    # Implement custom validation
    pass
```

## Maintenance Schedule

### Weekly Tasks
- Review test execution logs
- Monitor performance trends
- Update test data ranges

### Monthly Tasks  
- Validate test criteria against current NFRs
- Update documentation
- Review and optimize test performance

### Quarterly Tasks
- Full test suite review
- Update target thresholds if needed
- Enhance test coverage based on lessons learned

## Support

For issues with the verification suite:

1. Check this README troubleshooting section
2. Review logs in `logs/` directory
3. Run individual tests with `--verbose` for detailed output
4. Consult project documentation in `docs/` directory

## Version History

- **v1.0.0**: Initial implementation with AC1-AC5 coverage
- MVP target symbols: CL.c.0, SPY, ES.c.0, NG.c.0, HO.c.0, RB.c.0  
- Performance target: <5 seconds for standard queries
- Integrity target: <1% validation failure rate 