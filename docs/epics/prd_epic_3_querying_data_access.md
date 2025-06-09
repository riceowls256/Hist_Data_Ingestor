# PRD Epic 3: Querying & Data Access

**Source:** prd.md §8, Epic 3

**Summary:**
Specifies the features for querying ingested data, including a CLI interface, query module, and support for flexible, user-friendly data access patterns.

---

## Story 3.1: Implement CLI for Querying and Managing Data
**Reference:** PRD §8, Epic 3, Story 3.1

**As a** Developer
**I want to** implement a CLI for querying and managing data
**So that** users can easily access and manage ingested data

### Tasks
- [ ] Design CLI commands for querying and data management
- [ ] Implement filtering and aggregation options
- [ ] Provide output formatting and export options
- [ ] Write unit and integration tests for CLI features

### Acceptance Criteria
- [ ] CLI supports all required query and management operations
- [ ] Output is correctly formatted and exportable
- [ ] Tests pass for all CLI features 

# PRD Epic 3: Databento Integration & End-to-End Data Flow

**Source:** prd.md Epic 3

**Goal:** Implement the complete data ingestion pipeline (extraction, basic transformation, validation, storage) for the Databento API for the specified symbols and data frequency, reusing and extending the framework components built in Epic 1 & 2.

---

## Story 3.1: Configure Databento API Access and Parameters
**Story Statement:** As a Developer, I want to create an API-specific YAML configuration file for Databento (`configs/api_specific/databento_config.yaml`) that includes the API key (referencing environment variables for the secret), dataset IDs, target schemas (e.g., `mbo`, `trades`, `ohlcv-1m`), symbology type (`stype_in`), data extraction parameters (symbols, date ranges), and references to transformation/validation rules, so that the system can connect to and understand how to process data from Databento.

**Acceptance Criteria (ACs):**
1. Databento Configuration File Created: `databento_config.yaml` created in `configs/api_specific/`.
2. Authentication Configuration: YAML contains `api` section with `key_env_var` (e.g., `DATABENTO_API_KEY`).
3. Job Definition Structure: YAML includes a `jobs` list, each item with `dataset`, `schema`, `symbols`, `start_date`, `end_date`, `stype_in`, optional `date_chunk_interval_days`.
4. Data Extraction Parameters (General): YAML includes basic `retry_policy` for Databento.
5. Mapping and Validation References (Placeholders): YAML includes `mapping_config_path` (to `databento_mappings.yaml`) and `validation_schema_paths`.
6. YAML Validity and Pydantic Compatibility: `databento_config.yaml` is well-formed and aligns with Pydantic models from "Databento Downloader: Detailed Specifications".
7. Documentation (README Update): `configs/README.md` updated with Databento config example.

---

## Story 3.2: Implement Databento API Adapter using Python Client for Data Extraction
**Story Statement:** As a Developer, I want to implement a `DatabentoAdapter` class (e.g., in `src/ingestion/api_adapters/databento_adapter.py`) that utilizes the official `databento-python` client library to connect to the Databento API using the provided configuration (API key, dataset, symbols, schema, stype_in, date range), fetch historical data via `timeseries.get_range()`, iterate through the `DBNStore` to yield decoded DBN records, and handle API-specific nuances, so that raw, structured data objects from Databento can be reliably extracted.

**Acceptance Criteria (ACs):**
1. `DatabentoAdapter` Class Created: Class in `src/ingestion/api_adapters/databento_adapter.py`, ideally inheriting `BaseAdapter`.
2. Configuration Driven: Adapter constructor uses Databento config to init `databento.Historical` client and determine request params.
3. Data Fetching Method (`Workspace_historical_data`): Method takes job config, calls `client.timeseries.get_range()`, iterates `DBNStore`.
4. DBN Record to Pydantic Model Conversion: Adapter converts DBN records to corresponding Pydantic models from "Databento Downloader: Detailed Specifications".
5. Output Decoded Pydantic Records: `Workspace_historical_data` yields/returns list of validated Databento Pydantic model instances.
6. Handles Multiple Symbols & Date Chunking (as per config): Processes all symbols; implements date chunking if `date_chunk_interval_days` configured.
7. Basic Error Handling & Retries (Leveraging Tenacity): Adapter implements `tenacity` retry logic (respecting `Retry-After`) around `client.timeseries.get_range()`, using config parameters.
8. Unit Tests: Unit tests for `DatabentoAdapter` (mocking `databento.Historical` client) verify param passing, `DBNStore` iteration, Pydantic conversion, error handling, and date chunking.

---

## Story 3.3: Define and Implement Data Transformation Rules for Decoded Databento Records
**Story Statement:** As a Developer, I want to define and implement transformation rules (e.g., in a `src/transformation/mapping_configs/databento_mappings.yaml`) to map fields from the decoded Databento Pydantic record objects (e.g., `MboMsg`, `TradeMsg`, as defined in the "Databento Downloader: Detailed Specifications" document) into the standardized internal data model, so that Databento data is consistent with the system's common format. This may involve less transformation if the Pydantic models already handle price scaling and timestamp conversions.

**Acceptance Criteria (ACs):**
1. Databento Mapping Configuration File Created: `databento_mappings.yaml` created in `src/transformation/mapping_configs/`.
2. Field Mapping Rules (Pydantic to Standardized Model): YAML maps attributes from source Databento Pydantic models to standardized internal model fields.
3. Minimal Data Type Conversions (if still needed): YAML includes further type conversions if Databento Pydantic model types differ from internal model types.
4. Handling of Different Databento Schemas (Record Types): Mapping config and `RuleEngine` correctly apply mappings for different Databento record types (`MboMsg`, `TradeMsg`, `OhlcvMsg`).
5. Transformation Logic Integrated with `RuleEngine`: `RuleEngine` parses `databento_mappings.yaml` and applies rules to Databento Pydantic model instances.
6. Unit Tests for Databento Transformations: Unit tests verify `RuleEngine` correctly applies `databento_mappings.yaml` rules to sample Databento Pydantic objects, producing expected standardized output.

---

## Story 3.4: Define and Implement Data Validation Rules for Decoded Databento Records
**Story Statement:** As a Developer, I want to define and implement validation rules. Since the `databento-python` client and the provided Pydantic models (from "Databento Downloader: Detailed Specifications" document) already perform significant schema validation and type conversion: Initial validation will rely on the successful instantiation of these Databento-specific Pydantic models. Post-transformation (to standardized internal model) checks (e.g., using Pandera or custom functions) will focus on business rules and consistency checks outlined in NFR 3 (e.g., positive prices, High >= Low), so that the integrity and quality of Databento data are ensured before storage.

**Acceptance Criteria (ACs):**
1. Leverage Databento Pydantic Models for Initial Validation: `DatabentoAdapter` ensures DBN records convert to strict Pydantic models from "Databento Downloader: Detailed Specifications". Failed instantiations are logged & quarantined (NFR 3).
2. Post-Transformation Databento Data Quality Checks Defined: Validation rules (Pandera schemas or custom functions in `src/transformation/validators/databento_validators.py`) defined for standardized data from Databento. Checks include positive numerics for OHLCV, High >= Low, Open/Close within Low/High, valid timestamp, non-empty/expected symbol.
3. Validation Logic Implemented & Integrated: Post-transformation checks implemented and integrated into Databento data flow.
4. Validation Failure Handling (Log & Quarantine Implemented): Failed post-transformation records are logged (record, rule) and quarantined (NFR 3).
5. Unit Tests for Validation Rules: Unit tests for Databento Pydantic models (validation/rejection) and custom post-transformation validation functions/schemas.

---

## Story 3.5: Integrate Databento Data Flow into Pipeline Orchestrator
**Story Statement:** As a Developer, I want to ensure the `PipelineOrchestrator` can correctly use the Databento adapter, transformation, and validation components, so that an end-to-end ingestion process for Databento data can be triggered and managed, reusing the orchestration logic.

**Acceptance Criteria (ACs):**
1. `PipelineOrchestrator` Handles Databento API Type: Orchestrator identifies "databento" API type and loads its components.
2. Databento Pipeline Definition in Orchestrator: Orchestrator uses Databento config, adapter, transformation rules, validation rules, and common `TimescaleLoader`.
3. Sequential Step Execution for Databento: Orchestrator correctly executes: Load Databento job config -> Init Databento Adapter -> Fetch Pydantic records -> Initial validation (Pydantic) -> Transform to standardized model -> Post-transformation validation -> Pass data to storage layer.
4. Data Flow Between Components (Databento): Databento Pydantic objects, then standardized internal model data, passed correctly.
5. Error Propagation and Handling by Orchestrator (Databento): Orchestrator handles/logs errors from Databento pipeline steps, respects Log & Quarantine (NFR 3) and component-level retries (NFR 2).
6. CLI Trigger for Databento Pipeline: CLI command (e.g., `python main.py ingest --api databento --dataset <id> --schema <name> --symbols <sym1,sym2> --start_date <YYYY-MM-DD> --end_date <YYYY-MM-DD>`) triggers Databento pipeline.
7. Logging of Orchestration Steps (Databento): Orchestrator logs key lifecycle events for Databento pipeline run.

---

## Story 3.6: Test End-to-End Databento Data Ingestion and Storage
**Story Statement:** As a Developer, I want to perform end-to-end tests for the Databento data pipeline, fetching a small sample of historical data (using the `databento-python` client via the adapter), processing it through transformation and validation, and verifying its correct and idempotent storage in TimescaleDB, so that the complete data flow for Databento is confirmed to be working as expected using the established framework.

**Acceptance Criteria (ACs):**
1. Test Data Scope Defined (Databento): Small, specific test dataset defined for Databento (e.g., 1-2 symbols, specific dataset/schema, 1-2 days data), documented.
2. `TimescaleLoader` Reusability Confirmed: Existing `TimescaleLoader` processes standardized data from Databento pipeline without Databento-specific core logic changes.
3. End-to-End Pipeline Run for Databento Test Data: `PipelineOrchestrator` executes Databento pipeline for test data via CLI without unhandled errors.
4. Data Correctly Stored in TimescaleDB (Databento): Ingested, transformed, validated Databento test data is present and correct in TimescaleDB, verified by direct query.
5. Idempotency Verified (Databento): Second run with same test data does not create duplicates or incorrectly change valid records.
6. Quarantine Handling Verified (Databento - if applicable): Sample Databento data designed to fail validation is correctly quarantined; only valid data in main table.
7. Logs Confirm Successful Flow (Databento): Logs confirm successful completion of each stage for Databento test data, or errors/quarantining. 