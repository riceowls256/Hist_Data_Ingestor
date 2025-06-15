# Epic 2: Databento Integration & End-to-End Data Flow

> This document is a granulated shard from the main "Hist_Data_Ingestor Product Requirements Document (PRD)" focusing on "Epic 2: Databento Integration & End-to-End Data Flow".

**Goal**: Implement the complete data ingestion pipeline (extraction, basic transformation, validation, storage) for the Databento API for the specified symbols and data schemas (OHLCV, Trades, TBBO, Statistics), reusing and extending the framework components built in Epic 1.

**Stories**:
**Story 2.1: Configure Databento API Access and Parameters**
**Story Statement**: As a Developer, I want to create an API-specific YAML configuration file for Databento (configs/api_specific/databento_config.yaml) that includes the API key (referencing environment variables for the secret), dataset IDs, target schemas (e.g., ohlcv.1s, ohlcv.1m, ohlcv.1h, ohlcv.1d, trades, tbbo, statistics.market_summary), symbology type (stype_in), data extraction parameters (symbols, date ranges), and references to transformation/validation rules, so that the system can connect to and understand how to process data from Databento.
**Acceptance Criteria (ACs)**:
AC1: Databento Configuration File Created: databento_config.yaml created in configs/api_specific/.
AC2: Authentication Configuration: YAML contains api section with key_env_var (e.g., DATABENTO_API_KEY).
AC3: Job Definition Structure: YAML includes a jobs list, each item with dataset, schema (e.g., ohlcv.1s, trades, tbbo, statistics.daily_summary), symbols, start_date, end_date, stype_in, optional date_chunk_interval_days. The list of supported schemas must cover OHLCV (1s, 1m, 5m, 15m, 1h, 1d), Trades, TBBO, and a defined set of Statistics.
AC4: Data Extraction Parameters (General): YAML includes basic retry_policy for Databento.
AC5: Mapping and Validation References (Placeholders): YAML includes mapping_config_path (to databento_mappings.yaml) and validation_schema_paths.
AC6: YAML Validity and Pydantic Compatibility: databento_config.yaml is well-formed and aligns with Pydantic models from "Databento Downloader: Detailed Specifications" where applicable.
AC7: Documentation (README Update): configs/README.md updated with Databento config example, detailing how to specify the various schemas.

**Story 2.2: Implement Databento API Adapter using Python Client for Data Extraction**
**Story Statement**: As a Developer, I want to implement a DatabentoAdapter class (e.g., in src/ingestion/api_adapters/databento_adapter.py) that utilizes the official databento-python client library to connect to the Databento API using the provided configuration (API key, dataset, symbols, schema, stype_in, date range), fetch historical data via timeseries.get_range(), iterate through the DBNStore to yield decoded DBN records for various schemas (OHLCV, Trades, TBBO, Statistics), and handle API-specific nuances, so that raw, structured data objects from Databento can be reliably extracted.
**Acceptance Criteria (ACs)**:
AC1: DatabentoAdapter Class Created: Class in src/ingestion/api_adapters/databento_adapter.py, ideally inheriting BaseAdapter.
AC2: Configuration Driven: Adapter constructor uses Databento config to init databento.Historical client and determine request params for all configured schemas.
AC3: Data Fetching Method (Workspace_historical_data): Method takes job config, calls client.timeseries.get_range(), iterates DBNStore.
AC4: DBN Record to Pydantic Model Conversion: Adapter converts DBN records to corresponding Pydantic models from "Databento Downloader: Detailed Specifications" or custom Pydantic models for the defined schemas.
AC5: Output Decoded Pydantic Records: Workspace_historical_data yields/returns list of validated Databento Pydantic model instances for all requested schemas.
AC6: Handles Multiple Symbols & Date Chunking (as per config): Processes all symbols; implements date chunking if date_chunk_interval_days configured.
AC7: Basic Error Handling & Retries (Leveraging Tenacity): Adapter implements tenacity retry logic (respecting Retry-After) around client.timeseries.get_range(), using config parameters.
AC8: Unit Tests: Unit tests for DatabentoAdapter (mocking databento.Historical client) verify param passing, DBNStore iteration, Pydantic conversion for various schemas, error handling, and date chunking.

**Story 2.3: Define and Implement Data Transformation Rules for Decoded Databento Records**
**Story Statement**: As a Developer, I want to define and implement transformation rules (e.g., in a src/transformation/mapping_configs/databento_mappings.yaml) to map fields from the decoded Databento Pydantic record objects (e.g., for OHLCV, Trades, TBBO, Statistics, as defined in the "Databento Downloader: Detailed Specifications" document or custom models) into the standardized internal data model, so that Databento data is consistent with the system's common format. This may involve less transformation if the Pydantic models already handle price scaling and timestamp conversions.
**Acceptance Criteria (ACs)**:
AC1: Databento Mapping Configuration File Created: databento_mappings.yaml created in src/transformation/mapping_configs/.
AC2: Field Mapping Rules (Pydantic to Standardized Model): YAML maps attributes from source Databento Pydantic models to standardized internal model fields for all supported schemas.
AC3: Minimal Data Type Conversions (if still needed): YAML includes further type conversions if Databento Pydantic model types differ from internal model types.
AC4: Handling of Different Databento Schemas (Record Types): Mapping config and RuleEngine correctly apply mappings for different Databento record types (e.g., OhlcvMsg, TradeMsg, TbboMsg, StatisticMsg, or their equivalents).
AC5: Transformation Logic Integrated with RuleEngine: RuleEngine parses databento_mappings.yaml and applies rules to Databento Pydantic model instances.
AC6: Unit Tests for Databento Transformations: Unit tests verify RuleEngine correctly applies databento_mappings.yaml rules to sample Databento Pydantic objects for various schemas, producing expected standardized output.

**Story 2.4: Add Support for Databento Instrument Definition Schema**
**Story Statement**: As a Developer, I want to ingest, transform, and store historical instrument definition data from the Databento API, so that I can maintain a local, queryable database of instrument metadata (like expiration dates and strike prices) to enrich other financial time-series data.
**Acceptance Criteria (ACs)**:
AC1: Configuration Updated: The system can be configured to ingest the definition schema in databento_config.yaml.
AC2: Pydantic Model Created: A DatabentoDefinitionRecord Pydantic model is created in src/storage/models.py to represent the instrument definition record, including key fields like symbol, instrument_class, strike_price, and expiration.
AC3: Database Table Created: A definitions_data hypertable is created in TimescaleDB to store the standardized definition data. The creation script must be part of the storage layer's initialization logic.
AC4: API Adapter Enhanced: The DatabentoAdapter successfully fetches records for the definition schema and converts them into validated DatabentoDefinitionRecord instances.
AC5: Transformation Rules Added: A new mapping for the definition schema is added to databento_mappings.yaml, correctly transforming the Pydantic model to the target database format.
AC6: Basic Validation Implemented: Simple, field-level validation rules for definition data (e.g., checking for non-null required fields) are added to the transformation mapping.
AC7: End-to-End Test Case Added: A new end-to-end test exists that proves definition data can be ingested and stored correctly, triggered via a CLI command.
AC8: Documentation Updated: The prd.md, architecture.md, ingestion.md, and storage.md documents are all updated to reflect the addition of the new schema, Pydantic model, and database table.

**Story 2.5: Define and Implement Data Validation Rules for Decoded Databento Records**
**Story Statement**: As a Developer, I want to define and implement validation rules. Since the databento-python client and the provided Pydantic models (from "Databento Downloader: Detailed Specifications" document or custom models for schemas like TBBO, Statistics) already perform significant schema validation and type conversion: Initial validation will rely on the successful instantiation of these Databento-specific Pydantic models. Post-transformation (to standardized internal model) checks (e.g., using Pandera or custom functions) will focus on business rules and consistency checks outlined in NFR 3 (e.g., positive prices, High >= Low for OHLCV), so that the integrity and quality of Databento data are ensured before storage.
**Acceptance Criteria (ACs)**:
AC1: Leverage Databento Pydantic Models for Initial Validation: DatabentoAdapter ensures DBN records convert to strict Pydantic models. Failed instantiations are logged & quarantined (NFR 3).
AC2: Post-Transformation Databento Data Quality Checks Defined: Validation rules (Pandera schemas or custom functions in src/transformation/validators/databento_validators.py) defined for standardized data from Databento for all schemas. Checks include positive numerics for OHLCV, High >= Low, valid timestamps, non-empty/expected symbol, consistency for TBBO and Statistics fields.
AC3: Validation Logic Implemented & Integrated: Post-transformation checks implemented and integrated into Databento data flow.
AC4: Validation Failure Handling (Log & Quarantine Implemented): Failed post-transformation records are logged (record, rule) and quarantined (NFR 3).
AC5: Unit Tests for Validation Rules: Unit tests for Databento Pydantic models (validation/rejection) and custom post-transformation validation functions/schemas for all relevant schemas.

**Story 2.6: Integrate Databento Data Flow into Pipeline Orchestrator**
**Story Statement**: As a Developer, I want to ensure the PipelineOrchestrator can correctly use the Databento adapter, transformation, and validation components, so that an end-to-end ingestion process for Databento data (covering all defined schemas) can be triggered and managed, reusing the orchestration logic.
**Acceptance Criteria (ACs)**:
AC1: PipelineOrchestrator Handles Databento API Type: Orchestrator identifies "databento" API type and loads its components.
AC2: Databento Pipeline Definition in Orchestrator: Orchestrator uses Databento config, adapter, transformation rules, validation rules, and common TimescaleLoader.
AC3: Sequential Step Execution for Databento: Orchestrator correctly executes: Load Databento job config -> Init Databento Adapter -> Fetch Pydantic records for all schemas -> Initial validation (Pydantic) -> Transform to standardized model -> Post-transformation validation -> Pass data to storage layer.
AC4: Data Flow Between Components (Databento): Databento Pydantic objects, then standardized internal model data, passed correctly.
AC5: Error Propagation and Handling by Orchestrator (Databento): Orchestrator handles/logs errors from Databento pipeline steps, respects Log & Quarantine (NFR 3) and component-level retries (NFR 2).
AC6: CLI Trigger for Databento Pipeline: CLI command (e.g., python main.py ingest --api databento --dataset <id> --schema <name> --symbols <sym1,sym2> --start_date TSS-MM-DD --end_date TSS-MM-DD) triggers Databento pipeline for specified schemas.
AC7: Logging of Orchestration Steps (Databento): Orchestrator logs key lifecycle events for Databento pipeline run.

**Story 2.7: Test End-to-End Databento Data Ingestion and Storage**
**Story Statement**: As a Developer, I want to perform end-to-end tests for the Databento data pipeline, fetching a small sample of historical data for various schemas (using the databento-python client via the adapter), processing it through transformation and validation, and verifying its correct and idempotent storage in TimescaleDB, so that the complete data flow for Databento is confirmed to be working as expected using the established framework.
**Acceptance Criteria (ACs)**:
AC1: Test Data Scope Defined (Databento): Small, specific test dataset defined for Databento (e.g., 1-2 symbols, specific dataset/schemas like ohlcv.1m, trades, tbbo, 1-2 days data), documented.
AC2: TimescaleLoader Reusability Confirmed: Existing TimescaleLoader processes standardized data from Databento pipeline without Databento-specific core logic changes for all schemas.
AC3: End-to-End Pipeline Run for Databento Test Data: PipelineOrchestrator executes Databento pipeline for test data via CLI without unhandled errors.
AC4: Data Correctly Stored in TimescaleDB (Databento): Ingested, transformed, validated Databento test data for various schemas is present and correct in TimescaleDB, verified by direct query.
AC5: Idempotency Verified (Databento): Second run with same test data does not create duplicates or incorrectly change valid records.
AC6: Quarantine Handling Verified (Databento - if applicable): Sample Databento data designed to fail validation is correctly quarantined; only valid data in main table.
AC7: Logs Confirm Successful Flow (Databento): Logs confirm successful completion of each stage for Databento test data, or errors/quarantining.

