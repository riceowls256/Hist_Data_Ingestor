# Hist_Data_Ingestor Product Requirements Document (PRD)

---

## 1. Goal, Objective and Context

The core problem **Hist_Data_Ingestor** addresses is the current lack of a systematic and extensible method for acquiring historical financial data from diverse APIs and ingesting it into a structured storage system. This capability is crucial for enabling subsequent in-depth data analysis, the generation of trading ideas, and the development and backtesting of trading strategies. Hist_Data_Ingestor aims to solve this by providing a Python-based framework designed for the ingestion of historical financial data. Key characteristics of this framework will include API agnosticism, high configurability (primarily through YAML files), and a reusable foundational layer. The platform will manage the end-to-end process: data ingestion from multiple APIs, data transformation, validation, persistent storage (utilizing TimescaleDB), and a querying interface.

The vision for **Hist_Data_Ingestor** is to be the central, reliable, and highly flexible platform that empowers sophisticated financial analysis and strategy development by seamlessly providing access to a vast array of historical market data.

The primary goals for the MVP are:
* Successfully ingest historical data from Databento API, including various OHLCV granularities, trades, TBBO, and statistics.
* Implement a configurable data transformation and validation pipeline for the Databento API.
* Establish a TimescaleDB instance with a defined schema capable of storing the ingested data from Databento.
* Develop a basic querying interface allowing retrieval of the stored data by symbol and date range.

---

## 2. Functional Requirements (MVP)

The major functional requirements for the MVP of **Hist_Data_Ingestor** include:

* **API Integration Framework**: The foundational mechanism to connect to external financial data APIs, initially supporting Databento.
* **Configuration Management**: A system allowing API connection details, data extraction parameters, and transformation rules to be defined externally (primarily via YAML files).
* **Data Ingestion Module**: The component responsible for robustly fetching raw historical data from the configured API.
* **Data Transformation Engine**: A module to process, clean, and standardize the fetched raw data into a consistent internal format.
* **Data Validation Module**: A component to perform quality checks and ensure the integrity of the data before storage.
* **TimescaleDB Storage Layer**: The backend database (TimescaleDB) setup, including schema definition, for persisting the validated financial time-series data.
* **Basic Querying Interface**: An initial interface or method to allow the primary user and downstream modules to retrieve stored data based on common criteria (e.g., by symbol and date range).

---

## 3. Non-Functional Requirements (MVP)

### NFR 1: Configurability (MVP)
**Requirement**: The system must be configurable via external YAML files for API connection details, data extraction parameters, and transformation rules.
**MVP Scope & Detail**:
* Configuration will cover essential parameters for Databento integration, including:
    * Authentication credentials/mechanisms (referencing secure retrieval methods like environment variables).
    * Base URLs for the APIs.
    * Key endpoint paths to be used.
    * The list of symbols and data schemas (OHLCV, Trades, TBBO, Statistics) to ingest.
    * Primary field mappings and basic transformation rules.
* The system will use YAML as the configuration format.
* The framework will be designed for increased configuration granularity in future iterations.

### NFR 2: Reliability & Operational Stability (MVP)
**Requirement**: The system must reliably ingest data and handle transient errors gracefully. The target is **95%** of scheduled ingestion runs for Databento completing without manual intervention.
**MVP Scope & Detail (Error Handling)**:
* Implement a retry mechanism (3-5 retries) with exponential backoff for transient API errors (e.g., HTTP 5xx).
* All errors must be robustly logged with sufficient context.
* A formal Dead-Letter Queue (DLQ) is deferred post-MVP. Persistent failures will be identified through critical log monitoring.

### NFR 3: Data Integrity (MVP)
**Requirement**: The system must ensure data accuracy. The target is less than **1%** of processed records from Databento failing critical validation checks.
**MVP Scope & Detail (Validation Failure Handling)**:
* Perform schema validation on raw data (e.g., using Pydantic) and quality checks on transformed data (e.g., price > 0).
* If a record fails validation, it will be logged in detail and moved to a quarantine location (e.g., an error log file).
* The system will continue to process other valid data.

### NFR 4: Performance (MVP)
**Requirement**: The system must perform data ingestion and querying within acceptable timeframes.
**MVP Scope & Detail**:
* **Initial Bulk Ingestion**: Ingest 1 year of daily historical data for 5 specified symbols from Databento within **2-4 hours**.
* **Querying Interface**: Retrieve 1 month of daily data for a single symbol in under **5 seconds**.
* The system will leverage TimescaleDB's hypertables and Python's asynchronous features to meet these targets.

### NFR 5: Maintainability (MVP)
**Requirement**: The system must be easy to understand, modify, and extend.
**MVP Scope & Detail**:
* **Project Structure**: Implement a clear project structure with distinct directories for configs, source code, and tests.
* **Coding Standards**: Adhere to PEP 8 guidelines.
* **Docstrings**: Comprehensive docstrings are required for all public interfaces.
* **README Files**: A comprehensive top-level README.md and concise READMEs in major subdirectories will be created.

### NFR 6: Usability (for Primary User/Operator - MVP)
**Requirement**: The system must be straightforward for a technical user to configure, operate, and monitor.
**MVP Scope & Detail**:
* **Configuration**: Primary setup via well-documented YAML files.
* **Execution & Interaction (CLI)**:
    * Operated via a Command Line Interface (CLI).
    * Support essential commands for ingestion (`ingest`) and status checks (`status`).
    * Provide feedback during operations, such as progress bars.
* **Feedback & Logging**: Clear real-time console output and detailed logs for troubleshooting.

### NFR 7: Deployability & Consistency (Docker - MVP)
**Requirement**: The system must be containerized using Docker to ensure consistency and ease of setup.
**MVP Scope & Detail**:
* **Application Containerization**: The Python application will be packaged into a Docker container via a `Dockerfile`.
* **Database Containerization**: The TimescaleDB instance will run as a Docker container for local development.
* **Local Environment Orchestration**: A `docker-compose.yml` file will be provided to start all services with a single command.

### NFR 8: Cost-Effectiveness (MVP Deployment)
**Requirement**: The MVP must be deployable on local hardware without incurring mandatory cloud service costs.
**MVP Scope & Detail**:
* All core components will run locally using Docker and Docker Compose.
* Technology choices will support efficient local operation.

### NFR 9: Developer Experience (MVP)
**Requirement**: The development process must be manageable and productive.
**MVP Scope & Detail**:
* **Architectural Simplicity**: The MVP will be a monolith to reduce initial complexity.
* **Technology & Library Choices**: Preference for well-documented, widely-used Python libraries.
* **Documentation & Clarity**: Adhere to the Maintainability NFR.
* **Task Breakdown**: Work will be broken down into clear Epics and User Stories.

### NFR 10: Testability (MVP)
**Requirement**: The system must be testable to ensure core functionality and data integrity.
**MVP Scope & Detail**:
* **Unit Tests**: Prioritized for critical transformation logic, validation rules, and key utility functions.
* **Integration Tests**: Focus on end-to-end connectivity for the Databento API and verifying the data loading mechanism into TimescaleDB.

---

## 4. User Interaction and Design Goals (MVP)

Interaction is primarily through a **Command Line Interface (CLI)** and **YAML configuration files**. The design goals are covered by **NFR 6 (Usability)**, which emphasizes:

* Clarity of YAML configuration files.
* Clear and effective CLI commands.
* Meaningful feedback and logging to the console.

A graphical user interface (GUI) is **out of scope** for the MVP.

---

## 5. Technical Assumptions

* **Core Language**: Python 3.11.x
* **Primary Data Store**: TimescaleDB
* **Containerization**: Docker and Docker Compose
* **Initial Architecture**: Monolith with internal modularization
* **Configuration**: External YAML files and environment variables
* **MVP API Integration**: Databento API
* **MVP Data Focus**: OHLCV (multiple granularities), trades, TBBO, and statistics for CL, SPY (or /ES), NG, HO, and RB.
* **MVP Deployment**: Local hardware
* **Source Control**: Git / GitHub
* **Repository**: A single main repository containing all modules (`configs`, `src`, `tests`, `docs`).
* **Technical Debt**: The initial monolith architecture is the primary strategic technical debt accepted for MVP.

---

## 6. Epic Overview

### Epic 1: Foundational Setup & Core Framework
**Goal**: Establish the project structure, configuration, logging, Docker environment, and TimescaleDB setup.

* **Story 1.1**: Initialize Project Repository and Directory Structure
* **Story 1.2**: Implement Core Configuration Management for System Settings
* **Story 1.3**: Establish Dockerized Development Environment
* **Story 1.4**: Implement Basic Centralized Logging Framework
* **Story 1.5**: Initialize TimescaleDB and Establish SQLAlchemy Connection

### Epic 2: Databento Integration & End-to-End Data Flow
**Goal**: Implement the complete data ingestion pipeline for the Databento API.

* **Story 2.1**: Configure Databento API Access and Parameters
* **Story 2.2**: Implement Databento API Adapter using Python Client for Data Extraction
* **Story 2.3**: Define and Implement Data Transformation Rules for Decoded Databento Records
* **Story 2.4**: Define and Implement Data Validation Rules for Decoded Databento Records
* **Story 2.5**: Integrate Databento Data Flow into Pipeline Orchestrator
* **Story 2.6**: Test End-to-End Databento Data Ingestion and Storage

### Epic 3: Basic Querying Interface & MVP Wrap-up
**Goal**: Develop the basic querying interface and verify all MVP success metrics.

* **Story 3.1**: Design and Implement Basic Data Querying Logic
* **Story 3.2**: Expose Querying Functionality via CLI
* **Story 3.3**: Develop and Execute MVP Success Metric Verification Scripts/Tests
* **Story 3.4**: Finalize MVP Documentation (READMEs, Setup, Usage)
* **Story 3.5**: MVP Demonstration and Handoff Preparation

---

## 7. Databento Data Schemas (MVP)

### 7.1. General Considerations
* **Timestamps**: Stored in UTC with nanosecond precision where possible.
* **Instrument ID**: A consistent methodology will be used.
* **Data Quality**: Validation rules will be applied.

### 7.2. OHLCV Schemas (1S, 1M, 5M, 15M, 1H, 1D)

| Field Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `instrument_id` | STRING / INTEGER | N | Unique identifier for the financial instrument. |
| `bar_timestamp_utc` | TIMESTAMP | N | Start time of the bar interval (UTC). |
| `open_price` | DECIMAL(19,9) | N | Price at the start of the interval. |
| `high_price` | DECIMAL(19,9) | N | Highest price during the interval. |
| `low_price` | DECIMAL(19,9) | N | Lowest price during the interval. |
| `close_price` | DECIMAL(19,9) | N | Price at the end of the interval. |
| `volume` | BIGINT / DECIMAL | N | Total volume traded during the interval. |
| `trade_count` | INTEGER | Y | Number of trades forming the bar. |
| `vwap` | DECIMAL(19,9) | Y | Volume-weighted average price for the interval. |
| `granularity` | STRING | N | The bar granularity (e.g., '1M', '1D'). |
| `data_source` | STRING | N | Source of the data (e.g., 'Databento'). |

### 7.3. Trades Schema

| Field Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `instrument_id` | STRING / INTEGER | N | Unique identifier for the traded instrument. |
| `trade_timestamp_utc` | TIMESTAMP (ns) | N | UTC timestamp of when the trade occurred. |
| `received_timestamp_utc` | TIMESTAMP (ns) | N | UTC timestamp of when data was received. |
| `trade_id` | STRING | N | Unique identifier for the trade. |
| `price` | DECIMAL(19,9) | N | Price at which the trade was executed. |
| `size` | INTEGER / DECIMAL | N | Volume of the trade. |
| `aggressor_side` | ENUM | Y | Indicates if the trade was an aggressive buy/sell. |
| `data_source` | STRING | N | Source of the data (e.g., 'Databento'). |

### 7.4. TBBO (Top of Book Bids and Offers) Schema

| Field Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `instrument_id` | STRING / INTEGER | N | Unique identifier for the instrument. |
| `quote_timestamp_utc` | TIMESTAMP (ns) | N | UTC timestamp of when the quote was generated. |
| `received_timestamp_utc` | TIMESTAMP (ns) | N | UTC timestamp of when data was received. |
| `bid_price` | DECIMAL(19,9) | N | Best bid price. |
| `bid_size` | INTEGER / DECIMAL | N | Quantity at best bid. |
| `ask_price` | DECIMAL(19,9) | N | Best ask price. |
| `ask_size` | INTEGER / DECIMAL | N | Quantity at best ask. |
| `data_source` | STRING | N | Source of the data (e.g., 'Databento'). |

### 7.5. Statistics Schema

| Field Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `instrument_id` | STRING / INTEGER | N | Unique identifier for the instrument. |
| `statistic_name` | STRING | N | Name of the statistic (e.g., 'DAILY_HIGH'). |
| `statistic_value_numeric` | DECIMAL(24,9) | Y | Numerical value of the statistic. |
| `statistic_value_text` | TEXT | Y | Textual value of the statistic. |
| `effective_date_utc` | DATE | N | Date the statistic is valid for (UTC). |
| `data_source` | STRING | N | Primary data provider (e.g., 'Databento'). |

---

## 8. Key Reference Documents
* Architecting a Configurable and API-Agnostic Financial Data Platform with Python and TimescaleDB
* Databento Downloader: Detailed Specifications
* (Deferred) Interactive Brokers API Integration: A Comprehensive Analysis
* (Optional) technical-preferences.md

---

## 9. Out of Scope Ideas Post MVP
* **Interactive Brokers (IB) Integration**: The complete ingestion pipeline for IB.
* **Expanded API Integration**: Adding more data sources beyond Databento and IB.
* **Advanced Monitoring & Alerting**: Dashboards (Grafana) and automated alerts.
* **Full Dead-Letter Queue (DLQ) Implementation**: Formalized handling and reprocessing of failed data.
* **Architectural Evolution (Scalability)**: Refactoring to microservices or an Event-Driven Architecture (EDA).
* **Support for Additional Data Types**: Ingesting fundamentals, options data, news sentiment, etc.
* **Advanced Querying Interface/API**: A more feature-rich query service or direct analytical tool integration.
* **User Interface (GUI)**: A web-based GUI for configuration and monitoring.
* **Formalized Data Backup and Recovery**: Robust, automated backup procedures for production.
* **Enhanced Security Testing & Hardening**: Rigorous security scanning and analysis.