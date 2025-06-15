# End-to-End Testing Environment Setup Guide

**Story 2.7: Test End-to-End Databento Data Ingestion and Storage**

This guide provides step-by-step instructions for setting up the complete testing environment required for Epic 2 validation and Story 2.7 execution.

## Overview

The end-to-end testing framework validates the complete Databento data ingestion pipeline, including:
- ✅ API data extraction from Databento
- ✅ Data transformation and validation
- ✅ TimescaleDB storage and retrieval
- ✅ Error handling and quarantine mechanisms
- ✅ Pipeline orchestration and CLI interface

---

## Prerequisites

### System Requirements

- **Python 3.8+** with virtual environment support
- **Docker and Docker Compose** (for TimescaleDB)
- **Git** for repository access
- **Databento API Key** (free tier available)

### Required Python Packages

The following packages must be installed in your virtual environment:
```bash
pip install -r requirements.txt
```

Key dependencies:
- `databento>=0.57.0` - Databento Python client
- `psycopg2-binary>=2.9.0` - PostgreSQL/TimescaleDB connector
- `pydantic>=2.0.0` - Data validation
- `typer>=0.9.0` - CLI framework
- `structlog>=23.0.0` - Structured logging
- `tenacity>=8.0.0` - Retry mechanisms

---

## Step 1: Database Environment Setup

### Option A: Docker TimescaleDB (Recommended)

1. **Create Docker Compose configuration:**
```yaml
# docker-compose.test.yml
version: '3.8'

services:
  timescaledb-test:
    image: timescale/timescaledb:latest-pg15
    container_name: hist_data_test_db
    ports:
      - "5433:5432"  # Use different port to avoid conflicts
    environment:
      POSTGRES_DB: hist_data_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
      TIMESCALEDB_TELEMETRY: off
    volumes:
      - timescale_test_data:/var/lib/postgresql/data
      - ./sql:/docker-entrypoint-initdb.d/
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user -d hist_data_test"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  timescale_test_data:
```

2. **Start the test database:**
```bash
docker-compose -f docker-compose.test.yml up -d
```

3. **Verify database connectivity:**
```bash
docker exec -it hist_data_test_db psql -U test_user -d hist_data_test -c "SELECT version();"
```

### Option B: Local TimescaleDB Installation

1. **Install TimescaleDB:**
   - **macOS**: `brew install timescaledb`
   - **Ubuntu**: Follow [TimescaleDB installation guide](https://docs.timescale.com/install/latest/)

2. **Create test database:**
```sql
CREATE DATABASE hist_data_test;
CREATE USER test_user WITH PASSWORD 'test_password';
GRANT ALL PRIVILEGES ON DATABASE hist_data_test TO test_user;
```

3. **Enable TimescaleDB extension:**
```sql
\c hist_data_test
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

---

## Step 2: Environment Variables Configuration

### Create Test Environment File

Create `.env.test` file in project root:

```bash
# Databento API Configuration
DATABENTO_API_KEY=your_databento_api_key_here

# Test Database Configuration (Docker setup)
TIMESCALEDB_TEST_HOST=localhost
TIMESCALEDB_TEST_PORT=5433
TIMESCALEDB_TEST_DB=hist_data_test
TIMESCALEDB_TEST_USER=test_user
TIMESCALEDB_TEST_PASSWORD=test_password

# Test Execution Settings
PYTHONPATH=src
LOG_LEVEL=INFO
TEST_TIMEOUT=600

# Optional: Production Database (for comparison testing)
TIMESCALEDB_HOST=localhost
TIMESCALEDB_PORT=5432
TIMESCALEDB_DB=hist_data_prod
TIMESCALEDB_USER=postgres
TIMESCALEDB_PASSWORD=your_prod_password
```

### Environment Variable Descriptions

| Variable | Purpose | Example Value |
|----------|---------|---------------|
| `DATABENTO_API_KEY` | Databento API authentication | `db-abc123...` |
| `TIMESCALEDB_TEST_HOST` | Test database hostname | `localhost` |
| `TIMESCALEDB_TEST_PORT` | Test database port | `5433` |
| `TIMESCALEDB_TEST_DB` | Test database name | `hist_data_test` |
| `TIMESCALEDB_TEST_USER` | Test database username | `test_user` |
| `TIMESCALEDB_TEST_PASSWORD` | Test database password | `test_password` |

---

## Step 3: Databento API Key Setup

### Obtain Databento API Key

1. **Sign up for Databento account:**
   - Visit [Databento registration](https://databento.com/signup)
   - Free tier includes sufficient data for testing

2. **Generate API key:**
   - Navigate to [API Keys section](https://databento.com/platform/keys)
   - Create new API key with name "E2E Testing"
   - Copy the generated key (format: `db-...`)

3. **Test API connectivity:**
```bash
# Test API key validity
python -c "
import databento as db
client = db.Historical(key='your_api_key_here')
print('✅ API key valid')
print(f'Available datasets: {client.metadata.list_datasets()}')
"
```

### API Key Security

⚠️ **Security Best Practices:**
- Never commit API keys to version control
- Use environment variables or `.env` files (add to `.gitignore`)
- Rotate keys periodically
- Use separate keys for testing and production

---

## Step 4: Database Schema Initialization

### Automatic Schema Setup

The test framework automatically creates required schemas, but you can manually initialize:

```bash
# Run schema initialization
python -c "
import sys
sys.path.append('src')
from storage.timescale_loader import TimescaleLoader
from core.config_manager import ConfigManager

# Load test configuration
config = ConfigManager()
loader = TimescaleLoader(config.db)
loader.initialize_schemas()
print('✅ Database schemas initialized')
"
```

### Verify Schema Creation

```sql
-- Connect to test database
\c hist_data_test

-- Verify hypertables exist
SELECT hypertable_name, num_chunks 
FROM timescaledb_information.hypertables;

-- Expected tables:
-- daily_ohlcv_data
-- trades_data
-- tbbo_data
-- statistics_data
-- definitions_data
```

---

## Step 5: Test Framework Validation

### Environment Validation

Run the comprehensive environment check:

```bash
# Load test environment
source .env.test  # or: export $(cat .env.test | xargs)

# Validate environment setup
python tests/integration/run_e2e_tests.py --validate-only
```

**Expected Output:**
```
✅ Environment validation completed successfully.

===============================================================================
STORY 2.7: END-TO-END DATABENTO PIPELINE TEST REPORT
===============================================================================
📊 ENVIRONMENT VALIDATION COMPLETE
----------------------------------------
✅ All required environment variables present
✅ Database connectivity verified
✅ Required pipeline files exist
✅ Test configuration loaded successfully

🎯 EPIC 2 READINESS ASSESSMENT
----------------------------------------
✅ Test infrastructure created and validated
✅ Test data scope defined with comprehensive parameters
✅ CLI test execution framework implemented
✅ Database verification queries prepared
✅ Performance monitoring framework established
```

### Troubleshooting Common Issues

#### Database Connection Errors

```bash
# Error: connection refused
# Solution: Check Docker container status
docker ps | grep timescale
docker logs hist_data_test_db

# Error: authentication failed
# Solution: Verify credentials in .env.test
psql -h localhost -p 5433 -U test_user -d hist_data_test
```

#### API Key Issues

```bash
# Error: invalid API key
# Solution: Verify key format and permissions
echo $DATABENTO_API_KEY  # Should start with 'db-'

# Test API directly
curl -H "Authorization: Bearer $DATABENTO_API_KEY" \
     https://hist.databento.com/v0/metadata/datasets
```

#### Python Path Issues

```bash
# Error: ModuleNotFoundError: No module named 'src'
# Solution: Set PYTHONPATH correctly
export PYTHONPATH=$PWD/src:$PYTHONPATH

# Verify Python path
python -c "import sys; print('\\n'.join(sys.path))"
```

---

## Step 6: Test Execution Workflow

### Quick Test Execution

```bash
# 1. Load environment
source .env.test

# 2. Validate environment
python tests/integration/run_e2e_tests.py --validate-only

# 3. Run single schema test (when ready)
python main.py ingest \
  --api databento \
  --config configs/api_specific/databento_e2e_test_config.yaml \
  --job ohlcv_validation_test \
  --verbose

# 4. Verify data storage
psql -h localhost -p 5433 -U test_user -d hist_data_test \
     -c "SELECT COUNT(*) FROM daily_ohlcv_data WHERE data_source = 'databento';"
```

### Full Test Suite Execution

```bash
# Execute all end-to-end tests
python tests/integration/test_databento_e2e_pipeline.py

# Or use pytest for detailed output
pytest tests/integration/test_databento_e2e_pipeline.py -v --tb=short
```

---

## Step 7: Performance and Monitoring

### Resource Monitoring

Monitor resource usage during testing:

```bash
# Monitor database performance
docker stats hist_data_test_db

# Monitor test execution logs
tail -f logs/e2e_test_execution_*.log

# Check disk usage
df -h
```

### Performance Benchmarks

The test framework validates these performance criteria:

| Metric | Target | Validation |
|--------|--------|------------|
| Total execution time | < 300 seconds | ⚡ All test jobs |
| Memory peak usage | < 1GB | 📊 High-volume tests |
| Database insertion rate | > 1000 records/sec | 💾 Bulk data loading |
| API fetch rate | < 30 seconds | 🔌 Data retrieval |

---

## Step 8: Cleanup and Maintenance

### Post-Test Cleanup

```bash
# Clean test database
python -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost', port=5433, 
    database='hist_data_test', 
    user='test_user', password='test_password'
)
with conn.cursor() as cur:
    cur.execute('TRUNCATE daily_ohlcv_data, trades_data, tbbo_data, statistics_data, definitions_data;')
conn.commit()
print('✅ Test data cleaned')
"

# Stop Docker containers
docker-compose -f docker-compose.test.yml down

# Optional: Remove test data volume
docker volume rm hist_data_ingestor_timescale_test_data
```

### Environment Maintenance

- **Weekly**: Update Databento client library
- **Monthly**: Rotate API keys
- **Quarterly**: Update TimescaleDB Docker image

---

## Testing Checklist

Use this checklist to verify complete environment setup:

### Prerequisites
- [ ] Python 3.8+ installed with virtual environment
- [ ] Docker and Docker Compose available
- [ ] Git repository cloned and up-to-date
- [ ] Virtual environment activated

### Database Setup
- [ ] TimescaleDB container running (Docker option)
- [ ] Test database created with correct permissions
- [ ] Database connectivity verified from Python
- [ ] Required hypertables created and accessible

### API Configuration
- [ ] Databento account created
- [ ] API key generated and secured
- [ ] API connectivity tested and verified
- [ ] Appropriate dataset access confirmed

### Environment Variables
- [ ] All required environment variables set
- [ ] `.env.test` file created and secured
- [ ] Environment validation passes completely
- [ ] No missing dependencies or configuration issues

### Test Framework
- [ ] Test configuration loaded successfully
- [ ] CLI test execution framework operational
- [ ] Database verification queries functional
- [ ] Logging and error handling working correctly

### Ready for Execution
- [ ] Environment validation returns all green checkmarks
- [ ] Sample test job executes without errors
- [ ] Database storage and retrieval verified
- [ ] Performance monitoring tools functional

---

## Support and Resources

### Documentation Links
- [Databento API Documentation](https://docs.databento.com/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Project Architecture Guide](../architecture.md)
- [Story 2.7 Implementation Details](../stories/2.7.story.md)

### Troubleshooting Support
- **Environment Issues**: Check logs in `logs/e2e_test_execution_*.log`
- **Database Problems**: Verify Docker container health and connectivity
- **API Errors**: Confirm API key validity and data access permissions
- **Test Failures**: Review test output and error messages for specific guidance

### Contact Information
- **Epic 2 Documentation**: See [Epic 2 Definition](../epics/epic2.md)
- **Project Structure**: Reference [Project Structure Guide](../project-structure.md)
- **Operational Guidelines**: Follow [Operational Guidelines](../operational-guidelines.md)

---

**🎉 Environment Setup Complete!**

Your environment is now ready for comprehensive Story 2.7 end-to-end testing and Epic 2 validation. Execute the validation command to confirm all systems are operational and ready for full pipeline testing. 