# Project Retrospective: Lessons Learned

## Overview
This document captures key lessons learned and improvements made during the implementation of Story 1.3. It is intended as a living reference for future stories, agent handoffs, and contributors.

---

## 1. Docker Compose Version Field
- **Initial:** Used `version: '3.8'` at the top of docker-compose.yml.
- **Lesson:** Modern Docker Compose ignores the version field and emits a warning.
- **Fix:** Removed the version field for compatibility and to eliminate confusion.

## 2. Entrypoint Path and Project Structure
- **Initial:** Dockerfile and docker-compose.yml used `python -m src.main` as the entrypoint, assuming src was at the project root.
- **Lesson:** The actual path was hist_data_ingestor/src/main.py, so the entrypoint needed to be `python hist_data_ingestor/src/main.py`.
- **Fix:** Updated both Dockerfile and docker-compose.yml to use the correct path, ensuring the app container could start successfully.

## 3. main.py Content
- **Initial:** main.py was blank, so the container would start and immediately exit, or fail to find the module.
- **Lesson:** Even for environment testing, a minimal main.py is needed to verify the container and DB connection.
- **Fix:** Added a simple script to test TimescaleDB connectivity, providing clear feedback on success or failure.

## 4. .env File Location and Usage
- **Initial:** There was some ambiguity about where .env and .env.example should live and how they should be referenced.
- **Lesson:** For Docker Compose, .env should be in the project root, and .env.example should be provided as a template.
- **Fix:** Standardized on root-level .env and .env.example, updated documentation and cp commands accordingly.

## 5. Incremental, Granular Task Tracking
- **Initial:** Tasks were broad and high-level, which could obscure progress and make handoff harder.
- **Lesson:** Breaking down tasks into granular, actionable sub-tasks improves traceability, review, and handoff.
- **Fix:** Expanded the story file's Tasks section to include detailed sub-tasks, and checked them off as completed.

## 6. Documentation and Review Process
- **Initial:** README and story documentation were updated as a final step.
- **Lesson:** Iterative review and approval of each major deliverable (Dockerfile, compose, .env, README) ensures quality and shared understanding.
- **Fix:** Adopted a review-after-each-step workflow, logging approvals and changes in the story file.

## 7. ConfigManager Refactor (Story 1.2)
- **Initial:** The original ConfigManager used manual environment variable lookups and type-casting logic to override YAML config values, resulting in verbose and harder-to-maintain code.
- **Lesson:** Pydantic's BaseSettings can automatically handle environment variable overrides, type conversion, and validation, making manual logic unnecessary.
- **Fix:** Refactored ConfigManager and all config classes to inherit from Pydantic BaseSettings. Now, YAML provides defaults and environment variables override automatically. The code is leaner, more maintainable, and less error-prone. This change leverages Pydantic's strengths and reduces future maintenance burden.

## 8. Centralized Logging and Python Path Issues (Story 1.4)
- **Initial:** Implemented a centralized logger, but encountered issues with test discovery and imports due to Python path configuration.
- **Lesson:** Ensuring the correct PYTHONPATH and import structure is critical for consistent logger usage and successful test execution in a src-layout project.
- **Fix:** Standardized on using PYTHONPATH=src for test runs and updated imports in test files to match the project structure. Documented this in the story and README for future contributors.

## 9. Databento API Adapter Implementation (Story 2.2)
- **Initial:** Created complete DatabentoAdapter class with comprehensive features and robust error handling.
- **Lesson:** The adapter implementation showcased effective patterns for API adapters: environment-based configuration, date chunking for large requests, retry logic with exponential backoff, and proper inheritance from BaseAdapter interface.
- **Key Features:** Successfully implemented context manager support, multi-symbol batch processing, comprehensive error handling with structured logging, and DBN record to Pydantic model conversion for all schemas (OHLCV, Trades, TBBO, Statistics).

## 10. Architectural Improvement: Model Placement (Story 2.2)
- **Initial:** Pydantic models were created in `src/ingestion/api_adapters/databento_models.py`.
- **Lesson:** Data models shouldn't live in api_adapters directory as they serve as common data contracts for the entire pipeline (TransformationEngine, Validator, DataStorageLayer). API adapters should focus on data retrieval, not data schema definition.
- **Fix:** Moved models from `src/ingestion/api_adapters/databento_models.py` to `src/storage/models.py` for better architectural separation and reusability across the entire pipeline.

## 11. Critical Testing Oversight and Environment Resolution (Story 2.2)
- **Initial:** Implemented comprehensive functionality but failed to run tests during development - critical oversight in dev workflow.
- **Lesson:** Tests should be run early and frequently during development, not just at the end. When finally running tests, encountered numpy/conda environment conflict causing import errors.
- **Environment Issue:** `ImportError: Error importing numpy: you should not try to import numpy from its source directory.` caused by conda/pip package conflicts.
- **Fix:** Resolved by uninstalling and reinstalling packages cleanly: `pip uninstall -y numpy pandas databento databento-dbn` followed by `pip install numpy pandas databento`.
- **Outcome:** All 19 tests passed after fixing a minor date chunking logic error (expected chunk count correction).

## 12. Pydantic v2 Modernization (Story 2.2)
- **Initial:** Models used deprecated `json_encoders` in `model_config = ConfigDict()`, generating 24 deprecation warnings.
- **Lesson:** Staying current with framework updates is important for maintainability and avoiding deprecated features.
- **Fix:** Replaced deprecated `json_encoders` with modern Pydantic v2 `@field_serializer` decorators:
  - Added `@field_serializer` for `datetime` fields → ISO format strings using `isoformat()`
  - Added `@field_serializer` for `Decimal` fields → string representations using `str()`
  - Used `when_used='json'` parameter to ensure serializers only activate during JSON serialization
- **Outcome:** Eliminated all deprecation warnings while maintaining backward compatibility and proper JSON serialization.

## 13. Comprehensive Testing and Error Resolution (Story 2.2)
- **Initial:** Created comprehensive test suite with 19 test cases covering all adapter functionality.
- **Lesson:** Good test coverage includes success paths, error conditions, configuration validation, retry logic, and context manager behavior.
- **Testing Strategy:** Tests covered initialization, configuration validation, connection management, data fetching (success and failure), date chunking logic, and proper error handling.
- **Final Result:** 19/19 tests passing with comprehensive coverage and no warnings.

## 14. Critical Database Schema Alignment Issue (Story 2.3)
- **Initial:** Created comprehensive YAML mapping configurations and RuleEngine implementation, but mapped source fields to incorrect target field names.
- **Issue:** Field mappings used generic names (e.g., `open: "open"`, `symbol: "symbol"`) instead of actual database column names (e.g., `open: "open_price"`, no `symbol` column exists).
- **Discovery:** The Council review caught this critical oversight before testing - mappings were misaligned with actual TimescaleDB schema defined in architecture.md.
- **Impact:** This would have caused complete pipeline failure when the transformation engine produced dictionaries with keys that don't match database columns.
- **Root Cause:** Insufficient cross-referencing between transformation layer design and actual database schema definitions during implementation.
- **Fix:** 
  - Corrected all field mappings in both test and production YAML configs to match exact database column names
  - OHLCV: `open/high/low/close` → `open_price/high_price/low_price/close_price`
  - Removed non-existent fields like `symbol` from all mappings
  - Added missing required database columns with appropriate defaults
  - Updated validation rules to reference correct field names
- **Lesson:** **CRITICAL** - Always verify transformation output schema matches storage layer input schema exactly. The transformation layer is the bridge between external data formats and internal storage - both sides must align perfectly.
- **Process Improvement:** Add explicit schema validation step to ensure mapping configurations match database schemas before implementation.

## 15. Critical Data Integrity Fixes: Timezone and Precision Handling (Story 2.3)
- **Issue Discovery:** During implementation review, identified two critical data integrity risks that could cause silent errors:
  1. **Timezone Handling:** System assumed UTC timestamps without verification, risking off-by-hours errors if Databento client returns naive datetimes
  2. **Decimal Precision:** Need to verify all financial data uses Decimal type throughout pipeline to prevent precision loss
- **Timezone Findings:** 
  - ✅ **Good:** RuleEngine and YAML configs were designed for UTC normalization
  - ❌ **Risk:** No validation that incoming timestamps are timezone-aware; naive datetime assumptions could cause timing errors
- **Precision Findings:**
  - ✅ **Good:** All Pydantic models correctly use `Decimal` for price fields (open, high, low, close, vwap, bid_px, ask_px, stat_value, etc.)
  - ✅ **Good:** Database schema uses `NUMERIC` type to preserve precision
- **Fixes Implemented:**
  - **Pydantic Models:** Added `@field_validator` to all datetime fields in all models to ensure timezone-aware conversion (naive → UTC)
  - **RuleEngine:** Enhanced `_transform_field_value()` to properly handle naive datetime conversion with logging warnings
  - **RuleEngine:** Updated `_apply_global_transformations()` to ensure all output timestamps are timezone-aware UTC
  - **Logging:** Added warning logs when converting naive datetimes to help identify data source issues
- **Lesson:** **CRITICAL** - Never assume data source behavior. Always validate assumptions about timezone-awareness and data types at the earliest possible point in the pipeline.
- **Process Improvement:** Add explicit data integrity checks for timezone-awareness and numeric precision in transformation layer tests.

---

**Summary:**
Stories 2.2 and 2.3 demonstrated successful API adapter implementation and transformation rule engine development, but highlighted a critical lesson about schema alignment between pipeline layers. While the technical implementation was solid (comprehensive YAML configurations, robust RuleEngine with validation, proper error handling), the oversight of misaligned database field mappings would have caused complete pipeline failure. This emphasizes the importance of architectural cross-validation and the need for the transformation layer to serve as an exact bridge between external formats and internal storage schemas. The Council's review process proved invaluable in catching this critical issue before testing. 