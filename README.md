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
To run a CLI command inside the app container:
```sh
docker-compose exec app python -m src.cli ingest --api databento
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