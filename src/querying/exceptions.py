"""
Custom exceptions for the querying module.

This module defines specific exceptions for query-related errors to provide
better error handling and debugging capabilities.
"""


class QueryingError(Exception):
    """Base exception for all querying-related errors."""
    pass


class QueryExecutionError(QueryingError):
    """Raised when a database query fails to execute."""
    pass


class SymbolResolutionError(QueryingError):
    """Raised when symbols cannot be resolved to instrument_ids."""
    pass


class ConnectionError(QueryingError):
    """Raised when database connection fails."""
    pass


class ValidationError(QueryingError):
    """Raised when query parameters fail validation."""
    pass
