"""
Unit tests for CLI validation commands module.

Tests all validation-related commands including comprehensive pandas market calendar
integration testing with detailed documentation for team review.

This test suite provides extensive coverage of:
- Smart validation functionality
- Pandas market calendar integration 
- Exchange-aware calendar analysis
- Error handling and edge cases
- Performance testing
"""

from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from datetime import datetime, date

import pytest
from typer.testing import CliRunner
from rich.console import Console

from src.cli.commands.validation import (
    app as validation_app,
    validate_date_format,
    get_available_exchanges,
    analyze_market_calendar,
    _get_mock_calendar_analysis
)


class TestValidationCommands:
    """Comprehensive test suite for validation commands."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.runner = CliRunner()
        self.console = Console(file=StringIO(), force_terminal=True)
    
    # Test utility functions
    def test_validate_date_format_valid(self):
        """Test date format validation with valid dates."""
        assert validate_date_format("2024-01-01") is True
        assert validate_date_format("2023-12-31") is True
        assert validate_date_format("2025-02-28") is True
    
    def test_validate_date_format_invalid(self):
        """Test date format validation with invalid dates."""
        # Note: datetime.strptime is more lenient than expected, so some of these might pass
        # We test the actual invalid formats that should definitely fail
        assert validate_date_format("01-01-2024") is False
        assert validate_date_format("invalid") is False
        assert validate_date_format("2024/01/01") is False
        assert validate_date_format("") is False
        assert validate_date_format("2024-13-01") is False  # Invalid month
        assert validate_date_format("2024-01-32") is False  # Invalid day
    
    def test_get_available_exchanges_with_pandas(self):
        """Test exchange list retrieval with pandas available."""
        with patch('src.cli.commands.validation.PANDAS_AVAILABLE', True):
            with patch('src.cli.commands.validation.mcal') as mock_mcal:
                mock_mcal.get_calendar_names.return_value = ["NYSE", "NASDAQ", "CME_Equity"]
                
                exchanges = get_available_exchanges()
                
                assert isinstance(exchanges, list)
                assert "NYSE" in exchanges
                assert "NASDAQ" in exchanges
                mock_mcal.get_calendar_names.assert_called_once()
    
    def test_get_available_exchanges_without_pandas(self):
        """Test exchange list retrieval without pandas."""
        with patch('src.cli.commands.validation.PANDAS_AVAILABLE', False):
            exchanges = get_available_exchanges()
            
            assert isinstance(exchanges, list)
            assert len(exchanges) > 0
            assert "NYSE" in exchanges
            assert "NASDAQ" in exchanges
    
    def test_get_available_exchanges_fallback(self):
        """Test exchange list fallback when pandas fails."""
        with patch('src.cli.commands.validation.PANDAS_AVAILABLE', True):
            with patch('src.cli.commands.validation.mcal') as mock_mcal:
                mock_mcal.get_calendar_names.side_effect = Exception("API Error")
                
                exchanges = get_available_exchanges()
                
                assert isinstance(exchanges, list)
                assert len(exchanges) > 0
                assert "NYSE" in exchanges


class TestMarketCalendarIntegration:
    """
    Comprehensive tests for pandas market calendar integration.
    
    This test class focuses on the high-priority pandas market calendar
    functionality with detailed testing and documentation.
    """
    
    def setup_method(self):
        """Set up market calendar test fixtures."""
        self.runner = CliRunner()
        self.console = Console(file=StringIO(), force_terminal=True)
    
    @patch('src.cli.commands.validation.PANDAS_AVAILABLE', True)
    @patch('src.cli.commands.validation.mcal')
    @patch('src.cli.commands.validation.pd')
    def test_analyze_market_calendar_with_pandas_success(self, mock_pd, mock_mcal):
        """
        Test successful market calendar analysis with pandas_market_calendars.
        
        This test validates the complete pandas integration workflow including:
        - Calendar initialization
        - Trading day calculation
        - Schedule retrieval
        - Holiday detection
        - Analytics generation
        """
        # Mock calendar setup
        mock_calendar = Mock()
        mock_mcal.get_calendar.return_value = mock_calendar
        
        # Mock timestamp creation with proper dates using actual datetime objects
        from datetime import datetime, timedelta
        import pandas as pd
        
        # Create real timestamps for proper date arithmetic
        start_ts = pd.Timestamp("2024-01-01")
        end_ts = pd.Timestamp("2024-01-05")
        mock_pd.Timestamp.side_effect = [start_ts, end_ts]
        
        # Mock trading days (5 trading days)
        mock_trading_days = [Mock() for _ in range(5)]
        for i, day in enumerate(mock_trading_days):
            day.strftime.return_value = f"2024-01-{i+1:02d}"
        mock_calendar.valid_days.return_value = mock_trading_days
        
        # Mock schedule
        mock_schedule = Mock()
        mock_calendar.schedule.return_value = mock_schedule
        
        # Mock holidays
        mock_calendar.holidays.return_value.holidays = []
        
        # Execute analysis
        result = analyze_market_calendar("2024-01-01", "2024-01-05", "NYSE")
        
        # Verify pandas integration calls
        mock_mcal.get_calendar.assert_called_once_with("NYSE")
        mock_calendar.valid_days.assert_called_once_with(start_date=start_ts, end_date=end_ts)
        mock_calendar.schedule.assert_called_once_with(start_date=start_ts, end_date=end_ts)
        
        # Verify result structure
        assert result["analysis_success"] is True
        assert result["exchange"] == "NYSE"
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-01-05"
        assert result["trading_days"] == 5
        assert result["total_days"] == 5
        assert result["coverage_percentage"] == 100.0
        assert isinstance(result["trading_days_list"], list)
        assert len(result["trading_days_list"]) == 5
    
    @patch('src.cli.commands.validation.PANDAS_AVAILABLE', True)
    @patch('src.cli.commands.validation.mcal')
    def test_analyze_market_calendar_with_pandas_error(self, mock_mcal):
        """Test market calendar analysis error handling with pandas."""
        mock_mcal.get_calendar.side_effect = Exception("Calendar not found")
        
        result = analyze_market_calendar("2024-01-01", "2024-01-05", "INVALID")
        
        # Should fallback to mock analysis
        assert result["analysis_success"] is False
        assert "note" in result
        assert result["exchange"] == "INVALID"
    
    @patch('src.cli.commands.validation.PANDAS_AVAILABLE', False)
    def test_analyze_market_calendar_without_pandas(self):
        """Test market calendar analysis without pandas_market_calendars."""
        result = analyze_market_calendar("2024-01-01", "2024-01-31", "NYSE")
        
        assert result["analysis_success"] is False
        assert "note" in result
        assert result["exchange"] == "NYSE"
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-01-31"
        assert result["total_days"] == 31
        assert result["trading_days"] > 0  # Should have estimated trading days
        assert result["coverage_percentage"] > 0
    
    def test_get_mock_calendar_analysis_valid_dates(self):
        """Test mock calendar analysis with valid date inputs."""
        result = _get_mock_calendar_analysis("2024-01-01", "2024-01-10", "NYSE")
        
        assert result["analysis_success"] is False
        assert result["exchange"] == "NYSE"
        assert result["total_days"] == 10
        assert result["trading_days"] == 7  # 70% of 10 days
        assert result["coverage_percentage"] == 70.0
        assert "note" in result
    
    def test_get_mock_calendar_analysis_invalid_dates(self):
        """Test mock calendar analysis error handling."""
        result = _get_mock_calendar_analysis("invalid", "2024-01-10", "NYSE")
        
        assert result["analysis_success"] is False
        assert "error" in result
        assert result["exchange"] == "NYSE"
    
    def test_market_calendar_command_basic_analysis(self):
        """Test market calendar command basic functionality."""
        with patch('src.cli.commands.validation.analyze_market_calendar') as mock_analyze:
            mock_analyze.return_value = {
                "analysis_success": True,
                "exchange": "NYSE",
                "start_date": "2024-01-01",
                "end_date": "2024-01-05",
                "total_days": 5,
                "trading_days": 3,
                "non_trading_days": 2,
                "coverage_percentage": 60.0,
                "holidays": [],
                "trading_days_list": [],
                "schedule": None
            }
            
            result = self.runner.invoke(validation_app, [
                "market-calendar", "2024-01-01", "2024-01-05"
            ])
            
            assert result.exit_code == 0
            assert "Market Calendar Analysis" in result.stdout
            # Check for table content instead of specific format
            assert "Trading Days" in result.stdout
            assert "3" in result.stdout
            assert "60.0%" in result.stdout
            mock_analyze.assert_called_once_with("2024-01-01", "2024-01-05", "NYSE")
    
    def test_market_calendar_command_with_holidays(self):
        """Test market calendar command with holidays display."""
        with patch('src.cli.commands.validation.analyze_market_calendar') as mock_analyze:
            mock_analyze.return_value = {
                "analysis_success": True,
                "exchange": "NYSE",
                "start_date": "2024-12-23",
                "end_date": "2024-12-27",
                "total_days": 5,
                "trading_days": 3,
                "non_trading_days": 2,
                "coverage_percentage": 60.0,
                "holidays": ["2024-12-25"],
                "trading_days_list": [],
                "schedule": None
            }
            
            result = self.runner.invoke(validation_app, [
                "market-calendar", "2024-12-23", "2024-12-27", 
                "--exchange", "NYSE", "--holidays"
            ])
            
            assert result.exit_code == 0
            assert "Holidays in Date Range" in result.stdout
            assert "2024-12-25" in result.stdout
    
    def test_market_calendar_command_list_exchanges(self):
        """Test market calendar command exchange listing."""
        with patch('src.cli.commands.validation.get_available_exchanges') as mock_exchanges:
            mock_exchanges.return_value = ["NYSE", "NASDAQ", "CME_Equity", "LSE"]
            
            result = self.runner.invoke(validation_app, [
                "market-calendar", "2024-01-01", "2024-01-02", "--list-exchanges"
            ])
            
            assert result.exit_code == 0
            assert "Available Market Calendar Exchanges" in result.stdout
            assert "NYSE" in result.stdout
            assert "NASDAQ" in result.stdout
            mock_exchanges.assert_called_once()
    
    def test_market_calendar_command_coverage_only(self):
        """Test market calendar command coverage-only mode."""
        with patch('src.cli.commands.validation.analyze_market_calendar') as mock_analyze:
            mock_analyze.return_value = {
                "analysis_success": True,
                "total_days": 365,
                "trading_days": 252,
                "coverage_percentage": 69.0
            }
            
            result = self.runner.invoke(validation_app, [
                "market-calendar", "2024-01-01", "2024-12-31", "--coverage"
            ])
            
            assert result.exit_code == 0
            assert "Coverage Summary" in result.stdout
            assert "365" in result.stdout
            assert "252" in result.stdout
            assert "69.0%" in result.stdout
    
    def test_market_calendar_command_invalid_dates(self):
        """Test market calendar command with invalid date formats."""
        result = self.runner.invoke(validation_app, [
            "market-calendar", "invalid-date", "2024-01-05"
        ])
        
        assert result.exit_code == 1
        assert "Invalid start_date format" in result.stdout
    
    def test_market_calendar_command_date_order_validation(self):
        """Test market calendar command date order validation."""
        result = self.runner.invoke(validation_app, [
            "market-calendar", "2024-01-05", "2024-01-01"
        ])
        
        assert result.exit_code == 1
        assert "Start date must be before end date" in result.stdout


class TestValidateCommand:
    """Test suite for the validate command functionality."""
    
    def setup_method(self):
        """Set up validate command test fixtures."""
        self.runner = CliRunner()
    
    def test_validate_command_symbol_valid(self):
        """Test validate command with valid symbol."""
        with patch('src.cli.commands.validation.create_smart_validator') as mock_validator:
            mock_result = Mock()
            mock_result.is_valid = True
            mock_result.suggestions = []
            
            mock_smart_validator = Mock()
            mock_smart_validator.validate_symbol.return_value = mock_result
            mock_validator.return_value = mock_smart_validator
            
            result = self.runner.invoke(validation_app, [
                "validate", "ES.c.0", "--type", "symbol"
            ])
            
            assert result.exit_code == 0
            assert "Symbol 'ES.c.0' is valid" in result.stdout
            assert "Validation passed" in result.stdout
    
    def test_validate_command_symbol_invalid(self):
        """Test validate command with invalid symbol."""
        with patch('src.cli.commands.validation.create_smart_validator') as mock_validator:
            mock_result = Mock()
            mock_result.is_valid = False
            mock_result.suggestions = ["ES.c.0", "NQ.c.0"]
            
            mock_smart_validator = Mock()
            mock_smart_validator.validate_symbol.return_value = mock_result
            mock_validator.return_value = mock_smart_validator
            
            result = self.runner.invoke(validation_app, [
                "validate", "INVALID_SYM", "--type", "symbol"
            ])
            
            assert result.exit_code == 1
            assert "Symbol 'INVALID_SYM' validation failed" in result.stdout
            assert "Suggestions:" in result.stdout
    
    def test_validate_command_schema_valid(self):
        """Test validate command with valid schema."""
        result = self.runner.invoke(validation_app, [
            "validate", "ohlcv-1d", "--type", "schema"
        ])
        
        assert result.exit_code == 0
        assert "Schema 'ohlcv-1d' is valid" in result.stdout
    
    def test_validate_command_schema_invalid(self):
        """Test validate command with invalid schema."""
        result = self.runner.invoke(validation_app, [
            "validate", "invalid_schema", "--type", "schema"
        ])
        
        assert result.exit_code == 1
        assert "Invalid schema: invalid_schema" in result.stdout
        assert "Valid schemas:" in result.stdout
    
    def test_validate_command_date_valid(self):
        """Test validate command with valid date."""
        result = self.runner.invoke(validation_app, [
            "validate", "2024-01-01", "--type", "date"
        ])
        
        assert result.exit_code == 0
        assert "Date format is valid" in result.stdout
    
    def test_validate_command_date_invalid(self):
        """Test validate command with invalid date."""
        result = self.runner.invoke(validation_app, [
            "validate", "invalid-date", "--type", "date"
        ])
        
        assert result.exit_code == 1
        assert "Invalid date format: invalid-date" in result.stdout
        assert "Expected format: YYYY-MM-DD" in result.stdout
    
    def test_validate_command_date_range_valid(self):
        """Test validate command with valid date range."""
        with patch('src.cli.commands.validation.create_smart_validator') as mock_validator:
            mock_result = Mock()
            mock_result.is_valid = True
            mock_result.warnings = []
            
            mock_smart_validator = Mock()
            mock_smart_validator.validate_date_range.return_value = mock_result
            mock_validator.return_value = mock_smart_validator
            
            result = self.runner.invoke(validation_app, [
                "validate", "", "--type", "date_range",
                "--start-date", "2024-01-01", "--end-date", "2024-01-31"
            ])
            
            assert result.exit_code == 0
            assert "Date range is valid" in result.stdout
    
    def test_validate_command_date_range_missing_dates(self):
        """Test validate command date range without required dates."""
        result = self.runner.invoke(validation_app, [
            "validate", "", "--type", "date_range"
        ])
        
        assert result.exit_code == 1
        assert "Date range validation requires --start-date and --end-date" in result.stdout
    
    def test_validate_command_symbol_list(self):
        """Test validate command with symbol list."""
        result = self.runner.invoke(validation_app, [
            "validate", "ES.c.0,NQ.c.0,CL.c.0", "--type", "symbol_list"
        ])
        
        assert result.exit_code == 0
        assert "Found 3 symbols in list" in result.stdout
        assert "ES.c.0" in result.stdout
        assert "NQ.c.0" in result.stdout
        assert "CL.c.0" in result.stdout
    
    def test_validate_command_unknown_type(self):
        """Test validate command with unknown validation type."""
        result = self.runner.invoke(validation_app, [
            "validate", "test", "--type", "unknown_type"
        ])
        
        assert result.exit_code == 1
        assert "Unknown validation type: unknown_type" in result.stdout
        assert "Valid types:" in result.stdout


class TestValidationCommandErrorHandling:
    """Test error handling for validation commands."""
    
    def setup_method(self):
        """Set up error handling test fixtures."""
        self.runner = CliRunner()
    
    def test_validate_command_smart_validator_exception(self):
        """Test validate command when smart validator fails."""
        with patch('src.cli.commands.validation.create_smart_validator') as mock_validator:
            mock_validator.side_effect = Exception("Smart validator failed")
            
            result = self.runner.invoke(validation_app, [
                "validate", "ES.c.0", "--type", "symbol"
            ])
            
            assert result.exit_code == 0  # Should fallback gracefully
            assert "Smart symbol validation unavailable" in result.stdout
            assert "has valid format" in result.stdout
    
    def test_market_calendar_command_analysis_exception(self):
        """Test market calendar command when analysis fails."""
        with patch('src.cli.commands.validation.analyze_market_calendar') as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis failed")
            
            result = self.runner.invoke(validation_app, [
                "market-calendar", "2024-01-01", "2024-01-05"
            ])
            
            assert result.exit_code == 1
            assert "Market calendar analysis failed" in result.stdout


class TestValidationCommandPerformance:
    """Performance tests for validation commands."""
    
    def setup_method(self):
        """Set up performance test fixtures."""
        self.runner = CliRunner()
    
    def test_validate_command_performance(self):
        """Test validate command executes within performance threshold."""
        import time
        
        start_time = time.time()
        
        result = self.runner.invoke(validation_app, [
            "validate", "2024-01-01", "--type", "date"
        ])
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert result.exit_code == 0
        assert execution_time < 2.0  # Should execute in less than 2 seconds
    
    def test_market_calendar_list_exchanges_performance(self):
        """Test market calendar exchange listing performance."""
        with patch('src.cli.commands.validation.get_available_exchanges') as mock_exchanges:
            mock_exchanges.return_value = ["NYSE", "NASDAQ"] * 50  # 100 exchanges
            
            import time
            start_time = time.time()
            
            result = self.runner.invoke(validation_app, [
                "market-calendar", "2024-01-01", "2024-01-02", "--list-exchanges"
            ])
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            assert result.exit_code == 0
            assert execution_time < 3.0  # Should handle large exchange lists quickly


class TestValidationCommandIntegration:
    """Integration tests for validation commands."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.runner = CliRunner()
    
    @pytest.mark.integration
    def test_validate_command_all_types(self):
        """Test validate command with all supported validation types."""
        validation_tests = [
            (["validate", "2024-01-01", "--type", "date"], 0),
            (["validate", "ohlcv-1d", "--type", "schema"], 0),
            (["validate", "ES.c.0,NQ.c.0", "--type", "symbol_list"], 0),
            (["validate", "invalid", "--type", "unknown"], 1),
        ]
        
        for cmd_args, expected_exit_code in validation_tests:
            result = self.runner.invoke(validation_app, cmd_args)
            assert result.exit_code == expected_exit_code
    
    @pytest.mark.integration
    def test_market_calendar_command_comprehensive(self):
        """Test market calendar command with comprehensive options."""
        with patch('src.cli.commands.validation.analyze_market_calendar') as mock_analyze:
            mock_analyze.return_value = {
                "analysis_success": True,
                "exchange": "NYSE",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "total_days": 31,
                "trading_days": 22,
                "non_trading_days": 9,
                "coverage_percentage": 71.0,
                "holidays": ["2024-01-15"],
                "trading_days_list": [],
                "schedule": None
            }
            
            # Test various command combinations
            command_tests = [
                ["market-calendar", "2024-01-01", "2024-01-31"],
                ["market-calendar", "2024-01-01", "2024-01-31", "--holidays"],
                ["market-calendar", "2024-01-01", "2024-01-31", "--coverage"],
                ["market-calendar", "2024-01-01", "2024-01-31", "--exchange", "CME_Equity"],
            ]
            
            for cmd_args in command_tests:
                result = self.runner.invoke(validation_app, cmd_args)
                assert result.exit_code == 0
                assert "Market Calendar Analysis" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])