# Hist_Data_Ingestor Product Requirements Document (PRD)

## 1. Goal, Objective and Context

The core problem Hist_Data_Ingestor addresses is the current lack of a systematic and extensible method for acquiring historical financial data from diverse APIs and ingesting it into a structured storage system. This capability is crucial for enabling subsequent in-depth data analysis, the generation of trading ideas, and the development and backtesting of trading strategies. Hist_Data_Ingestor aims to solve this by providing a Python-based framework designed for the ingestion of historical financial data. Key characteristics of this framework will include API agnosticism, high configurability (primarily through YAML files), and a reusable foundational layer. The platform will manage the end-to-end process: data ingestion from multiple APIs, data transformation, validation, persistent storage (utilizing TimescaleDB), and a querying interface.

The **vision** for Hist_Data_Ingestor is to be the central, reliable, and highly flexible platform that empowers sophisticated financial analysis and strategy development by seamlessly providing access to a vast array of historical market data.

The **primary goals** for the MVP are:
* Successfully ingest historical data from Interactive Brokers and Databento APIs.
* Implement a configurable data transformation and validation pipeline for these initial two APIs.
* Establish a TimescaleDB instance with a defined schema capable of storing the ingested data from Interactive Brokers and Databento.
* Develop a basic querying interface allowing retrieval of the stored data by symbol and date range.

## 2. Functional Requirements (MVP)

The major functional requirements for the MVP of Hist_Data_Ingestor include:

1.  **API Integration Framework:** The foundational mechanism to connect to external financial data APIs, initially supporting Interactive Brokers and Databento.
2.  **Configuration Management:** A system allowing API connection details, data extraction parameters, and transformation rules to be defined externally (primarily via YAML files).
3.  **Data Ingestion Module:** The component responsible for robustly fetching raw historical data from the configured APIs.
4.  **Data Transformation Engine:** A module to process, clean, and standardize the fetched raw data into a consistent internal format.
5.  **Data Validation Module:** A component to perform quality checks and ensure the integrity of the data before storage.
6.  **TimescaleDB Storage Layer:** The backend database (TimescaleDB) setup, including schema definition, for persisting the validated financial time-series data.
7.  **Basic Querying Interface:** An initial interface or method to allow the primary user and downstream modules to retrieve stored data based on common criteria (e.g., by symbol and date range).

## 3. Non-Functional Requirements (MVP)

1.  **NFR 1: Configurability (MVP)**
    * **Requirement:** The system must be configurable via external YAML files for API connection details, data extraction parameters, and transformation rules.
    * **MVP Scope & Detail:**
        * Configuration will cover essential parameters for Interactive Brokers and Databento integration, including:
            * Authentication credentials/mechanisms (e.g., API key, token, relevant URLs – referencing secure retrieval methods like environment variables).
            * Base URLs for the APIs.
            * Key endpoint paths to be used for fetching the required data for the specified symbols.
            * The list of symbols to ingest for each API.
            * Primary field mappings from the API response to the internal data model.
            * Basic transformation rules (e.g., data type conversions for key fields).
        * The system will use YAML as the configuration format, as detailed in the project's foundational research.
        * The framework will be designed to allow for increased configuration granularity in future iterations.

2.  **NFR 2: Reliability & Operational Stability (MVP)**
    * **Requirement:** The system must reliably ingest data from the configured APIs and handle transient errors gracefully. The target operational stability for the MVP is 95% of scheduled ingestion runs for Interactive Brokers and Databento completing without manual intervention over a one-week monitoring period post-deployment.
    * **MVP Scope & Detail (Error Handling):**
        * Implement a standard retry mechanism (e.g., 3-5 retries) with exponential backoff for transient errors (e.g., network issues, HTTP 5xx server errors) encountered during API calls. This can be a global policy for the MVP.
        * All errors, especially persistent ones after retries are exhausted, must be robustly logged with sufficient context (API name, endpoint, parameters, error message, timestamp, correlation ID if available) to enable diagnosis.
        * A formal Dead-Letter Queue (DLQ) mechanism will be deferred post-MVP. For the MVP, persistent failures after retries will be identified through critical log monitoring.
        * Basic alerting for critical failure thresholds (e.g., a summary if X critical errors occur in a run) can be considered if straightforward to implement, otherwise, manual log monitoring for critical failures is the baseline for MVP.

3.  **NFR 3: Data Integrity (MVP)**
    * **Requirement:** The system must ensure the accuracy and consistency of the ingested financial data. The target for the MVP is to have less than 1% of processed records from Interactive Brokers and Databento failing critical validation checks.
    * **MVP Scope & Detail (Validation Failure Handling):**
        * The system will perform schema validation on raw API data (e.g., using Pydantic models or similar) and data quality checks on data post-transformation (e.g., using Pandera, Great Expectations, or custom validation functions for critical business rules like price > 0, timestamp validity).
        * If a record or a small, clearly defined batch of records fails a critical validation rule:
            * The failing record(s), the specific validation rule(s) violated, and the API source will be logged in detail.
            * The problematic record(s)/batch will be moved to a designated quarantine location (e.g., a separate error log file, a specific "quarantine" database table, or a designated directory for error files).
            * The system will continue to process other valid data within the current ingestion run.
        * The primary user will be responsible for monitoring the quarantine location and deciding on the disposition of quarantined data (e.g., correction and reprocessing if feasible, or discarding if unrecoverable).

4.  **NFR 4: Performance (MVP)**
    * **Requirement:** The system must perform data ingestion and querying tasks within acceptable timeframes for the MVP.
    * **MVP Scope & Detail:**
        * **Initial Bulk Data Ingestion:** The system must be capable of ingesting at least 1 year of daily historical data for the 5 specified symbols (CL, SPY or /ES, NG, HO, RB) from both Interactive Brokers and Databento within **2-4 hours**. This implies the need for efficient data handling and potentially asynchronous operations.
        * **Daily Incremental Updates:** Post initial bulk load, the system will primarily download daily updates. While a specific time target for daily updates isn't set for MVP, they must be efficient enough to complete reliably without manual intervention and support the overall operational stability target.
        * **Querying Interface:** The basic querying interface must retrieve 1 month of daily data for a single specified symbol in **under 5 seconds** for typical queries.
        * The system will leverage TimescaleDB's time-series capabilities (hypertables, partitioning, appropriate indexing) and Python's asynchronous processing features (e.g., `asyncio`, `aiohttp`) as appropriate to meet these performance targets.

5.  **NFR 5: Maintainability (MVP)**
    * **Requirement:** The system must be designed and documented to be easily understood, modified, debugged, and extended throughout its lifecycle.
    * **MVP Scope & Detail:**
        * **Project Structure:** The full recommended project structure (inspired by the research document, Section I.B - e.g., distinct directories for `configs`, `src/core`, `src/ingestion`, `src/transformation`, `src/storage`, `tests`) will be implemented from the start to ensure clear separation of concerns.
        * **Coding Standards:** Adherence to clean, readable Python code (PEP 8 guidelines) is mandatory.
        * **Docstrings:**
            * Comprehensive docstrings are required for all public interfaces (modules, classes, public functions/methods), explaining their purpose, arguments, return values, and any exceptions raised.
            * Clear docstrings are required for any non-trivial or complex internal (private) functions.
            * Simple, self-explanatory private utility functions may have brief or no docstrings if their purpose is immediately obvious from context and naming.
        * **README Files:**
            * A comprehensive top-level `README.md` will be created, detailing project setup, configuration, how to run the application, and an overview of its architecture.
            * A `README.md` within the `configs/` directory will explain the structure of configuration files and how to add/modify API configurations.
            * Concise `README.md` files will be included in each major `src` subdirectory (e.g., `src/core/`, `src/ingestion/`, `src/transformation/`, `src/storage/`) outlining the primary responsibility and key components/modules within that directory.

6.  **NFR 6: Usability (for Primary User/Operator - MVP)**
    * **Requirement:** The system must be straightforward for the primary technical user to configure, operate, and monitor for the MVP.
    * **MVP Scope & Detail:**
        * **Configuration:** The primary method for setup and defining API-specific parameters will be through well-documented YAML files, with a clear structure as outlined in the `configs/README.md`.
        * **Execution & Interaction (CLI):**
            * The system will be operated via a Command Line Interface (CLI).
            * The CLI will support essential commands for initiating ingestion tasks (e.g., `ingest --api <api_name> --start_date <date> --end_date <date>` for bulk/backfill; `ingest --api <api_name> --daily` for incremental updates).
            * The CLI will provide enhanced feedback during operations, such as progress indicators (e.g., progress bars or record counts) for long-running ingestion tasks.
            * The CLI will offer a command to check basic operational status (e.g., `status --api <api_name>` to show last successful run, record counts, or any persistent error states for an API).
        * **Feedback & Logging:** Clear, real-time console output will indicate key stages, progress, successes, and errors during operation. Detailed logs (as defined in the Reliability NFR) will be available for troubleshooting.

7.  **NFR 7: Deployability & Consistency (Docker - MVP)**
    * **Requirement:** The system must be containerized using Docker from its inception to ensure consistency across development, testing, and future deployment environments, and to facilitate ease of setup.
    * **MVP Scope & Detail:**
        * **Application Containerization:** The Python-based Hist_Data_Ingestor application (including all its services and modules) **must** be packaged into a Docker container, defined by a `Dockerfile`.
        * **Database Containerization (Local Development):** For local development and testing, the TimescaleDB instance **must** run as a Docker container.
        * **Local Environment Orchestration:** A `docker-compose.yml` file (or equivalent Compose specification) **must** be provided to define and manage the multi-container local development environment. This will allow the primary user to start all necessary services (Python application container, TimescaleDB container) with a single command (e.g., `docker-compose up`).
        * This comprehensive Dockerization approach is mandated to ensure maximum environment consistency and to lay a solid foundation for potential future cloud deployments or scaled-up local deployments.

8.  **NFR 8: Cost-Effectiveness (MVP Deployment)**
    * **Requirement:** The MVP system must be deployable and operable on local hardware (specifically, a high-end gaming PC as per the brief) without incurring mandatory cloud service costs for its core functionality.
    * **MVP Scope & Detail:**
        * All core components of the MVP (Python application, TimescaleDB database) will be run locally using Docker and Docker Compose.
        * Technology choices and architectural patterns for the MVP must support efficient local operation.
        * Any consideration of cloud services that incur costs will be deferred to post-MVP planning, unless explicitly approved as an exception for a critical MVP capability not achievable locally within reasonable effort.

9.  **NFR 9: Developer Experience (MVP)**
    * **Requirement:** The MVP development process must be manageable and productive for a developer new to this project scale, minimizing unnecessary complexity and promoting clarity.
    * **MVP Scope & Detail:**
        * **Architectural Simplicity:** The MVP will be built using a **monolith architecture** to reduce initial complexity, with a clear path for future evolution as outlined in the research document.
        * **Technology & Library Choices:** Preference will be given to well-documented, widely-used Python libraries and patterns that have a reasonable learning curve and robust community support, provided they meet functional and other non-functional requirements.
        * **Documentation & Clarity:** The project will adhere to the defined Maintainability NFR (Option A-), ensuring clear project structure, adequate code documentation (docstrings), and helpful README files to guide development.
        * **Development Environment:** The local development environment will be standardized and easy to set up using Docker and Docker Compose (as per NFR 7).
        * **Task Breakdown:** Work will be broken down into clear, achievable Epics and User Stories to allow for focused, incremental development.

10. **NFR 10: Testability (MVP)**
    * **Requirement:** The system must be testable to ensure core functionality, data integrity for the initial API integrations, and reliability of the data pipeline.
    * **MVP Scope & Detail:**
        * **Unit Tests:** Unit tests will be prioritized for:
            * Critical and complex data transformation logic.
            * Core data validation rules.
            * Key utility functions that are central to the pipeline's operation.
        * **Integration Tests:** Integration testing will focus on:
            * Verifying end-to-end connectivity for each of the two MVP APIs (Interactive Brokers and Databento). This includes successful authentication, making a basic data request (e.g., for one symbol over a small, recent date range to minimize data volume for the test), and correctly parsing the response structure.
            * Testing the basic data loading mechanism: Ensuring that a sample of transformed data can be successfully and idempotently inserted/upserted into the Dockerized TimescaleDB instance.
        * Extensive testing of all configuration variations, all API adapter edge cases, or comprehensive end-to-end pipeline scenarios with large datasets will be deferred post-MVP, with the understanding that the primary user will perform manual validation and operational monitoring for broader coverage during the MVP phase.

## 4. User Interaction and Design Goals (MVP)

Given that Hist_Data_Ingestor is primarily a backend data ingestion framework operated by a technical user via a Command Line Interface (CLI) and YAML configuration files for the MVP, extensive UI/UX design goals are not applicable at this stage.

The primary interaction design goals are covered by the Non-Functional Requirement for Usability (NFR 6), which emphasizes:
* Clarity and logical structure of YAML configuration files.
* Clear, effective, and discoverable CLI commands for core operations (ingestion, status checks).
* Meaningful feedback and logging to the console during CLI operations, including progress indicators for long-running tasks.

A graphical user interface (GUI) is out of scope for the MVP. Future iterations might consider a web interface for broader usability or advanced configuration management if the need arises.

## 5. Technical Assumptions

This section outlines foundational technical decisions and assumptions that will guide the Architect in designing the solution for Hist_Data_Ingestor.

* **Core Development Language:** Python 3.11 (or latest stable 3.11.x).
* **Primary Data Store:** TimescaleDB (as mandated by the Project Brief and supported by the foundational research document). The Architect will detail schema design and interaction patterns.
* **Containerization:** Docker **must** be used from the project's inception for the application and local database instances, managed via Docker Compose for the local development environment (as per NFR 7).
* **Initial Architectural Style (MVP):** The project will start with a **monolith architecture** for the MVP. This approach is chosen to facilitate initial development and establish a solid foundation, with the understanding (based on prior research and the Project Brief) that it can be evolved into a more distributed (e.g., microservices with EDA) architecture post-MVP if scale and complexity demand.
* **Configuration Management:** System configuration (API keys, endpoints, transformation rules) will be managed via external YAML files (as per NFR 1 and detailed in the research document). Secure handling of sensitive data (like API keys) will involve environment variables for local development and referencing secrets management solutions for potential future production deployments.
* **API Integrations (MVP):** The MVP will focus on integrating with:
    * Interactive Brokers (IB) API
    * Databento API
* **Data Focus (MVP):** Ingestion will initially target daily historical data for Crude Oil (CL), S&P 500 (e.g., SPY or /ES), Natural Gas (NG), Heating Oil (HO), and RBOB Gasoline (RB).
* **Target Deployment Environment (MVP):** Local hardware (high-end gaming PC), as per NFR 8, to defer cloud costs.
* **Source Control:** Git will be used for version control, with **GitHub** as the preferred hosting platform.
* **External Libraries/Frameworks:** While specific choices will be made by the Architect and development team, there's a preference for well-documented, widely-used Python libraries that align with the project goals and developer experience NFR (e.g., SQLAlchemy for database interaction, Pydantic for data validation, `aiohttp` for asynchronous API calls, as suggested in the research document). The user is not aware of specific starter templates to recommend at this stage; the Architect should evaluate this based on the research document and general best practices to see if any could accelerate development for a data engineering monolith.
* **Repository & Service Architecture (Monolith Detail):**
    * Given the monolith choice for MVP, the repository structure will be a single main repository on GitHub containing all modules (`configs`, `src`, `tests`, `docs`, etc.) as outlined in the foundational research document (Section I.B).
    * Within the `src` directory, the monolith will be internally modularized (e.g., `ingestion`, `transformation`, `storage`, `core`, `querying` modules) to ensure clear separation of concerns and to facilitate potential future refactoring into microservices.
* **Approach to Technical Debt (MVP):** The primary strategic technical debt accepted for the MVP is the initial monolith architecture, chosen for development speed, with a plan for future evolution. Any minor technical debt accrued during MVP development (e.g., areas identified for refactoring, temporary workarounds for non-critical issues) should be logged as issues (e.g., in the GitHub issues tracker for the project) for consideration in post-MVP refactoring efforts. This ensures that focus remains on delivering core MVP functionality while acknowledging areas for future improvement.

### Testing requirements

* The MVP testing strategy (as per NFR 10) will focus on:
    * **Unit Tests:** For critical transformation logic, validation rules, and key utility functions.
    * **Integration Tests:** For end-to-end connectivity with Interactive Brokers and Databento APIs, and for basic data loading into the local TimescaleDB instance.
    * The primary user will perform manual validation and operational monitoring for broader coverage during the MVP phase.


## 6. Epic Overview

The MVP for Hist_Data_Ingestor will be developed through the following logical Epics:

* **Epic 1: Foundational Setup & Core Framework**
    * **Goal:** Establish the initial project structure, core configuration loading, basic logging, Docker environment, and foundational TimescaleDB setup. This epic lays the groundwork for all subsequent development.
    * **Stories:**
        * **Story 1.1: Initialize Project Repository and Directory Structure**
            * **Story Statement:** As a Developer, I want to initialize a Git repository (on GitHub) and create the recommended baseline project directory structure (including `configs/`, `src/`, `tests/`, `docs/`, `.env.example`, `requirements.txt`, `README.md`), so that the project has a clean, organized foundation compliant with best practices and the research document.
            * **Acceptance Criteria (ACs):**
                1.  **AC1: GitHub Repository Created:** A new private Git repository named `Hist_Data_Ingestor` (or a user-confirmed name) is created on GitHub.
                2.  **AC2: Repository Cloned Locally:** The GitHub repository is successfully cloned to the local development environment.
                3.  **AC3: Core Directory Structure Established:** The following top-level directories are created within the local repository: `configs/`, `src/`, `tests/`, `docs/`.
                4.  **AC4: Initial Core Files Created:** The following files are created at the root of the repository: `.gitignore` (with common Python and OS-specific ignores, plus `.env`), `README.md` (with placeholder title and brief project description), `requirements.txt` (initially empty or with essential linters/formatters like `black`, `flake8`, `pydantic`), `.env.example` (with placeholders for `TIMESCALEDB_USER`, `TIMESCALEDB_PASSWORD`, `TIMESCALEDB_HOST`, `TIMESCALEDB_PORT`, `TIMESCALEDB_DBNAME`, `IB_API_KEY`, `DATABENTO_API_KEY`).
                5.  **AC5: Sub-directory Structure (Basic):** `configs/` contains `system_config.yaml` (placeholder) and `api_specific/`. `src/` contains an empty `__init__.py` and subdirectories: `core/`, `ingestion/`, `transformation/`, `storage/`, `querying/`, `utils/` (each with an empty `__init__.py`). `tests/` contains an empty `__init__.py` and subdirectories: `unit/`, `integration/` (each with an empty `__init__.py`). `docs/` is initially empty or contains placeholders.
                6.  **AC6: Initial Commit and Push:** All created directories and files (excluding gitignored) are committed with a meaningful initial commit message and pushed to the remote GitHub repository.
        * **Story 1.2: Implement Core Configuration Management for System Settings**
            * **Story Statement:** As a Developer, I want a core configuration management system that can load system-level settings (e.g., database connection details from environment variables, logging level) from a `configs/system_config.yaml` file and environment variables, so that basic application parameters are centrally managed and easily accessible.
            * **Acceptance Criteria (ACs):**
                1.  **AC1: `ConfigManager` Class Created:** A Python class (e.g., `ConfigManager`) is created within `src/core/`.
                2.  **AC2: Load `system_config.yaml`:** `ConfigManager` successfully loads and parses settings from `configs/system_config.yaml` (initially with placeholders like default logging level).
                3.  **AC3: Environment Variable Overrides & Secrets Handling:** `ConfigManager` securely accesses and prioritizes environment variables for settings like database credentials and API keys over `system_config.yaml`. Sensitive secrets are loaded exclusively from environment variables.
                4.  **AC4: Configuration Accessibility:** Loaded configuration values are easily accessible via an instance of `ConfigManager`.
                5.  **AC5: Basic Error Handling:** `ConfigManager` raises clear errors if `system_config.yaml` is missing or malformed.
                6.  **AC6: Unit Tests for `ConfigManager`:** Basic unit tests verify loading from YAML, environment variable overrides for secrets, and error handling.
        * **Story 1.3: Establish Dockerized Development Environment**
            * **Story Statement:** As a Developer, I want a `Dockerfile` for the Python application and a `docker-compose.yml` file to orchestrate the application container and a TimescaleDB container, so that I can quickly and consistently set up and run the entire development environment locally.
            * **Acceptance Criteria (ACs):**
                1.  **AC1: Python Application `Dockerfile` Created:** A `Dockerfile` at project root builds a Docker image for the Python app (Python 3.11-slim base, copies files, installs `requirements.txt`, defines a suitable default command/entrypoint).
                2.  **AC2: TimescaleDB Docker Configuration:** A TimescaleDB service (official image) is defined in `docker-compose.yml`.
                3.  **AC3: `docker-compose.yml` Created and Functional:** `docker-compose.yml` at project root defines app and DB services, sources environment variables from `.env`, configures persistent volumes for TimescaleDB data, and sets up inter-container networking.
                4.  **AC4: Environment Starts Successfully:** `docker-compose up -d` starts both containers without errors; app container remains running.
                5.  **AC5: Basic Connectivity Check (Manual):** TimescaleDB is accessible from the host via psql/GUI tool using `.env` credentials.
                6.  **AC6: README Updated with Docker Instructions:** `README.md` includes instructions for `docker-compose up` and `docker-compose down`.
        * **Story 1.4: Implement Basic Centralized Logging Framework**
            * **Story Statement:** As a Developer, I want a basic centralized logging framework configured (e.g., using Python's `logging` module, outputting to console and optionally a file) that can be used by all modules, so that application events, warnings, and errors are consistently recorded for debugging and monitoring.
            * **Acceptance Criteria (ACs):**
                1.  **AC1: Logging Configuration Module/Function:** A dedicated Python module/function (e.g., in `src/core/logging_config.py`) configures Python's `logging`.
                2.  **AC2: Standard Log Format (Files):** File logs have a consistent format: timestamp, level, logger name, detailed message.
                3.  **AC3: Console Output (Filtered & Configurable Level):** Console logs show `WARNING` and above by default (simpler format). Console level is configurable via `system_config.yaml` or an environment variable, overriding the default.
                4.  **AC4: Rotating File Output (Configurable):** Implements rotating log files (e.g., `logging.handlers.RotatingFileHandler`). Configuration for file path (e.g., `logs/app.log`), rotation (max size, backup count), and file log level (DEBUG, INFO) are in `system_config.yaml`.
                5.  **AC5: Ease of Use:** Modules can easily get and use a configured logger (`logging.getLogger(__name__)`).
                6.  **AC6: Log Levels Respected:** Configured log levels for console and file are adhered to.
                7.  **AC7: Basic Unit Tests for Logging Setup:** Unit tests verify initialization, message formats, and application of configuration parameters.
        * **Story 1.5: Initialize TimescaleDB and Establish SQLAlchemy Connection**
            * **Story Statement:** As a Developer, I want the TimescaleDB container to initialize correctly, and I want the Python application to be able to establish a basic connection to it using SQLAlchemy with credentials from the configuration, so that the database is ready for schema creation and data loading in subsequent epics.
            * **Acceptance Criteria (ACs):**
                1.  **AC1: TimescaleDB Container Healthy:** TimescaleDB container runs and accepts connections after `docker-compose up`.
                2.  **AC2: Database Exists:** The specified database (name from `.env` via `ConfigManager`) is created in TimescaleDB.
                3.  **AC3: Application Can Create SQLAlchemy Engine:** Python app can create a SQLAlchemy engine using connection params from `ConfigManager`.
                4.  **AC4: Basic SQLAlchemy Connection Test Utility:** A utility function/script uses the SQLAlchemy engine to connect and execute a trivial query (e.g., `SELECT 1`).
                5.  **AC5: Connection Test Success Logged:** The utility logs success or clear error on connection attempt.
                6.  **AC6: Credentials Not Hardcoded:** DB credentials sourced exclusively via `ConfigManager` (from environment variables).
                7.  **AC7: SQLAlchemy Installed:** SQLAlchemy and `psycopg2-binary` are in `requirements.txt` and the Docker image.

* **Epic 2: Interactive Brokers (IB) Integration & End-to-End Data Flow**
    * **Goal:** Implement the complete data ingestion pipeline (extraction, basic transformation, validation, storage) for the Interactive Brokers API for the specified symbols and data frequency.
    * **Stories:**
# Story 2.1 (Revised): Configure Interactive Brokers (IB) TWS API Access and Parameters

**Story Statement:** As a Developer, I want to create an API-specific YAML configuration file for Interactive Brokers (configs/api_specific/interactive_brokers_config.yaml) that includes TWS/Gateway connection details (host, port, clientId, referencing environment variables for any sensitive parts if necessary), parameters for reqHistoricalData (symbols, date ranges, frequency, whatToShow="TRADES", useRTH=1, formatDate=1, adjustForSplitsAndDividends=True, keepUpToDate=False), and references to transformation/validation rules, so that the system can connect to a running TWS/IB Gateway instance and understand how to request and process daily OHLCV data from IB.

**Acceptance Criteria (ACs):**

* **AC1: IB Configuration File Created:** A new YAML file named interactive_brokers_config.yaml is created within configs/api_specific/.

* **AC2: TWS/Gateway Connection Configuration:** The YAML file contains a connection (or authentication) section specifying:  
  * host (e.g., "127.0.0.1").  
  * port (e.g., 7497 for paper TWS, 7496 for live TWS, 4002 for paper gateway, 4001 for live gateway).  
  * clientId (a unique integer for this API connection, e.g., between 1 and 999).

* **AC3: Historical Data Request Parameters:** The YAML includes a historical_data_request section with parameters for reqHistoricalData, including:  
  * A default symbols list. Each symbol entry must allow for sufficient detail to define an ibapi.contract.Contract object (e.g., symbol: "ES", secType: "FUT", exchange: "CME", currency: "USD", and critically for futures, lastTradeDateOrContractMonth: "YYYYMM" or specific local symbol if preferred).  
  * Default frequency (e.g., "1 day").  
  * Parameters for date range specification, such as endDateTime_offset_days (e.g., 0 for current day, 1 for previous day, if formulating endDateTime string relative to current date) and durationStr_per_request (e.g., "1 M", "3 M", "1 Y" – the maximum duration IB allows per historical data request, which varies by bar size).  
  * whatToShow (e.g., "TRADES").  
  * useRTH (e.g., 1 for regular trading hours only, 0 for all hours).  
  * formatDate (e.g., 1 for "yyyyMMdd HH:mm:ss", 2 for epoch seconds).  
  * adjustForSplitsAndDividends (e.g., True).  
  * keepUpToDate (e.g., False for historical requests).

* **AC4: Rate Limiting Configuration (Client-Side Pacing):** The YAML includes rate_limiting parameters to help the client self-pace requests and stay within IB's known historical data request limits (e.g., no more than 60 requests per 600 seconds), such as:  
  * max_requests_per_defined_period (e.g., 50).  
  * defined_period_seconds (e.g., 600).  
  * delay_between_individual_requests_seconds (e.g., calculated based on the above, or a fixed minimum like 10.5 seconds).

* **AC5: Mapping and Validation References (Placeholders):** The YAML includes mapping_config_path (e.g., to src/transformation/mapping_configs/interactive_brokers_mappings.yaml) and validation_schema_paths (e.g., to configs/validation_schemas/ib_raw_schema.json).

* **AC6: YAML Validity:** interactive_brokers_config.yaml is well-formed YAML and adheres to a logical structure.

* **AC7: Documentation (README Update):** The configs/README.md is updated with a detailed section explaining the structure of interactive_brokers_config.yaml, providing examples for different security types (stocks, futures) and emphasizing correct Contract definition parameters.

* **AC8: Market Data Subscription Awareness in Docs:** The configs/README.md (or the IB config section within it) explicitly notes that access to historical data via the TWS API often requires corresponding market data subscriptions for the account and that "live data permissions" are usually a prerequisite for historical data requests.

* **AC9: Contract Definition Strategy in Docs:** The documentation for interactive_brokers_config.yaml clearly explains the importance of accurate Contract object parameters (symbol, secType, exchange, currency, lastTradeDateOrContractMonth for futures/options, primaryExchange for stocks if needed for disambiguation). It also notes that for rolling futures contracts, the lastTradeDateOrContractMonth or the specific ticker symbol might need to be dynamically resolved by the user or regularly updated in the configuration.

---

# Story 2.2 (Revised): Implement Interactive Brokers (IB) TWS API Adapter for Data Extraction

**Story Statement:** As a Developer, I want to implement an InteractiveBrokersAdapter class (e.g., in src/ingestion/api_adapters/interactive_brokers_adapter.py) that can connect to a running TWS/IB Gateway instance using the ibapi Python library and the provided configuration, define Contract objects, robustly fetch historical daily OHLCV data using reqHistoricalData for the specified symbols and date ranges (handling asynchronous responses via EWrapper callbacks), manage the EReader thread, implement client-side pagination for extended historical data, and handle API-specific errors and rate limits, so that raw bar data from IB can be reliably extracted.

**Acceptance Criteria (ACs):**

* **AC1: InteractiveBrokersAdapter Class Created:** An InteractiveBrokersAdapter class is created in src/ingestion/api_adapters/interactive_brokers_adapter.py, inheriting from a BaseAdapter (if defined in Epic 1), and encapsulating ibapi.client.EClient and ibapi.wrapper.EWrapper logic.

* **AC2: Configuration Driven:** The adapter's constructor accepts the IB-specific configuration (loaded from interactive_brokers_config.yaml) and uses it for TWS/Gateway connection parameters (host, port, clientId), contract parameters, and historical data request settings.

* **AC3: TWS/Gateway Connection Management:** The adapter successfully establishes a socket connection to TWS/Gateway using self.connect(host, port, clientId) and manages the EClient.run() loop in a separate thread (e.g., via threading.Thread). The nextValidId callback in EWrapper is successfully received and handled before making requests. A disconnect method properly closes the connection.

* **AC4: Data Fetching Method (fetch_historical_data):** The adapter has a primary method (e.g., fetch_historical_data(contract_config: dict, end_date_str: str, duration_str: str, bar_size_setting: str, what_to_show: str, use_rth: int, format_date: int, keep_up_to_date: bool)) that:  
  * Constructs an ibapi.contract.Contract object from contract_config parameters.  
  * Calls self.reqHistoricalData() with a unique reqId and all necessary parameters from the method arguments and configuration.

* **AC5: Asynchronous Response Handling:** EWrapper callback methods historicalData(reqId, bar: BarData) and historicalDataEnd(reqId, start: str, end: str) are implemented to collect the received BarData objects into a temporary storage (e.g., a list) associated with the reqId.

* **AC6: Iterative Fetching (Client-Side Pagination) Handled:** The adapter implements logic to fetch data for extended historical periods by making sequential reqHistoricalData calls. This involves calculating the appropriate endDateTime and durationStr for each call to respect IB's limitations (e.g., fetching one year of daily data might require multiple calls for shorter durations like "3 M" or "1 M" each). An appropriate delay (from config) is inserted between these sequential calls for the same contract.

* **AC7: Rate Limiting Adherence (Client-Side Pacing):** The adapter respects the client-side pacing parameters defined in the configuration (max_requests_per_defined_period, defined_period_seconds, delay_between_individual_requests_seconds) to avoid overwhelming the TWS/Gateway or hitting undocumented strict limits.

* **AC8: Robust Error Handling & Retries:** The EWrapper.error(reqId, errorCode, errorString, advancedOrderRejectJson) callback is implemented to catch and log TWS API errors. The adapter applies a retry policy (e.g., using tenacity) for specific recoverable error codes (e.g., connectivity issues, temporary server errors like 502, 504, or pacing violations like 162 if retryable) based on configuration. Non-retryable errors are logged and result in failure for that specific request/contract.

* **AC9: Raw Data Output:** The fetch_historical_data method (or the overall process coordinating callbacks for a full historical period) returns the collected raw data as a list of ibapi.common.BarData objects or a list of dictionaries derived from them.

* **AC10: Unit Tests & Basic Integration Test:** Unit tests mock ibapi.client.EClient and ibapi.wrapper.EWrapper calls. A basic integration test exists that connects to a running paper TWS/IB Gateway instance, requests a small amount of historical data (e.g., 5 days) for one simple stock symbol, and verifies data is received.

* **AC11: Contract Object Creation & Resolution:** The adapter can accurately create ibapi.contract.Contract objects using parameters from the configuration (symbol, secType, exchange, currency, lastTradeDateOrContractMonth, etc.). For futures and options, if a conId is not directly provided in the config, the adapter should (optionally, if enabled by a config flag, but recommended) first use reqContractDetails to find the correct conId based on other contract specifics to ensure data is requested for the exact instrument intended. If reqContractDetails is used, its results are logged for verification.
# Story 2.3 (Revised): Define and Implement Data Transformation Rules for IB BarData

**Story Statement:** As a Developer, I want to define and implement transformation rules (e.g., in src/transformation/mapping_configs/interactive_brokers_mappings.yaml and potentially custom Python functions) to convert raw IB BarData objects (attributes like date, open, high, low, close, volume) into the standardized internal data model, including careful handling of timestamps (parsing "YYYYMMDD" string, assuming UTC unless validated otherwise) and ensuring correct numeric types (Decimal for prices), so that IB data is consistent with the system's common format.

**Acceptance Criteria (ACs):**

* **AC1: IB Mapping Configuration File Created:** interactive_brokers_mappings.yaml created in src/transformation/mapping_configs/.

* **AC2: Define Standardized Internal Fields:** Standardized fields (e.g., event_timestamp, security_symbol, exchange, currency, open_price, high_price, low_price, close_price, trade_volume, data_source) are defined for the internal data model.

* **AC3: Field Mapping Rules:** The YAML file contains rules mapping attributes from ibapi.common.BarData objects (e.g., bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume) to the standardized internal fields. It also maps relevant fields from the ibapi.contract.Contract object used for the request (e.g., symbol, exchange, currency) to corresponding standardized fields.

* **AC4: Data Type Conversion Rules:** The YAML specifies rules for data type conversions:  
  * bar.date (string, typically "YYYYMMDD" if formatDate=1 for daily) to a Python datetime.date or datetime.datetime object.  
  * Prices (bar.open, bar.high, bar.low, bar.close) from float to Decimal for precision.  
  * bar.volume (potentially Decimal or int from IB) to a consistent numeric type (e.g., Decimal or int) in the internal model.

* **AC5: Timestamp Transformation & Timezone Handling:** The bar.date string (e.g., "YYYYMMDD") is parsed. If representing daily data, it's typically converted to a datetime.datetime object representing midnight UTC for that day, unless empirical validation of the TWS API's historicalData callback for daily bars with formatDate=1 indicates a different timezone or time component, which must then be documented and handled.

* **AC6: Server-Side Adjustments Confirmed:** Transformation logic assumes that reqHistoricalData with adjustForSplitsAndDividends=True (as configured in Story 2.1) provides data already adjusted by IB for splits and dividends; no client-side adjustment for these events is implemented in the transformation stage.

* **AC7: Transformation Logic Implemented/Integrated:** The RuleEngine (or equivalent transformation component) can parse interactive_brokers_mappings.yaml and apply these rules to structures representing IB BarData and associated Contract details.

* **AC8: Unit Tests for Transformations:** Unit tests cover timestamp parsing (including assumed timezone handling), numeric conversions (float to Decimal), and field mapping for sample BarData-like inputs, ensuring the output matches the standardized internal model.

---

# Story 2.4 (Revised): Define and Implement Data Validation Rules for IB Data

**Story Statement:** As a Developer, I want to define and implement validation rules (e.g., Pydantic for raw BarData-like structures, Pandera/custom functions for post-transformation checks) specific to IB data characteristics, ensuring dates are valid, OHLCV values are numeric and consistent (e.g., high >= low), and volume is non-negative, so that the integrity and quality of IB data are ensured before storage.

**Acceptance Criteria (ACs):**

* **AC1: Raw IB Data Structure Validation (Conceptual via Adapter):** The InteractiveBrokersAdapter is expected to receive structured BarData objects from the ibapi library. Validation at this stage focuses on ensuring the adapter correctly populates these objects and handles cases where expected attributes might be missing or malformed from the API's perspective (though ibapi usually provides well-formed objects). If the adapter itself creates an intermediate dictionary before yielding, a Pydantic model can be used to validate this intermediate structure.

* **AC2: Post-Transformation Data Quality Checks Defined:** Validation rules are defined for the transformed, standardized IB data. These checks must include:  
  * event_timestamp is a valid datetime object.  
  * open_price, high_price, low_price, close_price are Decimal, non-negative.  
  * trade_volume is a non-negative Decimal or int.  
  * high_price >= low_price.  
  * open_price and close_price are between low_price and high_price (inclusive), if data is clean. (Note: some valid bars can have open/close outside H/L if it's the first/last print of a volatile period within the bar's formation).  
  * security_symbol is not null/empty.

* **AC3: Validation Logic Implemented & Integrated:** The defined post-transformation checks are implemented (e.g., using Pandera on a DataFrame of standardized records, or custom Python functions) and integrated into the IB data processing pipeline.

* **AC4: Validation Failure Handling:** Records failing post-transformation validation are logged in detail (record content, rule violated) and quarantined as per NFR 3.

* **AC5: Unit Tests for Validation Rules:** Unit tests cover the validation of compliant and non-compliant transformed data samples originating from IB, ensuring rules for timestamps, OHLCV consistency, and non-negativity are correctly applied.

* **AC6: Completeness Check:** Validation includes checks for missing essential fields in the transformed data (e.g., close_price or event_timestamp should not be null for a valid record intended for storage).

# Story 2.5: Integrate IB Data Flow into Pipeline Orchestrator

* **Story Statement:** As a Developer, I want to integrate the IB adapter, transformation, and validation components into the main pipeline orchestrator (e.g., `src/core/pipeline_orchestrator.py`), so that an end-to-end ingestion process for IB data can be triggered and managed.

* **Acceptance Criteria (ACs):**
    1. **AC1: `PipelineOrchestrator` Enhancement (if needed):** `PipelineOrchestrator` in `src/core/` can manage an API-specific ingestion pipeline.
    2. **AC2: IB Pipeline Definition/Configuration:** Orchestrator can be invoked for IB, dynamically using IB config, adapter, transformation rules, and validation rules.
    3. **AC3: Sequential Step Execution for IB:** Orchestrator correctly executes: Load IB config -> Init IB Adapter -> Fetch raw data -> Raw data validation -> Transform raw data -> Validate transformed data -> Pass valid data to storage layer.
    4. **AC4: Data Flow Between Components:** Data is correctly passed between adapter, validators, transformer, and storage layer entry.
    5. **AC5: Error Propagation and Handling by Orchestrator:** Orchestrator handles/logs errors from pipeline steps, respects Log & Quarantine (NFR 3) and retry policies (NFR 2).
    6. **AC6: Basic CLI Trigger for IB Pipeline:** CLI command (e.g., `python main.py ingest --api interactive_brokers --start_datePRIMATEC-MM-DD --end_dateꗩ-MM-DD`) triggers the IB pipeline.
    7. **AC7: Logging of Orchestration Steps:** Orchestrator logs key lifecycle events for the IB pipeline run with relevant details.

---

# Story 2.6: Test End-to-End Interactive Brokers Data Ingestion and Storage

* **Story Statement:** As a Developer, I want to perform end-to-end tests for the IB data pipeline, fetching a small sample of historical data, processing it through transformation and validation, and verifying its correct and idempotent storage in TimescaleDB, so that the complete data flow for IB is confirmed to be working as expected.

* **Acceptance Criteria (ACs):**
    1. **AC1: Test Data Scope Defined:** Small, specific test dataset defined for IB (e.g., 1-2 symbols, 5-10 days daily data), documented for repeatability.
    2. **AC2: `TimescaleLoader` Implemented for Standardized Data:** `TimescaleLoader` (`src/storage/`) accepts standardized data, defines/creates TimescaleDB table schema (hypertable, partitioned by timestamp, columns for standard fields + JSONB metadata), connects via SQLAlchemy, and idempotently inserts/upserts data (unique constraint: timestamp, symbol, data_source).
    3. **AC3: End-to-End Pipeline Run for IB Test Data:** `PipelineOrchestrator` successfully executes IB pipeline for test data via CLI without unhandled errors.
    4. **AC4: Data Correctly Stored in TimescaleDB:** Ingested, transformed, validated IB test data is present and correct in TimescaleDB, verified by direct query.
    5. **AC5: Idempotency Verified:** Second run with same test data does not create duplicates or incorrectly change valid records.
    6. **AC6: Quarantine Handling Verified (if applicable):** Sample data designed to fail validation is correctly quarantined; only valid data in main table.
    7. **AC7: Logs Confirm Successful Flow:** Logs confirm successful completion of each stage for IB test data, or errors/quarantining.

* **Epic 3: Databento Integration & End-to-End Data Flow**
    * **Goal:** Implement the complete data ingestion pipeline (extraction, basic transformation, validation, storage) for the Databento API for the specified symbols and data frequency, reusing and extending the framework components built in Epic 1 & 2.
    * **Stories:**
        * **Story 3.1: Configure Databento API Access and Parameters**
            * **Story Statement:** As a Developer, I want to create an API-specific YAML configuration file for Databento (`configs/api_specific/databento_config.yaml`) that includes the API key (referencing environment variables for the secret), dataset IDs, target schemas (e.g., `mbo`, `trades`, `ohlcv-1m`), symbology type (`stype_in`), data extraction parameters (symbols, date ranges), and references to transformation/validation rules, so that the system can connect to and understand how to process data from Databento.
            * **Acceptance Criteria (ACs):**
                1.  **AC1: Databento Configuration File Created:** `databento_config.yaml` created in `configs/api_specific/`.
                2.  **AC2: Authentication Configuration:** YAML contains `api` section with `key_env_var` (e.g., `DATABENTO_API_KEY`).
                3.  **AC3: Job Definition Structure:** YAML includes a `jobs` list, each item with `dataset`, `schema`, `symbols`, `start_date`, `end_date`, `stype_in`, optional `date_chunk_interval_days`.
                4.  **AC4: Data Extraction Parameters (General):** YAML includes basic `retry_policy` for Databento.
                5.  **AC5: Mapping and Validation References (Placeholders):** YAML includes `mapping_config_path` (to `databento_mappings.yaml`) and `validation_schema_paths`.
                6.  **AC6: YAML Validity and Pydantic Compatibility:** `databento_config.yaml` is well-formed and aligns with Pydantic models from "Databento Downloader: Detailed Specifications".
                7.  **AC7: Documentation (README Update):** `configs/README.md` updated with Databento config example.
        * **Story 3.2: Implement Databento API Adapter using Python Client for Data Extraction**
            * **Story Statement:** As a Developer, I want to implement a `DatabentoAdapter` class (e.g., in `src/ingestion/api_adapters/databento_adapter.py`) that utilizes the official `databento-python` client library to connect to the Databento API using the provided configuration (API key, dataset, symbols, schema, stype_in, date range), fetch historical data via `timeseries.get_range()`, iterate through the `DBNStore` to yield decoded DBN records, and handle API-specific nuances, so that raw, structured data objects from Databento can be reliably extracted.
            * **Acceptance Criteria (ACs):**
                1.  **AC1: `DatabentoAdapter` Class Created:** Class in `src/ingestion/api_adapters/databento_adapter.py`, ideally inheriting `BaseAdapter`.
                2.  **AC2: Configuration Driven:** Adapter constructor uses Databento config to init `databento.Historical` client and determine request params.
                3.  **AC3: Data Fetching Method (`Workspace_historical_data`):** Method takes job config, calls `client.timeseries.get_range()`, iterates `DBNStore`.
                4.  **AC4: DBN Record to Pydantic Model Conversion:** Adapter converts DBN records to corresponding Pydantic models from "Databento Downloader: Detailed Specifications".
                5.  **AC5: Output Decoded Pydantic Records:** `Workspace_historical_data` yields/returns list of validated Databento Pydantic model instances.
                6.  **AC6: Handles Multiple Symbols & Date Chunking (as per config):** Processes all symbols; implements date chunking if `date_chunk_interval_days` configured.
                7.  **AC7: Basic Error Handling & Retries (Leveraging Tenacity):** Adapter implements `tenacity` retry logic (respecting `Retry-After`) around `client.timeseries.get_range()`, using config parameters.
                8.  **AC8: Unit Tests:** Unit tests for `DatabentoAdapter` (mocking `databento.Historical` client) verify param passing, `DBNStore` iteration, Pydantic conversion, error handling, and date chunking.
        * **Story 3.3: Define and Implement Data Transformation Rules for Decoded Databento Records**
            * **Story Statement:** As a Developer, I want to define and implement transformation rules (e.g., in a `src/transformation/mapping_configs/databento_mappings.yaml`) to map fields from the decoded Databento Pydantic record objects (e.g., `MboMsg`, `TradeMsg`, as defined in the "Databento Downloader: Detailed Specifications" document) into the standardized internal data model, so that Databento data is consistent with the system's common format. This may involve less transformation if the Pydantic models already handle price scaling and timestamp conversions.
            * **Acceptance Criteria (ACs):**
                1.  **AC1: Databento Mapping Configuration File Created:** `databento_mappings.yaml` created in `src/transformation/mapping_configs/`.
                2.  **AC2: Field Mapping Rules (Pydantic to Standardized Model):** YAML maps attributes from source Databento Pydantic models to standardized internal model fields.
                3.  **AC3: Minimal Data Type Conversions (if still needed):** YAML includes further type conversions if Databento Pydantic model types differ from internal model types.
                4.  **AC4: Handling of Different Databento Schemas (Record Types):** Mapping config and `RuleEngine` correctly apply mappings for different Databento record types (`MboMsg`, `TradeMsg`, `OhlcvMsg`).
                5.  **AC5: Transformation Logic Integrated with `RuleEngine`:** `RuleEngine` parses `databento_mappings.yaml` and applies rules to Databento Pydantic model instances.
                6.  **AC6: Unit Tests for Databento Transformations:** Unit tests verify `RuleEngine` correctly applies `databento_mappings.yaml` rules to sample Databento Pydantic objects, producing expected standardized output.
        * **Story 3.4: Define and Implement Data Validation Rules for Decoded Databento Records**
            * **Story Statement:** As a Developer, I want to define and implement validation rules. Since the `databento-python` client and the provided Pydantic models (from "Databento Downloader: Detailed Specifications" document) already perform significant schema validation and type conversion: Initial validation will rely on the successful instantiation of these Databento-specific Pydantic models. Post-transformation (to standardized internal model) checks (e.g., using Pandera or custom functions) will focus on business rules and consistency checks outlined in NFR 3 (e.g., positive prices, High >= Low), so that the integrity and quality of Databento data are ensured before storage.
            * **Acceptance Criteria (ACs):**
                1.  **AC1: Leverage Databento Pydantic Models for Initial Validation:** `DatabentoAdapter` ensures DBN records convert to strict Pydantic models from "Databento Downloader: Detailed Specifications". Failed instantiations are logged & quarantined (NFR 3).
                2.  **AC2: Post-Transformation Databento Data Quality Checks Defined:** Validation rules (Pandera schemas or custom functions in `src/transformation/validators/databento_validators.py`) defined for standardized data from Databento. Checks include positive numerics for OHLCV, High >= Low, Open/Close within Low/High, valid timestamp, non-empty/expected symbol.
                3.  **AC3: Validation Logic Implemented & Integrated:** Post-transformation checks implemented and integrated into Databento data flow.
                4.  **AC4: Validation Failure Handling (Log & Quarantine Implemented):** Failed post-transformation records are logged (record, rule) and quarantined (NFR 3).
                5.  **AC5: Unit Tests for Validation Rules:** Unit tests for Databento Pydantic models (validation/rejection) and custom post-transformation validation functions/schemas.
        * **Story 3.5: Integrate Databento Data Flow into Pipeline Orchestrator**
            * **Story Statement:** As a Developer, I want to ensure the `PipelineOrchestrator` can correctly use the Databento adapter, transformation, and validation components, so that an end-to-end ingestion process for Databento data can be triggered and managed, reusing the orchestration logic.
            * **Acceptance Criteria (ACs):**
                1.  **AC1: `PipelineOrchestrator` Handles Databento API Type:** Orchestrator identifies "databento" API type and loads its components.
                2.  **AC2: Databento Pipeline Definition in Orchestrator:** Orchestrator uses Databento config, adapter, transformation rules, validation rules, and common `TimescaleLoader`.
                3.  **AC3: Sequential Step Execution for Databento:** Orchestrator correctly executes: Load Databento job config -> Init Databento Adapter -> Fetch Pydantic records -> Initial validation (Pydantic) -> Transform to standardized model -> Post-transformation validation -> Pass data to storage layer.
                4.  **AC4: Data Flow Between Components (Databento):** Databento Pydantic objects, then standardized internal model data, passed correctly.
                5.  **AC5: Error Propagation and Handling by Orchestrator (Databento):** Orchestrator handles/logs errors from Databento pipeline steps, respects Log & Quarantine (NFR 3) and component-level retries (NFR 2).
                6.  **AC6: CLI Trigger for Databento Pipeline:** CLI command (e.g., `python main.py ingest --api databento --dataset <id> --schema <name> --symbols <sym1,sym2> --start_dateGTBaseAlert-MM-DD --end_date𒑳-MM-DD`) triggers Databento pipeline.
                7.  **AC7: Logging of Orchestration Steps (Databento):** Orchestrator logs key lifecycle events for Databento pipeline run.
        * **Story 3.6: Test End-to-End Databento Data Ingestion and Storage**
            * **Story Statement:** As a Developer, I want to perform end-to-end tests for the Databento data pipeline, fetching a small sample of historical data (using the `databento-python` client via the adapter), processing it through transformation and validation, and verifying its correct and idempotent storage in TimescaleDB, so that the complete data flow for Databento is confirmed to be working as expected using the established framework.
            * **Acceptance Criteria (ACs):**
                1.  **AC1: Test Data Scope Defined (Databento):** Small, specific test dataset defined for Databento (e.g., 1-2 symbols, specific dataset/schema, 1-2 days data), documented.
                2.  **AC2: `TimescaleLoader` Reusability Confirmed:** Existing `TimescaleLoader` processes standardized data from Databento pipeline without Databento-specific core logic changes.
                3.  **AC3: End-to-End Pipeline Run for Databento Test Data:** `PipelineOrchestrator` executes Databento pipeline for test data via CLI without unhandled errors.
                4.  **AC4: Data Correctly Stored in TimescaleDB (Databento):** Ingested, transformed, validated Databento test data is present and correct in TimescaleDB, verified by direct query.
                5.  **AC5: Idempotency Verified (Databento):** Second run with same test data does not create duplicates or incorrectly change valid records.
                6.  **AC6: Quarantine Handling Verified (Databento - if applicable):** Sample Databento data designed to fail validation is correctly quarantined; only valid data in main table.
                7.  **AC7: Logs Confirm Successful Flow (Databento):** Logs confirm successful completion of each stage for Databento test data, or errors/quarantining.

* **Epic 4: Basic Querying Interface & MVP Wrap-up**
    * **Goal:** Develop the basic querying interface to retrieve stored data from TimescaleDB by symbol and date range, and ensure all MVP success metrics can be demonstrated.
    * **Stories:**
        * **Story 4.1: Design and Implement Basic Data Querying Logic**
            * **Story Statement:** As a Developer, I want to implement a data querying module (e.g., in `src/querying/query_builder.py` or as part of `src/storage/timescale_handler.py`) that uses SQLAlchemy to construct and execute SQL queries against the TimescaleDB `financial_time_series_data` table, allowing data retrieval by `security_symbol` and a `event_timestamp` date range.
            * **Acceptance Criteria (ACs):**
                1.  **AC1: Querying Module/Functions Created:** Python module(s) and functions are created (e.g., within `src/querying/` or as methods in `src/storage/timescale_handler.py`) to encapsulate data retrieval logic from TimescaleDB.
                2.  **AC2: SQLAlchemy for Query Construction:** The querying logic uses SQLAlchemy Core or ORM to construct type-safe SQL queries for the `financial_time_series_data` table (or the determined primary data table name).
                3.  **AC3: Filter by Symbol:** The querying functions accept a `security_symbol` (string) or a list of `security_symbols` (list of strings) as a parameter and correctly filter the data for the specified symbol(s).
                4.  **AC4: Filter by Date Range:** The querying functions accept `start_date` and `end_date` (Python `date` or `datetime` objects) as parameters and correctly filter the data for records where `event_timestamp` falls within this range (inclusive of start and end dates).
                5.  **AC5: Data Returned in Usable Format:** The querying functions return the retrieved data in a well-defined, documented format suitable for CLI output and potential programmatic use by other modules (e.g., a list of Python dictionaries, a list of Pydantic model instances representing the standardized record, or a Pandas DataFrame). The specific format will be determined during implementation with a preference for simplicity and ease of use.
                6.  **AC6: Handles No Data Found:** If no data matches the query criteria, the function returns an empty list (or equivalent empty structure for the chosen format) gracefully, without raising an error.
                7.  **AC7: Basic Error Handling:** Basic error handling for database connection issues or query execution failures is implemented, logging errors appropriately using the established logging framework.
                8.  **AC8: Performance Consideration & Index Utilization:** The query construction is designed to leverage existing indexes on `security_symbol` and `event_timestamp` in TimescaleDB to meet the performance NFR (under 5 seconds for a typical query of 1 month of daily data for one symbol).
                9.  **AC9: Unit Tests for Query Logic:** Unit tests are created for the querying functions. These tests will mock the SQLAlchemy engine/session and database responses to verify correct query construction based on input parameters (symbol, date range) and correct handling of various return scenarios (data found, no data found).
        * **Story 4.2: Expose Querying Functionality via CLI**
            * **Story Statement:** As a Developer, I want to add a new CLI command (e.g., `python main.py query --symbols <symbol1,symbol2> --start_date <YYYY-MM-DD> --end_date <YYYY-MM-DD> [--output_format <csv/json>])` that utilizes the data querying module to fetch data for one or more symbols and output it to the console or a specified file format (e.g., CSV, JSON).
            * **Acceptance Criteria (ACs):**
                1.  **AC1: New CLI `query` Command Implemented:** A new subcommand `query` is added to the main CLI application (`main.py` or equivalent entry point).
                2.  **AC2: Accepts Multiple Symbols Parameter:** The `query` command accepts a `--symbols` (or `-s`) argument that can take one or more security symbols. The input mechanism should be user-friendly (e.g., a comma-separated list like `--symbols AAPL,MSFT`, or allowing the argument to be specified multiple times like `-s AAPL -s MSFT`). The underlying query logic from Story 4.1 must support filtering by a list of symbols.
                3.  **AC3: Accepts Date Range Parameters:** The `query` command accepts `--start_date` (or `-sd`) and `--end_date` (or `-ed`) arguments, expecting dates in "YYYY-MM-DD" format. Input validation for date format should be present.
                4.  **AC4: Optional Output Format Parameter:** The `query` command accepts an optional `--output_format` (or `-f`) argument, supporting at least "csv" and "json". It should default to a user-friendly console output (e.g., a well-formatted table for fewer records, or JSON for more complex/numerous records if direct console table rendering is too noisy).
                5.  **AC5: Optional Output File Parameter:** The `query` command accepts an optional `--output_file` (or `-o`) argument. If provided, the output is written to this file in the specified (or default) format; otherwise, output is directed to the console.
                6.  **AC6: Invokes Query Logic:** The CLI command correctly parses all input parameters and calls the querying functions developed in Story 4.1, passing the symbols list, date range, and any other relevant query criteria.
                7.  **AC7: Handles Query Results:**
                    * If data is returned, it's formatted according to the `--output_format` and directed to the console or the specified output file.
                    * If no data is returned for the given criteria, a user-friendly message like "No data found for the specified criteria." is displayed on the console.
                8.  **AC8: Handles Errors Gracefully:** Errors from the querying logic (e.g., invalid date format provided by user, database connection issues during query) are caught, and user-friendly error messages are presented on the CLI. Detailed error information should still be logged to the log files.
                9.  **AC9: README Updated with Query CLI Usage:** The main `README.md` is updated with clear instructions and examples on how to use the `query` CLI command, including how to specify single and multiple symbols, date ranges, output formats, and file output.
## Story 4.3: Develop and Execute MVP Success Metric Verification Scripts/Tests

* **Story Statement:** As a Developer, I want to create and run scripts or automated tests that verify the MVP success metrics defined in the PRD (Goal section), such as confirming data availability, testing querying capability and performance, calculating data integrity rates, and monitoring operational stability, so that we can objectively assess if the MVP goals have been met.

* **Acceptance Criteria (ACs):**
    1. **AC1:** Data Availability Verification Script/Test:
        * A script (or automated test) is created that queries TimescaleDB (e.g., via the CLI query tool from Story 4.2 or direct SQLAlchemy calls) to confirm the presence of data for at least two of the MVP target symbols (e.g., CL, SPY) from both Interactive Brokers and Databento for a known, recent, small period (e.g., the last complete trading day).
        * The script reports success if data is found for both sources for the sample symbols and period.
    2. **AC2:** Querying Capability & Performance Test Script:
        * A script utilizes the CLI query command (from Story 4.2) to execute a predefined set of benchmark queries. This includes, at a minimum, retrieving 1 month of daily data for each of the 5 MVP symbols individually.
        * The script measures the response time for each query and verifies it meets the performance NFR (under 5 seconds per query).
        * The script confirms that queries return data (or an appropriate "no data" message if a symbol legitimately has no data for a period) without errors.
    3. **AC3:** Data Integrity Rate Calculation Method/Script:
        * A method or script is developed to analyze ingestion logs and the quarantine data location (from NFR 3 implementation) for a test period covering at least one full ingestion run for both IB and Databento (for a sample dataset).
        * The script calculates (or provides data to easily calculate) the percentage of records that failed validation versus successfully processed and stored records for both IB and Databento sources.
        * The calculated rate is documented and compared against the <1% target defined in NFR 3.
    4. **AC4:** Operational Stability Monitoring Plan & Initial Check:
        * A brief plan is documented outlining how the "95% operational stability" metric (NFR 2) will be tracked by the primary user post-MVP (e.g., daily checks of ingestion logs for completion status).
        * For this story's completion, at least one automated ingestion run for both IB and Databento (for a small, recent dataset) is executed via the CLI and completes successfully without manual intervention beyond the initial trigger, with success confirmed in the logs.
    5. **AC5:** Test Execution and Results Documentation: All verification scripts/tests developed are executed at least once. A summary report or log entries are produced documenting the execution steps and the results of each success metric check against its target.
    6. **AC6:** Scripts Version Controlled: All verification scripts and any supporting test data definition files developed are committed to the Git repository (e.g., in a dedicated `scripts/verification/` or `tests/mvp_metrics/` directory).

## Story 4.4: Finalize MVP Documentation (READMEs, Setup, Usage)

* **Story Statement:** As a Developer, I want to review and finalize all project documentation (especially the top-level `README.md`, `configs/README.md`, and module-level READMEs for `src` subdirectories) to ensure they accurately reflect the MVP's functionality, setup instructions, configuration details, CLI usage for ingestion and querying, and basic troubleshooting, so that the primary user can effectively use and maintain the system.

* **Acceptance Criteria (ACs):**
    1. **AC1:** Top-Level `README.md` Review and Update: The main project `README.md` is reviewed and updated to include:
        * A concise project overview (purpose, what it does).
        * Prerequisites for setting up and running the system (e.g., Python 3.11, Docker, Docker Compose, Git).
        * Clear, step-by-step instructions for cloning the repository, setting up the `.env` file from `.env.example`, and starting the Docker environment (`docker-compose up`).
        * Instructions for running the primary CLI commands for data ingestion (for both IB and Databento examples) and data querying (with examples for different parameters, including multiple symbols).
        * Pointers to where logs and quarantined data can be found (e.g., `logs/app.log`, `dlq/` directory if using the one from the Databento specification).
        * Basic troubleshooting tips for common setup or operational issues (e.g., TWS/Gateway not running for IB, API key issues).
        * A section outlining a 'Periodic Health Check Routine' for the primary user (e.g., checking logs, quarantine, sample queries).
        * A note clarifying that for the local MVP deployment, backup of the TimescaleDB Docker volume is the user's responsibility.
        * A brief overview of the project structure, referencing the more detailed module READMEs.
    2. **AC2:** `configs/README.md` Review and Update: The `configs/README.md` is reviewed and updated to accurately describe:
        * The structure of `system_config.yaml` and its key parameters (e.g., logging levels, default DB connection placeholders).
        * The structure of API-specific configuration files (`interactive_brokers_config.yaml`, `databento_config.yaml`), with clear explanations of all configurable parameters for the MVP (as defined in Stories 2.1 and 3.1).
        * How to add configurations for new APIs (at a high level, for future reference), emphasizing the modular design.
    3. **AC3:** `src/` Module-Level READMEs Review and Update: The concise `README.md` files in each major `src` subdirectory (`src/core/`, `src/ingestion/`, `src/transformation/`, `src/storage/`, `src/querying/`, `src/utils/`) are reviewed and updated to briefly describe the purpose and key components/modules within that directory as implemented for the MVP.
    4. **AC4:** Code Docstrings Review (Spot Check): A spot check of docstrings for key public modules, classes, and functions (especially in `core` components like `ConfigManager`, `PipelineOrchestrator`, and the base/API adapters) is performed to ensure they meet the standards defined in NFR 5 (clarity, explaining purpose, args, returns).
    5. **AC5:** Consistency and Accuracy: All documentation is checked for consistency in terminology (e.g., "symbol" vs "security_symbol" internally) and accuracy with respect to the implemented MVP functionality. Outdated comments or instructions are removed or corrected.
    6. **AC6:** Documentation Formatted and Readable: All markdown documentation is well-formatted (e.g., proper use of headings, code blocks, lists) and easy to read.

---

## Story 4.5: MVP Demonstration and Handoff Preparation

* **Story Statement:** As a Developer, I want to prepare a demonstration of the end-to-end MVP functionality (local setup, configuration, data ingestion for IB & Databento for a sample, CLI querying, log review, quarantine review) and package the final MVP codebase, so that it can be handed off to the primary user.

* **Acceptance Criteria (ACs):**
    1. **AC1:** MVP Demonstration Plan Created: A brief plan or script for demonstrating the MVP's key functionalities is outlined. This includes:
        * Setting up the project from a fresh clone.
        * Configuring API keys in the `.env` file.
        * Running `docker-compose up`.
        * Triggering data ingestion via CLI for a small sample from Interactive Brokers.
        * Triggering data ingestion via CLI for a small sample from Databento.
        * Reviewing logs to show successful ingestion (or quarantined data if test samples include deliberate errors).
        * Querying the ingested data via the CLI for both sources.
        * Showing the structure of the TimescaleDB data.
    2. **AC2:** Successful MVP Demonstration Performed: The MVP demonstration is performed (e.g., via screen share, or by the primary user following the script with developer support) and successfully showcases all functionalities outlined in the demonstration plan.
    3. **AC3:** Final Code Review & Cleanup (Minor): A final pass is made over the MVP codebase for any obvious last-minute cleanup (e.g., removing unused experimental code, ensuring all committed code aligns with the final MVP features).
    4. **AC4:** All Code Committed and Pushed: All final MVP code, including documentation, scripts, and configurations, is committed to the main branch of the GitHub repository and pushed.
    5. **AC5:** Project Archived/Tagged (Optional): Optionally, a Git tag (e.g., `v0.1.0-mvp`) is created to mark the state of the codebase at MVP completion.
    6. **AC6:** Handoff Checklist (Simple): A simple checklist of "next steps" for the primary user is prepared (e.g., how to schedule regular ingestion runs, how to monitor logs, how to add new symbols to the config).
---
## Key Reference Documents

The following documents provide critical background, research, and detailed specifications that inform this PRD and should be consulted by the Architect and development team:

1.  **Architecting a Configurable and API-Agnostic Financial Data Platform with Python and TimescaleDB:** (User-provided foundational research document detailing core architectural concepts, patterns, and technology considerations).
2.  **Databento Downloader: Detailed Specifications:** (User-provided document with in-depth specifics for the Databento API, including Pydantic models, DB schema examples, and operational algorithms).
3.  **Interactive Brokers API Integration: A Comprehensive Analysis for Hist_Data_Ingestor:** (To be provided by the project initiator, detailing authentication, endpoints, request/response structures, rate limits, and `ibapi` client library usage for fetching historical daily data via the TWS API).
4.  *(Optional)* `technical-preferences.md`: (If created by the user, containing any overriding technical preferences).

## Out of Scope Ideas Post MVP

The following features and considerations are explicitly out of scope for the current MVP but are noted for potential future development or evolution of the Hist_Data_Ingestor platform. The primary rationale for deferring these is to ensure a focused and achievable MVP for the initial 6-week timeframe, especially as this is the primary developer's first project of this scale, prioritizing getting the core system operational so that analysis can begin.

1.  **Expanded API Integration:** Systematically integrate a broader range of financial data APIs beyond the initial MVP scope of Interactive Brokers and Databento.
2.  **Enhanced Data Transformation Engine:** Introduce more sophisticated capabilities within the transformation engine, potentially allowing for more complex user-defined transformation scripts, a richer declarative rule language, or integration with external transformation services.
3.  **Advanced Monitoring & Alerting:** Implement comprehensive monitoring dashboards (e.g., using Grafana/Prometheus if deployed to cloud or other suitable tools) and automated alerting for pipeline health, data quality anomalies, API connectivity issues, and system resource utilization, beyond the MVP's basic logging and manual checks.
4.  **Full Dead-Letter Queue (DLQ) Implementation:** Develop a more formal and automated DLQ mechanism for failed ingestion tasks, including tools or procedures for inspection, automated retries with modified parameters, and easier reprocessing of quarantined data.
5.  **Architectural Evolution (Scalability):** Evaluate and potentially refactor parts of the initial monolith architecture into microservices, possibly incorporating an Event-Driven Architecture (EDA), to enhance scalability, resilience, and decoupling as data volume and processing complexity grow. This aligns with considerations in the foundational research document and acknowledges the MVP's focus on initial operational capability.
6.  **Support for Additional Data Types:** Investigate and potentially incorporate support for ingesting other types of financial data beyond daily OHLCV (e.g., fundamentals, options data, tick data for more sources, alternative datasets like news sentiment).
7.  **Advanced Querying Interface/API:** Develop a more feature-rich querying API or interface beyond the basic CLI tool, potentially with more complex filtering options, aggregations, direct integration points for analytical tools (like Jupyter notebooks or BI platforms), or a dedicated query service.
8.  **User Interface (GUI):** Develop a web-based graphical user interface for configuration management, job monitoring, data exploration, and administration, to make the platform accessible to less technical users or for easier overall management.
9.  **Formalized Data Backup and Recovery for Production:** If the system moves beyond local MVP deployment to a more critical production-like environment, implement robust, automated backup and recovery procedures for the TimescaleDB database.
10. **Transition Documentation & Strategy for Real-Time Platform:** Evaluate architectural learnings, documentation, and framework components from the Hist_Data_Ingestor (historical data platform) to inform the design and development of a future real-time data ingestion platform. Consider creating a "transition guide" or "lessons learned" document to identify reusable patterns and potential divergences.
11. **Enhanced Security Testing & Hardening:** Implement more rigorous security testing (e.g., dependency vulnerability scanning integrated into CI/CD, static/dynamic code analysis for security, penetration testing if ever exposed externally) and apply further security hardening measures based on findings.
12. **Formalized Data Retention Policy Implementation:** Define and implement automated data retention policies within TimescaleDB (e.g., dropping old chunks) based on long-term storage plans and costs.

## Initial Architect Prompt

**To the Architect Agent:**

This Product Requirements Document (PRD) for **Hist_Data_Ingestor (MVP)** has been completed and approved. Your primary objective is to design the technical architecture for this system based on the requirements detailed herein and the referenced foundational research documents ("Architecting a Configurable and API-Agnostic Financial Data Platform with Python and TimescaleDB," "Databento Downloader: Detailed Specifications," and "Interactive Brokers API Integration: A Comprehensive Analysis for Hist_Data_Ingestor").

**Key Directives & Context for Architecture Design:**

1.  **Primary Input:** This full PRD document.
2.  **Core MVP Goal:** Design a Python-based framework to ingest historical daily OHLCV data from two initial APIs (Interactive Brokers TWS API via `ibapi`, and Databento via its Python client), transform and validate this data, store it in a local TimescaleDB instance, and provide a basic CLI querying capability.
3.  **Key Technical Mandates & Assumptions (from PRD Section 5):**
    * **Architecture Style:** Monolith for MVP (internally modular, single GitHub repository).
    * **Language:** Python 3.11.
    * **Database:** TimescaleDB.
    * **Containerization:** Docker for the application and TimescaleDB, orchestrated with Docker Compose for local development.
    * **Configuration:** YAML-based external configuration for system and API specifics.
    * **Deployment Target (MVP):** Local hardware (high-end PC).
4.  **Critical Non-Functional Requirements to Address Architecturally:**
    * **Configurability (NFR 1):** Design for easy management of API and system parameters via YAML.
    * **Reliability (NFR 2):** Incorporate patterns for error handling and retries, especially for API interactions.
    * **Data Integrity (NFR 3):** Ensure the architecture supports the defined validation and quarantining strategies.
    * **Performance (NFR 4):** Design for efficient bulk ingestion (2-4 hours for initial load) and query response (<5s for typical queries). Consider asynchronous operations where appropriate.
    * **Maintainability (NFR 5):** Adhere to the specified project structure, coding standards, and documentation requirements.
    * **Deployability & Consistency (NFR 7):** Ensure the architecture is fully compatible with the Dockerized local deployment model.
    * **Developer Experience (NFR 9):** Prioritize simplicity and clarity in design choices suitable for the MVP scope.
    * **Testability (NFR 10):** Design components to be unit and integration testable as outlined.
5.  **Key Functional Components to Design (from PRD Section 2 & Epics):**
    * API Integration Layer (adapters for IB and Databento).
    * Configuration Management (`ConfigManager`).
    * Data Ingestion Orchestration (`PipelineOrchestrator`).
    * Data Transformation Engine (`RuleEngine` with YAML-defined rules).
    * Data Validation Module.
    * TimescaleDB Storage Layer (`TimescaleLoader` with SQLAlchemy, schema definition for `financial_time_series_data` hypertable, idempotent writes).
    * Basic Querying Module.
    * CLI interface for ingestion and querying.
6.  **Output:** Produce a comprehensive Architecture Document (as per `architecture-tmpl.txt`) that details the system design, component interactions, data models, sequence diagrams, technology choices (expanding on those in this PRD's Technical Assumptions), and specific implementation guidance for the development team. Ensure your design addresses all functional and non-functional requirements for the MVP. Pay particular attention to the complexities of the IB TWS API integration and the design of the API-agnostic aspects of the framework.

Please review this PRD thoroughly and proceed with the "Create Architecture" task.