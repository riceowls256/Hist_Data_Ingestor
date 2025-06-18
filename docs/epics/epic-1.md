# Epic 1: Foundational Setup & Core Framework

> This document is a granulated shard from the main "Hist_Data_Ingestor Product Requirements Document (PRD)" focusing on "Epic 1: Foundational Setup & Core Framework".

**Goal**: Establish the initial project structure, core configuration loading, basic logging, Docker environment, and foundational TimescaleDB setup. This epic lays the groundwork for all subsequent development.

**Stories**:
**Story 1.1: Initialize Project Repository and Directory Structure**
**Story Statement**: As a Developer, I want to initialize a Git repository (on GitHub) and create the recommended baseline project directory structure (including configs/, src/, tests/, docs/, .env.example, requirements.txt, README.md), so that the project has a clean, organized foundation compliant with best practices and the research document.
**Acceptance Criteria (ACs)**:
AC1: GitHub Repository Created: A new private Git repository named Hist_Data_Ingestor (or a user-confirmed name) is created on GitHub.
AC2: Repository Cloned Locally: The GitHub repository is successfully cloned to the local development environment.
AC3: Core Directory Structure Established: The following top-level directories are created within the local repository: configs/, src/, tests/, docs/.
AC4: Initial Core Files Created: The following files are created at the root of the repository: .gitignore (with common Python and OS-specific ignores, plus .env), README.md (with placeholder title and brief project description), requirements.txt (initially empty or with essential linters/formatters like black, flake8, pydantic), .env.example (with placeholders for TIMESCALEDB_USER, TIMESCALEDB_PASSWORD, TIMESCALEDB_HOST, TIMESCALEDB_PORT, TIMESCALEDB_DBNAME, DATABENTO_API_KEY).
AC5: Sub-directory Structure (Basic): configs/ contains system_config.yaml (placeholder) and api_specific/. src/ contains an empty __init__.py and subdirectories: core/, ingestion/, transformation/, storage/, querying/, utils/ (each with an empty __init__.py). tests/ contains an empty __init__.py and subdirectories: unit/, integration/ (each with an empty __init__.py). docs/ is initially empty or contains placeholders.
AC6: Initial Commit and Push: All created directories and files (excluding gitignored) are committed with a meaningful initial commit message and pushed to the remote GitHub repository.

**Story 1.2: Implement Core Configuration Management for System Settings**
**Story Statement**: As a Developer, I want a core configuration management system that can load system-level settings (e.g., database connection details from environment variables, logging level) from a configs/system_config.yaml file and environment variables, so that basic application parameters are centrally managed and easily accessible.
**Acceptance Criteria (ACs)**:
AC1: ConfigManager Class Created: A Python class (e.g., ConfigManager) is created within src/core/.
AC2: Load system_config.yaml: ConfigManager successfully loads and parses settings from configs/system_config.yaml (initially with placeholders like default logging level).
AC3: Environment Variable Overrides & Secrets Handling: ConfigManager securely accesses and prioritizes environment variables for settings like database credentials and API keys over system_config.yaml. Sensitive secrets are loaded exclusively from environment variables.
AC4: Configuration Accessibility: Loaded configuration values are easily accessible via an instance of ConfigManager.
AC5: Basic Error Handling: ConfigManager raises clear errors if system_config.yaml is missing or malformed.
AC6: Unit Tests for ConfigManager: Basic unit tests verify loading from YAML, environment variable overrides for secrets, and error handling.

**Story 1.3: Establish Dockerized Development Environment**
**Story Statement**: As a Developer, I want a Dockerfile for the Python application and a docker-compose.yml file to orchestrate the application container and a TimescaleDB container, so that I can quickly and consistently set up and run the entire development environment locally.
**Acceptance Criteria (ACs)**:
AC1: Python Application Dockerfile Created: A Dockerfile at project root builds a Docker image for the Python app (Python 3.11-slim base, copies files, installs requirements.txt, defines a suitable default command/entrypoint).
AC2: TimescaleDB Docker Configuration: A TimescaleDB service (official image) is defined in docker-compose.yml.
AC3: docker-compose.yml Created and Functional: docker-compose.yml at project root defines app and DB services, sources environment variables from .env, configures persistent volumes for TimescaleDB data, and sets up inter-container networking.
AC4: Environment Starts Successfully: docker-compose up -d starts both containers without errors; app container remains running.
AC5: Basic Connectivity Check (Manual): TimescaleDB is accessible from the host via psql/GUI tool using .env credentials.
AC6: README Updated with Docker Instructions: README.md includes instructions for docker-compose up and docker-compose down.

**Story 1.4: Implement Basic Centralized Logging Framework**
**Story Statement**: As a Developer, I want a basic centralized logging framework configured (e.g., using Python's logging module, outputting to console and optionally a file) that can be used by all modules, so that application events, warnings, and errors are consistently recorded for debugging and monitoring.
**Acceptance Criteria (ACs)**:
AC1: Logging Configuration Module/Function: A dedicated Python module/function (e.g., in src/core/logging_config.py) configures Python's logging.
AC2: Standard Log Format (Files): File logs have a consistent format: timestamp, level, logger name, detailed message.
AC3: Console Output (Filtered & Configurable Level): Console logs show WARNING and above by default (simpler format). Console level is configurable via system_config.yaml or an environment variable, overriding the default.
AC4: Rotating File Output (Configurable): Implements rotating log files (e.g., logging.handlers.RotatingFileHandler). Configuration for file path (e.g., logs/app.log), rotation (max size, backup count), and file log level (DEBUG, INFO) are in system_config.yaml.
AC5: Ease of Use: Modules can easily get and use a configured logger (logging.getLogger(__name__)).
AC6: Log Levels Respected: Configured log levels for console and file are adhered to.
AC7: Basic Unit Tests for Logging Setup: Unit tests verify initialization, message formats, and application of configuration parameters.

**Story 1.5: Initialize TimescaleDB and Establish SQLAlchemy Connection**
**Story Statement**: As a Developer, I want the TimescaleDB container to initialize correctly, and I want the Python application to be able to establish a basic connection to it using SQLAlchemy with credentials from the configuration, so that the database is ready for schema creation and data loading in subsequent epics.
**Acceptance Criteria (ACs)**:
AC1: TimescaleDB Container Healthy: TimescaleDB container runs and accepts connections after docker-compose up.
AC2: Database Exists: The specified database (name from .env via ConfigManager) is created in TimescaleDB.
AC3: Application Can Create SQLAlchemy Engine: Python app can create a SQLAlchemy engine using connection params from ConfigManager.
AC4: Basic SQLAlchemy Connection Test Utility: A utility function/script uses the SQLAlchemy engine to connect and execute a trivial query (e.g., SELECT 1).
AC5: Connection Test Success Logged: The utility logs success or clear error on connection attempt.
AC6: Credentials Not Hardcoded: DB credentials sourced exclusively via ConfigManager (from environment variables).
AC7: SQLAlchemy Installed: SQLAlchemy and psycopg2-binary are in requirements.txt and the Docker image.