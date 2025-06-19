"""
Unit tests for CLI querying commands module.

Tests all querying-related commands including the main query command
with comprehensive parameter validation and output formatting.
"""

from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from datetime import datetime, date
from decimal import Decimal

import pytest
from typer.testing import CliRunner
from rich.console import Console

from src.cli.commands.querying import (
    app as querying_app, 
    validate_date_format, 
    parse_query_symbols, 
    parse_date_string,
    validate_query_scope,
    format_table_output,
    format_csv_output,
    format_json_output,
    write_output_file
)


class TestQueryingCommands:
    """Comprehensive test suite for querying commands."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.runner = CliRunner()
        self.console = Console(file=StringIO(), force_terminal=True)
    
    # Test utility functions
    def test_validate_date_format_valid(self):
        """Test date format validation with valid dates."""
        assert validate_date_format("2024-01-01") is True
        assert validate_date_format("2023-12-31") is True
    
    def test_validate_date_format_invalid(self):
        """Test date format validation with invalid dates."""
        assert validate_date_format("2024-1-1") is False
        assert validate_date_format("01-01-2024") is False
        assert validate_date_format("invalid") is False
    
    def test_parse_query_symbols_comma_separated(self):
        """Test symbol parsing with comma-separated input."""
        result = parse_query_symbols(["ES.c.0,NQ.c.0,CL.c.0"])
        assert result == ["ES.c.0", "NQ.c.0", "CL.c.0"]
    
    def test_parse_query_symbols_multiple_flags(self):
        """Test symbol parsing with multiple flag inputs."""
        result = parse_query_symbols(["ES.c.0", "NQ.c.0", "CL.c.0"])
        assert result == ["ES.c.0", "NQ.c.0", "CL.c.0"]
    
    def test_parse_query_symbols_mixed_input(self):
        """Test symbol parsing with mixed comma-separated and flag inputs."""
        result = parse_query_symbols(["ES.c.0,NQ.c.0", "CL.c.0"])
        assert result == ["ES.c.0", "NQ.c.0", "CL.c.0"]
    
    def test_parse_query_symbols_empty_input(self):
        """Test symbol parsing with empty input."""
        result = parse_query_symbols([])
        assert result == []
        
        result = parse_query_symbols(["", "  "])
        assert result == []
    
    def test_parse_date_string(self):
        """Test date string parsing to date object."""
        result = parse_date_string("2024-01-01")
        assert result == date(2024, 1, 1)
    
    @patch('src.cli.commands.querying.typer.confirm')
    def test_validate_query_scope_trades_warning(self, mock_confirm):
        """Test query scope validation for trades data over multiple days."""
        mock_confirm.return_value = True
        
        symbols = ["ES.c.0"]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 3)  # Multiple days
        schema = "trades"
        
        result = validate_query_scope(symbols, start_date, end_date, schema)
        assert result is True
        mock_confirm.assert_called_once()
    
    @patch('src.cli.commands.querying.typer.confirm')
    def test_validate_query_scope_many_symbols_warning(self, mock_confirm):
        """Test query scope validation for many symbols."""
        mock_confirm.return_value = True
        
        symbols = [f"SYMBOL_{i}" for i in range(15)]  # More than 10 symbols
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 2)
        schema = "ohlcv-1d"
        
        result = validate_query_scope(symbols, start_date, end_date, schema)
        assert result is True
        mock_confirm.assert_called_once()
    
    def test_validate_query_scope_normal_query(self):
        """Test query scope validation for normal query (no warnings)."""
        symbols = ["ES.c.0", "NQ.c.0"]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 2)
        schema = "ohlcv-1d"
        
        result = validate_query_scope(symbols, start_date, end_date, schema)
        assert result is True
    
    def test_format_table_output_empty_results(self):
        """Test table formatting with empty results."""
        table = format_table_output([], "ohlcv-1d")
        # Should return a table with "No data found" message
        assert table.title == "Query Results"
    
    def test_format_table_output_with_data(self):
        """Test table formatting with sample data."""
        results = [
            {
                "symbol": "ES.c.0",
                "date": "2024-01-01", 
                "open_price": Decimal("4800.50"),
                "close_price": Decimal("4825.75"),
                "volume": 100000
            },
            {
                "symbol": "ES.c.0",
                "date": "2024-01-02",
                "open_price": Decimal("4825.75"),
                "close_price": Decimal("4850.25"),
                "volume": 120000
            }
        ]
        
        table = format_table_output(results, "ohlcv-1d")
        assert "OHLCV-1D" in table.title
    
    def test_format_csv_output_empty_results(self):
        """Test CSV formatting with empty results."""
        result = format_csv_output([])
        assert "No data found" in result
    
    def test_format_csv_output_with_data(self):
        """Test CSV formatting with sample data."""
        results = [
            {
                "symbol": "ES.c.0",
                "date": "2024-01-01",
                "price": Decimal("4800.50")
            }
        ]
        
        csv_output = format_csv_output(results)
        assert "symbol,date,price" in csv_output
        assert "ES.c.0,2024-01-01,4800.50" in csv_output
    
    def test_format_json_output_empty_results(self):
        """Test JSON formatting with empty results."""
        result = format_json_output([])
        assert "No data found" in result
        assert '"results": []' in result
    
    def test_format_json_output_with_data(self):
        """Test JSON formatting with sample data."""
        results = [
            {
                "symbol": "ES.c.0",
                "date": date(2024, 1, 1),
                "price": Decimal("4800.50")
            }
        ]
        
        json_output = format_json_output(results)
        assert '"count": 1' in json_output
        assert '"symbol": "ES.c.0"' in json_output
        assert '"price": 4800.5' in json_output  # Decimal converted to float
        assert '"date": "2024-01-01"' in json_output  # Date converted to ISO format
    
    @patch('src.cli.commands.querying.Path')
    @patch('builtins.open')
    def test_write_output_file_success(self, mock_open, mock_path):
        """Test successful file writing."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent.mkdir = Mock()
        mock_path_instance.stat.return_value.st_size = 1024
        
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Should not raise exception
        write_output_file("test content", "/tmp/test.csv", "csv")
        
        mock_open.assert_called_once()
        mock_file.write.assert_called_once_with("test content")


class TestQueryCommand:
    """Test suite for the query command."""
    
    def setup_method(self):
        """Set up test fixtures for query command tests."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.querying.QueryBuilder')
    def test_query_command_basic_execution(self, mock_query_builder):
        """Test basic query command execution."""
        # Mock QueryBuilder and query method
        mock_qb = Mock()
        mock_query_builder.return_value = mock_qb
        
        mock_query_method = Mock()
        mock_query_method.return_value = [
            {
                "symbol": "ES.c.0",
                "date": "2024-01-01",
                "open_price": Decimal("4800.50"),
                "close_price": Decimal("4825.75")
            }
        ]
        mock_qb.query_daily_ohlcv = mock_query_method
        
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02"
        ])
        
        assert result.exit_code == 0
        assert "Query completed successfully" in result.stdout
        mock_query_method.assert_called_once()
    
    @patch('src.cli.commands.querying.QueryBuilder')
    def test_query_command_multiple_symbols(self, mock_query_builder):
        """Test query command with multiple symbols."""
        # Mock QueryBuilder
        mock_qb = Mock()
        mock_query_builder.return_value = mock_qb
        
        mock_query_method = Mock()
        mock_query_method.return_value = []  # Empty results
        mock_qb.query_daily_ohlcv = mock_query_method
        
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "ES.c.0,NQ.c.0,CL.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02"
        ])
        
        assert result.exit_code == 0
        # Verify symbols were parsed correctly
        call_args = mock_query_method.call_args[1]
        assert call_args["symbols"] == ["ES.c.0", "NQ.c.0", "CL.c.0"]
    
    @patch('src.cli.commands.querying.QueryBuilder')
    def test_query_command_with_limit(self, mock_query_builder):
        """Test query command with result limit."""
        # Mock QueryBuilder
        mock_qb = Mock()
        mock_query_builder.return_value = mock_qb
        
        mock_query_method = Mock()
        mock_query_method.return_value = []
        mock_qb.query_trades = mock_query_method
        
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02",
            "--schema", "trades",
            "--limit", "1000"
        ])
        
        assert result.exit_code == 0
        # Verify limit was passed
        call_args = mock_query_method.call_args[1]
        assert call_args["limit"] == 1000
    
    def test_query_command_missing_required_params(self):
        """Test query command with missing required parameters."""
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "ES.c.0"
            # Missing start-date and end-date
        ])
        
        assert result.exit_code != 0
        assert "Missing option" in result.stdout
    
    def test_query_command_invalid_dates(self):
        """Test query command with invalid date formats."""
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "invalid-date",
            "--end-date", "2024-01-02"
        ])
        
        assert result.exit_code == 1
        assert "Invalid start_date format" in result.stdout
    
    def test_query_command_invalid_schema(self):
        """Test query command with invalid schema."""
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02",
            "--schema", "invalid_schema"
        ])
        
        assert result.exit_code == 1
        assert "Invalid schema: invalid_schema" in result.stdout
    
    def test_query_command_invalid_output_format(self):
        """Test query command with invalid output format."""
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02",
            "--output-format", "invalid_format"
        ])
        
        assert result.exit_code == 1
        assert "Invalid output format: invalid_format" in result.stdout
    
    def test_query_command_invalid_limit(self):
        """Test query command with invalid limit."""
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02",
            "--limit", "-1"
        ])
        
        assert result.exit_code == 1
        assert "Limit must be a positive integer" in result.stdout
    
    def test_query_command_dry_run(self):
        """Test query command in dry run mode."""
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01", 
            "--end-date", "2024-01-02",
            "--dry-run"
        ])
        
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.stdout
        assert "Query Preview" in result.stdout
    
    def test_query_command_validate_only(self):
        """Test query command in validate-only mode."""
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02",
            "--validate-only"
        ])
        
        assert result.exit_code == 0
        assert "Validation passed" in result.stdout
        assert "parameters are valid" in result.stdout
    
    @patch('src.cli.commands.querying.GuidedMode')
    @patch('src.cli.commands.querying.QueryBuilder')
    def test_query_command_guided_mode(self, mock_query_builder, mock_guided_mode):
        """Test query command in guided mode."""
        # Mock guided mode
        mock_guided_mode.guided_query.return_value = {
            "symbols": ["ES.c.0"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
            "schema": "ohlcv-1d",
            "output_format": "table"
        }
        
        # Mock QueryBuilder
        mock_qb = Mock()
        mock_query_builder.return_value = mock_qb
        mock_query_method = Mock()
        mock_query_method.return_value = []
        mock_qb.query_daily_ohlcv = mock_query_method
        
        result = self.runner.invoke(querying_app, [
            "query",
            "--guided"
        ])
        
        assert result.exit_code == 0
        mock_guided_mode.guided_query.assert_called_once()
        mock_query_method.assert_called_once()
    
    @patch('src.cli.commands.querying.QueryBuilder')
    def test_query_command_csv_output(self, mock_query_builder):
        """Test query command with CSV output format."""
        # Mock QueryBuilder
        mock_qb = Mock()
        mock_query_builder.return_value = mock_qb
        
        mock_query_method = Mock()
        mock_query_method.return_value = [
            {"symbol": "ES.c.0", "date": "2024-01-01", "price": Decimal("4800.50")}
        ]
        mock_qb.query_daily_ohlcv = mock_query_method
        
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02",
            "--output-format", "csv"
        ])
        
        assert result.exit_code == 0
        assert "symbol,date,price" in result.stdout
        assert "ES.c.0,2024-01-01,4800.50" in result.stdout
    
    @patch('src.cli.commands.querying.QueryBuilder')
    def test_query_command_json_output(self, mock_query_builder):
        """Test query command with JSON output format."""
        # Mock QueryBuilder
        mock_qb = Mock()
        mock_query_builder.return_value = mock_qb
        
        mock_query_method = Mock()
        mock_query_method.return_value = [
            {"symbol": "ES.c.0", "date": date(2024, 1, 1), "price": Decimal("4800.50")}
        ]
        mock_qb.query_daily_ohlcv = mock_query_method
        
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02",
            "--output-format", "json"
        ])
        
        assert result.exit_code == 0
        assert '"count": 1' in result.stdout
        assert '"symbol": "ES.c.0"' in result.stdout


class TestQueryCommandErrorHandling:
    """Test error handling for query commands."""
    
    def setup_method(self):
        """Set up error handling test fixtures."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.querying.QueryBuilder')
    def test_query_command_query_error(self, mock_query_builder):
        """Test query command handling QueryingError."""
        from querying.exceptions import QueryingError
        
        # Mock QueryBuilder to raise QueryingError
        mock_qb = Mock()
        mock_query_builder.return_value = mock_qb
        mock_qb.query_daily_ohlcv.side_effect = QueryingError("Database connection failed")
        
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02"
        ])
        
        assert result.exit_code == 1
        assert "Query error" in result.stdout
        assert "Database connection failed" in result.stdout
    
    @patch('src.cli.commands.querying.QueryBuilder')
    def test_query_command_symbol_resolution_error(self, mock_query_builder):
        """Test query command handling SymbolResolutionError."""
        from querying.exceptions import SymbolResolutionError
        
        # Mock QueryBuilder to raise SymbolResolutionError
        mock_qb = Mock()
        mock_query_builder.return_value = mock_qb
        mock_qb.query_daily_ohlcv.side_effect = SymbolResolutionError("Symbol not found")
        
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "INVALID.SYMBOL",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02"
        ])
        
        assert result.exit_code == 1
        assert "Symbol resolution error" in result.stdout
        assert "Symbol not found" in result.stdout


class TestQueryCommandPerformance:
    """Performance tests for query commands."""
    
    def setup_method(self):
        """Set up performance test fixtures."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.querying.QueryBuilder')
    def test_query_command_performance(self, mock_query_builder):
        """Test query command executes within performance threshold."""
        # Mock QueryBuilder
        mock_qb = Mock()
        mock_query_builder.return_value = mock_qb
        
        mock_query_method = Mock()
        mock_query_method.return_value = []
        mock_qb.query_daily_ohlcv = mock_query_method
        
        import time
        start_time = time.time()
        
        result = self.runner.invoke(querying_app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02",
            "--dry-run"  # Use dry run to test setup performance only
        ])
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert result.exit_code == 0
        assert execution_time < 2.0  # Should execute validation in less than 2 seconds
    
    def test_parse_query_symbols_performance(self):
        """Test symbol parsing performance with large symbol lists."""
        import time
        
        # Create large symbol list
        large_symbol_list = [f"SYMBOL_{i}.c.0" for i in range(1000)]
        comma_separated = ",".join(large_symbol_list)
        
        start_time = time.time()
        result = parse_query_symbols([comma_separated])
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert len(result) == 1000
        assert execution_time < 1.0  # Should parse 1000 symbols in less than 1 second


class TestQueryCommandIntegration:
    """Integration tests for query commands."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.runner = CliRunner()
    
    @pytest.mark.integration
    @patch('src.cli.commands.querying.QueryBuilder')
    def test_query_command_all_schemas(self, mock_query_builder):
        """Test query command with all supported schemas."""
        from src.cli.common.constants import SUPPORTED_SCHEMAS
        
        # Mock QueryBuilder with all schema methods
        mock_qb = Mock()
        mock_query_builder.return_value = mock_qb
        
        # Mock all query methods
        for attr in dir(mock_qb):
            if attr.startswith('query_'):
                setattr(mock_qb, attr, Mock(return_value=[]))
        
        supported_schemas = SUPPORTED_SCHEMAS + ["ohlcv"]  # Include alias
        
        for schema in supported_schemas:
            result = self.runner.invoke(querying_app, [
                "query",
                "--symbols", "ES.c.0",
                "--start-date", "2024-01-01",
                "--end-date", "2024-01-02",
                "--schema", schema,
                "--dry-run"
            ])
            
            assert result.exit_code == 0, f"Schema {schema} should be valid but failed"
            assert "DRY RUN MODE" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])