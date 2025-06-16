# Hist_Data_Ingestor (MVP) - Consolidated Architecture Document v2.0

## Introduction / Preamble

This document outlines the overall project architecture for the Hist_Data_Ingestor (MVP), including backend systems, shared services, and non-UI specific concerns. Its primary goal is to serve as the guiding architectural blueprint for all development, particularly for AI-driven implementation, ensuring consistency and adherence to the chosen patterns and technologies.

Note: As this project is primarily a backend data ingestion framework for the MVP, a separate Frontend Architecture Document is not applicable at this stage. If a significant UI were added post-MVP, such a document would then be created.

## Table of Contents

1. Introduction / Preamble
1. Table of Contents
1. Technical Summary
1. High-Level Overview
1. Architectural / Design Patterns Adopted
1. Component View
1. Project Structure
1. API Reference
1. Data Models
1. Core Workflow / Sequence Diagrams
1. Definitive Tech Stack Selections
1. Infrastructure and Deployment Overview
1. Error Handling Strategy
1. Coding Standards
1. Overall Testing Strategy
1. Security Best Practices
1. Key Reference Documents
1. Change Log

## Technical Summary

The architecture for the Hist_Data_Ingestor will be a Python-based, internally-modular monolith designed for the MVP. Its primary function is to provide a systematic and extensible method for acquiring historical financial data. For the MVP, the focus is on daily OHLCV data from the Databento API.

The system is designed to be highly configurable and resilient. Key architectural features include:
- **YAML-based Configuration:** Provides flexibility to modify system behavior, such as API credentials and transformation rules, without code changes.
- **Modular Internal Structure:** Facilitates maintainability and future evolution, including the addition of other data types or APIs post-MVP. The design employs an Adapter Pattern for API interactions to ensure the system remains API-agnostic.
- **Robust Data Validation:** Leverages Pydantic for type-safe configuration and data model validation, ensuring data integrity from ingestion to storage.
- **Time-Series Optimized Storage:** Data is stored in a TimescaleDB database, utilizing hypertables for efficient time-series data management.
- **Command Line Interface (CLI):** A basic CLI, built with Typer, serves as the primary interface for initiating ingestion jobs and querying stored data.
- **Resilience and Reliability:** The system incorporates the tenacity library for robust API retry logic and a file-based Dead-Letter Queue (DLQ) to handle persistent data failures, preventing pipeline blockages.
- **Structured Logging:** Comprehensive monitoring is achieved through structured, JSON-formatted logging via structlog, providing clear, machine-readable logs for debugging and analysis.
- **Containerized Deployment:** The application and its database dependency are containerized using Docker, ensuring a consistent and reproducible deployment environment.

## High-Level Overview

The Hist_Data_Ingestor MVP adopts a Monolith architectural style for initial development simplicity and to establish a solid foundation, as mandated by the project's requirements. The entire codebase will reside within a single GitHub repository.

The primary data flow is initiated by a user via the CLI, specifying the API source (Databento), symbols, and a date range. The PipelineOrchestrator reads the job configuration and invokes the appropriate API Adapter within the APIExtractionLayer to fetch the raw historical data. This data is then passed to the DataTransformationEngine, which applies a set of declarative rules to convert it into a standardized internal format. The standardized data undergoes rigorous validation; invalid data is quarantined. Finally, the valid, transformed data is loaded into a TimescaleDB hypertable by the DataStorageLayer, ensuring idempotent writes to prevent duplication. A DownloadProgressTracker maintains the state of the job, enabling resumable downloads.

The following C4-style diagrams provide a visual contract for the system, illustrating the context and container views. These diagrams correctly depict the system's external dependencies, reinforcing the API-agnostic principle at the highest level of abstraction. This visual guide ensures that all development work is aligned with the core architectural goal of supporting multiple data sources from the outset, preventing the need for future refactoring that would result from a single-API focus.

```mermaid
graph TD
   subgraph Hist_Data_Ingestor_System_Context
       direction LR
       actor User [Primary User/Operator]
       rectangle HistDataIngestor
       database TimescaleDB
       rectangle Databento

       User -- Manages/Initiates via CLI --> HistDataIngestor
       HistDataIngestor -- Ingests from/Configures --> Databento
       HistDataIngestor -- Stores/Retrieves data --> TimescaleDB
   end
```

```mermaid
graph TD
   subgraph Hist_Data_Ingestor_Container_View [Container View - Level 2]
       direction LR
       actor User [Primary User/Operator]

       rectangle AppContainer {
           rectangle CLI
           rectangle Orchestrator [Pipeline Orchestrator]
           rectangle ConfigMgr [Config Manager]
           rectangle APIAdapters
           rectangle Transformer
           rectangle Validator
           rectangle StorageLoader
           rectangle QueryModule [Querying Module]
           rectangle ProgressTracker
       }

       database DBContainer

       rectangle Databento_API

       User -- Interacts via --> CLI
       CLI --> Orchestrator
       CLI --> QueryModule
       Orchestrator --> ConfigMgr
       Orchestrator --> APIAdapters
       Orchestrator --> Transformer
       Orchestrator --> Validator
       Orchestrator --> StorageLoader
       Orchestrator --> ProgressTracker
       APIAdapters -- Fetches data --> Databento_API
       StorageLoader -- Writes/Reads --> DBContainer
       QueryModule -- Reads --> DBContainer
       ProgressTracker -- Writes/Reads --> DBContainer
   end
```

## Architectural / Design Patterns Adopted

The system's architecture is founded on several key design patterns. Adherence to these patterns is critical for achieving the project's goals of modularity, extensibility, and maintainability. The inclusion of a clear rationale for each pattern provides developers with the intent behind the choice, empowering them to make implementation decisions that align with the long-term architectural vision.
- **Modular Monolith:** The system is built as a single, deployable Python application.
- **Rationale:** This simplifies initial development, deployment, and operational management for the MVP. The internal structure is intentionally divided into distinct modules with clear responsibilities to promote separation of concerns, making the system easier to understand, maintain, and potentially refactor into microservices in the future.
- **Adapter Pattern:** Used for the APIExtractionLayer to interact with external financial data APIs. The Databento API has its own adapter implementing a common interface.
- **Rationale:** This pattern is fundamental to the project's API-agnostic goal. It decouples the core application logic from the specific details of external APIs, making it straightforward to add new data sources or modify existing integrations without impacting the rest of the system.
- **Pipeline / Orchestrator Pattern:** A central PipelineOrchestrator component manages the sequence of operations in the Extract, Transform, Load (ETL) process.
- **Rationale:** This provides a clear, manageable, and sequential workflow for data processing. It centralizes control, making it easier to manage state, handle errors, and coordinate the various stages of the ingestion pipeline.
- **Rules Engine Pattern / Declarative Configuration:** System behavior, especially for data transformations and validations, is driven by external YAML configuration files rather than being hardcoded.
- **Rationale:** This enhances flexibility and maintainability. It allows operators to modify data mapping, apply new validation rules, or adjust API parameters without requiring code changes and redeployment, directly supporting the high configurability requirement.
- **Retry Pattern:** The system uses the tenacity library to implement a robust retry mechanism with exponential backoff for transient API errors.
- **Rationale:** This ensures reliability when interacting with external network services. By automatically retrying failed requests, the system can recover from temporary issues like network glitches or rate limiting (respecting Retry-After headers), improving the overall success rate of data ingestion.
- **Dead-Letter Queue (DLQ) Pattern:** Data chunks that fail persistently after all retries are routed to a file-based DLQ.
- **Rationale:** This pattern enhances resilience by preventing a single bad batch of data from halting the entire ingestion process. Failed data is isolated for later inspection and reprocessing, ensuring that valid data continues to flow through the system.
- **Repository Pattern (Conceptual):** The DataStorageLayer acts as a repository, abstracting the specifics of TimescaleDB interaction from the rest of the application.
- **Rationale:** This centralizes data access logic, decouples business logic from database specifics, and improves testability by allowing the data access layer to be easily mocked.
- **Strategy Pattern (Conceptual):** The principle is applied to how configuration drives behavior. Different YAML configurations lead to different operational strategies (e.g., which API adapter to use, which transformation rules to apply) without changing the component's core code.
- **Rationale:** This allows for flexible behavior modification through external configuration, reinforcing the system's adaptability and configurability.

## Component View

The application is composed of several logical components, each with a distinct responsibility within the monolithic structure. This modular design is essential for maintaining a clean and understandable codebase.
- **ConfigManager:** Provides centralized and type-safe access to all application configurations. It loads settings from YAML files and environment variables, validating them using Pydantic models, and makes them available to other components.
- **APIExtractionLayer:** Manages all direct communication with external financial data APIs, specifically Databento via its Python client. This layer contains a specific API Adapter (DatabentoAdapter) that implements a common interface. It handles API-specific connection, authentication, request formation, data fetching, pagination, and initial response parsing, incorporating error handling and retry mechanisms.
- **DataTransformationEngine (RuleEngine):** Transforms raw data received from the APIExtractionLayer into a standardized internal data model. It applies declarative transformation rules defined in API-specific YAML files, such as field mapping and type conversions.
- **DataValidationModule:** Ensures data quality and integrity through a two-stage process. It performs initial validation of raw API responses and post-transformation validation of standardized records using Pandera schemas to check against business rules (e.g., price > 0). Failing records are quarantined.
- **DataStorageLayer (TimescaleLoader):** Manages all persistence operations to the TimescaleDB database. This includes creating and managing the schema for hypertables and ensuring idempotent writes. For performance, it can employ strategies like psycopg2's copy_from for large initial bulk insertions, while using INSERT... ON CONFLICT DO UPDATE (UPSERT) for subsequent, idempotent updates.
- **DownloadProgressTracker:** Maintains the state of data ingestion jobs, including chunks, watermarks, and status, in a dedicated TimescaleDB table. This enables resumable and incremental downloads, preventing re-ingestion of already processed data.
- **PipelineOrchestrator:** Coordinates the entire ETL workflow for a given data ingestion job. It sequences calls to the APIExtractionLayer, DataTransformationEngine, DataValidationModule, and DataStorageLayer, managing the overall process and high-level error handling.
- **QueryingModule:** Provides comprehensive functionality to retrieve stored financial data from TimescaleDB based on user-specified criteria. Features automatic symbol-to-instrument_id resolution, support for all 5 Databento schemas (OHLCV, Trades, TBBO, Statistics, Definitions), TimescaleDB-optimized queries, and both list-of-dictionaries and Pandas DataFrame output formats. Implements SQLAlchemy 2.0 Core with connection pooling and comprehensive error handling.
- **CLI (Command Line Interface):** Serves as the primary user interface for the MVP. Built using Typer, it allows users to initiate data ingestion jobs and query stored data.
- **LoggingModule (Cross-Cutting Concern):** Provides a consistent, structured (JSON) logging mechanism across all components using structlog for effective debugging and monitoring.

The following diagram illustrates the interactions between these components, showing the primary data flow as well as cross-cutting concerns like configuration and logging.

```mermaid
graph LR
   subgraph UserInteraction
       CLI_Tool
   end

   subgraph ApplicationCore
       direction TB
       Orchestrator[Pipeline Orchestrator]
       Config[ConfigManager]
       Tracker

       subgraph IngestionPipeline
           direction LR
           API_Extract[APIExtractionLayer]
           Transformer
           Validator
           Storer
       end

       QueryMod[QueryingModule]
       Logger[Logging (Global - structlog)]
   end

   subgraph ExternalServices
       direction RL
       DB
       Databento_API
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

   API_Extract -- Connects to --> Databento_API

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
   class Databento_API external;
```

## Project Structure

The project structure is a physical manifestation of the architecture, designed to enforce a clean separation of concerns and promote modularity. The following idealized structure serves as the blueprint for the repository, providing a clear and scalable organization for source code, configuration, documentation, and tests. Adhering to this structure is essential for maintaining code quality and combating entropy as the project evolves.

```
.
├── ai-docs/                        # AI agent documentation and persona files
├── build/                          # Build artifacts or scripts (if used)
├── configs/                        # Configuration files for the project
│   ├── api_specific/               # API-specific config files (e.g., for Databento, IB)
│   ├── system_config.yaml          # Main system configuration (YAML)
│   └── validation_schemas/         # JSON schemas for validating data
├── data_temp/                      # Temporary data storage (if used)
├── dlq/                            # Dead-letter queue or error data (if used)
├── docs/                           # Project documentation
│   ├── api/                        # API documentation
│   ├── architecture.md             # System architecture overview
│   ├── contributing.md             # Contribution guidelines
│   ├── epics/                      # Epic-level documentation
│   ├── faq.md                      # Frequently asked questions
│   ├── index.md                    # Docs index/landing page
│   ├── modules/                    # Module-level documentation
│   ├── prd.md                      # Product requirements document
│   ├── project-retrospective.md    # Lessons learned and retrospectives
│   ├── setup.md                    # Setup instructions
│   └── stories/                    # User stories and story files
│       ├── 1.1.story.md            # Story 1.1: Project initialization
│       ├── 1.2.story.md            # Story 1.2: Config management
│       ├── 1.3.story.md            # Story 1.3: Docker environment
│       └── 1.4.story.md            # Story 1.4: Centralized logging
├── infra/                          # Infrastructure-as-code or deployment scripts
├── logs/                           # Application and test log files
│   ├── app.log                     # Main application log
│   ├── test_app.log                # Log file for tests
│   └── test_console.log            # Console log for tests
├── specs/                          # Technical specifications (if used)
├── src/                            # Main source code
│   ├── __init__.py                 # Marks src as a Python package
│   ├── __pycache__/                # Python bytecode cache
│   ├── cli/                        # Command-line interface code
│   │   ├── __init__.py
│   │   └── commands.py
│   ├── core/                       # Core system modules (e.g., config, orchestrator)
│   │   ├── __init__.py
│   │   ├── config_manager.py       # Configuration manager implementation
│   │   ├── module_loader.py        # Module loading logic
│   │   └── pipeline_orchestrator.py# Pipeline orchestration logic
│   ├── hist_data_ingestor.egg-info/# Package metadata (if installed as a package)
│   │   ├── dependency_links.txt
│   │   ├── PKG-INFO
│   │   ├── SOURCES.txt
│   │   └── top_level.txt
│   ├── ingestion/                  # Data ingestion logic
│   │   ├── __init__.py
│   │   ├── api_adapters/           # API adapter modules
│   │   └── data_fetcher.py         # Data fetching logic
│   ├── main.py                     # Main entry point (if used)
│   ├── querying/                   # Querying logic
│   │   ├── __init__.py
│   │   └── query_builder.py
│   ├── storage/                    # Data storage logic
│   │   ├── __init__.py
│   │   ├── models.py               # Data models
│   │   └── timescale_loader.py     # TimescaleDB loader
│   ├── transformation/             # Data transformation logic
│   │   ├── __init__.py
│   │   ├── mapping_configs/        # Mapping configuration files
│   │   ├── rule_engine/            # Rule engine logic
│   │   └── validators/             # Data validators
│   └── utils/                      # Utility modules
│       ├── __init__.py
│       └── custom_logger.py        # Centralized logging setup
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── __pycache__/
│   ├──.DS_Store
│   ├── fixtures/                   # Test fixtures
│   │   └──.gitkeep
│   ├── integration/                # Integration tests
│   │   └── test_data_pipeline.py
│   ├── unit/                       # Unit tests
│   │   ├── __init__.py
│   │   ├── core/
│   │   └── ingestion/
│   └── utils/                      # Utility tests
│       └── test_custom_logger.py   # Logger unit tests
├── venv/                           # Python virtual environment
├──.claude/                        # Claude AI config (if used)
├──.DS_Store                       # macOS system file
├──.env                            # Environment variables (not committed)
├──.git/                           # Git version control
├──.gitignore                      # Git ignore rules
├──.pytest_cache/                  # Pytest cache
├──.vscode/                        # VSCode editor settings
│   └── settings.json
├── create_project_structure.sh     # Script to create project structure
├── docker-compose.yml              # Docker Compose config
├── Dockerfile                      # Docker build file
├── ide-bmad-orchestrator.cfg.md    # BMAD orchestrator config (relative paths)
├── ide-bmad-orchestrator.md        # BMAD orchestrator main doc
├── pyproject.toml                  # Python project metadata/config
├── README.md                       # Project overview and instructions
├── requirements.txt                # Python dependencies
```

## API Reference

This section provides a comprehensive reference for the external Databento API consumed by the system.

External APIs Consumed

## Databento Historical API

- **Purpose:** To acquire historical market data across a wide variety of schemas, including OHLCV, trades, top-of-book, and venue-published statistics.
- **Client Library:** databento-python.
- **Authentication:** Handled via a 32-character API key (starting with db-), which should be provided through a secure environment variable (DATABENTO_API_KEY).
- **Key Method Used:** The primary interaction for historical data is the timeseries.get_range() method from the databento-python client library.
- **Data Format:** The API returns data in the Databento Binary Encoding (DBN) format, a highly efficient, zero-copy serialization format that is decoded by the client library.

Supported Schemas

The system will interact with several key Databento schemas. A schema is a specific data record format.

OHLCV (Open, High, Low, Close, Volume)

- **Description:** Provides aggregated bar data for open, high, low, and close prices, along with the total volume traded during a specified interval. The schema name indicates the interval, such as ohlcv-1s (1-second), ohlcv-1m (1-minute), ohlcv-1h (1-hour), and ohlcv-1d (1-day).
- **Key Fields:**

| Field | Type | Description |
| :--- | :--- | :--- |
| ts_event | uint64_t | The inclusive start time of the bar aggregation period, as nanoseconds since the UNIX epoch. |
| open | int64_t | The open price for the bar, scaled by 1e-9. |
| high | int64_t | The high price for the bar, scaled by 1e-9. |
| low | int64_t | The low price for the bar, scaled by 1e-9. |
| close | int64_t | The close price for the bar, scaled by 1e-9. |
| volume | uint64_t | The total volume traded during the aggregation period. |
- **Notes:** The ts_event timestamp marks the beginning of the interval. If no trades occur within an interval, no OHLCV record is generated for that period. While convenient, it is recommended to construct OHLCV bars from the trades schema for maximum transparency and consistency, as vendor implementations can differ.

Trades

- **Description:** Provides a record for every individual trade event, often referred to as "time and sales" or "tick data". This schema is a subset of the more granular Market by Order (MBO) data.
- **Key Fields:**

| Field | Type | Description |
| :--- | :--- | :--- |
| ts_event | uint64_t | The matching-engine-received timestamp as nanoseconds since the UNIX epoch. |
| price | int64_t | The trade price, scaled by 1e-9. |
| size | uint32_t | The quantity of the trade. |
| action | char | The event action, which is always 'T' for the trades schema. |
| side | char | The side that initiated the trade (e.g., 'A' for ask, 'B' for bid). |
| flags | uint8_t | A bit field indicating event characteristics and data quality. |
| depth | uint8_t | The book level where the trade occurred. |
| sequence | uint32_t | The message sequence number from the venue. |
- **Notes:** This schema is fundamental and can be used to derive less granular schemas like OHLCV. For some venues, the highest level of detail is achieved by combining the trades feed with the MBO feed.

TBBO (BBO on Trade)

- **Description:** Provides every trade event along with the Best Bid and Offer (BBO) that was present on the book immediately before the trade occurred. This schema operates in "trade space," meaning a record is generated only when a trade happens. It is a subset of the MBP-1 schema.
- **Key Fields:**

| Field | Type | Description |
| :--- | :--- | :--- |
| ts_event | uint64_t | The matching-engine-received timestamp as nanoseconds since the UNIX epoch. |
| price | int64_t | The trade price, scaled by 1e-9. |
| size | uint32_t | The trade quantity. |
| action | char | The event action. Always 'T' (Trade) in the TBBO schema. |
| side | char | The side that initiated the trade. |
| flags | uint8_t | A bit field indicating event characteristics. |
| depth | uint8_t | The book level where the update occurred. |
- **Notes:** The fields are similar to the trades schema, but the record also contains the state of the BBO at the time of the trade. This is useful for constructing trading signals based on trade events without the higher volume of data from a full top-of-book feed like MBP-1.

Statistics

- **Description:** Provides official summary statistics for an instrument as published by the venue. This can include daily volume, open interest, settlement prices (preliminary and final), and official open, high, and low prices.
- **Key Fields:**

| Field | Type | Description |
| :--- | :--- | :--- |
| ts_event | uint64_t | The matching-engine-received timestamp as nanoseconds since the UNIX epoch. |
| ts_ref | uint64_t | The reference timestamp for the statistic (e.g., the time the settlement price applies to). |
| price | int64_t | The value for a price-based statistic, scaled by 1e-9. Unused fields contain INT64_MAX. |
| quantity | int32_t | The value for a quantity-based statistic. Unused fields contain INT32_MAX. |
| stat_type | uint16_t | An enum indicating the type of statistic (e.g., 1: Opening price, 3: Settlement price, 9: Open interest). |
| update_action | uint8_t | Indicates if the statistic is new (1) or a deletion (2). |
| stat_flags | uint8_t | Additional flags associated with the statistic (e.g., indicating a final vs. preliminary price). |
- **Notes:** This schema is the correct source for official settlement data, which may differ from data derived from electronic trading sessions (like the ohlcv-1d schema) because it can include block trades or other adjustments. The meaning of the price and quantity fields depends on the stat_type.

Internal APIs Provided

For the MVP, which is a monolithic application, there are no internal APIs exposed in the sense of separate network services. All internal component interactions occur via direct Python method calls.

## Data Models

This section defines the precise data structures used within the system, from the Pydantic models that represent data in Python to the physical database schemas in TimescaleDB. A well-defined data model is crucial for data integrity and consistency across the application.

### Pydantic Data Models

After raw DBN data is decoded by the databento-python client, it will be validated and structured using the following Pydantic models. These models ensure type safety and provide a consistent object interface for the transformation and storage layers.

Common Base Models

```python
from typing import Optional
from decimal import Decimal
import datetime
from pydantic import BaseModel, Field

class RecordHeader(BaseModel):
   """Represents the DBN record header structure."""
   publisher_id: int
   instrument_id: int
   ts_event: datetime.datetime

class DatabentoRecordBase(BaseModel):
   """A base model including fields common to many DBN records."""
   hd: RecordHeader
   ts_recv: datetime.datetime
   ts_in_delta: Optional[int] = None
   sequence: Optional[int] = None

Schema-Specific Models
- **OhlcvMsg:** Represents a single OHLCV bar. Note its simpler structure, which does not require all fields from DatabentoRecordBase.

```python
class OhlcvMsg(BaseModel):
   """OHLCV bar message for various intervals (1s, 1m, 1h, 1d)."""
   publisher_id: int
   instrument_id: int
   ts_event: datetime.datetime
   open: Decimal
   high: Decimal
   low: Decimal
   close: Decimal
   volume: int

- **TradeMsg:** Represents a single trade event.

```python
class TradeMsg(DatabentoRecordBase):
   """Trade message, corresponding to the 'trades' schema."""
   price: Decimal
   size: int
   action: str
   side: str
   flags: int
   depth: int

- **TbboMsg:** Represents a trade event along with the best bid and offer (BBO) immediately preceding it.

```python
class TbboMsg(DatabentoRecordBase):
   """TBBO message, containing a trade and the preceding BBO."""
   price: Decimal
   size: int
   action: str
   side: str
   flags: int
   depth: int
   # BBO fields
   bid_px_00: Optional = None
   ask_px_00: Optional = None
   bid_sz_00: Optional[int] = None
   ask_sz_00: Optional[int] = None
   bid_ct_00: Optional[int] = None
   ask_ct_00: Optional[int] = None

- **StatisticsMsg:** Represents a venue-published statistic.

```python
class StatisticsMsg(DatabentoRecordBase):
   """Statistics message for venue-published data like open interest or settlement prices."""
   ts_ref: datetime.datetime
   price: Optional = None
   quantity: Optional[int] = None
   stat_type: int
   channel_id: int
   update_action: int
   stat_flags: int

### Database Schemas (TimescaleDB)

The standardized data is persisted in TimescaleDB hypertables, optimized for time-series workloads. Each supported schema will have a dedicated table.

daily_ohlcv_data Hypertable

This table stores daily OHLCV data, as defined in the initial MVP scope.

```sql
CREATE TABLE IF NOT EXISTS daily_ohlcv_data (
   ts_event TIMESTAMPTZ NOT NULL,
   instrument_id INTEGER NOT NULL,
   open_price NUMERIC NOT NULL,
   high_price NUMERIC NOT NULL,
   low_price NUMERIC NOT NULL,
   close_price NUMERIC NOT NULL,
   volume BIGINT NOT NULL,
   trade_count INTEGER NULL,
   vwap NUMERIC NULL,
   granularity VARCHAR(10) NOT NULL,
   data_source VARCHAR(50) NOT NULL,
   PRIMARY KEY (instrument_id, ts_event, granularity)
);
SELECT create_hypertable('daily_ohlcv_data', by_range('ts_event', chunk_time_interval => INTERVAL '7 days'), if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_daily_ohlcv_instrument_time ON daily_ohlcv_data (instrument_id, ts_event DESC);
```

trades_data Hypertable

This table stores individual trade events from the trades schema.

```sql
CREATE TABLE IF NOT EXISTS trades_data (
   ts_event TIMESTAMPTZ NOT NULL,
   ts_recv TIMESTAMPTZ NOT NULL,
   publisher_id SMALLINT NOT NULL,
   instrument_id INTEGER NOT NULL,
   price NUMERIC NOT NULL,
   size INTEGER NOT NULL,
   action CHAR(1) NOT NULL,
   side CHAR(1) NOT NULL,
   flags SMALLINT NOT NULL,
   depth SMALLINT NOT NULL,
   sequence INTEGER NULL,
   ts_in_delta INTEGER NULL,
   PRIMARY KEY (instrument_id, ts_event, sequence, price, size, side)
);
SELECT create_hypertable('trades_data', by_range('ts_event', INTERVAL '1 day'), if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_trades_instrument_time ON trades_data (instrument_id, ts_event DESC);
```

tbbo_data Hypertable

This table stores trade events along with the corresponding top-of-book quote from the tbbo schema.

```sql
CREATE TABLE IF NOT EXISTS tbbo_data (
   ts_event TIMESTAMPTZ NOT NULL,
   ts_recv TIMESTAMPTZ NOT NULL,
   publisher_id SMALLINT NOT NULL,
   instrument_id INTEGER NOT NULL,
   price NUMERIC NOT NULL,
   size INTEGER NOT NULL,
   action CHAR(1) NOT NULL,
   side CHAR(1) NOT NULL,
   flags SMALLINT NOT NULL,
   depth SMALLINT NOT NULL,
   sequence INTEGER NULL,
   ts_in_delta INTEGER NULL,
   bid_px_00 NUMERIC NULL,
   ask_px_00 NUMERIC NULL,
   bid_sz_00 INTEGER NULL,
   ask_sz_00 INTEGER NULL,
   bid_ct_00 INTEGER NULL,
   ask_ct_00 INTEGER NULL,
   PRIMARY KEY (instrument_id, ts_event, sequence, price, size, side)
);
SELECT create_hypertable('tbbo_data', by_range('ts_event', INTERVAL '1 day'), if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_tbbo_instrument_time ON tbbo_data (instrument_id, ts_event DESC);
```

statistics_data Hypertable

This table stores official summary statistics from the statistics schema.

```sql
CREATE TABLE IF NOT EXISTS statistics_data (
   ts_event TIMESTAMPTZ NOT NULL,
   ts_recv TIMESTAMPTZ NOT NULL,
   ts_ref TIMESTAMPTZ NOT NULL,
   publisher_id SMALLINT NOT NULL,
   instrument_id INTEGER NOT NULL,
   price NUMERIC NULL,
   quantity INTEGER NULL,
   sequence INTEGER NOT NULL,
   ts_in_delta INTEGER NOT NULL,
   stat_type SMALLINT NOT NULL,
   channel_id SMALLINT NOT NULL,
   update_action SMALLINT NOT NULL,
   stat_flags SMALLINT NOT NULL,
   PRIMARY KEY (instrument_id, ts_event, stat_type, sequence)
);
SELECT create_hypertable('statistics_data', by_range('ts_event', INTERVAL '7 days'), if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_statistics_instrument_time_type ON statistics_data (instrument_id, ts_event DESC, stat_type);

definitions_data Hypertable

This table stores instrument definitions and metadata for all market instruments, including contract specifications, trading parameters, and multi-leg instrument details.

SQL
CREATE TABLE IF NOT EXISTS definitions_data (
   ts_event TIMESTAMPTZ NOT NULL,
   ts_recv TIMESTAMPTZ NOT NULL,
   rtype SMALLINT NOT NULL,
   publisher_id SMALLINT NOT NULL,
   instrument_id INTEGER NOT NULL,
   raw_symbol VARCHAR(255) NOT NULL,
   security_update_action CHAR(1) NOT NULL,
   instrument_class CHAR(2) NOT NULL,
   min_price_increment NUMERIC NOT NULL,
   display_factor NUMERIC NOT NULL,
   expiration TIMESTAMPTZ NOT NULL,
   activation TIMESTAMPTZ NOT NULL,
   high_limit_price NUMERIC NOT NULL,
   low_limit_price NUMERIC NOT NULL,
   max_price_variation NUMERIC NOT NULL,
   unit_of_measure_qty NUMERIC,
   min_price_increment_amount NUMERIC,
   price_ratio NUMERIC,
   inst_attrib_value INTEGER NOT NULL,
   underlying_id INTEGER,
   raw_instrument_id BIGINT,
   market_depth_implied INTEGER NOT NULL,
   market_depth INTEGER NOT NULL,
   market_segment_id INTEGER NOT NULL,
   max_trade_vol BIGINT NOT NULL,
   min_lot_size INTEGER NOT NULL,
   min_lot_size_block INTEGER,
   min_lot_size_round_lot INTEGER,
   min_trade_vol BIGINT NOT NULL,
   contract_multiplier INTEGER,
   decay_quantity INTEGER,
   original_contract_size INTEGER,
   appl_id SMALLINT,
   maturity_year SMALLINT,
   decay_start_date DATE,
   channel_id SMALLINT NOT NULL,
   currency VARCHAR(4) NOT NULL,
   settl_currency VARCHAR(4),
   secsubtype VARCHAR(6),
   security_group VARCHAR(21) NOT NULL,
   exchange VARCHAR(5) NOT NULL,
   asset VARCHAR(11) NOT NULL,
   cfi VARCHAR(7),
   security_type VARCHAR(7),
   unit_of_measure VARCHAR(31),
   underlying VARCHAR(21),
   strike_price_currency VARCHAR(4),
   strike_price NUMERIC,
   match_algorithm CHAR(1),
   main_fraction SMALLINT,
   price_display_format SMALLINT,
   sub_fraction SMALLINT,
   underlying_product SMALLINT,
   maturity_month SMALLINT,
   maturity_day SMALLINT,
   maturity_week SMALLINT,
   user_defined_instrument CHAR(1),
   contract_multiplier_unit SMALLINT,
   flow_schedule_type SMALLINT,
   tick_rule SMALLINT,
   leg_count SMALLINT NOT NULL,
   leg_index SMALLINT,
   leg_instrument_id INTEGER,
   leg_raw_symbol VARCHAR(255),
   leg_instrument_class CHAR(2),
   leg_side CHAR(1),
   leg_price NUMERIC,
   leg_delta NUMERIC,
   leg_ratio_price_numerator INTEGER,
   leg_ratio_price_denominator INTEGER,
   leg_ratio_qty_numerator INTEGER,
   leg_ratio_qty_denominator INTEGER,
   leg_underlying_id INTEGER,
   PRIMARY KEY (instrument_id, ts_event, leg_index)
);
SELECT create_hypertable('definitions_data', by_range('ts_event', INTERVAL '90 days'), if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_definitions_instrument_time ON definitions_data (instrument_id, ts_event DESC);

## Core Workflow / Sequence Diagrams

The following sequence diagram illustrates the primary end-to-end workflow for a data ingestion job. This diagram provides a clear, step-by-step view of component interactions, from the initial user command to the final storage of data, including the handling of successful and failed data batches.

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

   User->>CLI: Run ingest command (e.g., --api databento --symbols AAPL --start 2023-01-01)
   CLI->>PipelineOrchestrator: initiate_ingestion_job(job_params)
   PipelineOrchestrator->>ConfigManager: load_job_config(job_params.api)
   ConfigManager-->>PipelineOrchestrator: return api_config
   
   PipelineOrchestrator->>DownloadProgressTracker: get_or_create_job_chunks(job_params)
   DownloadProgressTracker-->>PipelineOrchestrator: return list_of_chunks_to_process
   
   loop For each chunk in list
       PipelineOrchestrator->>DownloadProgressTracker: update_chunk_status(chunk_id, 'in_progress')
       PipelineOrchestrator->>APIExtractionLayer: fetch_data(chunk_details, api_config)
       APIExtractionLayer-->>PipelineOrchestrator: return raw_api_data_batch
       
       alt Raw data fetched successfully
           PipelineOrchestrator->>DataTransformationEngine: transform_data(raw_api_data_batch, api_config.mapping_rules)
           DataTransformationEngine-->>PipelineOrchestrator: return standardized_data_batch
      
           PipelineOrchestrator->>DataValidationModule: validate_data(standardized_data_batch)
           DataValidationModule-->>PipelineOrchestrator: return valid_data_batch, quarantined_records
           
           opt If quarantined_records exist
               PipelineOrchestrator->>DataStorageLayer: save_quarantined_records(quarantined_records)
           end
           
           opt If valid_data_batch exists
               PipelineOrchestrator->>DataStorageLayer: store_data(valid_data_batch)
               DataStorageLayer->>TimescaleDB: Upsert data into hypertable
               TimescaleDB-->>DataStorageLayer: storage_success
               DataStorageLayer-->>PipelineOrchestrator: batch_storage_confirmation
               PipelineOrchestrator->>DownloadProgressTracker: update_chunk_status(chunk_id, 'completed')
           else
                PipelineOrchestrator->>DownloadProgressTracker: update_chunk_status(chunk_id, 'completed_empty')
           end
       else API fetch or other critical error
           PipelineOrchestrator->>DownloadProgressTracker: update_chunk_status(chunk_id, 'failed', error_details)
           PipelineOrchestrator->>CLI: Report error for chunk
       end
   end
   
   PipelineOrchestrator-->>CLI: Job summary
   CLI-->>User: Display job summary
```

## Definitive Tech Stack Selections

This consolidated table provides a single source of truth for the entire project's technology landscape. It eliminates ambiguity and ensures all developers are using the same, approved set of tools. The "Justification" column forces a deliberate choice for each technology, preventing "dependency creep" and ensuring every tool has a clear purpose.

Category
Technology
Version / Details
Description / Purpose
Justification
Languages
```python
3.11.x
Core language for the entire application.
Mandated by project requirements; excellent for data processing.
Containerization
Docker
Latest Stable
For creating reproducible application containers.
Standard for consistent deployment and local development.

Docker Compose
Latest Stable
To orchestrate the local multi-container environment.
Simplifies local setup of the application and database.
Database
TimescaleDB
Latest Stable
Primary time-series database.
Mandated; optimized for time-series data, based on PostgreSQL.

SQLAlchemy
2.0.x
Core database toolkit and ORM.
For interacting with TimescaleDB in a Pythonic way.

psycopg2-binary
>=2.9.5
PostgreSQL adapter for Python.
Required dependency for SQLAlchemy to connect to PostgreSQL.
Configuration
YAML
N/A
Format for configuration files.
Human-readable and good for structured data.

Pydantic
>=2.5.0
Data validation and settings management.
For parsing/validating YAML configs and API responses.

pydantic-settings
>=2.1.0
For loading Pydantic models from env vars/files.
Works with Pydantic for layered configuration.
API Interaction
databento-python
>=0.52.0
Official Python client for Databento API.
Official library for Databento data ingestion.

tenacity
>=8.2.0
General-purpose retrying library.
For robust API call retries with exponential backoff.
Data Handling
Pandas
>=2.0.0
Data analysis and manipulation library.
Used with Pandera and for general data processing.

Pandera
Latest Stable
Data validation library for Pandas DataFrames.
For post-transformation data quality checks.
CLI Development
Typer
Latest Stable
Library for building Command Line Interfaces.
For creating a modern, user-friendly CLI.
Logging
structlog
>=23.0.0
Advanced structured logging for Python.
For flexible, context-aware, structured JSON logging.
Linting/Formatting
Ruff / Black
Latest Stable
To enforce code style and quality standards.
Ruff is a modern, high-performance linter; Black is the standard formatter.

MyPy
Latest Stable
Optional static type checker for Python.
For enforcing type safety and catching bugs early.
Documentation
Sphinx
Latest Stable
To generate HTML documentation from code.
Standard tool for creating professional Python project documentation.

MyST Parser
Latest Stable
Sphinx extension for Markdown support.
Allows writing documentation in Markdown for ease of use.
```

## Infrastructure and Deployment Overview

* Target Deployment Environment (MVP): For the MVP, the system is designed for local deployment and execution on developer hardware. Cloud deployment is not in scope for the initial version.
* Containerization: The entire local environment, including the Python application and the TimescaleDB database, is defined and managed using Docker and Docker Compose. The application's Dockerfile and the project's docker-compose.yml file serve as the Infrastructure as Code (IaC) for this local setup.
* Deployment Strategy: Deployment consists of building the application's Docker image and running the services using docker-compose up. Updates are handled by pulling the latest code changes from Git, rebuilding the image if necessary, and restarting the containers.
* Rollback Strategy: A rollback can be performed by checking out a previous, stable Git commit and rebuilding/restarting the Docker containers. Data-related issues may require manual intervention, such as restoring a database volume or re-running ingestion jobs.
* CI/CD: While a full CI/CD pipeline for automated deployment is out of scope for the local MVP, a CI pipeline using GitHub Actions is recommended for automated linting, testing, and code quality checks on every commit.

## Error Handling Strategy

A robust error handling strategy is essential for a reliable data pipeline. The system's approach is multi-layered, combining retries for transient issues with quarantine procedures for persistent failures.
* General Approach: The system will retry transient errors, log all events using the structured logger, and route persistent failures to a Dead-Letter Queue (DLQ) to prevent pipeline blockage. Custom Python exceptions are used to signal specific error conditions.
* External API Calls: The tenacity library will be configured to automatically retry transient network errors, HTTP 5xx server errors, and HTTP 429 rate-limiting errors. It will use an exponential backoff strategy with jitter and will respect the Retry-After header when provided. Persistent API errors that fail after all retries will cause the relevant data chunk to be marked as 'failed' and logged with full context.
* Database Operations: All database write operations for a batch of data will be performed within a single atomic transaction. If an error occurs during the write (e.g., a data type mismatch or constraint violation), the transaction will be rolled back to prevent partial data insertion. The entire problematic batch will then be sent to the DLQ for analysis.
* Data Processing and Validation: Errors that occur during data transformation or validation will result in the specific problematic record or batch being quarantined. The pipeline will continue to process other valid records, ensuring that a single malformed record does not halt the entire job.

## Coding Standards

All code contributed to the project must adhere to a strict set of standards to ensure quality, consistency, and maintainability.
* Style Guide & Linters: Code must adhere to PEP 8. It will be automatically formatted with Black and linted with Ruff. These tools will be configured in pyproject.toml and enforced in the CI pipeline.
* Type Safety: All new code must be fully type-hinted using Python's standard type annotation syntax. Static type checking will be performed with MyPy to catch potential type-related errors before runtime.
* Documentation: All public modules, classes, and functions must have comprehensive Google-style docstrings. This format is required for automated documentation generation using Sphinx.
* Dependency Management: All project dependencies must be explicitly defined in requirements.txt with pinned versions. New dependencies must be vetted for necessity, maintenance status, and license compatibility before being added.
* Conventions and Anti-Patterns: Developers must follow standard Python conventions, including snake_case for variables and functions, PascalCase for classes, absolute imports, and the use of with statements for resource management. Hardcoding configuration values and bypassing architectural layers are strictly forbidden.

## Overall Testing Strategy

A comprehensive testing strategy is crucial for verifying the correctness and reliability of the data pipeline.
* Tools: The primary testing framework is PyTest. Mocking of external dependencies will be handled using unittest.mock (or pytest-mock).
* Unit Tests: Unit tests are the foundation of the testing strategy. They will be prioritized for individual functions and classes, especially critical business logic within the transformation, validation, and storage components. All external dependencies, such as APIs and the database, must be mocked to ensure tests are fast and isolated. Tests will be located in the tests/unit/ directory, mirroring the src/ structure.
* Integration Tests: Integration tests will focus on verifying the interactions between components. Key scenarios include testing the full pipeline flow (Extract -> Transform -> Validate -> Store) for a small, controlled dataset, and verifying connectivity and basic data parsing from the live (or recorded) Databento API into a test TimescaleDB instance running in Docker.
* End-to-End (E2E) Tests: Comprehensive E2E tests are out of scope for the MVP. However, manual validation will be performed using CLI-driven test scenarios to verify the behavior of the complete application for well-defined use cases.
* Test Data Management: Small, static test data files, such as sample API responses or .dbn files, will be stored in the tests/fixtures/ directory and used to provide consistent inputs for tests.

## Security Best Practices

Security is a primary concern and will be addressed through the following mandatory practices.
* Secrets Management: API keys, database credentials, and other secrets must not be hardcoded in the source code or committed to version control. They will be loaded exclusively from environment variables or a local .env file (which is git-ignored) at runtime using pydantic-settings.
* Input Validation: All data received from external APIs will be strictly validated by Pydantic models upon ingestion to prevent processing of malformed or unexpected data structures. All inputs from the CLI will be validated by Typer.
* Dependency Security: Project dependencies will be regularly scanned for known vulnerabilities using a tool like pip-audit. Dependencies will be kept up-to-date to mitigate security risks.
* Information Disclosure: Detailed internal error information, such as stack traces, will never be shown to the user on the console. Such details will be written to secure, structured logs, while generic, user-friendly error messages will be displayed on the CLI.
* Principle of Least Privilege: When configuring database connections, the application user should be granted only the permissions necessary to perform its tasks (e.g., SELECT, INSERT, UPDATE), rather than full administrative privileges.

## Key Reference Documents

Maintaining links to foundational project documents is crucial for providing context to developers and stakeholders. It ensures that the rationale behind key decisions is not lost over time.
* Product Requirements Document (PRD) for Hist_Data_Ingestor (MVP): (Path: docs/prd.md) - Defines the project's goals, scope, functional and non-functional requirements, and user stories.
* Architecting a Configurable and API-Agnostic Financial Data Platform with Python and TimescaleDB: Foundational research document informing the core architectural concepts of modularity, configurability, and the choice of TimescaleDB.
* Databento Downloader: Detailed Specifications: Research document providing specific implementation details and best practices for integrating with the Databento API.

## Change Log

This architecture document is a living document. All significant changes to the architecture must be recorded in the change log to maintain a history of its evolution.

Change
Date
Version
Description
Author
Initial Draft for MVP Architecture
2025-06-01
1.0.0
First complete draft of the MVP architecture.
Architect
Consolidated Architecture
(Current Date)
2.0.0
Merged detailed v1 architecture with recent updates, re-establishing API-agnostic scope and adding detailed API/data models.
Architect
