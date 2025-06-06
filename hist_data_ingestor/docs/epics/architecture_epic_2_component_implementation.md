# Architecture Epic 2: Component Implementation

**Source:** architecture.md §6

**Summary:**
Describes the implementation of all core components required for the data ingestion pipeline. Each component is responsible for a distinct part of the ETL process, from configuration management to data extraction, transformation, validation, storage, progress tracking, orchestration, querying, CLI, and logging.

**Components:**
- ConfigManager
- APIExtractionLayer (with adapters for IB and Databento)
- DataTransformationEngine (RuleEngine)
- DataValidationModule
- DataStorageLayer (TimescaleLoader)
- DownloadProgressTracker
- PipelineOrchestrator
- QueryingModule
- CLI (Typer-based)
- LoggingModule (structlog-based)

**Traceability:** See architecture.md §6 for detailed responsibilities and interactions.

---

## Story 2.1: Implement ConfigManager
**Reference:** Architecture Doc §6 (ConfigManager)

**As a** developer
**I want to** implement a ConfigManager that loads and validates all configurations
**So that** all components receive type-safe, validated configuration data

### Tasks
- [ ] Load system, API, and transformation configs from YAML files
- [ ] Validate configs using Pydantic models
- [ ] Make configs available to other modules via a clear interface
- [ ] Handle missing/invalid configs with clear errors and logs

### Acceptance Criteria
- [ ] ConfigManager loads and validates all configs
- [ ] Errors are logged and surfaced clearly
- [ ] Other modules can access configs easily

---

## Story 2.2: Implement APIExtractionLayer
**Reference:** Architecture Doc §6 (APIExtractionLayer)

**As a** developer
**I want to** implement adapters for Interactive Brokers and Databento APIs
**So that** the system can fetch raw historical data from multiple sources in a consistent way

### Tasks
- [ ] Implement BaseAdapter interface
- [ ] Implement InteractiveBrokersAdapter and DatabentoAdapter
- [ ] Handle authentication, connection, and request formation for each API
- [ ] Support asynchronous data fetching
- [ ] Handle API errors and rate limits

### Acceptance Criteria
- [ ] Adapters fetch data as specified
- [ ] Errors and rate limits are handled gracefully

---

## Story 2.3: Implement DataTransformationEngine
**Reference:** Architecture Doc §6 (DataTransformationEngine)

**As a** developer
**I want to** transform raw API data into a standardized internal format using YAML-defined rules
**So that** all ingested data conforms to a common schema

### Tasks
- [ ] Load transformation rules from YAML mapping configs
- [ ] Apply field mappings and type conversions
- [ ] Support custom Python functions for complex transformations
- [ ] Output data in the standardized internal model

### Acceptance Criteria
- [ ] Transformation logic is configurable and robust
- [ ] Output matches the standardized model

---

## Story 2.4: Implement DataValidationModule
**Reference:** Architecture Doc §6 (DataValidationModule)

**As a** developer
**I want to** validate both raw and transformed data using Pydantic and Pandera schemas
**So that** only high-quality, valid data is stored

### Tasks
- [ ] Validate raw API responses with Pydantic models
- [ ] Validate transformed data with Pandera schemas
- [ ] Quarantine invalid records and log errors

### Acceptance Criteria
- [ ] Invalid data is quarantined and logged
- [ ] Valid data passes all checks

---

## Story 2.5: Implement DataStorageLayer
**Reference:** Architecture Doc §6 (DataStorageLayer)

**As a** developer
**I want to** store validated data in TimescaleDB using SQLAlchemy models and upsert strategies
**So that** data is persisted efficiently and without duplication

### Tasks
- [ ] Define SQLAlchemy models for all tables
- [ ] Implement upsert logic
- [ ] Handle batch insertions
- [ ] Manage schema creation and migrations

### Acceptance Criteria
- [ ] Data is stored idempotently and efficiently
- [ ] Schema matches architecture doc

---

## Story 2.6: Implement DownloadProgressTracker
**Reference:** Architecture Doc §6 (DownloadProgressTracker)

**As a** developer
**I want to** track the progress and status of ingestion jobs and chunks
**So that** jobs can be resumed, retried, and monitored accurately

### Tasks
- [ ] Maintain state for each ingestion job and chunk
- [ ] Update status after each processing step
- [ ] Support resumable and incremental ingestion

### Acceptance Criteria
- [ ] Progress is tracked and visible
- [ ] Jobs can be resumed or retried as needed

---

## Story 2.7: Implement PipelineOrchestrator
**Reference:** Architecture Doc §6 (PipelineOrchestrator)

**As a** developer
**I want to** sequence the ETL steps and manage errors
**So that** the data pipeline runs smoothly and robustly

### Tasks
- [ ] Orchestrate calls to all pipeline components
- [ ] Handle chunking and parallelization
- [ ] Manage error handling and reporting
- [ ] Update DownloadProgressTracker

### Acceptance Criteria
- [ ] Pipeline runs end-to-end as designed
- [ ] Errors are handled and logged

---

## Story 2.8: Implement QueryingModule
**Reference:** Architecture Doc §6 (QueryingModule)

**As a** developer
**I want to** provide a way to query stored data by symbol, date range, and other criteria
**So that** users can access ingested data for analysis

### Tasks
- [ ] Build dynamic SQL queries based on user input
- [ ] Return results in a user-friendly format
- [ ] Integrate with CLI for user access

### Acceptance Criteria
- [ ] Querying is flexible and performant
- [ ] Results are accurate and easy to use

---

## Story 2.9: Implement CLI
**Reference:** Architecture Doc §6 (CLI)

**As a** developer
**I want to** implement a CLI using Typer for job initiation and data querying
**So that** users can interact with the system easily from the command line

### Tasks
- [ ] Implement commands for ingestion and querying
- [ ] Validate user input and provide helpful error messages
- [ ] Display progress and results clearly

### Acceptance Criteria
- [ ] CLI is user-friendly and robust
- [ ] All core operations are accessible via CLI

---

## Story 2.10: Implement LoggingModule
**Reference:** Architecture Doc §6 (LoggingModule)

**As a** developer
**I want to** provide structured, context-rich logging using structlog
**So that** all events, errors, and context are captured for debugging and monitoring

### Tasks
- [ ] Configure structlog for JSON output
- [ ] Ensure all components use the logging module
- [ ] Include contextual information in all logs

### Acceptance Criteria
- [ ] Logs are structured, complete, and useful for debugging 