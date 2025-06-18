"""
Querying module for TimescaleDB financial data retrieval.

This module provides comprehensive querying capabilities for financial time-series
data stored in TimescaleDB, with support for all Databento schemas.
"""

from .query_builder import QueryBuilder
from .exceptions import (
    QueryingError,
    QueryExecutionError,
    SymbolResolutionError,
    ConnectionError,
    ValidationError
)

__all__ = [
    'QueryBuilder',
    'QueryingError',
    'QueryExecutionError',
    'SymbolResolutionError',
    'ConnectionError',
    'ValidationError'
]
