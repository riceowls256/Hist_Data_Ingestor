# Configuration Files Documentation

This directory contains all configuration files for the Hist_Data_Ingestor application. The configuration system is designed to be modular, with separate files for different aspects of the system.

## Directory Structure

```
configs/
├── README.md                    # This file
├── system_config.yaml          # System-wide configuration
├── api_specific/               # API-specific configurations
│   ├── databento_config.yaml   # Databento API configuration
│   └── interactive_brokers_config.yaml  # Interactive Brokers configuration (future)
└── validation_schemas/         # Data validation schemas
    ├── databento_ohlcv_schema.yaml
    ├── databento_trades_schema.yaml
    ├── databento_tbbo_schema.yaml
    └── databento_statistics_schema.yaml
```

## System Configuration (`system_config.yaml`)

Contains system-wide settings such as:
- Database connection parameters
- Logging configuration
- Default retry policies
- Performance settings

## API-Specific Configurations

### Databento Configuration (`api_specific/databento_config.yaml`)

The Databento configuration file defines how to connect to and extract data from the Databento API. It includes the following main sections:

#### API Authentication
```yaml
api:
  key_env_var: "DATABENTO_API_KEY"  # Environment variable containing API key
  base_url: "https://hist.databento.com"  # API base URL
  timeout: 30  # Request timeout in seconds
```

#### Job Definitions
Each job defines a specific data extraction task:

```yaml
jobs:
  - name: "ohlcv_1d"              # Unique job identifier
    dataset: "GLBX.MDP3"          # Databento dataset ID
    schema: "ohlcv-1d"            # Data schema type
    symbols: ["CL.FUT", "ES.FUT"] # List of symbols to extract
    stype_in: "continuous"        # Symbol type (continuous, native, etc.)
    start_date: "2023-01-01"      # Start date (YYYY-MM-DD)
    end_date: "2024-01-01"        # End date (YYYY-MM-DD)
    date_chunk_interval_days: 365 # Days per processing chunk
```

#### Supported Databento Schemas

The configuration supports the following data schemas:

**OHLCV (Open, High, Low, Close, Volume) Data:**
- `ohlcv-1s` - 1-second bars
- `ohlcv-1m` - 1-minute bars
- `ohlcv-5m` - 5-minute bars
- `ohlcv-15m` - 15-minute bars
- `ohlcv-1h` - 1-hour bars
- `ohlcv-1d` - 1-day bars

**Market Data:**
- `trades` - Individual trade records
- `tbbo` - Top of Book Bid/Offer quotes
- `statistics` - Market statistics and derived data

#### Symbol Configuration

**Futures Symbols (CME Globex - GLBX.MDP3):**
- `CL.FUT` - Crude Oil futures
- `ES.FUT` - E-mini S&P 500 futures
- `NG.FUT` - Natural Gas futures
- `HO.FUT` - Heating Oil futures
- `RB.FUT` - RBOB Gasoline futures

**Equity Symbols (NASDAQ - XNAS.ITCH):**
- `SPY` - SPDR S&P 500 ETF

#### Symbol Types (`stype_in`)
- `continuous` - Use continuous contract series (recommended for futures)
- `native` - Use native exchange symbols (recommended for equities)

#### Date Chunking Strategy

Different schemas use different chunking strategies based on data volume:
- **1-second data**: 7-day chunks (high volume)
- **Minute data**: 30-day chunks (medium volume)
- **Hourly/Daily data**: 90-365 day chunks (lower volume)
- **Trades/TBBO**: 1-day chunks (very high volume)

#### Retry Policy Configuration

```yaml
retry_policy:
  max_retries: 3                    # Maximum retry attempts
  base_delay: 1.0                   # Initial delay between retries (seconds)
  max_delay: 60.0                   # Maximum delay between retries (seconds)
  backoff_multiplier: 2.0           # Exponential backoff multiplier
  retry_on_status_codes: [429, 500, 502, 503, 504]  # HTTP codes to retry
  respect_retry_after: true         # Honor Retry-After headers
```

#### Transformation and Validation References

```yaml
transformation:
  mapping_config_path: "src/transformation/mapping_configs/databento_mappings.yaml"
  enable_price_scaling: true
  enable_timestamp_conversion: true
  enable_symbol_normalization: true

validation:
  validation_schema_paths:
    - "configs/validation_schemas/databento_ohlcv_schema.yaml"
    - "configs/validation_schemas/databento_trades_schema.yaml"
    - "configs/validation_schemas/databento_tbbo_schema.yaml"
    - "configs/validation_schemas/databento_statistics_schema.yaml"
  strict_validation: true
  quarantine_invalid_records: true
```

## Environment Variables

The following environment variables must be set:

### Required
- `DATABENTO_API_KEY` - Your Databento API key

### Optional
- `TIMESCALEDB_HOST` - TimescaleDB host (default: localhost)
- `TIMESCALEDB_PORT` - TimescaleDB port (default: 5432)
- `TIMESCALEDB_USER` - Database username
- `TIMESCALEDB_PASSWORD` - Database password
- `TIMESCALEDB_DBNAME` - Database name

## Adding New API Configurations

To add a new API configuration:

1. **Create API-specific config file**: `configs/api_specific/{api_name}_config.yaml`

2. **Follow the standard structure**:
   ```yaml
   api:
     # Authentication configuration
   
   jobs:
     # Job definitions
   
   retry_policy:
     # Retry configuration
   
   transformation:
     # Transformation settings
   
   validation:
     # Validation settings
   ```

3. **Create corresponding validation schemas**: Add schema files to `configs/validation_schemas/`

4. **Update this README**: Document the new API configuration structure and parameters

5. **Create mapping configuration**: Add transformation mappings to `src/transformation/mapping_configs/`

## Configuration Validation

All configuration files should be validated before use:

1. **YAML syntax validation**: Ensure proper YAML formatting
2. **Schema validation**: Validate against Pydantic models
3. **Reference validation**: Ensure all referenced files exist
4. **Environment variable validation**: Verify required environment variables are set

## Best Practices

1. **Security**: Never hardcode API keys or sensitive data in configuration files
2. **Environment Variables**: Use environment variables for all secrets and environment-specific settings
3. **Documentation**: Comment complex configurations and provide examples
4. **Validation**: Always validate configurations before deployment
5. **Versioning**: Version control all configuration files
6. **Testing**: Test configurations with small datasets before full deployment

## Troubleshooting

### Common Issues

1. **Invalid YAML syntax**: Use a YAML validator to check syntax
2. **Missing environment variables**: Ensure all required environment variables are set
3. **Invalid date formats**: Use YYYY-MM-DD format for dates
4. **Symbol not found**: Verify symbols exist in the specified dataset
5. **Schema not supported**: Check Databento documentation for supported schemas

### Validation Commands

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('configs/api_specific/databento_config.yaml'))"

# Test configuration loading
python -m src.core.config_manager --validate-config configs/api_specific/databento_config.yaml
```

## Support

For configuration-related issues:
1. Check this documentation
2. Validate YAML syntax and structure
3. Verify environment variables are set correctly
4. Consult API-specific documentation (e.g., Databento docs)
5. Check application logs for detailed error messages 