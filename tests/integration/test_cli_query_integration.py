"""
Integration tests for CLI query command.

Tests actual database connectivity and QueryBuilder integration.
Requires running TimescaleDB instance and test data.
"""

import os
import pytest
import tempfile
from pathlib import Path
from typer.testing import CliRunner

# Import the main app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from main import app


class TestCLIQueryIntegration:
    """Integration tests for CLI query command."""
    
    @classmethod
    def setup_class(cls):
        """Set up test class with database connection check."""
        cls.runner = CliRunner()
        
        # Check if we have database environment variables
        required_env_vars = ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB']
        cls.has_db_config = all(os.getenv(var) for var in required_env_vars)
        
        if not cls.has_db_config:
            pytest.skip("Database environment variables not configured")
    
    def setup_method(self):
        """Set up each test method."""
        if not self.has_db_config:
            pytest.skip("Database not configured")
    
    def test_query_command_help(self):
        """Test query command help output."""
        result = self.runner.invoke(app, ["query", "--help"])
        
        assert result.exit_code == 0
        assert "Query historical financial data" in result.stdout
        assert "--symbols" in result.stdout
        assert "--start-date" in result.stdout
        assert "--end-date" in result.stdout
        assert "--schema" in result.stdout
        assert "--output-format" in result.stdout
    
    def test_query_command_missing_required_params(self):
        """Test query command with missing required parameters."""
        result = self.runner.invoke(app, ["query"])
        
        assert result.exit_code == 2  # Typer error for missing required params
        assert "Missing option" in result.stdout
    
    def test_query_command_invalid_symbol_graceful_error(self):
        """Test query command with invalid symbol shows graceful error."""
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "INVALID_SYMBOL_12345",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-01"
        ])
        
        # Should exit with error but show helpful message
        assert result.exit_code == 1
        # Should contain either symbol error or no data found message
        assert any(phrase in result.stdout for phrase in [
            "Symbol error", 
            "No data found",
            "Available symbols"
        ])
    
    def test_query_command_future_date_no_data(self):
        """Test query command with future dates returns no data gracefully."""
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2030-01-01",
            "--end-date", "2030-01-01"
        ])
        
        # Should succeed but find no data
        assert result.exit_code == 0
        assert "No data found" in result.stdout
    
    def test_query_command_csv_output_format(self):
        """Test query command with CSV output format."""
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-01",
            "--output-format", "csv"
        ])
        
        # Should succeed regardless of data availability
        assert result.exit_code == 0
        
        # If data found, should contain CSV headers or no data message
        if "No data found" not in result.stdout:
            # Should contain CSV-like output
            assert any(header in result.stdout for header in [
                "symbol", "ts_event", "open_price", "close_price"
            ])
    
    def test_query_command_json_output_format(self):
        """Test query command with JSON output format."""
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-01",
            "--output-format", "json"
        ])
        
        # Should succeed regardless of data availability
        assert result.exit_code == 0
        
        # If data found, should contain JSON-like output or no data message
        if "No data found" not in result.stdout:
            # Should contain JSON brackets or no data message
            assert any(char in result.stdout for char in ["[", "]", "{", "}"])
    
    def test_query_command_different_schemas(self):
        """Test query command with different schema types."""
        schemas = ["ohlcv-1d", "trades", "tbbo", "statistics", "definitions"]
        
        for schema in schemas:
            result = self.runner.invoke(app, [
                "query",
                "--symbols", "ES.c.0",
                "--start-date", "2024-01-01",
                "--end-date", "2024-01-01",
                "--schema", schema
            ])
            
            # Should succeed for all valid schemas
            assert result.exit_code == 0, f"Schema {schema} failed"
            
            # Should either find data or show no data message
            assert any(phrase in result.stdout for phrase in [
                "Found", "No data found", "Query completed"
            ]), f"Schema {schema} didn't show expected output"
    
    def test_query_command_file_output(self):
        """Test query command with file output."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            result = self.runner.invoke(app, [
                "query",
                "--symbols", "ES.c.0",
                "--start-date", "2024-01-01",
                "--end-date", "2024-01-01",
                "--output-format", "csv",
                "--output-file", tmp_path
            ])
            
            # Should succeed
            assert result.exit_code == 0
            
            # File should be created
            assert Path(tmp_path).exists()
            
            # Should mention file output in stdout
            assert tmp_path in result.stdout or "Output written" in result.stdout
            
        finally:
            # Clean up
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()
    
    def test_query_command_limit_parameter(self):
        """Test query command with limit parameter."""
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-31",
            "--limit", "5"
        ])
        
        # Should succeed
        assert result.exit_code == 0
        
        # Should show limit in configuration or results
        assert any(phrase in result.stdout for phrase in [
            "Limit", "5", "Query completed"
        ])
    
    def test_query_command_multiple_symbols_comma_separated(self):
        """Test query command with comma-separated symbols."""
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0,NQ.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-01"
        ])
        
        # Should succeed
        assert result.exit_code == 0
        
        # Should show both symbols in configuration
        assert "ES.c.0" in result.stdout
        assert "NQ.c.0" in result.stdout
    
    def test_query_command_multiple_symbol_flags(self):
        """Test query command with multiple -s flags."""
        result = self.runner.invoke(app, [
            "query",
            "-s", "ES.c.0",
            "-s", "NQ.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-01"
        ])
        
        # Should succeed
        assert result.exit_code == 0
        
        # Should show both symbols in configuration
        assert "ES.c.0" in result.stdout
        assert "NQ.c.0" in result.stdout
    
    def test_query_command_execution_time_reporting(self):
        """Test that query command reports execution time."""
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-01"
        ])
        
        # Should succeed
        assert result.exit_code == 0
        
        # Should report execution time
        assert any(phrase in result.stdout for phrase in [
            "seconds", "Time:", "Query completed"
        ])
    
    def test_query_command_configuration_display(self):
        """Test that query command displays configuration before execution."""
        result = self.runner.invoke(app, [
            "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-01",
            "--schema", "ohlcv-1d",
            "--output-format", "table"
        ])
        
        # Should succeed
        assert result.exit_code == 0
        
        # Should display configuration
        assert "Query configuration" in result.stdout
        assert "ES.c.0" in result.stdout
        assert "2024-01-01" in result.stdout
        assert "ohlcv-1d" in result.stdout
        assert "table" in result.stdout


class TestCLIQueryDatabaseConnectivity:
    """Test database connectivity aspects of CLI query."""
    
    def setup_method(self):
        """Set up each test method."""
        self.runner = CliRunner()
    
    def test_query_command_database_connection_error_handling(self):
        """Test query command handles database connection errors gracefully."""
        # Temporarily modify environment to cause connection failure
        original_host = os.environ.get('POSTGRES_HOST')
        os.environ['POSTGRES_HOST'] = 'invalid_host_12345'
        
        try:
            result = self.runner.invoke(app, [
                "query",
                "--symbols", "ES.c.0",
                "--start-date", "2024-01-01",
                "--end-date", "2024-01-01"
            ])
            
            # Should fail gracefully
            assert result.exit_code == 1
            
            # Should show database error message
            assert any(phrase in result.stdout for phrase in [
                "Database error", "connection", "Check database"
            ])
            
        finally:
            # Restore original environment
            if original_host:
                os.environ['POSTGRES_HOST'] = original_host
            elif 'POSTGRES_HOST' in os.environ:
                del os.environ['POSTGRES_HOST']


if __name__ == "__main__":
    pytest.main([__file__]) 