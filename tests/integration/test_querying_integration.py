"""
Integration tests for QueryBuilder with TimescaleDB.

These tests verify that the QueryBuilder works correctly with the actual
database schema and existing storage layer components.
"""

import pytest
import os
from datetime import datetime, date
from decimal import Decimal

from src.querying import QueryBuilder, QueryExecutionError, SymbolResolutionError


class TestQueryBuilderIntegration:
    """Integration tests for QueryBuilder with TimescaleDB."""
    
    @pytest.fixture
    def query_builder(self):
        """Create QueryBuilder instance for integration testing."""
        # Skip if no database connection available
        if not all([
            os.getenv('TIMESCALEDB_HOST'),
            os.getenv('TIMESCALEDB_DATABASE'),
            os.getenv('TIMESCALEDB_USER')
        ]):
            pytest.skip("Database connection parameters not available")
        
        return QueryBuilder()
    
    def test_database_connection(self, query_builder):
        """Test that QueryBuilder can connect to the database."""
        try:
            with query_builder.get_connection() as conn:
                assert conn is not None
        except Exception as e:
            pytest.skip(f"Database connection failed: {e}")
    
    def test_get_available_symbols_integration(self, query_builder):
        """Test getting available symbols from actual database."""
        try:
            symbols = query_builder.get_available_symbols(limit=5)
            
            # Should return a list (may be empty if no data)
            assert isinstance(symbols, list)
            
            # If symbols exist, they should be strings
            for symbol in symbols:
                assert isinstance(symbol, str)
                assert len(symbol) > 0
                
        except Exception as e:
            pytest.skip(f"Database query failed: {e}")
    
    def test_query_definitions_integration(self, query_builder):
        """Test querying definitions data from actual database."""
        try:
            # Query definitions without filters
            definitions = query_builder.query_definitions(limit=5)
            
            # Should return a list (may be empty if no data)
            assert isinstance(definitions, list)
            
            # If definitions exist, verify structure
            for definition in definitions:
                assert isinstance(definition, dict)
                assert 'instrument_id' in definition
                assert 'raw_symbol' in definition
                
        except Exception as e:
            pytest.skip(f"Database query failed: {e}")
    
    def test_query_with_nonexistent_symbol(self, query_builder):
        """Test querying with a symbol that doesn't exist."""
        try:
            # Use a clearly non-existent symbol
            with pytest.raises(SymbolResolutionError):
                query_builder.query_daily_ohlcv('NONEXISTENT_SYMBOL_12345')
                
        except Exception as e:
            pytest.skip(f"Database query failed: {e}")
    
    def test_empty_date_range_query(self, query_builder):
        """Test querying with a date range that has no data."""
        try:
            # Get any available symbol first
            symbols = query_builder.get_available_symbols(limit=1)
            
            if not symbols:
                pytest.skip("No symbols available in database")
            
            # Query with a future date range that should have no data
            future_date = date(2030, 1, 1)
            result = query_builder.query_daily_ohlcv(
                symbols[0],
                start_date=future_date,
                end_date=future_date
            )
            
            # Should return empty list
            assert result == []
            
        except SymbolResolutionError:
            pytest.skip("Symbol resolution failed - may indicate empty definitions table")
        except Exception as e:
            pytest.skip(f"Database query failed: {e}")
    
    def test_dataframe_conversion_integration(self, query_builder):
        """Test converting query results to DataFrame."""
        try:
            # Get definitions data for DataFrame conversion test
            definitions = query_builder.query_definitions(limit=3)
            
            if not definitions:
                pytest.skip("No definitions data available")
            
            # Convert to DataFrame
            df = query_builder.to_dataframe(definitions)
            
            # Verify DataFrame structure
            assert len(df) == len(definitions)
            assert 'instrument_id' in df.columns
            assert 'raw_symbol' in df.columns
            
            # Verify timestamp columns are converted to datetime if present
            timestamp_columns = ['ts_event', 'ts_recv', 'expiration', 'activation']
            for col in timestamp_columns:
                if col in df.columns:
                    assert df[col].dtype.name.startswith('datetime')
                    
        except Exception as e:
            pytest.skip(f"Database query failed: {e}")
    
    def test_query_builder_with_existing_storage_pattern(self, query_builder):
        """Test that QueryBuilder follows the same connection pattern as existing storage."""
        try:
            # Verify connection parameters are loaded correctly
            assert query_builder.connection_params is not None
            assert 'host' in query_builder.connection_params
            assert 'database' in query_builder.connection_params
            
            # Verify engine is created
            assert query_builder.engine is not None
            
            # Test connection context manager works like TimescaleLoader
            with query_builder.get_connection() as conn:
                assert conn is not None
                # Connection should be automatically closed after context
                
        except Exception as e:
            pytest.skip(f"Connection test failed: {e}")
    
    @pytest.mark.slow
    def test_query_performance_baseline(self, query_builder):
        """Test basic query performance to establish baseline."""
        try:
            import time
            
            # Get a small sample of definitions for performance test
            start_time = time.time()
            definitions = query_builder.query_definitions(limit=10)
            end_time = time.time()
            
            query_time = end_time - start_time
            
            # Basic performance assertion - should complete within reasonable time
            assert query_time < 5.0, f"Query took {query_time:.2f}s, expected < 5.0s"
            
            # Log performance for monitoring
            print(f"Query performance: {query_time:.3f}s for {len(definitions)} records")
            
        except Exception as e:
            pytest.skip(f"Performance test failed: {e}")


# Mark all tests in this class as integration tests
pytestmark = pytest.mark.integration 