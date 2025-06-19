"""
CLI-specific type definitions for the Historical Data Ingestor.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import date

# Type aliases for CLI operations
CLIConfig = Dict[str, Any]
CommandResult = Dict[str, Any]
SymbolList = List[str]
DateRange = tuple[date, date]
OutputFormat = str
SchemaType = str

# CLI command parameter types
IngestParams = Dict[str, Union[str, List[str], date, bool, int]]
QueryParams = Dict[str, Union[str, List[str], date, int, Optional[str]]]
ValidationParams = Dict[str, Union[str, List[str], bool]]

# Progress and status types
ProgressCallback = callable
StatusInfo = Dict[str, Union[str, int, bool, List[str]]]