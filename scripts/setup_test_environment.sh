#!/bin/bash

# ================================================================================================
# End-to-End Testing Environment Setup Script
# Story 2.7: Test End-to-End Databento Data Ingestion and Storage
# ================================================================================================

set -euo pipefail  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/test_setup_$(date +%Y%m%d_%H%M%S).log"

# Ensure logs directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging functions
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}ℹ️  INFO: $1${NC}"
}

log_success() {
    log "${GREEN}✅ SUCCESS: $1${NC}"
}

log_warning() {
    log "${YELLOW}⚠️  WARNING: $1${NC}"
}

log_error() {
    log "${RED}❌ ERROR: $1${NC}"
}

# Help function
show_help() {
    cat << EOF
End-to-End Testing Environment Setup Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --help, -h          Show this help message
    --skip-docker       Skip Docker setup (use existing database)
    --skip-api-test     Skip API connectivity testing
    --api-key KEY       Specify Databento API key directly
    --force             Force reinstall/recreation of components
    --verbose, -v       Enable verbose output

EXAMPLES:
    $0                                    # Full setup with prompts
    $0 --api-key db-abc123...             # Setup with API key
    $0 --skip-docker --api-key db-abc123  # Use existing DB
    $0 --force                            # Force clean reinstall

ENVIRONMENT:
    Set these environment variables to skip prompts:
    - DATABENTO_API_KEY
    - SKIP_DOCKER_SETUP
    - FORCE_SETUP

EOF
}

# Parse command line arguments
SKIP_DOCKER=false
SKIP_API_TEST=false
API_KEY=""
FORCE_SETUP=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --skip-api-test)
            SKIP_API_TEST=true
            shift
            ;;
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --force)
            FORCE_SETUP=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Verbose mode setup
if [[ "$VERBOSE" == "true" ]]; then
    set -x
fi

log_info "Starting End-to-End Testing Environment Setup"
log_info "Project Root: $PROJECT_ROOT"
log_info "Log File: $LOG_FILE"

# ================================================================================================
# STEP 1: Prerequisites Check
# ================================================================================================

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    else
        python_version=$(python3 --version | cut -d' ' -f2)
        log_success "Python $python_version found"
    fi
    
    # Check Docker (if not skipping)
    if [[ "$SKIP_DOCKER" == "false" ]]; then
        if ! command -v docker &> /dev/null; then
            missing_tools+=("docker")
        else
            log_success "Docker found"
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            missing_tools+=("docker-compose")
        else
            log_success "Docker Compose found"
        fi
    fi
    
    # Check psql
    if ! command -v psql &> /dev/null; then
        log_warning "psql not found - will install via pip"
    else
        log_success "PostgreSQL client found"
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install missing tools and run again"
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

# ================================================================================================
# STEP 2: Virtual Environment Setup
# ================================================================================================

setup_virtual_environment() {
    log_info "Setting up Python virtual environment..."
    
    cd "$PROJECT_ROOT"
    
    # Check if venv exists and force recreation if requested
    if [[ -d "venv" && "$FORCE_SETUP" == "true" ]]; then
        log_warning "Force mode: Removing existing virtual environment"
        rm -rf venv
    fi
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        log_info "Creating new virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    if [[ -f "requirements.txt" ]]; then
        log_info "Installing Python dependencies..."
        pip install -r requirements.txt
    else
        log_warning "requirements.txt not found - installing minimal dependencies"
        pip install psycopg2-binary pydantic typer structlog tenacity databento
    fi
    
    log_success "Virtual environment setup complete"
}

# ================================================================================================
# STEP 3: Database Setup
# ================================================================================================

setup_database() {
    if [[ "$SKIP_DOCKER" == "true" ]]; then
        log_info "Skipping Docker setup (using existing database)"
        return 0
    fi
    
    log_info "Setting up test database with Docker..."
    
    cd "$PROJECT_ROOT"
    
    # Check if test database is already running
    if docker ps | grep -q "hist_data_test_db"; then
        if [[ "$FORCE_SETUP" == "true" ]]; then
            log_warning "Force mode: Stopping existing test database"
            docker-compose -f docker-compose.test.yml down
        else
            log_info "Test database already running"
            return 0
        fi
    fi
    
    # Start test database
    log_info "Starting TimescaleDB test container..."
    docker-compose -f docker-compose.test.yml up -d timescaledb-test
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    max_attempts=30
    attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if docker exec hist_data_test_db pg_isready -U test_user -d hist_data_test &> /dev/null; then
            log_success "Database is ready"
            break
        fi
        
        ((attempt++))
        log_info "Waiting for database... (attempt $attempt/$max_attempts)"
        sleep 2
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        log_error "Database failed to start within expected time"
        docker logs hist_data_test_db
        exit 1
    fi
    
    # Verify TimescaleDB extension
    log_info "Verifying TimescaleDB extension..."
    docker exec hist_data_test_db psql -U test_user -d hist_data_test -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
    
    log_success "Database setup complete"
}

# ================================================================================================
# STEP 4: Environment Variables Setup
# ================================================================================================

setup_environment_variables() {
    log_info "Setting up environment variables..."
    
    # Get API key
    if [[ -z "$API_KEY" ]]; then
        if [[ -n "${DATABENTO_API_KEY:-}" ]]; then
            API_KEY="$DATABENTO_API_KEY"
            log_info "Using API key from environment variable"
        else
            log_warning "Databento API key required for testing"
            echo -n "Enter your Databento API key (or press Enter to skip): "
            read -r API_KEY
            
            if [[ -z "$API_KEY" ]]; then
                log_warning "No API key provided - some tests will be skipped"
            fi
        fi
    fi
    
    # Create .env.test file
    local env_file="$PROJECT_ROOT/.env.test"
    
    if [[ -f "$env_file" && "$FORCE_SETUP" != "true" ]]; then
        log_info "Environment file already exists: $env_file"
    else
        log_info "Creating environment configuration file..."
        
        cat > "$env_file" << EOF
# End-to-End Testing Environment Configuration
# Generated by setup script on $(date)

# Databento API Configuration
DATABENTO_API_KEY=${API_KEY}

# Test Database Configuration
TIMESCALEDB_TEST_HOST=localhost
TIMESCALEDB_TEST_PORT=5433
TIMESCALEDB_TEST_DB=hist_data_test
TIMESCALEDB_TEST_USER=test_user
TIMESCALEDB_TEST_PASSWORD=test_password

# Test Execution Settings
PYTHONPATH=src
LOG_LEVEL=INFO
TEST_TIMEOUT=600

# Performance Testing
ENABLE_PERFORMANCE_TESTS=true
MAX_MEMORY_USAGE_MB=1024
EOF
        
        log_success "Environment file created: $env_file"
    fi
    
    # Load environment variables
    if [[ -f "$env_file" ]]; then
        source "$env_file"
        log_success "Environment variables loaded"
    fi
}

# ================================================================================================
# STEP 5: API Connectivity Test
# ================================================================================================

test_api_connectivity() {
    if [[ "$SKIP_API_TEST" == "true" || -z "${DATABENTO_API_KEY:-}" ]]; then
        log_info "Skipping API connectivity test"
        return 0
    fi
    
    log_info "Testing Databento API connectivity..."
    
    # Activate virtual environment if not already active
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        source "$PROJECT_ROOT/venv/bin/activate"
    fi
    
    # Test API connectivity
    python3 -c "
import databento as db
import sys

try:
    client = db.Historical(key='$DATABENTO_API_KEY')
    datasets = client.metadata.list_datasets()
    print('✅ API key valid')
    print(f'Available datasets: {len(datasets)}')
    
    # Check for GLBX.MDP3 dataset (required for tests)
    if 'GLBX.MDP3' in [d.dataset for d in datasets]:
        print('✅ GLBX.MDP3 dataset accessible')
    else:
        print('⚠️  GLBX.MDP3 dataset not found - some tests may fail')
        
except Exception as e:
    print(f'❌ API connectivity failed: {e}')
    sys.exit(1)
" || {
        log_error "API connectivity test failed"
        exit 1
    }
    
    log_success "API connectivity verified"
}

# ================================================================================================
# STEP 6: Test Framework Validation
# ================================================================================================

validate_test_framework() {
    log_info "Validating test framework..."
    
    cd "$PROJECT_ROOT"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Load environment variables
    if [[ -f ".env.test" ]]; then
        source .env.test
    fi
    
    # Run framework validation
    log_info "Running comprehensive environment validation..."
    python tests/integration/run_e2e_tests.py --validate-only || {
        log_error "Test framework validation failed"
        exit 1
    }
    
    log_success "Test framework validation complete"
}

# ================================================================================================
# STEP 7: Optional Quick Test
# ================================================================================================

run_quick_test() {
    if [[ -z "${DATABENTO_API_KEY:-}" ]]; then
        log_info "Skipping quick test (no API key)"
        return 0
    fi
    
    echo -n "Run a quick test to verify the pipeline? (y/N): "
    read -r run_test
    
    if [[ "$run_test" =~ ^[Yy]$ ]]; then
        log_info "Running quick pipeline test..."
        
        cd "$PROJECT_ROOT"
        source venv/bin/activate
        source .env.test
        
        # Run simple OHLCV test
        python main.py ingest \
            --api databento \
            --config configs/api_specific/databento_e2e_test_config.yaml \
            --job ohlcv_validation_test \
            --verbose || {
            log_warning "Quick test failed - check logs for details"
            return 1
        }
        
        log_success "Quick test completed successfully"
    fi
}

# ================================================================================================
# MAIN EXECUTION
# ================================================================================================

main() {
    log_info "=========================================="
    log_info "Story 2.7: E2E Test Environment Setup"
    log_info "=========================================="
    
    # Execute setup steps
    check_prerequisites
    setup_virtual_environment
    setup_database
    setup_environment_variables
    test_api_connectivity
    validate_test_framework
    run_quick_test
    
    # Final status and next steps
    log_success "=========================================="
    log_success "Environment Setup Complete!"
    log_success "=========================================="
    
    cat << EOF

🎉 Your end-to-end testing environment is ready!

NEXT STEPS:
1. Load the environment:
   source .env.test

2. Run framework validation:
   python tests/integration/run_e2e_tests.py --validate-only

3. Execute test suite:
   python tests/integration/test_databento_e2e_pipeline.py

4. Or run individual jobs:
   python main.py ingest --api databento --config configs/api_specific/databento_e2e_test_config.yaml --job ohlcv_validation_test

RESOURCES:
- Documentation: docs/testing/e2e-environment-setup.md
- Test Configuration: configs/api_specific/databento_e2e_test_config.yaml
- Setup Log: $LOG_FILE

TROUBLESHOOTING:
- Database: docker logs hist_data_test_db
- API Issues: Check your Databento API key and permissions
- Environment: source .env.test before running tests

Happy testing! 🚀

EOF
}

# Trap errors and cleanup
trap 'log_error "Setup failed at line $LINENO"' ERR

# Run main function
main "$@" 