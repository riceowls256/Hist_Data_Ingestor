# Hist_Data_Ingestor

A Python-based framework for ingesting, transforming, validating, and storing historical financial data from multiple APIs (e.g., Interactive Brokers, Databento) into TimescaleDB.

## Features
- Modular ETL pipeline
- API-agnostic adapters
- Configurable via YAML and environment variables
- Data validation and transformation
- CLI for ingestion and querying
- Dockerized for local development

## Quick Start
1. Clone the repository
2. Set up your `.env` file from `.env.example`
3. Build and start with Docker Compose:
   ```sh
   docker-compose up --build
   ```
4. Run the CLI for ingestion or querying

## Directory Structure
See `docs/architecture.md` and `docs/prd.md` for full details.

## Requirements
- Python 3.11+
- Docker & Docker Compose

## License
MIT
