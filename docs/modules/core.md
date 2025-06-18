# Core Module

The core module contains the foundational components and central services that are essential for the application's operation. It manages system-wide concerns like configuration, module loading, and pipeline orchestration.

## Overview

The primary goal of the core module is to provide a stable and flexible foundation for the entire system. It initializes and coordinates the other modules, ensuring that they have the necessary configuration and resources to function correctly.

## Key Components

### 1. `config_manager.py` - System Configuration Manager

This is the most critical component in the core module. The `ConfigManager` is responsible for loading, validating, and providing access to the system's configuration.

#### Features

-   **Centralized Configuration**: Loads settings from a single `configs/system_config.yaml` file.
-   **Environment Variable Overrides**: Seamlessly overrides YAML settings with environment variables. This is ideal for production deployments and CI/CD pipelines.
-   **Pydantic-Based Validation**: Uses Pydantic's `BaseSettings` to enforce data types and validate that all required settings are present at startup.
-   **Structured and Nested**: Configuration is organized into logical, nested Pydantic models (`DBConfig`, `LoggingConfig`, `APIConfig`).

#### Configuration Hierarchy

The `ConfigManager` loads configuration in a specific order of precedence:

1.  **Environment Variables** (Highest precedence)
2.  **Values from `system_config.yaml`**
3.  **Default values defined in the Pydantic models** (Lowest precedence)

#### Pydantic Settings Models

The configuration is structured using the following Pydantic models:

-   `DBConfig`: Manages all TimescaleDB connection settings.
-   `LoggingConfig`: Manages logging level and file path.
-   `APIConfig`: Holds API keys for external services like Databento.
-   `SystemConfig`: The top-level model that nests all other configuration models.

#### Usage Example

```python
# How to get the system configuration in any module
from src.core.config_manager import ConfigManager

# Initialize the manager and get the validated config object
config_manager = ConfigManager()
system_config = config_manager.get()

# Access nested configuration settings
db_host = system_config.db.host
api_key = system_config.api.databento_api_key
log_level = system_config.logging.level

print(f"Connecting to DB on host: {db_host}")
```

#### Environment Variable Overrides

To override a nested setting, use a double underscore `__` as the delimiter.

For example, to override the database host and the Databento API key, you would set the following environment variables:

```sh
export TIMESCALEDB_HOST=my-production-db.com
export DATABENTO_API_KEY=my-secret-production-key
```

The `ConfigManager` will automatically pick these up, overriding any values present in `system_config.yaml`.

#### Example `system_config.yaml`

```yaml
# configs/system_config.yaml

db:
  user: "db_user_placeholder"
  password: "db_password_placeholder" # Recommended to set via TIMESCALEDB_PASSWORD env var
  host: "db.example.com"
  port: 5432
  dbname: "hist_data_ingestor_db"

logging:
  level: "INFO"
  file: "logs/app.log"

api:
  ib_api_key: "ib_key_placeholder"           # Recommended to set via IB_API_KEY env var
  databento_api_key: "databento_key_placeholder" # Recommended to set via DATABENTO_API_KEY env var
```

### 2. `module_loader.py` (Placeholder)

This component is reserved for a future dynamic module loading system. It could be used to load adapters or plugins without changing the core codebase.

### 3. `pipeline_orchestrator.py` (Placeholder)

This component is reserved for the main pipeline orchestration logic. It will be responsible for initializing the ingestion, transformation, and storage modules and running data processing jobs. 