## Getting Started

### Local Development Setup (Recommended for frequent CLI usage)

**Prerequisites:**
- **Python 3.11+** with pip
- **TimescaleDB** running locally or accessible remotely
- **Virtual environment** (recommended)

**Setup:**
1. **Clone and set up the project:**
   ```sh
   git clone https://github.com/riceowls256/Hist_Data_Ingestor.git
   cd Hist_Data_Ingestor
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```sh
   # Copy and edit environment file
   cp .env.example .env
   
   # Or export directly for quick setup
   export POSTGRES_USER=your_user
   export POSTGRES_PASSWORD=your_password
   export POSTGRES_HOST=localhost
   export POSTGRES_PORT=5432
   export POSTGRES_DB=your_database
   export DATABENTO_API_KEY=your_api_key  # For data ingestion
   ```

3. **Test the setup:**
   ```sh
   python main.py --help
   python main.py status  # Check database connectivity
   ```

4. **Start querying:**
   ```sh
   python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31
   ```

**Pro Tip:** Create an alias for even easier access:
```sh
# Add to your ~/.bashrc or ~/.zshrc
alias hdq="python /path/to/hist_data_ingestor/main.py query"

# Then you can simply run:
hdq -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31
```

## Getting Started (Docker)

### Prerequisites
- **Docker** (https://docs.docker.com/get-docker/)
- **Docker Compose** (https://docs.docker.com/compose/)

### Configuration
1. **Clone the repository:**
   ```sh
   git clone https://github.com/riceowls256/Hist_Data_Ingestor.git
   cd Hist_Data_Ingestor
   ```
2. **Set up environment variables:**
   - Copy the example file and fill in your secrets:
     ```sh
     cp .env.example .env
     ```
   - Edit `.env` with your API keys and database credentials.

### Running the Application
```sh
docker-compose up --build -d
```
- The app will be available on port 8000 (or as configured).
- TimescaleDB will be available on port 5432.

### Using the CLI

#### Data Ingestion
To run data ingestion inside the app container:
```sh
docker-compose exec app python -m src.cli ingest --api databento
```

#### Querying Historical Data
The CLI provides powerful querying capabilities for historical financial data.

**Local Development (Recommended for frequent querying):**
```sh
# Set up your environment variables first
export POSTGRES_USER=your_user
export POSTGRES_PASSWORD=your_password
export POSTGRES_HOST=localhost  # or your TimescaleDB host
export POSTGRES_PORT=5432
export POSTGRES_DB=your_database

# Query daily OHLCV data for ES futures
python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31

# Query multiple symbols with CSV output
python main.py query --symbols ES.c.0,NQ.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --output-format csv

# Query trades data with JSON output to file
python main.py query -s ES.c.0 --schema trades --start-date 2024-01-01 --end-date 2024-01-01 --output-file trades.json --output-format json

# Query with result limit
python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --limit 100
```

**Docker Environment (for isolated/production use):**
```sh
# Query daily OHLCV data for ES futures
docker-compose exec app python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31

# Query multiple symbols with CSV output
docker-compose exec app python main.py query --symbols ES.c.0,NQ.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --output-format csv
```

**Query Command Options:**
- `--symbols, -s`: Security symbols (comma-separated or multiple flags)
- `--start-date, -sd`: Start date (YYYY-MM-DD format)
- `--end-date, -ed`: End date (YYYY-MM-DD format)
- `--schema`: Data schema (ohlcv-1d, trades, tbbo, statistics, definitions)
- `--output-format, -f`: Output format (table, csv, json)
- `--output-file, -o`: Output file path (optional)
- `--limit`: Limit number of results (optional)

**Supported Schemas:**
- `ohlcv-1d`: Daily OHLCV data (default)
- `trades`: Individual trade records
- `tbbo`: Top of book bid/offer data
- `statistics`: Market statistics
- `definitions`: Symbol definitions

**Output Formats:**
- `table`: Rich formatted table for console viewing (default)
- `csv`: Comma-separated values
- `json`: JSON format with proper datetime/decimal serialization

**Symbol Input Flexibility:**
```sh
# Comma-separated symbols
python main.py query --symbols ES.c.0,NQ.c.0,CL.c.0 --start-date 2024-01-01 --end-date 2024-01-31

# Multiple symbol flags
python main.py query -s ES.c.0 -s NQ.c.0 -s CL.c.0 --start-date 2024-01-01 --end-date 2024-01-31
```

**File Output Examples:**
```sh
# Save CSV to file (local development)
python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --output-format csv --output-file data.csv

# Save JSON to file (local development)
python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --output-format json --output-file data.json

# Docker environment file output
docker-compose exec app python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --output-format csv --output-file /app/data.csv
```

**Error Handling:**
The query command provides helpful error messages and suggestions:
- Invalid symbols show available symbol suggestions
- Date format validation with clear error messages
- Database connection issues with troubleshooting hints
- Large query warnings with confirmation prompts

For more query options and examples, run:
```sh
docker-compose exec app python main.py query --help
```

### Stopping the Environment
To stop and remove all containers:
```sh
docker-compose down
```

### (Optional) pgAdmin
- To enable pgAdmin, uncomment the `pgadmin` service in `docker-compose.yml` and set the credentials in `.env`.
- Access pgAdmin at [http://localhost:5050](http://localhost:5050).

## Centralized Logging Framework

This project uses a centralized logging setup powered by [structlog](https://www.structlog.org/) and Python's standard logging module.

- **Console logs** are human-readable (pretty-printed).
- **File logs** (`logs/app.log`) are JSON-formatted for easy parsing and analysis.
- **Log rotation** is enabled: each log file is up to 5MB, with 3 backups kept.
- **Log level** is configurable via the `logging.level` key in `configs/system_config.yaml` or by setting the `LOG_LEVEL` environment variable. Default is `INFO`.

### Usage
- All modules should use the logger via:
  ```python
  from src.utils.custom_logger import get_logger
  logger = get_logger(__name__)
  logger.info("Message")
  ```
- The logging system is initialized at application startup with `setup_logging()`.

### Troubleshooting
- If you do not see log files, ensure the `logs/` directory exists and is writable.
- If console logs do not appear, check your terminal settings and log level configuration.
- For permission errors, verify that your user has write access to the `logs/` directory.

### Advanced
- File logs are in JSON format, suitable for ingestion by log management tools.
- Console logs are pretty-printed for developer readability.
- The logging setup can be extended to support additional handlers or formats as needed. 