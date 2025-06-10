# System Architecture

This document provides a high-level overview of the system architecture for the Hist Data Ingestor project.

- [Epics](epics/)
- [Module Documentation](modules/)

## Overview Diagram

```
mermaid
flowchart TD
    Ingestion --> Transformation --> Storage --> Querying
```

## Components
- **Ingestion:** Handles data fetching and normalization from external APIs.
- **Transformation:** Applies mapping, validation, and business rules.
- **Storage:** Persists data in timescale or other databases.
- **Querying:** Provides access to stored data for downstream consumers.

# Hist_Data_Ingestor (MVP) Architecture Document

## 1. Introduction / Preamble
This document outlines the overall project architecture for the Hist_Data_Ingestor (MVP), including backend systems, shared services, and non-UI specific concerns. Its primary goal is to serve as the guiding architectural blueprint for AI-driven development, ensuring consistency and adherence to chosen patterns and technologies.

> **Note:** As this project is primarily a backend data ingestion framework for the MVP, a separate Frontend Architecture Document is not applicable at this stage. If a significant UI were added post-MVP, such a document would then be created.

## 2. Table of Contents
- [Introduction / Preamble](#1-introduction--preamble)
- [Table of Contents](#2-table-of-contents)
- [Technical Summary](#3-technical-summary)
- [High-Level Overview](#4-high-level-overview)
- [Architectural / Design Patterns Adopted](#5-architectural--design-patterns-adopted)
- [Component View](#6-component-view)
- [Project Structure](#7-project-structure)
- [API Reference](#8-api-reference)
- [Data Models](#9-data-models)
- [Core Workflow / Sequence Diagrams](#10-core-workflow--sequence-diagrams)
- [Definitive Tech Stack Selections](#11-definitive-tech-stack-selections)
- [Infrastructure and Deployment Overview](#12-infrastructure-and-deployment-overview)
- [Error Handling Strategy](#13-error-handling-strategy)
- [Coding Standards](#14-coding-standards)
- [Overall Testing Strategy](#15-overall-testing-strategy)
- [Security Best Practices](#16-security-best-practices)
- [Key Reference Documents](#17-key-reference-documents)
- [Change Log](#18-change-log)

## 3. Technical Summary
The Hist_Data_Ingestor (MVP) is designed as a Python-based, monolithic application aimed at providing a systematic and extensible method for acquiring historical financial data. For the MVP, the focus is on daily OHLCV data from Interactive Brokers and Databento APIs. The core objective is to ingest this data, perform transformations and validations, and store it into a local TimescaleDB database, making it accessible via a basic Command Line Interface (CLI) for subsequent analysis and trading strategy development. 

Key architectural features include:
- YAML-based configuration for flexibility
- Modular internal structure to facilitate maintainability and future evolution (including the addition of other data types like tick or statistics data post-MVP)
- Docker containerization for consistent deployment
- Focus on reliability and data integrity
- Adapter pattern for API interactions
- Declarative rule engine for transformations
- Pydantic/Pandera for data validation
- Orchestration by a central pipeline manager

## 4. High-Level Overview
The Hist_Data_Ingestor MVP adopts a **Monolith architectural style** for initial development simplicity and to establish a solid foundation, as mandated by the PRD. The entire codebase will reside within a single GitHub repository.

**Primary data flow:**
1. A user initiates an ingestion job via the CLI, specifying the API source (Interactive Brokers or Databento), symbols, and date range.
2. The PipelineOrchestrator reads the job configuration (managed by ConfigManager).
3. The appropriate API Adapter (within the APIExtractionLayer) fetches raw historical data from the specified external API. This process is asynchronous where possible to enhance performance.
4. The raw data is passed to the DataTransformationEngine, which applies YAML-defined rules to convert it into a standardized internal format.
5. The standardized data undergoes validation by the DataValidationModule (using Pydantic for initial schema checks and Pandera for quality rules). Invalid data is quarantined.
6. Valid, transformed data is then loaded into a TimescaleDB hypertable by the DataStorageLayer (TimescaleLoader), ensuring idempotent writes.
7. Progress and status are tracked by the DownloadProgressTracker.
8. Users can also use the CLI to invoke the QueryingModule to retrieve stored data from TimescaleDB.

Below is a C4-style Level 1 System Context diagram and Level 2 Container diagram illustrating this overview:

```mermaid
graph TD
    subgraph Hist_Data_Ingestor_System_Context [System Context - Level 1]
        direction LR
        actor User [Primary User/Operator]
        rectangle HistDataIngestor [Hist_Data_Ingestor System\n(Python Monolith, Dockerized)]
        database TimescaleDB [(Local TimescaleDB\nDockerized)]
        rectangle IB [Interactive Brokers API]
        rectangle Databento [Databento API]

        User -- Manages/Initiates via CLI --> HistDataIngestor
        HistDataIngestor -- Ingests from/Configures --> IB
        HistDataIngestor -- Ingests from/Configures --> Databento
        HistDataIngestor -- Stores/Retrieves data --> TimescaleDB
    end
```

```mermaid
graph TD
    subgraph Hist_Data_Ingestor_Container_View [Container View - Level 2]
        direction LR
        actor User [Primary User/Operator]

        rectangle AppContainer [Hist_Data_Ingestor Application\n(Docker Container)\n---Monolithic Python Application---] {
            rectangle CLI [CLI Interface\n(Typer)]
            rectangle Orchestrator [Pipeline Orchestrator]
            rectangle ConfigMgr [Config Manager]
            rectangle APIAdapters [API Extraction Layer\n(IB & Databento Adapters)]
            rectangle Transformer [Data Transformation Engine]
            rectangle Validator [Data Validation Module]
            rectangle StorageLoader [Data Storage Layer\n(TimescaleLoader w/ SQLAlchemy)]
            rectangle QueryModule [Querying Module]
            rectangle ProgressTracker [Download Progress Tracker]
        }

        database DBContainer [(TimescaleDB\n(Docker Container))]

        rectangle IB_API [Interactive Brokers API\n(External)]
        rectangle Databento_API [Databento API\n(External)]

        User -- Interacts via --> CLI

        CLI --> Orchestrator
        CLI --> QueryModule

        Orchestrator --> ConfigMgr
        Orchestrator --> APIAdapters
        Orchestrator --> Transformer
        Orchestrator --> Validator
        Orchestrator --> StorageLoader
        Orchestrator --> ProgressTracker

        APIAdapters -- Fetches data --> IB_API
        APIAdapters -- Fetches data --> Databento_API

        StorageLoader -- Writes/Reads --> DBContainer
        QueryModule -- Reads --> DBContainer
        ProgressTracker -- Writes/Reads --> DBContainer
    end
```

## 5. Architectural / Design Patterns Adopted
The Hist_Data_Ingestor MVP will adhere to several key architectural and design patterns to ensure modularity, extensibility, and maintainability, as guided by the "Architecting a Configurable and API-Agnostic Financial Data Platform with Python and TimescaleDB" document (Framework Architecture Document).

- **Monolith Architecture (for MVP):** The system will be built as a single, deployable Python application.
  - *Rationale:* Simplifies initial development, deployment, and operational management for the MVP, aligning with PRD NFR 9. The internal structure will be modular to allow for potential future refactoring into microservices if required.
- **Modular Design:** Internally, the monolith will be divided into distinct modules with clear responsibilities and well-defined interfaces (e.g., ingestion, transformation, storage, core services).
  - *Rationale:* Promotes separation of concerns, making the system easier to understand, develop, test, and maintain. This is crucial for supporting future extensions, including different data types or APIs.
- **Adapter Pattern:** Used for the APIExtractionLayer to interact with external financial data APIs. Each API (Interactive Brokers, Databento) will have its own adapter implementing a common interface.
  - *Rationale:* Decouples the core application logic from the specific details of external APIs, enhancing API agnosticism and making it easier to add new APIs or modify existing integrations.
- **Strategy Pattern (Conceptual for Configuration):** While not explicitly creating strategy objects for every configuration choice, the principle applies to how configuration drives behavior. Different configurations (e.g., for API authentication, transformation rules) will lead to different operational strategies within components without changing the component's core code.
  - *Rationale:* Allows for flexible behavior modification through external YAML configuration, supporting configurability (NFR 1).
- **Repository Pattern (Conceptual for Data Storage):** The DataStorageLayer (TimescaleLoader) will act as a repository, abstracting the specifics of TimescaleDB interaction from the rest of the application.
  - *Rationale:* Centralizes data access logic, improves testability by allowing data access to be mocked, and decouples business logic from database specifics.
- **Declarative Configuration:** System behavior, especially for API specifics, data transformations, and validations, will be driven by external YAML configuration files. Pydantic models will be used for parsing and validating these configurations.
  - *Rationale:* Enhances flexibility, maintainability, and allows some changes without code modification, fulfilling NFR 1.
- **Pipeline Orchestration:** A central PipelineOrchestrator component will manage the sequence of operations in the ETL (Extract, Transform, Load) process.
  - *Rationale:* Provides a clear and manageable flow for data processing, error handling, and state tracking.

## 6. Component View
The Hist_Data_Ingestor MVP is composed of several key logical components, designed to work together within the monolithic application structure. Each component has a distinct responsibility in the data ingestion, processing, storage, and querying pipeline.

### ConfigManager
- **Responsibility:** Provides centralized and type-safe access to all application configurations. It loads settings from YAML files (system-level, API-specific, transformation rules) and environment variables, validating them using Pydantic models. It makes these configurations available to other components that require them.
- **Key Interactions:** Used by PipelineOrchestrator, APIExtractionLayer, DataTransformationEngine, DataStorageLayer, and Logging modules to retrieve their respective configurations.

### APIExtractionLayer
- **Responsibility:** Manages all direct communication with external financial data APIs (Interactive Brokers via ib_insync, Databento via its Python client). This layer includes specific API Adapters (e.g., InteractiveBrokersAdapter, DatabentoAdapter) that implement a common BaseAdapter interface. These adapters handle API-specific connection, authentication, request formation, data fetching (for daily OHLCV in MVP), pagination logic, and initial response parsing. It also incorporates error handling and retry mechanisms (e.g., using tenacity) respectful of API rate limits. Asynchronous operations (asyncio) are utilized here for I/O-bound tasks.
- **Key Interactions:** Invoked by the PipelineOrchestrator to fetch raw data. Receives API configurations from ConfigManager.

### DataTransformationEngine (RuleEngine)
- **Responsibility:** Transforms raw data received from the APIExtractionLayer into a standardized internal data model suitable for validation and storage. It loads and applies declarative transformation rules defined in API-specific YAML files (e.g., field mapping, type conversions). It supports invoking custom Python functions for complex transformations not covered by YAML rules.
- **Key Interactions:** Receives raw data from the APIExtractionLayer (via PipelineOrchestrator). Uses transformation rule configurations provided by ConfigManager. Outputs standardized data to the DataValidationModule.

### DataValidationModule
- **Responsibility:** Ensures data quality and integrity. It performs two stages of validation:
  1. Initial validation of raw API responses against Pydantic models.
  2. Post-transformation validation of the standardized data records using Pandera schemas to check against business rules and data quality constraints (e.g., price > 0, high >= low). Failing records are logged and quarantined as per PRD NFR 3.
- **Key Interactions:** Receives data from the DataTransformationEngine. Validated data is passed to the DataStorageLayer. Quarantined data is handled according to defined procedures.

### DataStorageLayer (TimescaleLoader)
- **Responsibility:** Manages all persistence operations to the TimescaleDB database. This includes creating and managing the schema for hypertables (e.g., daily_ohlcv_data) using SQLAlchemy models. It ensures idempotent writes using INSERT ... ON CONFLICT DO UPDATE (UPSERT) strategies to prevent data duplication. It will handle batch insertions for efficiency.
- **Key Interactions:** Receives validated, transformed data from the DataValidationModule. Interacts with TimescaleDB. Database connection parameters are sourced from ConfigManager.

### DownloadProgressTracker
- **Responsibility:** Maintains the state of data ingestion jobs and their individual chunks (e.g., API source, symbols, date range, last downloaded timestamp/watermark, status, retry count) in a dedicated TimescaleDB table. This enables resumable downloads and incremental updates.
- **Key Interactions:** Updated by the PipelineOrchestrator after each processing step (fetch, store). Read by the PipelineOrchestrator to determine the next steps for a job. Interacts with TimescaleDB via the DataStorageLayer or directly using SQLAlchemy.

### PipelineOrchestrator
- **Responsibility:** Coordinates the entire ETL workflow for a given data ingestion job. It sequences calls to the APIExtractionLayer, DataTransformationEngine, DataValidationModule, and DataStorageLayer. It manages date range chunking for historical data and updates the DownloadProgressTracker. It also handles high-level error management for the pipeline.
- **Key Interactions:** Triggered by the CLI. Uses ConfigManager for job definitions. Interacts with all other main data processing components and the DownloadProgressTracker.

### QueryingModule
- **Responsibility:** Provides functionality to retrieve stored financial data from TimescaleDB based on specified criteria (e.g., symbol, date range). It constructs and executes SQL queries, likely using SQLAlchemy.
- **Key Interactions:** Invoked by the CLI. Reads data from TimescaleDB via the DataStorageLayer or direct SQLAlchemy interaction.

### CLI (Command Line Interface)
- **Responsibility:** Serves as the primary user interface for the MVP. It allows users to initiate data ingestion jobs (specifying APIs, symbols, dates) and to query stored data. Built using Typer.
- **Key Interactions:** Takes user commands and parameters. Invokes the PipelineOrchestrator for ingestion tasks and the QueryingModule for data retrieval tasks. Provides feedback and output to the user on the console.

### LoggingModule (Cross-Cutting Concern)
- **Responsibility:** Provides a consistent logging mechanism across all components. Uses Python's standard logging module configured with structlog for structured JSON output. Facilitates debugging and monitoring.
- **Key Interactions:** Used by all other components to log events, errors, and contextual information.

```mermaid
graph LR
    subgraph UserInteraction
        CLI_Tool[CLI (Typer)]
    end

    subgraph ApplicationCore [Hist_Data_Ingestor Monolith]
        direction TB
        Orchestrator[Pipeline Orchestrator]
        Config[ConfigManager]
        Tracker[DownloadProgressTracker]

        subgraph IngestionPipeline
            direction LR
            API_Extract[APIExtractionLayer]
            Transformer[DataTransformationEngine]
            Validator[DataValidationModule]
            Storer[DataStorageLayer (TimescaleLoader)]
        end

        QueryMod[QueryingModule]
        Logger[Logging (Global - structlog)]
    end

    subgraph ExternalServices
        direction RL
        DB[(TimescaleDB)]
        IB_API[Interactive Brokers API]
        DBento_API[Databento API]
    end

    CLI_Tool -- Initiates Job/Query --> Orchestrator
    CLI_Tool -- Initiates Query --> QueryMod

    Orchestrator -- Uses --> Config
    Orchestrator -- Updates/Reads --> Tracker
    Orchestrator -- Calls --> API_Extract
    API_Extract -- Gets Raw Data --> Transformer
    Transformer -- Transforms --> Validator
    Validator -- Validates --> Storer
    Storer -- Stores --> DB

    QueryMod -- Retrieves --> DB

    API_Extract -- Connects to --> IB_API
    API_Extract -- Connects to --> DBento_API

    Tracker -- Persists to/Reads from --> DB

    %% Cross-cutting
    Config -.-> API_Extract
    Config -.-> Transformer
    Config -.-> Validator
    Config -.-> Storer
    Config -.-> QueryMod
    Config -.-> Tracker
    Config -.-> Logger

    Orchestrator -.-> Logger
    API_Extract -.-> Logger
    Transformer -.-> Logger
    Validator -.-> Logger
    Storer -.-> Logger
    QueryMod -.-> Logger
    Tracker -.-> Logger
    CLI_Tool -.-> Logger

    classDef component fill:#f9f,stroke:#333,stroke-width:2px;
    classDef external fill:#lightblue,stroke:#333,stroke-width:2px;
    classDef database fill:#lightgrey,stroke:#333,stroke-width:2px;
    classDef user_interaction fill:#lightgreen,stroke:#333,stroke-width:2px;

    class CLI_Tool user_interaction;
    class Orchestrator,Config,Tracker,API_Extract,Transformer,Validator,Storer,QueryMod,Logger component;
    class DB database;
    class IB_API,DBento_API external;
```

## 7. Project Structure
The project will adhere to the following directory structure. This structure is designed to promote a clear separation of concerns, making it intuitive to locate code related to specific functionalities (e.g., ingestion, transformation) and configurations for different APIs.

```plaintext
hist_data_ingestor/
├── .claude/                    # Future use: Claude AI tool specific configurations/cache
├── .github/                    # CI/CD workflows (e.g., GitHub Actions)
│   └── workflows/
│       └── main.yml
├── .vscode/                    # VSCode settings (optional)
│   └── settings.json
├── ai-docs/                    # AI-related documentation (e.g., prompts, agent interaction logs)
├── build/                      # Compiled output (if applicable, often git-ignored)
├── configs/                    # Centralized directory for all configurations
│   ├── system_config.yaml          # Global settings: DB, logging, orchestration params
│   ├── api_specific/             # Subdirectory for individual API configurations
│   │   ├── interactive_brokers_config.yaml # Config for Interactive Brokers
│   │   └── databento_config.yaml         # Config for Databento
│   └── validation_schemas/         # Schemas for validating API data / transformed data
│       ├── ib_raw_schema.json          # JSONSchema for raw Interactive Brokers data (conceptual)
│       └── databento_raw_schema.json   # JSONSchema for raw Databento data (Pydantic models serve this role)
├── docs/                       # Project documentation (PRD, Arch, this doc, etc.)
│   ├── index.md
│   ├── prd.md
│   ├── architecture.md           # This document
│   └── ... (other .md files for epics, stories, etc.)
├── infra/                      # Infrastructure as Code (e.g., Docker Compose files for local setup)
│   └── docker-compose.yml
├── logs/                       # Application logs (git-ignored)
│   └── app.log
├── specs/                      # Detailed technical specifications (e.g., data structures, specific designs)
├── venv/                       # Python virtual environment (git-ignored)
├── src/                        # Application source code
│   ├── __init__.py
│   ├── core/                     # Core framework logic
│   │   ├── __init__.py
│   │   ├── pipeline_orchestrator.py  # Manages the overall ETL flow
│   │   ├── config_manager.py         # Loads and manages configurations
│   │   └── module_loader.py          # Dynamically loads API-specific modules (Post-MVP or if complex)
│   ├── ingestion/                  # Data extraction components
│   │   ├── __init__.py
│   │   ├── api_adapters/             # Adapter pattern implementations for each API
│   │   │   ├── __init__.py
│   │   │   ├── base_adapter.py         # Abstract base class for adapters
│   │   │   ├── interactive_brokers_adapter.py
│   │   │   └── databento_adapter.py
│   │   └── data_fetcher.py           # Orchestrates data fetching using adapters (can be part of orchestrator)
│   ├── transformation/             # Data transformation and validation
│   │   ├── __init__.py
│   │   ├── rule_engine/              # Engine to apply declarative transformation rules
│   │   │   ├── __init__.py
│   │   │   └── engine.py
│   │   ├── mapping_configs/          # YAML files defining field mappings per API
│   │   │   ├── interactive_brokers_mappings.yaml
│   │   │   └── databento_mappings.yaml
│   │   └── validators/               # Data validation logic (e.g., using Pandera)
│   │       ├── __init__.py
│   │       └── data_validator.py
│   ├── storage/                    # Data loading and database interaction
│   │   ├── __init__.py
│   │   ├── timescale_loader.py       # TimescaleDB specific logic (hypertables, upserts)
│   │   └── models.py                 # SQLAlchemy ORM models for TimescaleDB tables
│   ├── querying/                   # Module for querying stored data
│   │   ├── __init__.py
│   │   └── query_builder.py          # Builds dynamic queries against TimescaleDB
│   ├── cli/                        # CLI specific modules
│   │   ├── __init__.py
│   │   └── commands.py               # Typer commands
│   ├── utils/                      # Shared utilities
│   │   ├── __init__.py
│   │   └── custom_logger.py          # Logging setup
│   └── main.py                     # Application entry point (CLI using Typer)
├── tests/                      # Automated tests
│   ├── __init__.py
│   ├── fixtures/                   # Test fixtures, sample API responses
│   ├── unit/                     # Unit tests (mirroring src structure)
│   │   ├── core/
│   │   └── ingestion/
│   │   └── ...
│   └── integration/                # Integration tests
│       └── test_data_pipeline.py
├── .env.example                # Template for environment variables
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python package dependencies
├── pyproject.toml              # Project metadata, build system config (e.g., for Black, Flake8, MyPy)
├── Dockerfile                  # Docker build instructions for the application
└── README.md                   # Project overview and setup instructions
```

**Key Directory Descriptions (with additions):**

- `.claude/`: Intended for future use with the Claude AI tool, possibly for configurations or cached data. (Note: If this contains user-specific settings, it should typically be added to .gitignore. If it contains project-wide Claude configurations intended for sharing, it would be version-controlled.)
- `ai-docs/`: Contains documentation specifically related to AI development for this project, such as prompt engineering examples, agent interaction logs, or AI-assisted design artifacts.
- `configs/`: Centralized directory for all configurations, including system-wide settings, API-specific parameters, and validation schemas.
  - `api_specific/`: Contains individual YAML configuration files for each data source API (e.g., interactive_brokers_config.yaml, databento_config.yaml).
- `docs/`: Contains general project planning and reference documentation, including this architecture document, the PRD, epics, and stories.
- `infra/`: Holds Infrastructure as Code definitions. For the MVP, this will primarily contain the docker-compose.yml file for local environment orchestration.
- `logs/`: Directory for storing application log files. This directory will be git-ignored.
- `specs/`: Houses detailed technical specification documents that may be too granular for the docs/ folder, such as specific data format specifications, detailed API contract definitions, or in-depth designs for particular components.
- `src/`: Contains the main application source code, organized into sub-modules for clear separation of concerns.
  - `core/`: Houses fundamental framework logic like the PipelineOrchestrator and ConfigManager.
  - `ingestion/`: Contains components related to data extraction from external APIs, including the API adapters.
  - `transformation/`: Includes the RuleEngine for applying declarative transformation rules and data validation logic. `mapping_configs/` within this directory will store API-specific field mapping YAMLs.
  - `storage/`: Manages interactions with TimescaleDB, including data loading logic (TimescaleLoader) and SQLAlchemy table models.
  - `querying/`: Modules responsible for building and executing queries to retrieve data from storage.
  - `cli/`: Contains the modules for the command-line interface, using Typer.
  - `utils/`: Shared utility functions, such as custom logging configurations.
  - `main.py`: The main entry point for the Python application, likely initializing and running the CLI.
- `tests/`: Contains all automated tests, with subdirectories for unit and integration tests, and fixtures. Unit tests should mirror the src/ directory structure.
- **Root Files:** (Descriptions as before for .env.example, requirements.txt, pyproject.toml, Dockerfile, README.md)

> **Notes on Project Structure:**
>
> This structure is designed to be modular, allowing new APIs, transformation rules, or storage mechanisms to be added with minimal impact on other parts of the system. It closely follows the recommendations from the "Framework Architecture Document" and is tailored for a Python-based data engineering monolith.

## 8. API Reference
This section outlines the external APIs consumed by the Hist_Data_Ingestor system for the MVP and any internal APIs it might expose (though for the MVP monolith, internal APIs in the traditional inter-service sense are not applicable).

### External APIs Consumed

#### 1. Interactive Brokers (IB) API (via ib_insync)

- **Purpose:** To fetch historical daily OHLCV data for specified financial instruments.
- **Client Library:** ib_insync (Python library).
- **Connection Details (via ib_insync):**
  - Host: Typically `127.0.0.1` (for a locally running TWS/IB Gateway).
  - Port: Configurable, e.g., 7497 (TWS live), 7496 (TWS paper), 4001 (Gateway live), 4002 (Gateway paper).
  - clientId: A unique integer for the API connection.
  - Authentication: Relies on an active, authenticated session with a running Trader Workstation (TWS) or IB Gateway instance. The ib_insync client connects to this authenticated instance. Credentials for TWS/Gateway login are managed by the user.
- **Key Function Used (via ib_insync for Daily OHLCV):** `ib.reqHistoricalData()`
  - **Description:** Requests historical bar data for a specified contract.
  - **Key ib_insync.Contract Parameters for Request:**
    - symbol: e.g., 'SPY', 'ES', 'CL'.
    - secType: e.g., 'STK' (for SPY), 'FUT' (for /ES, CL, NG, HO, RB), 'CONTFUT' (for continuous futures, if used for daily series).
    - exchange: e.g., 'ARCA' (for SPY), 'GLOBEX' (for ES), 'NYMEX' (for CL, NG, HO, RB).
    - currency: e.g., 'USD'.
    - lastTradeDateOrContractMonth: Required for specific futures contracts if not using CONTFUT.
  - **Key reqHistoricalData Parameters:** contract, endDateTime, durationStr, barSizeSetting ("1 day" for MVP), whatToShow ('ADJUSTED_LAST' for SPY, 'TRADES' for futures - with back-adjustment as a separate concern), useRTH (True), formatDate (2 for datetime objects).

**Example Code Snippet (ib_insync):**
```python
from ib_insync import IB, Stock, util
import datetime

ib = IB()
try:
    # Host, port, and clientId will come from ConfigManager
    ib.connect(host='127.0.0.1', port=7497, clientId=1) 

    contract = Stock('SPY', 'ARCA', 'USD', primaryExchange='ARCA')
    ib.qualifyContracts(contract)

    bars = ib.reqHistoricalData(
        contract,
        endDateTime='', 
        durationStr='30 D', 
        barSizeSetting='1 day',
        whatToShow='ADJUSTED_LAST', 
        useRTH=True,
        formatDate=2 
    )

    if bars:
        # Further processing by DataTransformationEngine
        pass 
except Exception as e:
    print(f"Error with IB: {e}") 
finally:
    if ib.isConnected():
        ib.disconnect()
```
*Snippet adapted from IB Spec Appendix B*

- **Success Response Structure (from ib_insync):** A list of `ib_insync.objects.BarData` objects. Key attributes include: `date` (datetime.date or datetime.datetime), `open_` (float), `high` (float), `low` (float), `close` (float), `volume` (float or Decimal), `barCount` (int), `average` (float) (VWAP).
- **Error Handling:** Handle common error codes (200, 162, 165, 420, 2105, 10186) from ib_insync error events/exceptions.
- **Rate Limits:** No more than 60 historical data queries in a 600-second period. Client-side throttling is required.
- **Links:** [TWS API Docs](https://interactivebrokers.github.io/tws-api/) | [ib_insync Docs](https://ib-insync.readthedocs.io/)

#### 2. Databento API

- **Purpose:** To fetch historical daily OHLCV data for specified financial instruments.
- **Client Library:** databento-python.
- **Authentication:** API Key passed to the `databento.Historical` client constructor (sourced from environment variable `DATABENTO_API_KEY`).
- **Key Function Used (via databento-python for Daily OHLCV):** `client.timeseries.get_range()`
  - **Description:** Retrieves a DBN (Databento Binary Encoding) stream.
  - **Key get_range Parameters:**
    - dataset (e.g., "GLBX.MDP3")
    - schema ("ohlcv-1d" for MVP)
    - symbols (list of strings or "ALL_SYMBOLS")
    - start (datetime.date or YYYY-MM-DD string)
    - end (datetime.date or YYYY-MM-DD string, exclusive)
    - stype_in ("raw_symbol", "instrument_id", "continuous")

**Example Code Snippet (databento-python):**
```python
import databento
import datetime

# API key will come from ConfigManager
api_key = "YOUR_DATABENTO_API_KEY" # Placeholder
client = databento.Historical(api_key)

dataset_id = "GLBX.MDP3" 
schema_type = "ohlcv-1d" 
symbols_list = ["ES.c.0"] 
start_date = datetime.date(2023, 1, 1)
end_date = datetime.date(2023, 1, 5)

try:
    data_dbn_store = client.timeseries.get_range(
        dataset=dataset_id,
        schema=schema_type,
        symbols=symbols_list,
        start=start_date,
        end=end_date,
        stype_in="continuous" 
    )
    # DBNStore is iterated for DBN records (e.g., OhlcvMsg)
    # for record in data_dbn_store:
    #     pass # Processing by DataTransformationEngine
except databento.common.error.BentoError as e: # Catch base BentoError
    print(f"Databento error: {e}")
```
*Snippet conceptualized from Databento Spec sections*

- **Success Response Structure:** `DBNStore` object, iterating yields DBN records like `databento.dbn.OhlcvMsg`. Key fields in Pydantic OhlcvMsg: `hd.ts_event`, `hd.instrument_id`, `open`, `high`, `low`, `close`, `volume`.
- **Error Handling:** Handle `BentoClientError` (4xx) and `BentoServerError` (5xx), respecting `Retry-After` headers for 429 errors.
- **Rate Limits:** Client library has built-in rate limiting (e.g., ~100 requests/sec/IP).
- **Link:** [Databento Docs](https://databento.com/docs)

### Internal APIs Provided

For the MVP, which is a monolithic application, there are no internal APIs exposed in the sense of separate network services. Components interact via Python method calls.

## 9. Data Models
This section details the primary data structures used within the Hist_Data_Ingestor system.

### 1. Standardized Internal Data Model for Daily OHLCV

After raw data is fetched and processed by the DataTransformationEngine, it will conform to this standardized internal Python structure (conceptually, likely represented by Pydantic models):

- `ts_event`: `datetime.datetime` (timezone-aware, UTC) - Start of the daily bar.
- `symbol`: `str` - Standardized financial instrument symbol.
- `api_source`: `str` - Identifier for the source API (e.g., 'interactive_brokers', 'databento').
- `open_price`: `Decimal` - Opening price.
- `high_price`: `Decimal` - Highest price.
- `low_price`: `Decimal` - Lowest price.
- `close_price`: `Decimal` - Closing price.
- `volume`: `Decimal` or `int` - Trading volume.
- `metadata_`: `dict` (for JSONB storage) - Additional API-specific or contextual data.

### 2. Database Schema (TimescaleDB)

**daily_ohlcv_data Hypertable**

- **Purpose:** To store standardized daily OHLCV data.
- **SQLAlchemy Model (Conceptual - in `src/storage/models.py`):**

```python
from sqlalchemy import Column, DateTime, String, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class DailyOhlcvData(Base):
    __tablename__ = 'daily_ohlcv_data'

    ts_event = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    symbol = Column(String, primary_key=True, nullable=False)
    api_source = Column(String, primary_key=True, nullable=False)

    open_price = Column(Numeric(precision=19, scale=4), nullable=False)
    high_price = Column(Numeric(precision=19, scale=4), nullable=False)
    low_price = Column(Numeric(precision=19, scale=4), nullable=False)
    close_price = Column(Numeric(precision=19, scale=4), nullable=False)
    volume = Column(Numeric(precision=22, scale=0), nullable=False)

    metadata_ = Column(JSONB, nullable=True)
```

- **TimescaleDB Hypertable Configuration:**

```sql
SELECT create_hypertable('daily_ohlcv_data', by_range('ts_event', chunk_time_interval => INTERVAL '7 days'), if_not_exists => TRUE);
```
(Chunk interval configurable).

- **Primary Key / Unique Constraint:** (`ts_event`, `symbol`, `api_source`).
- **Key Indexes:**
  - Index on `ts_event` (automatic by TimescaleDB).
  - Composite index on (`symbol`, `ts_event` DESC).
  - Optional: (`api_source`, `symbol`, `ts_event` DESC).
  - GIN index on `metadata_` (post-MVP if needed).
- **Rationale for Numeric:** Ensures exact precision for financial data.
- **Extensibility:** Other data types (tick, MBO) will have separate, dedicated hypertables.

## 10. Core Workflow / Sequence Diagrams
This section illustrates the primary workflow for a data ingestion job.

### Main Data Ingestion Workflow

```mermaid
sequenceDiagram
    actor User
    participant CLI
    participant PipelineOrchestrator
    participant ConfigManager
    participant APIExtractionLayer
    participant DataTransformationEngine
    participant DataValidationModule
    participant DataStorageLayer
    participant DownloadProgressTracker
    participant TimescaleDB

    User->>CLI: Run ingest command (e.g., --api databento --symbols AAPL --start 2023-01-01 --end 2023-01-05)
    CLI->>PipelineOrchestrator: initiate_ingestion_job(job_params)
    PipelineOrchestrator->>ConfigManager: load_job_config(job_params.api)
    ConfigManager-->>PipelineOrchestrator: return api_config
    
    PipelineOrchestrator->>DownloadProgressTracker: get_or_create_job_chunks(job_params, api_config)
    DownloadProgressTracker-->>PipelineOrchestrator: return list_of_chunks_to_process
    
    loop For each chunk in list_of_chunks_to_process
        PipelineOrchestrator->>DownloadProgressTracker: update_chunk_status(chunk_id, 'in_progress')
        PipelineOrchestrator->>APIExtractionLayer: fetch_data(chunk_details, api_config)
        APIExtractionLayer-->>PipelineOrchestrator: return raw_api_data_batch
        
        alt Raw data fetched successfully
            PipelineOrchestrator->>DataTransformationEngine: transform_data(raw_api_data_batch, api_config.mapping_rules)
            DataTransformationEngine-->>PipelineOrchestrator: return standardized_data_batch
            
            PipelineOrchestrator->>DataValidationModule: validate_data(standardized_data_batch, api_config.validation_rules)
            DataValidationModule-->>PipelineOrchestrator: return valid_data_batch, quarantined_records
            
            opt If quarantined_records exist
                PipelineOrchestrator->>DataStorageLayer: save_quarantined_records(quarantined_records)
                DataStorageLayer->>TimescaleDB: Store quarantined data (e.g., error file/table)
            end
            
            opt If valid_data_batch exists
                PipelineOrchestrator->>DataStorageLayer: store_data(valid_data_batch)
                DataStorageLayer->>TimescaleDB: Upsert data into hypertable (e.g., daily_ohlcv_data)
                TimescaleDB-->>DataStorageLayer: storage_success
                DataStorageLayer-->>PipelineOrchestrator: batch_storage_confirmation
                PipelineOrchestrator->>DownloadProgressTracker: update_chunk_status(chunk_id, 'completed', last_ts_in_batch)
            else
                 PipelineOrchestrator->>DownloadProgressTracker: update_chunk_status(chunk_id, 'completed_empty')
            end
        else API fetch or other critical error
            PipelineOrchestrator->>DownloadProgressTracker: update_chunk_status(chunk_id, 'failed', error_details)
            PipelineOrchestrator->>CLI: Report error for chunk
        end
    end
    
    PipelineOrchestrator-->>CLI: Job summary (success/failures)
    CLI-->>User: Display job summary
```

**Diagram Explanation:**

1. The User initiates an ingestion job via the CLI.
2. The CLI calls the PipelineOrchestrator.
3. The PipelineOrchestrator uses ConfigManager for job configurations and DownloadProgressTracker for managing data chunks.
4. For each chunk, it calls APIExtractionLayer (fetch), DataTransformationEngine (transform), DataValidationModule (validate), and DataStorageLayer (store to TimescaleDB).
5. The PipelineOrchestrator updates DownloadProgressTracker and handles error reporting.
6. A job summary is reported back to the User via the CLI. (Retry mechanisms within components are abstracted here.)

## 11. Definitive Tech Stack Selections
This section outlines the definitive technology choices for the Hist_Data_Ingestor (MVP) project.

| Category            | Technology         | Version / Details                                 | Description / Purpose                                 | Justification (Optional)                                      |
|---------------------|-------------------|---------------------------------------------------|-------------------------------------------------------|----------------------------------------------------------------|
| Languages           | Python            | 3.11.x                                            | Primary backend language for the application           | Mandated by PRD; good for data processing & scripting.         |
| Runtime             | Python Interpreter| 3.11.x                                            | Execution environment for the Python application      | Matches language version.                                      |
| Databases           | TimescaleDB       | Latest Stable (e.g., 2.14.x with PostgreSQL 15/16) | Primary time-series data store, running in Docker      | Mandated by PRD; optimized for time-series data, PostgreSQL-based. |
| Configuration       | YAML              | N/A                                               | Format for configuration files (system, API, transforms)| Mandated by PRD; human-readable, good for structured data.      |
|                     | Pydantic          | >=2.5.0                                           | Data validation and settings management for Python     | For parsing/validating YAML configs & API responses. Version from Databento spec (>=2.0), using a recent stable. |
|                     | Pydantic-Settings | >=2.1.0                                           | For loading Pydantic models from env vars/files        | Works with Pydantic for layered configuration. Version from Databento spec (>=2.0), using a recent stable. |
|                     | python-dotenv      | Latest Stable                                     | Loading environment variables from .env files for local dev | Standard practice for local development secrets/config.         |
| API Interaction     | ib_insync         | Latest Stable (e.g., 0.9.8x)                      | Python client for Interactive Brokers TWS API          | Recommended for IB integration; built on asyncio.               |
|                     | databento-python  | >=0.52.0                                          | Official Python client for Databento API               | For Databento data ingestion. Version from Databento spec.      |
|                     | aiohttp           | Latest Stable                                     | Asynchronous HTTP client/server for Python             | For asyncio-based API calls if needed directly, or used by SDKs.|
|                     | tenacity          | >=8.2.0                                           | General-purpose retrying library for Python            | For robust API call retries (exponential backoff, jitter). Version from Databento spec. |
| Database ORM/Client | SQLAlchemy        | Latest Stable (e.g., 2.0.x)                       | Python SQL toolkit and ORM                            | For interacting with TimescaleDB (PostgreSQL).                  |
|                     | psycopg2-binary   | >=2.9.5                                           | PostgreSQL adapter for Python (SQLAlchemy dependency)  | Required for SQLAlchemy to connect to PostgreSQL/TimescaleDB. Version from Databento spec. |
| Data Handling       | Pandera           | Latest Stable                                     | Data validation for Pandas DataFrames                  | For post-transformation data quality checks.                     |
|                     | Pandas            | >=2.0.0                                           | Data analysis and manipulation library                 | Used with Pandera and for data processing. Version from Databento spec. |
| CLI Development     | Typer             | Latest Stable                                     | Library for building Command Line Interfaces           | For creating a user-friendly CLI.                                |
| Logging             | Python logging module | Built-in                                        | Standard Python logging facility (used with structlog) | Core logging functionality.                                     |
|                     | structlog         | >=23.0.0                                          | Advanced structured logging for Python                 | For flexible, powerful, and context-aware structured JSON logging. Version from Databento spec. |
| Containerization    | Docker            | Latest Stable                                     | Containerization platform                              | For application and database containerization.                   |
|                     | Docker Compose    | Latest Stable (v2.x)                              | Tool for defining and running multi-container Docker apps | For orchestrating local development environment.                 |
| Version Control     | Git               | Latest Stable                                     | Distributed version control system                     | For source code management.                                      |
|                     | GitHub            | N/A                                               | Platform for hosting Git repositories                  | Preferred hosting platform.                                      |
| Code Quality        | Black             | Latest Stable                                     | Python code formatter                                  | To ensure consistent code style.                                 |
|                     | Flake8            | Latest Stable                                     | Python linter (wrapper around PyFlakes, pycodestyle, McCabe) | For identifying code errors and style issues.                    |
|                     | MyPy              | Latest Stable                                     | Optional static type checker for Python                | For enforcing type safety.                                       |

## 12. Infrastructure and Deployment Overview
This section outlines the infrastructure, deployment strategy, and operational environment for the Hist_Data_Ingestor (MVP).

- **Target Deployment Environment (MVP):** Local hardware (high-end PC, as per PRD NFR 8).
- **Containerization:** Docker for the application and TimescaleDB, orchestrated with Docker Compose (`docker-compose.yml`) for local development. Includes a Dockerfile for the Python application.
- **Core Services Utilized (Local MVP Context):**
  - Docker Engine
  - Docker Compose
  - TimescaleDB (Docker container)
  - Python Application (Docker container)
- **Infrastructure as Code (IaC) - Local Context:** Dockerfile and `docker-compose.yml` serve as IaC.
- **Deployment Strategy (Local MVP):**
  1. Build Docker image (`docker build`)
  2. Run services (`docker-compose up`)
  3. Updates involve `git pull`, image rebuild (if needed), and `docker-compose down/up`
- **Environments (MVP):** Primarily local development/execution, configuration via `.env` file.
- **Environment Promotion (MVP):** Not applicable for local-only MVP.
- **Rollback Strategy (Local MVP):**
  - Code/config via Git rollback and Docker rebuild.
  - Data issues via user-managed Docker volume backups or re-ingestion.
  - Application errors via `docker-compose down/up` after fixes.
- **CI/CD:** Full CI/CD for deployment is out of scope for local MVP. CI for automated testing/linting (e.g., GitHub Actions) is recommended.

## 13. Error Handling Strategy
This section details the strategy for handling errors within the Hist_Data_Ingestor application.

- **General Approach:** Python exceptions (custom classes inheriting from `AppException`) are primary. Unhandled exceptions are caught, logged, and result in user-friendly CLI errors.
- **Logging:** `structlog` for structured JSON output. Includes timestamp, level, logger name, contextual job info, correlation ID (conceptual for MVP), and full stack traces. No sensitive data logged.
- **Specific Handling Patterns:**
  - **External API Calls (APIExtractionLayer):**
    - Retries via `tenacity` (3-5 attempts, exponential backoff, jitter) for transient network errors, HTTP 5xx, and HTTP 429 (respecting Retry-After header).
    - Configurable timeouts for all calls.
    - Persistent API errors (after retries) are translated to app-specific exceptions, logged, and the relevant data chunk is marked 'failed'.
  - **Data Transformation & Validation Errors:**
    - Problematic records are logged and quarantined (per PRD NFR 3).
    - Pipeline continues with other records if possible.
  - **Database Errors (DataStorageLayer):**
    - Connection errors: Retry a few times; if persistent, fail the operation and log.
    - COPY/UPSERT errors (e.g., `psycopg2.DataError`, `psycopg2.IntegrityError`): Rollback transaction, quarantine the batch, log details.
    - Transaction Management: All batch writes are atomic.
  - **Internal Errors:**
    - Caught by higher-level handlers, logged, may mark current chunk 'failed'.
  - **Dead-Letter Queue (DLQ) / Quarantine:**
    - Records/chunks failing persistently are moved to a quarantine location (file-based for MVP) with associated error metadata.

## 14. Coding Standards
All code must adhere to the following standards:

- **Primary Language & Runtime:** Python 3.11.x.
- **Style Guide & Linters:**
  - PEP 8
  - Black for formatting
  - Flake8 for linting
  - MyPy for static type checking (strive for `disallow_untyped_defs = True`). Configurations in `pyproject.toml`. Errors/warnings must be resolved.
- **Naming Conventions:**
  - Variables & Functions/Methods: `snake_case`
  - Classes & Type Aliases: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Modules/Packages: `snake_case`
  - Private Members: Single leading underscore `_internal_member`
- **File Structure:** Adhere to the "Project Structure" section.
- **Unit Test File Organization:** In `tests/unit/`, mirroring `src/`. Filenames `test_*.py`, test functions `test_*`.
- **Asynchronous Operations (asyncio):** Use `async`/`await` for I/O-bound operations (API calls, ib_insync).
- **Type Safety (Python Type Hints):**
  - Mandatory for all function/method signatures.
  - Variables type-hinted for clarity.
  - Use `typing` module; use `Any` sparingly.
- **Comments & Documentation:**
  - Code Comments: Explain why, not what, for complex logic.
  - Docstrings: Google style for all public modules, classes, functions, methods (purpose, args, returns, exceptions).
  - READMEs: Concise READMEs for key modules; main `README.md` for project overview.
- **Dependency Management:**
  - Tool: `pip` with `requirements.txt`. `pyproject.toml` for tool config.
  - Policy: Minimize new dependencies. Vet for necessity, maintenance, license, security. Obtain user approval.
  - Versioning: Pin exact versions in `requirements.txt`. Manual management for MVP.
- **Python Specific Conventions:**
  - Immutability: Prefer immutable structures where practical.
  - Error Handling: Raise specific custom exceptions. Avoid broad `except Exception:`.
  - Resource Management: Always use `with` statements for files, DB connections (if not auto-managed by SQLAlchemy session scope).
  - Logging: Use configured `structlog` logger with context.
  - Imports: Absolute imports. Grouped (stdlib, third-party, local) and sorted alphabetically (use isort).
- **Anti-Patterns to Avoid:**
  - Overly complex/nested logic
  - Single-letter variables (except loop counters)
  - Bypassing architectural layers
  - Hardcoding configs

## 15. Overall Testing Strategy
This strategy aligns with PRD NFR 10.

- **Primary Testing Framework:** PyTest.
- **Tools:**
  - PyTest
  - unittest.mock (or pytest-mock)
  - Docker/Compose for test environments
- **Unit Tests:**
  - **Scope:** Individual functions/classes (transformation logic, validation rules, utilities, adapter logic with mocked APIs).
  - **Location:** `tests/unit/` mirroring `src/`.
  - **Mocking:** All external dependencies (APIs, DB, file system) must be mocked.
  - **AI Agent Responsibility:** Must generate comprehensive unit tests for all new/modified code.
- **Integration Tests:**
  - **Scope (MVP):**
    - API connectivity for IB and Databento (auth, basic request, response parsing – using recorded responses or carefully controlled live calls for small data).
    - Basic data loading pipeline (Extract -> Transform -> Validate -> Store) for a small, controlled dataset into a test TimescaleDB instance.
  - **Location:** `tests/integration/`.
  - **Environment:** Temporary TimescaleDB via Docker for DB tests.
  - **AI Agent Responsibility:** May create/extend integration tests for key interactions.
- **End-to-End (E2E) Tests (MVP Scope):**
  - **Approach:** CLI-driven test scenarios verifying outputs, logs, DB state, and quarantined files for small, defined datasets. Manual validation by user for broader coverage.
  - **AI Agent Responsibility:** Ensure implemented stories are testable via CLI; may assist in scripting simple E2E scenarios.
- **Test Coverage:** Goal is high-quality tests for critical paths/logic. Coverage reports via `pytest-cov` for review.
- **Mocking Strategy:** Focus on testing one unit at a time. Use clear, maintainable mocks.
- **Test Data Management:** Small API response samples in `tests/fixtures/`. Test DBs are ephemeral or reset.

## 16. Security Best Practices
Mandatory practices for all development:

- **Input Sanitization/Validation:**
  - API Configurations: Validated by Pydantic models in ConfigManager.
  - CLI Inputs: Validated by Typer command functions.
  - API Responses: Initial structure/type validation via Pydantic models mapping.
- **Output Encoding:**
  - CLI Output: Plain text/formatted tables; ensure no terminal rendering issues with special characters.
  - Log Output: Handled by structlog JSON serializer.
- **Secrets Management:**
  - Never hardcode API keys/DB credentials or commit to Git.
  - Load from environment variables (via .env locally, git-ignored) at runtime, accessed via ConfigManager.
- **Dependency Security:**
  - Vet new dependencies (necessity, maintenance, license, known vulnerabilities via pip-audit). Obtain user approval.
  - Pin exact versions in requirements.txt.
- **Authentication/Authorization (External APIs):** API keys/session management for IB/Databento as per "API Reference" and "Secrets Management." No internal app auth for CLI MVP.
- **Principle of Least Privilege:** Conceptual for local DB user permissions. Application file access restricted by OS/Docker.
- **API Security (Consuming External APIs):** HTTPS for all calls. Validate parameters sent to APIs.
- **Error Handling & Information Disclosure:** No sensitive internal details (stack traces, raw API errors) in CLI user-facing messages. Log details server-side.
- **Local File Handling:** Use pathlib for safe path construction for logs/quarantined files.

## 17. Key Reference Documents

- **Product Requirements Document (PRD) for Hist_Data_Ingestor (MVP):** (Path: `docs/prd.md`) - Defines project goals, scope, requirements, and user stories.
- **Architecting a Configurable and API-Agnostic Financial Data Platform with Python and TimescaleDB:** (Path: User-provided, typically in `docs/research/` or linked) - Foundational research informing architectural concepts.
- **Databento Downloader: Detailed Specifications:** (Path: User-provided, typically in `docs/research/` or linked) - Specifics for Databento API integration.
- **Interactive Brokers API Integration: A Comprehensive Analysis for Hist_Data_Ingestor:** (Path: User-provided, typically in `docs/research/` or linked) - Details for Interactive Brokers TWS API integration.
- **technical-preferences.md (Optional):** (Path: User-provided, e.g., `docs/technical-preferences.md`) - User's overriding technical preferences.

> This list will be updated as new key documents are created or referenced.

## 18. Change Log

| Change                                 | Date       | Version | Description                          | Author           |
|----------------------------------------|------------|---------|--------------------------------------|------------------|
| Initial Draft for MVP Architecture     | 2025-06-01 | 0.1.0   | First complete draft of the MVP architecture. | Architect (Fred) |

> This log will be updated as the architecture evolves.

---

This concludes the generation of the Hist_Data_Ingestor (MVP) Architecture Document.

**Summary of architect-checklist Validation:**

The architecture document has been successfully validated against all relevant sections of the architect-checklist. We've confirmed alignment with requirements, sound architectural fundamentals, defined tech stack, appropriate resilience and operational readiness for the MVP, key security practices, implementation guidance, dependency management, and suitability for AI agent implementation.