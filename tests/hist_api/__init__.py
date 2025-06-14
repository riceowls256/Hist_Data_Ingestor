"""
Historical API Tests

This module contains tests for validating historical data API integrations,
specifically for the Databento Historical API.

Test Scripts:
- test_api_connection.py: Basic connectivity and authentication validation
- test_futures_api.py: Comprehensive futures contract testing across schemas
- test_statistics_schema.py: Statistics schema exploration and validation
- test_definitions_schema.py: Definitions schema testing for instrument metadata
- analyze_stats_fields.py: Comprehensive statistics field analysis
- test_cme_statistics.py: CME Globex MDP 3.0 compliance verification
- debug_databento_record.py: Record structure debugging utilities

Usage:
Run from project root with virtual environment activated:
    source venv/bin/activate
    python tests/hist_api/test_api_connection.py

Environment Requirements:
- DATABENTO_API_KEY: 32-character API key starting with 'db-'
- DATABENTO_API_URL: https://hist.databento.com

See docs/api/databento_testing_guide.md for comprehensive testing procedures.
""" 