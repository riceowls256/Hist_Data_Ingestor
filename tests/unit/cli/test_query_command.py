"""
Unit tests for CLI query command functionality.

Tests parameter parsing, validation, output formatting, and error handling
without requiring actual database connectivity.
"""

import json
import pytest
from datetime import date, datetime
from decimal import Decimal
from io import StringIO
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner

# Import the main app and helper functions
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from main import app, parse_query_symbols, parse_date_string, validate_query_scope
from main import format_table_output, format_csv_output, format_json_output
from querying.exceptions import SymbolResolutionError, QueryExecutionError


class TestSymbolParsing:
    """Test symbol parsing functionality."""
    
    def test_parse_single_symbol(self):
        """Test parsing a single symbol."""
        result = parse_query_symbols(["ES.c.0"])
        assert result == ["ES.c.0"]
    
    def test_parse_comma_separated_symbols(self):
        """Test parsing comma-separated symbols."""
        result = parse_query_symbols(["ES.c.0,NQ.c.0,CL.c.0"])
        assert result == ["ES.c.0", "NQ.c.0", "CL.c.0"]
    
    def test_parse_multiple_symbol_flags(self):
        """Test parsing multiple symbol flags."""
        result = parse_query_symbols(["ES.c.0", "NQ.c.0", "CL.c.0"])
        assert result == ["ES.c.0", "NQ.c.0", "CL.c.0"]
    
    def test_parse_mixed_symbol_input(self):
        """Test parsing mixed comma-separated and multiple flags."""
        result = parse_query_symbols(["ES.c.0,NQ.c.0", "CL.c.0"])
        assert result == ["ES.c.0", "NQ.c.0", "CL.c.0"]
    
    def test_parse_symbols_with_whitespace(self):
        """Test parsing symbols with extra whitespace."""
        result = parse_query_symbols([" ES.c.0 , NQ.c.0 ", " CL.c.0 "])
        assert result == ["ES.c.0", "NQ.c.0", "CL.c.0"]
    
    def test_parse_empty_symbols(self):
        """Test parsing empty symbol input."""
        result = parse_query_symbols([""])
        assert result == []


class TestDateParsing:
    """Test date parsing and validation."""
    
    def test_parse_valid_date(self):
        """Test parsing valid date string."""
        result = parse_date_string("2024-01-15")
        assert result == date(2024, 1, 15)
    
    def test_parse_date_invalid_format(self):
        """Test parsing invalid date format."""
        with pytest.raises(ValueError):
            parse_date_string("01/15/2024")
    
    def test_parse_date_invalid_date(self):
        """Test parsing invalid date."""
        with pytest.raises(ValueError):
            parse_date_string("2024-13-45")


class TestQueryScopeValidation:
    """Test query scope validation."""
    
    @patch('main.typer.confirm')
    def test_validate_large_trades_query(self, mock_confirm):
        """Test validation for large trades query."""
        mock_confirm.return_value = True
        
        symbols = ["ES.c.0"]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 5)  # 4 days
        schema = "trades"
        
        result = validate_query_scope(symbols, start_date, end_date, schema)
        assert result is True
        mock_confirm.assert_called_once()
    
    @patch('main.typer.confirm')
    def test_validate_large_tbbo_query(self, mock_confirm):
        """Test validation for large TBBO query."""
        mock_confirm.return_value = False
        
        symbols = ["ES.c.0"]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 3)  # 2 days
        schema = "tbbo"
        
        result = validate_query_scope(symbols, start_date, end_date, schema)
        assert result is False
        mock_confirm.assert_called_once()
    
    @patch('main.typer.confirm')
    def test_validate_many_symbols_query(self, mock_confirm):
        """Test validation for query with many symbols."""
        mock_confirm.return_value = True
        
        symbols = [f"SYM{i}.c.0" for i in range(15)]  # 15 symbols
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 1)
        schema = "ohlcv-1d"
        
        result = validate_query_scope(symbols, start_date, end_date, schema)
        assert result is True
        mock_confirm.assert_called_once()
    
    def test_validate_normal_query(self):
        """Test validation for normal query scope."""
        symbols = ["ES.c.0", "NQ.c.0"]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        schema = "ohlcv-1d"
        
        result = validate_query_scope(symbols, start_date, end_date, schema)
        assert result is True


class TestOutputFormatting:
    """Test output formatting functions."""
    
    def test_format_table_output_ohlcv(self):
        """Test table formatting for OHLCV data."""
        results = [
            {
                "symbol": "ES.c.0",
                "ts_event": datetime(2024, 1, 15, 9, 30),
                "open_price": Decimal("4500.25"),
                "high_price": Decimal("4510.75"),
                "low_price": Decimal("4495.50"),
                "close_price": Decimal("4505.00"),
                "volume": 1000
            }
        ]
        
        table = format_table_output(results, "ohlcv-1d")
        assert table.columns[0].header == "Symbol"
        assert table.columns[1].header == "Date"
        assert len(table.rows) == 1
    
    def test_format_table_output_trades(self):
        """Test table formatting for trades data."""
        results = [
            {
                "symbol": "ES.c.0",
                "ts_event": datetime(2024, 1, 15, 9, 30, 15),
                "price": Decimal("4500.25"),
                "size": 10,
                "side": "B"
            }
        ]
        
        table = format_table_output(results, "trades")
        assert table.columns[0].header == "Symbol"
        assert table.columns[1].header == "Timestamp"
        assert table.columns[2].header == "Price"
        assert len(table.rows) == 1
    
    def test_format_table_output_empty(self):
        """Test table formatting for empty results."""
        from rich.console import Console
        from io import StringIO
        
        table = format_table_output([], "ohlcv-1d")
        assert table.columns[0].header == "Message"
        assert len(table.rows) == 1
        
        # Test that the table actually contains the no data message by rendering it
        console = Console(file=StringIO(), width=80)
        console.print(table)
        output = console.file.getvalue()
        assert "No data found for the specified criteria" in output
    
    def test_format_csv_output(self):
        """Test CSV formatting."""
        results = [
            {
                "symbol": "ES.c.0",
                "ts_event": datetime(2024, 1, 15, 9, 30),
                "price": Decimal("4500.25")
            }
        ]
        
        csv_output = format_csv_output(results)
        lines = csv_output.strip().split('\n')
        
        assert "symbol,ts_event,price" in lines[0]
        assert "ES.c.0" in lines[1]
        assert "4500.25" in lines[1]
    
    def test_format_csv_output_empty(self):
        """Test CSV formatting for empty results."""
        csv_output = format_csv_output([])
        assert csv_output == ""
    
    def test_format_json_output(self):
        """Test JSON formatting."""
        results = [
            {
                "symbol": "ES.c.0",
                "ts_event": datetime(2024, 1, 15, 9, 30),
                "price": Decimal("4500.25")
            }
        ]
        
        json_output = format_json_output(results)
        parsed = json.loads(json_output)
        
        assert len(parsed) == 1
        assert parsed[0]["symbol"] == "ES.c.0"
        assert parsed[0]["price"] == "4500.25"
        assert "2024-01-15T09:30:00" in parsed[0]["ts_event"]


class TestCLIQueryCommand:
    """Test CLI query command integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('main.QueryBuilder')
    def test_query_command_basic_success(self, mock_qb_class):
        """Test basic successful query command."""
        # Mock QueryBuilder
        mock_qb = MagicMock()
        mock_qb_class.return_value = mock_qb  # Remove context manager setup
        mock_qb.query_daily_ohlcv.return_value = [
            {
                "symbol": "ES.c.0",
                "ts_event": datetime(2024, 1, 15),
                "open_price": Decimal("4500.25"),
                "high_price": Decimal("4510.75"),
                "low_price": Decimal("4495.50"),
                "close_price": Decimal("4505.00"),
                "volume": 1000
            }
        ]
        
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-31"
        ])
        
        assert result.exit_code == 0
        assert "Found 1 records in" in result.stdout  # Updated to match new format
        assert "Query completed successfully" in result.stdout
        mock_qb.query_daily_ohlcv.assert_called_once()
    
    @patch('main.QueryBuilder')
    def test_query_command_multiple_symbols(self, mock_qb_class):
        """Test query command with multiple symbols."""
        mock_qb = MagicMock()
        mock_qb_class.return_value = mock_qb  # Remove context manager setup
        mock_qb.query_daily_ohlcv.return_value = []
        
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0,NQ.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-31"
        ])
        
        assert result.exit_code == 0
        assert "No data found for the specified criteria" in result.stdout  # Updated to match new format
        
        # Verify symbols were parsed correctly
        call_args = mock_qb.query_daily_ohlcv.call_args
        assert call_args[1]["symbols"] == ["ES.c.0", "NQ.c.0"]
    
    @patch('main.QueryBuilder')
    def test_query_command_different_schema(self, mock_qb_class):
        """Test query command with different schema."""
        mock_qb = MagicMock()
        mock_qb_class.return_value = mock_qb  # Remove context manager setup
        mock_qb.query_trades.return_value = []
        
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-01",
            "--schema", "trades"
        ])
        
        assert result.exit_code == 0
        mock_qb.query_trades.assert_called_once()
    
    def test_query_command_invalid_date_format(self):
        """Test query command with invalid date format."""
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "01/01/2024",
            "--end-date", "2024-01-31"
        ])
        
        assert result.exit_code == 1
        assert "start-date must be in YYYY-MM-DD format" in result.stdout
    
    def test_query_command_invalid_date_range(self):
        """Test query command with invalid date range."""
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-31",
            "--end-date", "2024-01-01"
        ])
        
        assert result.exit_code == 1
        assert "start-date must be before or equal to end-date" in result.stdout
    
    def test_query_command_invalid_schema(self):
        """Test query command with invalid schema."""
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-31",
            "--schema", "invalid_schema"
        ])
        
        assert result.exit_code == 1
        assert "Invalid schema 'invalid_schema'" in result.stdout
    
    def test_query_command_invalid_output_format(self):
        """Test query command with invalid output format."""
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-31",
            "--output-format", "xml"
        ])
        
        assert result.exit_code == 1
        assert "Invalid output format" in result.stdout
    
    @patch('main.QueryBuilder')
    def test_query_command_symbol_resolution_error(self, mock_qb_class):
        """Test query command with symbol resolution error."""
        mock_qb = MagicMock()
        mock_qb_class.return_value = mock_qb  # Remove context manager setup
        mock_qb.query_daily_ohlcv.side_effect = SymbolResolutionError("Symbol not found: INVALID")
        mock_qb.get_available_symbols.return_value = ["ES.c.0", "NQ.c.0"]
        
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "INVALID",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-31"
        ])
        
        assert result.exit_code == 1
        assert "Symbol error" in result.stdout
        assert "Available symbols" in result.stdout
    
    @patch('main.QueryBuilder')
    def test_query_command_database_error(self, mock_qb_class):
        """Test query command with database error."""
        mock_qb = MagicMock()
        mock_qb_class.return_value = mock_qb  # Remove context manager setup
        mock_qb.query_daily_ohlcv.side_effect = QueryExecutionError("Database connection failed")
        
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-31"
        ])
        
        assert result.exit_code == 1
        assert "Database error" in result.stdout
        assert "Check database connection" in result.stdout
    
    @patch('main.QueryBuilder')
    @patch('main.write_output_file')
    def test_query_command_csv_output_to_file(self, mock_write_file, mock_qb_class):
        """Test query command with CSV output to file."""
        mock_qb = MagicMock()
        mock_qb_class.return_value = mock_qb  # Remove context manager setup
        mock_qb.query_daily_ohlcv.return_value = [
            {
                "symbol": "ES.c.0",
                "ts_event": datetime(2024, 1, 15),
                "open_price": Decimal("4500.25"),
                "high_price": Decimal("4510.75"),
                "low_price": Decimal("4495.50"),
                "close_price": Decimal("4505.00"),
                "volume": 1000
            }
        ]
        
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-31",
            "--output-format", "csv",
            "--output-file", "test.csv"
        ])
        
        assert result.exit_code == 0
        mock_write_file.assert_called_once()
        
        # Verify CSV content was generated with OHLCV fields
        call_args = mock_write_file.call_args
        assert "symbol" in call_args[0][0]
        assert "open_price" in call_args[0][0]
    
    @patch('main.QueryBuilder')
    def test_query_command_with_limit(self, mock_qb_class):
        """Test query command with limit parameter."""
        mock_qb = MagicMock()
        mock_qb_class.return_value = mock_qb  # Remove context manager setup
        mock_qb.query_daily_ohlcv.return_value = []
        
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-31",
            "--limit", "100"
        ])
        
        assert result.exit_code == 0
        
        # Verify limit was passed to query
        call_args = mock_qb.query_daily_ohlcv.call_args
        assert call_args is not None, "query_daily_ohlcv should have been called"
        assert call_args[1]["limit"] == 100


if __name__ == "__main__":
    pytest.main([__file__]) 