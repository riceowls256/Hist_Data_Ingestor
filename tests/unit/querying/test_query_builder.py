"""
Unit tests for QueryBuilder class.

Tests query construction, symbol resolution, error handling, and data formatting
using mocked database connections.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from decimal import Decimal

from src.querying.query_builder import QueryBuilder
from src.querying.exceptions import QueryExecutionError, SymbolResolutionError


class TestQueryBuilder:
    """Test cases for QueryBuilder class."""
    
    @pytest.fixture
    def mock_connection_params(self):
        """Mock connection parameters for testing."""
        return {
            'host': 'test_host',
            'port': 5432,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass'
        }
    
    @pytest.fixture
    def query_builder(self, mock_connection_params):
        """Create QueryBuilder instance with mocked connection."""
        with patch('src.querying.query_builder.create_engine'):
            return QueryBuilder(mock_connection_params)
    
    @pytest.fixture
    def mock_connection(self):
        """Mock database connection."""
        connection = Mock()
        connection.execute.return_value = Mock()
        connection.close.return_value = None
        return connection
    
    @pytest.fixture
    def mock_symbol_resolution_result(self):
        """Mock result for symbol resolution query."""
        mock_row = Mock()
        mock_row.instrument_id = 12345
        mock_row.raw_symbol = 'ES.c.0'
        
        mock_result = Mock()
        mock_result.fetchall.return_value = [mock_row]
        return mock_result
    
    @pytest.fixture
    def mock_ohlcv_query_result(self):
        """Mock result for OHLCV query."""
        mock_row = Mock()
        mock_row._mapping = {
            'ts_event': datetime(2024, 1, 15, 0, 0, 0),
            'instrument_id': 12345,
            'open_price': Decimal('4500.00'),
            'high_price': Decimal('4520.00'),
            'low_price': Decimal('4490.00'),
            'close_price': Decimal('4510.00'),
            'volume': 1000000,
            'granularity': '1d',
            'data_source': 'databento'
        }
        
        mock_result = Mock()
        mock_result.fetchall.return_value = [mock_row]
        return mock_result
    
    def test_init_with_custom_params(self, mock_connection_params):
        """Test QueryBuilder initialization with custom connection parameters."""
        with patch('src.querying.query_builder.create_engine') as mock_create_engine:
            qb = QueryBuilder(mock_connection_params)
            
            assert qb.connection_params == mock_connection_params
            mock_create_engine.assert_called_once()
    
    def test_init_with_env_params(self):
        """Test QueryBuilder initialization with environment variables."""
        with patch('src.querying.query_builder.create_engine') as mock_create_engine, \
             patch.dict('os.environ', {
                 'TIMESCALEDB_HOST': 'env_host',
                 'TIMESCALEDB_PORT': '5433',
                 'TIMESCALEDB_DBNAME': 'env_db',
                 'TIMESCALEDB_USER': 'env_user',
                 'TIMESCALEDB_PASSWORD': 'env_pass'
             }):
            
            qb = QueryBuilder()
            
            expected_params = {
                'host': 'env_host',
                'port': 5433,
                'database': 'env_db',
                'user': 'env_user',
                'password': 'env_pass'
            }
            assert qb.connection_params == expected_params
            mock_create_engine.assert_called_once()
    
    def test_resolve_symbols_single_symbol(self, query_builder, mock_connection, mock_symbol_resolution_result):
        """Test symbol resolution with single symbol."""
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            
            # Mock table existence check (definitions table exists)
            mock_table_check = Mock()
            mock_table_check.fetchone.return_value = [True]  # Return list with boolean
            
            mock_connection.execute.side_effect = [
                mock_table_check,               # Table existence check
                mock_symbol_resolution_result   # Symbol resolution query
            ]
            
            result = query_builder._resolve_symbols_to_instrument_ids('ES.c.0')
            
            assert result == [12345]
            assert mock_connection.execute.call_count == 2
    
    def test_resolve_symbols_multiple_symbols(self, query_builder, mock_connection):
        """Test symbol resolution with multiple symbols."""
        # Mock multiple symbol results
        mock_row1 = Mock()
        mock_row1.instrument_id = 12345
        mock_row1.raw_symbol = 'ES.c.0'
        
        mock_row2 = Mock()
        mock_row2.instrument_id = 67890
        mock_row2.raw_symbol = 'CL.c.0'
        
        mock_result = Mock()
        mock_result.fetchall.return_value = [mock_row1, mock_row2]
        
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            
            # Mock table existence check (definitions table exists)
            mock_table_check = Mock()
            mock_table_check.fetchone.return_value = [True]  # Return list with boolean
            
            mock_connection.execute.side_effect = [
                mock_table_check,  # Table existence check
                mock_result        # Symbol resolution query
            ]
            
            result = query_builder._resolve_symbols_to_instrument_ids(['ES.c.0', 'CL.c.0'])
            
            assert result == [12345, 67890]
    
    def test_resolve_symbols_not_found(self, query_builder, mock_connection):
        """Test symbol resolution when symbols are not found."""
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            
            # Mock table existence check (definitions table exists)
            mock_table_check = Mock()
            mock_table_check.fetchone.return_value = [True]  # Return list with boolean
            
            mock_connection.execute.side_effect = [
                mock_table_check,  # Table existence check
                mock_result        # Empty symbol resolution query
            ]
            
            with pytest.raises(SymbolResolutionError):
                query_builder._resolve_symbols_to_instrument_ids('INVALID_SYMBOL')
    
    def test_resolve_symbols_partial_match(self, query_builder, mock_connection):
        """Test symbol resolution with partial matches (some symbols not found)."""
        # Only one symbol found out of two requested
        mock_row = Mock()
        mock_row.instrument_id = 12345
        mock_row.raw_symbol = 'ES.c.0'
        
        mock_result = Mock()
        mock_result.fetchall.return_value = [mock_row]
        
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            
            # Mock table existence check (definitions table exists)
            mock_table_check = Mock()
            mock_table_check.fetchone.return_value = [True]  # Return list with boolean
            
            mock_connection.execute.side_effect = [
                mock_table_check,  # Table existence check
                mock_result        # Partial symbol resolution query
            ]
            
            # Should return found symbols and log warning for missing ones
            result = query_builder._resolve_symbols_to_instrument_ids(['ES.c.0', 'INVALID'])
            
            assert result == [12345]
    
    def test_resolve_symbols_fallback_to_direct_query(self, query_builder, mock_connection):
        """Test symbol resolution fallback when definitions table doesn't exist."""
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            
            # Mock table existence check (definitions table does NOT exist)
            mock_table_check = Mock()
            mock_table_check.fetchone.return_value = [False]  # Return list with boolean
            
            mock_connection.execute.side_effect = [mock_table_check]
            
            # Should raise SymbolResolutionError to trigger fallback in calling method
            with pytest.raises(SymbolResolutionError, match="definitions_data table does not exist"):
                query_builder._resolve_symbols_to_instrument_ids('ES.c.0')
    
    def test_query_daily_ohlcv_success_with_definitions(self, query_builder, mock_connection, 
                                      mock_symbol_resolution_result, mock_ohlcv_query_result):
        """Test successful daily OHLCV query when definitions table exists."""
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            
            # Mock table existence check (definitions table exists)
            mock_table_check = Mock()
            mock_table_check.fetchone.return_value = [True]  # Return list with boolean
            
            # Mock symbol resolution and data query
            mock_connection.execute.side_effect = [
                mock_table_check,               # Table existence check
                mock_symbol_resolution_result,  # Symbol resolution
                mock_ohlcv_query_result,        # OHLCV data query
                mock_symbol_resolution_result   # Symbol name lookup
            ]
            
            result = query_builder.query_daily_ohlcv(
                'ES.c.0',
                start_date=date(2024, 1, 15),
                end_date=date(2024, 1, 16)
            )
            
            assert len(result) == 1
            assert result[0]['instrument_id'] == 12345
            assert result[0]['open_price'] == Decimal('4500.00')
            assert result[0]['symbol'] == 'ES.c.0'
    
    def test_query_daily_ohlcv_success_with_fallback(self, query_builder, mock_connection):
        """Test successful daily OHLCV query using direct symbol fallback."""
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            
            # Mock table existence check (definitions table does NOT exist)
            mock_table_check = Mock()
            mock_table_check.fetchone.return_value = [False]  # Return list with boolean
            
            # Mock direct OHLCV query result (includes symbol field for fallback)
            mock_fallback_row = Mock()
            mock_fallback_row._mapping = {
                'ts_event': datetime(2024, 1, 15, 0, 0, 0),
                'instrument_id': 12345,
                'symbol': 'ES.c.0',  # Include symbol field for fallback
                'open_price': Decimal('4500.00'),
                'high_price': Decimal('4520.00'),
                'low_price': Decimal('4490.00'),
                'close_price': Decimal('4510.00'),
                'volume': 1000000,
                'granularity': '1d',
                'data_source': 'databento'
            }
            
            mock_fallback_result = Mock()
            mock_fallback_result.fetchall.return_value = [mock_fallback_row]
            
            # Mock direct OHLCV query (fallback)
            mock_connection.execute.side_effect = [
                mock_table_check,     # Table existence check (fails)
                mock_fallback_result  # Direct OHLCV query by symbol
            ]
            
            result = query_builder.query_daily_ohlcv(
                'ES.c.0',
                start_date=date(2024, 1, 15),
                end_date=date(2024, 1, 16)
            )
            
            assert len(result) == 1
            assert result[0]['instrument_id'] == 12345
            assert result[0]['open_price'] == Decimal('4500.00')
            assert result[0]['symbol'] == 'ES.c.0'
    
    def test_query_daily_ohlcv_empty_result(self, query_builder, mock_connection, mock_symbol_resolution_result):
        """Test daily OHLCV query with no data found."""
        mock_empty_result = Mock()
        mock_empty_result.fetchall.return_value = []
        
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            
            # Mock table existence check (definitions table exists)
            mock_table_check = Mock()
            mock_table_check.fetchone.return_value = [True]  # Return list with boolean
            
            mock_connection.execute.side_effect = [
                mock_table_check,               # Table existence check
                mock_symbol_resolution_result,  # Symbol resolution
                mock_empty_result               # Empty OHLCV data query
            ]
            
            result = query_builder.query_daily_ohlcv('ES.c.0')
            
            assert result == []
    
    def test_query_trades_with_side_filter(self, query_builder, mock_connection, mock_symbol_resolution_result):
        """Test trades query with side filter."""
        mock_trade_row = Mock()
        mock_trade_row._mapping = {
            'ts_event': datetime(2024, 1, 15, 10, 30, 0),
            'instrument_id': 12345,
            'price': Decimal('4505.25'),
            'size': 10,
            'side': 'B',
            'action': 'T'
        }
        
        mock_trades_result = Mock()
        mock_trades_result.fetchall.return_value = [mock_trade_row]
        
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            
            # Mock table existence check (definitions table exists)
            mock_table_check = Mock()
            mock_table_check.fetchone.return_value = [True]  # Return list with boolean
            
            mock_connection.execute.side_effect = [
                mock_table_check,               # Table existence check
                mock_symbol_resolution_result,  # Symbol resolution
                mock_trades_result,             # Trades data query
                mock_symbol_resolution_result   # Symbol name lookup
            ]
            
            result = query_builder.query_trades('ES.c.0', side='B')
            
            assert len(result) == 1
            assert result[0]['side'] == 'B'
            assert result[0]['price'] == Decimal('4505.25')
    
    def test_query_statistics_with_stat_type(self, query_builder, mock_connection, mock_symbol_resolution_result):
        """Test statistics query with stat_type filter."""
        mock_stat_row = Mock()
        mock_stat_row._mapping = {
            'ts_event': datetime(2024, 1, 15, 0, 0, 0),
            'instrument_id': 12345,
            'stat_type': 1,
            'price': Decimal('4500.00'),
            'quantity': 1000
        }
        
        mock_stats_result = Mock()
        mock_stats_result.fetchall.return_value = [mock_stat_row]
        
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            
            # Mock table existence check (definitions table exists)
            mock_table_check = Mock()
            mock_table_check.fetchone.return_value = [True]  # Return list with boolean
            
            mock_connection.execute.side_effect = [
                mock_table_check,               # Table existence check
                mock_symbol_resolution_result,  # Symbol resolution
                mock_stats_result,              # Statistics data query
                mock_symbol_resolution_result   # Symbol name lookup
            ]
            
            result = query_builder.query_statistics('ES.c.0', stat_type=1)
            
            assert len(result) == 1
            assert result[0]['stat_type'] == 1
    
    def test_query_definitions_by_asset(self, query_builder, mock_connection):
        """Test definitions query filtered by asset."""
        mock_def_row = Mock()
        mock_def_row._mapping = {
            'instrument_id': 12345,
            'raw_symbol': 'ES.c.0',
            'asset': 'ES',
            'exchange': 'GLBX',
            'instrument_class': 'FUT'
        }
        
        mock_defs_result = Mock()
        mock_defs_result.fetchall.return_value = [mock_def_row]
        
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            mock_connection.execute.return_value = mock_defs_result
            
            result = query_builder.query_definitions(asset='ES')
            
            assert len(result) == 1
            assert result[0]['asset'] == 'ES'
    
    def test_to_dataframe_conversion(self, query_builder):
        """Test conversion of query results to DataFrame."""
        results = [
            {
                'ts_event': datetime(2024, 1, 15, 0, 0, 0),
                'instrument_id': 12345,
                'open_price': Decimal('4500.00'),
                'close_price': Decimal('4510.00'),
                'volume': 1000000
            },
            {
                'ts_event': datetime(2024, 1, 16, 0, 0, 0),
                'instrument_id': 12345,
                'open_price': Decimal('4510.00'),
                'close_price': Decimal('4520.00'),
                'volume': 1200000
            }
        ]
        
        df = query_builder.to_dataframe(results)
        
        assert len(df) == 2
        assert 'ts_event' in df.columns
        assert 'instrument_id' in df.columns
        # Check that timestamp columns are converted to datetime
        assert df['ts_event'].dtype.name.startswith('datetime')
    
    def test_to_dataframe_empty_results(self, query_builder):
        """Test DataFrame conversion with empty results."""
        df = query_builder.to_dataframe([])
        
        assert len(df) == 0
        assert df.empty
    
    def test_get_available_symbols(self, query_builder, mock_connection):
        """Test getting available symbols from database."""
        mock_symbol_rows = [
            Mock(raw_symbol='ES.c.0'),
            Mock(raw_symbol='CL.c.0'),
            Mock(raw_symbol='GC.c.0')
        ]
        
        mock_symbols_result = Mock()
        mock_symbols_result.fetchall.return_value = mock_symbol_rows
        
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            mock_connection.execute.return_value = mock_symbols_result
            
            result = query_builder.get_available_symbols()
            
            assert result == ['ES.c.0', 'CL.c.0', 'GC.c.0']
    
    def test_connection_error_handling(self, query_builder):
        """Test handling of database connection errors."""
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.side_effect = Exception("Connection failed")
            
            with pytest.raises(QueryExecutionError):
                query_builder.query_daily_ohlcv('ES.c.0')
    
    def test_query_execution_error_handling(self, query_builder, mock_connection):
        """Test handling of query execution errors."""
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            mock_connection.execute.side_effect = Exception("Query failed")
            
            with pytest.raises(Exception):  # The specific exception type depends on the error
                query_builder._resolve_symbols_to_instrument_ids('ES.c.0')
    
    def test_build_base_query_with_all_filters(self, query_builder):
        """Test base query construction with all filter types."""
        from src.querying.table_definitions import daily_ohlcv_data
        
        query = query_builder._build_base_query(
            daily_ohlcv_data,
            instrument_ids=[12345, 67890],
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 16),
            additional_filters=[daily_ohlcv_data.c.granularity == '1d'],
            limit=100
        )
        
        # Verify query object is created (detailed SQL testing would require more complex setup)
        assert query is not None
    
    def test_add_symbol_names_to_results(self, query_builder, mock_connection):
        """Test adding symbol names to query results."""
        results = [
            {'instrument_id': 12345, 'price': Decimal('4500.00')},
            {'instrument_id': 67890, 'price': Decimal('75.50')}
        ]
        
        mock_symbol_rows = [
            Mock(instrument_id=12345, raw_symbol='ES.c.0'),
            Mock(instrument_id=67890, raw_symbol='CL.c.0')
        ]
        
        mock_symbols_result = Mock()
        mock_symbols_result.fetchall.return_value = mock_symbol_rows
        
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            mock_connection.execute.return_value = mock_symbols_result
            
            enriched_results = query_builder._add_symbol_names_to_results(results)
            
            assert enriched_results[0]['symbol'] == 'ES.c.0'
            assert enriched_results[1]['symbol'] == 'CL.c.0'
    
    def test_date_range_filtering(self, query_builder, mock_connection, mock_symbol_resolution_result):
        """Test date range filtering in queries."""
        mock_filtered_result = Mock()
        mock_filtered_result.fetchall.return_value = []
        
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            
            # Mock table existence check (definitions table exists)
            mock_table_check = Mock()
            mock_table_check.fetchone.return_value = [True]  # Return list with boolean
            
            mock_connection.execute.side_effect = [
                mock_table_check,               # Table existence check
                mock_symbol_resolution_result,  # Symbol resolution
                mock_filtered_result            # Filtered query result
            ]
            
            result = query_builder.query_daily_ohlcv(
                'ES.c.0',
                start_date=datetime(2024, 1, 15, 0, 0, 0),
                end_date=datetime(2024, 1, 16, 23, 59, 59)
            )
            
            # Verify the query was executed (result handling tested separately)
            assert mock_connection.execute.call_count == 3
    
    def test_multiple_symbols_query(self, query_builder, mock_connection):
        """Test querying with multiple symbols."""
        # Mock multiple symbol resolution
        mock_symbols = [
            Mock(instrument_id=12345, raw_symbol='ES.c.0'),
            Mock(instrument_id=67890, raw_symbol='CL.c.0')
        ]
        
        mock_symbol_result = Mock()
        mock_symbol_result.fetchall.return_value = mock_symbols
        
        mock_data_result = Mock()
        mock_data_result.fetchall.return_value = []
        
        with patch.object(query_builder, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection
            
            # Mock table existence check (definitions table exists)
            mock_table_check = Mock()
            mock_table_check.fetchone.return_value = [True]  # Return list with boolean
            
            mock_connection.execute.side_effect = [
                mock_table_check,    # Table existence check
                mock_symbol_result,  # Symbol resolution
                mock_data_result     # Data query
            ]
            
            result = query_builder.query_daily_ohlcv(['ES.c.0', 'CL.c.0'])
            
            # Verify multiple symbols were processed
            assert mock_connection.execute.call_count == 3 