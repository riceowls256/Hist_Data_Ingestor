"""
Shared constants for CLI commands.
"""

from typing import Dict, Any

# Schema mapping for CLI query command
SCHEMA_MAPPING = {
    "ohlcv-1d": "query_daily_ohlcv",
    "ohlcv": "query_daily_ohlcv",  # Alias
    "trades": "query_trades",
    "tbbo": "query_tbbo",
    "statistics": "query_statistics",
    "definitions": "query_definitions"
}

# Default configuration values
DEFAULT_CONFIGS = {
    "output_format": "table",
    "limit": 100,
    "timeout": 300,
    "batch_size": 1000,
    "retry_attempts": 3,
    "log_level": "INFO"
}

# Supported output formats
OUTPUT_FORMATS = ["table", "csv", "json", "parquet"]

# Supported data schemas
SUPPORTED_SCHEMAS = [
    "ohlcv-1d", "ohlcv-1s", "ohlcv-1m", "ohlcv-1h",
    "trades", "tbbo", "statistics", "definitions"
]

# Symbol type mappings
SYMBOL_TYPES = {
    "continuous": "continuous",
    "parent": "parent", 
    "raw_symbol": "raw_symbol",
    "instrument_id": "instrument_id"
}

# Date format patterns
DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d/%m/%Y"
]

# API provider configurations
API_PROVIDERS = {
    "databento": {
        "name": "Databento",
        "base_url": "https://hist.databento.com",
        "supported_schemas": SUPPORTED_SCHEMAS,
        "rate_limit": 1000
    }
}

# CLI help text constants
HELP_TEXT = {
    "quick_start": """
🚀 Quick Start Guide:
1. Check system status: python main.py status
2. Run ingestion: python main.py ingest --api databento --job ohlcv_1d
3. Query data: python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31
""",
    "common_patterns": """
📋 Common Usage Patterns:
• Daily OHLCV: --schema ohlcv-1d --symbols ES.FUT,CL.FUT
• Trade data: --schema trades --symbols ES.c.0 --start-date 2024-01-01 --end-date 2024-01-02
• Definitions: --schema definitions --symbols ES.FUT --stype-in parent
"""
}