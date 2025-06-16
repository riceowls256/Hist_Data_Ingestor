# Epic 3: Basic Querying Interface & MVP Wrap-up
> This document is a granulated shard from the main "Hist_Data_Ingestor Product Requirements Document (PRD)" focusing on "Epic 3: Basic Querying Interface & MVP Wrap-up".

**Goal**: Develop the basic querying interface to retrieve stored data from TimescaleDB by symbol and date range, and ensure all MVP success metrics can be demonstrated.

**Stories**:
**Story 3.1: Design and Implement Basic Data Querying Logic**
**Story Statement**: As a Developer, I want to implement a data querying module (e.g., in src/querying/query_builder.py or as part of src/storage/timescale_handler.py) that uses SQLAlchemy to construct and execute SQL queries against the TimescaleDB financial_time_series_data table (and potentially other tables for different Databento schemas), allowing data retrieval by security_symbol and a event_timestamp date range.
**Acceptance Criteria (ACs)**:
AC1: Querying Module/Functions Created: Python module(s) and functions are created (e.g., within src/querying/ or as methods in src/storage/timescale_handler.py) to encapsulate data retrieval logic from TimescaleDB.
AC2: SQLAlchemy for Query Construction: The querying logic uses SQLAlchemy Core or ORM to construct type-safe SQL queries for the relevant data tables.
AC3: Filter by Symbol: The querying functions accept a security_symbol (string) or a list of security_symbols (list of strings) as a parameter and correctly filter the data for the specified symbol(s).
AC4: Filter by Date Range: The querying functions accept start_date and end_date (Python date or datetime objects) as parameters and correctly filter the data for records where event_timestamp falls within this range (inclusive of start and end dates).
AC5: Data Returned in Usable Format: The querying functions return the retrieved data in a well-defined, documented format suitable for CLI output and potential programmatic use by other modules (e.g., a list of Python dictionaries, a list of Pydantic model instances representing the standardized record, or a Pandas DataFrame). The specific format will be determined during implementation with a preference for simplicity and ease of use.
AC6: Handles No Data Found: If no data matches the query criteria, the function returns an empty list (or equivalent empty structure for the chosen format) gracefully, without raising an error.
AC7: Basic Error Handling: Basic error handling for database connection issues or query execution failures is implemented, logging errors appropriately using the established logging framework.
AC8: Performance Consideration & Index Utilization: The query construction is designed to leverage existing indexes on security_symbol and event_timestamp in TimescaleDB to meet the performance NFR (under 5 seconds for a typical query of 1 month of daily data for one symbol).
AC9: Unit Tests for Query Logic: Unit tests are created for the querying functions. These tests will mock the SQLAlchemy engine/session and database responses to verify correct query construction based on input parameters (symbol, date range) and correct handling of various return scenarios (data found, no data found).

**Story 3.2: Expose Querying Functionality via CLI**
**Story Statement**: As a Developer, I want to add a new CLI command (e.g., python main.py query --symbols <symbol1,symbol2> --start_date <YYYY-MM-DD> --end_date <YYYY-MM-DD> [--schema <schema_name>][--output_format <csv/json>]) that utilizes the data querying module to fetch data for one or more symbols and output it to the console or a specified file format (e.g., CSV, JSON).
**Acceptance Criteria (ACs)**:
AC1: New CLI query Command Implemented: A new subcommand query is added to the main CLI application (main.py or equivalent entry point).
AC2: Accepts Multiple Symbols Parameter: The query command accepts a --symbols (or -s) argument that can take one or more security symbols. The input mechanism should be user-friendly (e.g., a comma-separated list like --symbols AAPL,MSFT, or allowing the argument to be specified multiple times like -s AAPL -s MSFT). The underlying query logic from Story 3.1 must support filtering by a list of symbols.
AC3: Accepts Date Range Parameters: The query command accepts --start_date (or -sd) and --end_date (or -ed) arguments, expecting dates in "YYYY-MM-DD" format. Input validation for date format should be present.
AC4: Optional Schema Parameter: The query command accepts an optional --schema argument to specify which Databento schema to query (e.g., ohlcv.1m, trades). Defaults to a primary schema if not provided (e.g., daily OHLCV).
AC5: Optional Output Format Parameter: The query command accepts an optional --output_format (or -f) argument, supporting at least "csv" and "json". It should default to a user-friendly console output.
AC6: Optional Output File Parameter: The query command accepts an optional --output_file (or -o) argument. If provided, the output is written to this file in the specified (or default) format; otherwise, output is directed to the console.
AC7: Invokes Query Logic: The CLI command correctly parses all input parameters and calls the querying functions developed in Story 3.1.
AC8: Handles Query Results:
If data is returned, it's formatted according to the --output_format and directed to the console or the specified output file.
If no data is returned for the given criteria, a user-friendly message like "No data found for the specified criteria." is displayed on the console.
AC9: Handles Errors Gracefully: Errors from the querying logic are caught, and user-friendly error messages are presented on the CLI.
AC10: README Updated with Query CLI Usage: The main README.md is updated with clear instructions and examples on how to use the query CLI command.

**Story 3.3: Develop and Execute MVP Success Metric Verification Scripts/Tests**
**Story Statement**: As a Developer, I want to create and run scripts or automated tests that verify the MVP success metrics defined in the PRD (Goal section), such as confirming data availability from Databento, testing querying capability and performance, calculating data integrity rates, and monitoring operational stability, so that we can objectively assess if the MVP goals have been met.
**Acceptance Criteria (ACs)**:
AC1: Data Availability Verification Script/Test:
A script queries TimescaleDB to confirm presence of data for MVP target symbols from Databento for a recent period across key schemas (e.g., ohlcv.1d, trades).
Reports success if data is found.
AC2: Querying Capability & Performance Test Script:
A script uses the CLI query command for benchmark queries (e.g., 1 month daily data for 5 MVP symbols).
Measures response time (target <5s) and confirms data return without errors.
AC3: Data Integrity Rate Calculation Method/Script:
Method/script analyzes ingestion logs and quarantine for a test period for Databento.
Calculates/provides data for % records failed validation vs. stored.
Compares against <1% target (NFR 3).
AC4: Operational Stability Monitoring Plan & Initial Check:
Brief plan documented for user to track "95% operational stability" (NFR 2) post-MVP.
At least one automated Databento ingestion run (small dataset) completes successfully without manual intervention, confirmed in logs.
AC5: Test Execution and Results Documentation: Verification scripts/tests executed. Summary report/logs document execution and results against targets.
AC6: Scripts Version Controlled: Scripts and supporting files committed to Git.

**Story 3.4: Finalize MVP Documentation (READMEs, Setup, Usage)**
**Story Statement**: As a Developer, I want to review and finalize all project documentation to ensure they accurately reflect the MVP's functionality, setup, configuration, CLI usage for Databento ingestion and querying, and basic troubleshooting, so that the primary user can effectively use and maintain the system.
**Acceptance Criteria (ACs)**:
AC1: Top-Level README.md Review and Update: Includes project overview, prerequisites, setup instructions (.env, docker-compose up), CLI examples for Databento ingestion and querying, log/quarantine locations, troubleshooting, health check routine, DB backup note, project structure overview.
AC2: configs/README.md Review and Update: Describes system_config.yaml, databento_config.yaml structure (explaining parameters for various schemas), and high-level notes on adding new API configs.
AC3: src/ Module-Level READMEs Review and Update: Concise READMEs in src subdirectories describe purpose and key components.
AC4: Code Docstrings Review (Spot Check): Spot check key public modules/classes/functions for clarity and adherence to NFR 5.
AC5: Consistency and Accuracy: Documentation checked for consistency and accuracy with implemented MVP.
AC6: Documentation Formatted and Readable: Markdown is well-formatted and easy to read.

**Story 3.5: MVP Demonstration and Handoff Preparation**
**Story Statement**: As a Developer, I want to prepare a demonstration of the end-to-end MVP functionality (local setup, configuration, data ingestion for Databento for a sample of schemas, CLI querying, log review, quarantine review) and package the final MVP codebase, so that it can be handed off to the primary user.
**Acceptance Criteria (ACs)**:
AC1: MVP Demonstration Plan Created: Outline for demonstrating setup, .env config, docker-compose up, Databento ingestion (sample schemas), log/quarantine review, CLI querying, TimescaleDB data structure.
AC2: Successful MVP Demonstration Performed: Demonstration successfully showcases all planned functionalities.
AC3: Final Code Review & Cleanup (Minor): Final pass over codebase for minor cleanup.
AC4: All Code Committed and Pushed: All final MVP code, documentation, scripts, configurations committed to main branch.
AC5: Project Archived/Tagged (Optional): Git tag (e.g., v0.1.0-mvp) created.
AC6: Handoff Checklist (Simple): Simple "next steps" checklist for primary user (scheduling ingestion, monitoring, adding symbols).