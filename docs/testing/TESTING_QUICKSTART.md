# 🚀 Testing Quick Start Guide

**Story 2.7: End-to-End Databento Pipeline Testing**

Get your testing environment up and running in under 5 minutes!

## TL;DR - One Command Setup

```bash
# Run the automated setup script
./scripts/setup_test_environment.sh
```

This script will:
- ✅ Check prerequisites (Python, Docker)
- ✅ Set up virtual environment
- ✅ Start test database with Docker
- ✅ Configure environment variables
- ✅ Test API connectivity
- ✅ Validate test framework

---

## Prerequisites (2 minutes)

**Required:**
- Python 3.8+
- Docker & Docker Compose
- Git (already have this!)

**Install on macOS:**
```bash
# Install Docker Desktop from https://docker.com/products/docker-desktop
# Or via Homebrew:
brew install --cask docker
```

**Install on Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-venv docker.io docker-compose
```

---

## Quick Setup Options

### Option 1: Fully Automated (Recommended)
```bash
# Full setup with API key prompt
./scripts/setup_test_environment.sh

# Or provide API key directly
./scripts/setup_test_environment.sh --api-key db-your-key-here
```

### Option 2: Manual Steps (3 minutes)
```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Start test database
docker-compose -f docker-compose.test.yml up -d

# 3. Create environment file
cat > .env.test << EOF
DATABENTO_API_KEY=your_api_key_here
TIMESCALEDB_TEST_HOST=localhost
TIMESCALEDB_TEST_PORT=5433
TIMESCALEDB_TEST_DB=hist_data_test
TIMESCALEDB_TEST_USER=test_user
TIMESCALEDB_TEST_PASSWORD=test_password
PYTHONPATH=src
LOG_LEVEL=INFO
EOF

# 4. Load environment and validate
source .env.test
python tests/integration/run_e2e_tests.py --validate-only
```

---

## Get Your Databento API Key (Free!)

1. **Sign up:** [https://databento.com/signup](https://databento.com/signup)
2. **Generate key:** [https://databento.com/platform/keys](https://databento.com/platform/keys)
3. **Copy key:** Format: `db-abc123...`

The free tier includes enough data for all testing needs!

---

## Verification (30 seconds)

After setup, verify everything works:

```bash
# Load test environment
source .env.test

# Validate framework
python tests/integration/run_e2e_tests.py --validate-only

# Expected output:
# ✅ Environment validation completed successfully.
# ✅ All required environment variables present
# ✅ Database connectivity verified
# ✅ Test configuration loaded successfully
```

---

## Run Your First Test

```bash
# Execute single test job
python main.py ingest \
  --api databento \
  --config configs/api_specific/databento_e2e_test_config.yaml \
  --job ohlcv_validation_test \
  --verbose

# Or run full test suite
python tests/integration/test_databento_e2e_pipeline.py
```

---

## Common Issues & Quick Fixes

### "Docker not found"
```bash
# Install Docker Desktop: https://docker.com/products/docker-desktop
# Start Docker Desktop application
```

### "Database connection refused"
```bash
# Check Docker container status
docker ps | grep timescale

# Restart if needed
docker-compose -f docker-compose.test.yml restart
```

### "Module not found" errors
```bash
# Ensure virtual environment is active
source venv/bin/activate

# Ensure Python path is set
export PYTHONPATH=src
```

### "Invalid API key"
```bash
# Verify key format (should start with 'db-')
echo $DATABENTO_API_KEY

# Test key directly
python -c "import databento; databento.Historical(key='$DATABENTO_API_KEY')"
```

---

## Available Test Jobs

| Job Name | Purpose | Data Volume | Duration |
|----------|---------|-------------|----------|
| `ohlcv_validation_test` | Basic OHLCV data validation | ~25 records | 10s |
| `trades_high_volume_test` | High-volume trades processing | 250K+ records | 60s |
| `comprehensive_schema_test` | All 5 schemas end-to-end | 400K+ records | 120s |
| `performance_benchmark_test` | Pipeline performance validation | 500K+ records | 180s |

---

## Help & Resources

- **Detailed Setup:** [docs/testing/e2e-environment-setup.md](docs/testing/e2e-environment-setup.md)
- **Story Details:** [docs/stories/2.7.story.md](docs/stories/2.7.story.md)
- **Test Configuration:** [configs/api_specific/databento_e2e_test_config.yaml](configs/api_specific/databento_e2e_test_config.yaml)

## Support Commands

```bash
# Get help with setup script
./scripts/setup_test_environment.sh --help

# Check container logs
docker logs hist_data_test_db

# View test execution logs
tail -f logs/e2e_test_execution_*.log

# Clean up everything
docker-compose -f docker-compose.test.yml down
rm -rf venv .env.test
```

---

**🎯 Ready to test Epic 2 completion!** Your environment is now configured for comprehensive end-to-end validation of the entire Databento data ingestion pipeline. 