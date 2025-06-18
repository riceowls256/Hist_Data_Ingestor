# Core Module

The core module provides the foundational framework for the Historical Data Ingestor, including configuration management, pipeline orchestration, and centralized logging. This module serves as the backbone for all other system components.

## Components

### Configuration Manager (`config_manager.py`)

Centralized configuration management using Pydantic v2 BaseSettings with environment variable support.

**Key Features:**
- **Environment Variable Integration**: Automatic loading from `.env` files and system environment
- **Type Validation**: Pydantic models ensure configuration type safety and validation
- **Nested Configuration**: Support for complex configuration hierarchies
- **Environment Overrides**: Development, staging, and production configurations

**Usage:**
```python
from src.core.config_manager import get_config

# Load system configuration
config = get_config()

# Access database settings
db_config = config.database
print(f"Database Host: {db_config.host}")
print(f"Database Port: {db_config.port}")

# Access API configurations
databento_config = config.get_api_config("databento")
print(f"Databento Dataset: {databento_config.dataset}")
```

**Configuration Classes:**
- `DatabaseConfig`: TimescaleDB connection and performance settings
- `LoggingConfig`: Log levels, file rotation, and output formats
- `DatabentoConfig`: API authentication and dataset configurations
- `SystemConfig`: Overall system settings and feature flags

### Pipeline Orchestrator (`pipeline_orchestrator.py`)

Coordinates data ingestion workflows, managing the flow from API extraction through transformation to storage.

**Key Features:**
- **Job Management**: Execute and monitor data ingestion jobs
- **Error Handling**: Comprehensive error boundaries with retry logic
- **Progress Tracking**: Real-time progress monitoring with Rich progress bars
- **Resource Management**: Efficient memory and connection pool management
- **Validation Integration**: Seamless integration with data validation pipeline

**Usage:**
```python
from src.core.pipeline_orchestrator import PipelineOrchestrator
from datetime import date

# Initialize orchestrator
orchestrator = PipelineOrchestrator()

# Execute a data ingestion job
job_config = {
    "name": "daily_ohlcv_ingestion",
    "api": "databento",
    "dataset": "GLBX.MDP3",
    "schema": "ohlcv-1d",
    "symbols": ["ES.c.0", "NQ.c.0"],
    "start_date": date(2024, 1, 1),
    "end_date": date(2024, 1, 31)
}

result = orchestrator.execute_job(job_config)
print(f"Ingested {result.records_processed} records")
```

**Workflow Stages:**
1. **Job Validation**: Verify job configuration and dependencies
2. **API Extraction**: Fetch data from configured API endpoints
3. **Data Transformation**: Apply mapping rules and data normalization
4. **Validation**: Validate data against schemas with quarantine handling
5. **Storage**: Persist validated data to TimescaleDB
6. **Cleanup**: Resource cleanup and progress reporting

### Logging Framework (`logging.py`)

Centralized logging system using structlog for structured, JSON-formatted logs with human-readable console output.

**Key Features:**
- **Structured Logging**: JSON-formatted file logs for machine parsing
- **Pretty Console Output**: Human-readable console logs with colors and formatting
- **Log Rotation**: Automatic file rotation (5MB files, 3 backups retained)
- **Contextual Logging**: Request IDs, job IDs, and execution context tracking
- **Multiple Handlers**: Console and file handlers with different formatters

**Usage:**
```python
from src.utils.custom_logger import get_logger

# Get module-specific logger
logger = get_logger(__name__)

# Basic logging
logger.info("Starting data ingestion job")
logger.warning("API rate limit approaching", remaining_calls=100)
logger.error("Database connection failed", error_code="DB_CONN_TIMEOUT")

# Contextual logging
logger.info(
    "Job completed successfully",
    job_id="job_123",
    records_processed=15000,
    duration_seconds=45.2,
    symbols=["ES.c.0", "NQ.c.0"]
)
```

**Log Output Locations:**
- **File Logs**: `logs/app.log` (JSON format, machine-readable)
- **Console Logs**: Pretty-printed with colors and structured formatting
- **Test Logs**: Separate test execution logs in `logs/test_*.log`

## Configuration Examples

### Database Configuration
```python
# In configs/system_config.yaml
database:
  host: localhost
  port: 5432
  database: hist_data
  user: ${POSTGRES_USER}
  password: ${POSTGRES_PASSWORD}
  connection_pool_size: 10
  max_overflow: 20
  echo_queries: false
```

### API Configuration
```python
# In configs/api_specific/databento_config.yaml
api:
  key_env_var: "DATABENTO_API_KEY"
  base_url: "https://hist.databento.com"
  timeout: 30
  retry_policy:
    max_retries: 3
    base_delay: 1.0
    max_delay: 60.0
    backoff_multiplier: 2.0
```

### Logging Configuration
```python
# In configs/system_config.yaml
logging:
  level: INFO
  console_output: true
  file_output: true
  file_max_bytes: 5242880  # 5MB
  backup_count: 3
  json_file_format: true
```

## Error Handling

The core module implements comprehensive error handling patterns:

**Configuration Errors:**
- Missing environment variables with helpful error messages
- Invalid configuration values with validation details
- Configuration file parsing errors with line numbers

**Runtime Errors:**
- Database connection failures with retry logic
- API authentication errors with clear remediation steps
- Resource exhaustion errors with cleanup procedures

**Example Error Handling:**
```python
from src.core.config_manager import ConfigurationError
from src.core.pipeline_orchestrator import PipelineError

try:
    config = get_config()
    orchestrator = PipelineOrchestrator()
    result = orchestrator.execute_job(job_config)
except ConfigurationError as e:
    logger.error("Configuration error", error=str(e), config_file=e.config_file)
except PipelineError as e:
    logger.error("Pipeline execution failed", error=str(e), job_id=e.job_id)
```

## Extension Points

### Adding New API Adapters

1. **Create adapter class** inheriting from `BaseAPIAdapter`
2. **Register in configuration** under `configs/api_specific/`
3. **Update orchestrator** to handle new adapter type
4. **Add validation schemas** for new data formats

### Custom Transformation Rules

1. **Implement transformation function** following signature patterns
2. **Register in mapping configuration** under `src/transformation/mapping_configs/`
3. **Add validation rules** for transformed data
4. **Update orchestrator** pipeline configuration

### Additional Configuration Sources

1. **Extend BaseSettings** with new configuration classes
2. **Add environment variable** mappings
3. **Update configuration loading** logic in `config_manager.py`
4. **Add validation rules** for new configuration parameters

## Best Practices

### Configuration Management
- Use environment variables for secrets and environment-specific values
- Validate all configuration at startup to fail fast
- Document all configuration parameters with examples
- Use type hints and Pydantic models for validation

### Logging
- Use structured logging with consistent field names
- Include relevant context (job_id, symbol, timestamp)
- Log at appropriate levels (DEBUG for development, INFO for operations)
- Avoid logging sensitive information like API keys

### Error Handling
- Implement specific exception types for different error categories
- Include actionable information in error messages
- Use retry logic with exponential backoff for transient failures
- Log errors with sufficient context for debugging

### Performance
- Use connection pooling for database connections
- Implement proper resource cleanup in finally blocks
- Monitor memory usage during large data processing
- Use asynchronous operations where appropriate 