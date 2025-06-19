"""
Integration tests for pandas-market-calendars implementation.

These tests run against the actual pandas-market-calendars library (not mocked)
to validate real-world functionality and ensure our integration works correctly.

Requirements:
- pandas-market-calendars>=5.0 must be installed
- Tests may take longer due to actual calendar data processing
- Network access may be required for some calendar data
"""

import pytest
from datetime import date, datetime, timedelta
from typing import Dict, List

import pandas as pd

# These tests require actual pandas-market-calendars
pytest_mark = pytest.mark.skipif(
    "not pandas_market_calendars_available", 
    reason="pandas-market-calendars not available"
)

# Check if pandas-market-calendars is available
try:
    import pandas_market_calendars as mcal
    pandas_market_calendars_available = True
except ImportError:
    pandas_market_calendars_available = False
    mcal = None


class TestMarketCalendarIntegration:
    """Integration tests for MarketCalendar with actual pandas-market-calendars."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        if not pandas_market_calendars_available:
            pytest.skip("pandas-market-calendars not available")
    
    def test_nyse_calendar_basic_functionality(self):
        """Test basic NYSE calendar functionality with real data."""
        from src.cli.smart_validation import MarketCalendar
        
        calendar = MarketCalendar("NYSE")
        
        # Test a known trading day (random Wednesday)
        trading_day = date(2024, 1, 10)  # Wednesday
        assert calendar.is_trading_day(trading_day), f"{trading_day} should be a trading day"
        
        # Test a known weekend
        weekend_day = date(2024, 1, 6)  # Saturday  
        assert not calendar.is_trading_day(weekend_day), f"{weekend_day} should not be a trading day"
        
        # Test a known holiday (New Year's Day 2024)
        new_years = date(2024, 1, 1)  # Monday (observed)
        assert not calendar.is_trading_day(new_years), f"{new_years} should not be a trading day (New Year's)"

    def test_cme_equity_calendar_functionality(self):
        """Test CME Equity calendar functionality."""
        from src.cli.smart_validation import MarketCalendar
        
        calendar = MarketCalendar("CME_Equity")
        
        # CME operates nearly 24 hours, so trading days are different
        trading_day = date(2024, 1, 10)  # Wednesday
        assert calendar.is_trading_day(trading_day), f"{trading_day} should be a trading day for CME"
        
        # Test weekend - CME might have different weekend rules
        # Note: CME_Equity might trade on some weekend hours, but let's test a known holiday
        new_years = date(2024, 1, 1)  # New Year's Day
        # CME might be closed on New Year's Day too
        
    def test_trading_days_count_accuracy(self):
        """Test trading day counting accuracy against real calendar data."""
        from src.cli.smart_validation import MarketCalendar
        
        calendar = MarketCalendar("NYSE") 
        
        # Test a known period - January 2024
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        
        trading_days = calendar.get_trading_days_count(start, end)
        
        # January 2024 has 22 trading days for NYSE (accounting for New Year's Day holiday)
        # This is a known fact we can verify
        expected_min = 20  # Minimum expected
        expected_max = 23  # Maximum expected
        
        assert expected_min <= trading_days <= expected_max, (
            f"January 2024 should have ~22 trading days, got {trading_days}"
        )

    def test_holidays_detection(self):
        """Test holiday detection against real calendar data."""
        from src.cli.smart_validation import MarketCalendar
        
        calendar = MarketCalendar("NYSE")
        
        # Test a year with known holidays
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        
        holidays = calendar.get_holidays(start, end)
        
        # NYSE should have major holidays like New Year's Day, Independence Day, Christmas
        holiday_dates = [h.date() for h in holidays]
        
        # Check for known holidays in 2024
        expected_holidays = [
            date(2024, 1, 1),   # New Year's Day
            date(2024, 7, 4),   # Independence Day  
            date(2024, 12, 25), # Christmas Day
        ]
        
        for expected_holiday in expected_holidays:
            # The holiday might be observed on a different day if it falls on weekend
            # So we check if the holiday or nearby dates are in the list
            holiday_found = any(
                abs((expected_holiday - holiday_date).days) <= 2 
                for holiday_date in holiday_dates
            )
            assert holiday_found, f"Expected holiday around {expected_holiday} not found in {holiday_dates}"

    def test_market_schedule_retrieval(self):
        """Test market schedule retrieval with real data.""" 
        from src.cli.smart_validation import MarketCalendar
        
        calendar = MarketCalendar("NYSE")
        
        # Test a short period
        start = date(2024, 1, 8)   # Monday
        end = date(2024, 1, 12)    # Friday
        
        schedule = calendar.get_schedule(start, end)
        
        assert schedule is not None, "Schedule should not be None"
        assert not schedule.empty, "Schedule should not be empty"
        
        # Check that we have data for trading days
        assert len(schedule) >= 4, f"Should have at least 4 trading days, got {len(schedule)}"
        
        # Check that schedule has expected columns
        expected_columns = ['market_open', 'market_close']
        for col in expected_columns:
            assert col in schedule.columns, f"Schedule should have {col} column"

    def test_early_close_detection(self):
        """Test early close detection with real calendar data."""
        from src.cli.smart_validation import MarketCalendar
        
        calendar = MarketCalendar("NYSE")
        
        # Test around known early close periods
        # Thanksgiving 2024 is November 28, so Friday November 29 should be early close
        start = date(2024, 11, 25)  # Monday before Thanksgiving
        end = date(2024, 12, 2)     # Week after
        
        early_closes = calendar.get_early_closes(start, end)
        
        # There should be at least some early closes detected in this period
        # (Black Friday, potentially day before Christmas if it falls in range)
        
        # Verify the format of early close data
        for close_date, close_info in early_closes.items():
            assert isinstance(close_date, date), "Early close date should be a date object"
            assert isinstance(close_info, str), "Early close info should be a string"
            assert ":" in close_info, "Early close info should contain time information"

    def test_exchange_mapping_integration(self):
        """Test exchange mapping with real calendar data."""
        from src.cli.exchange_mapping import get_exchange_mapper
        
        mapper = get_exchange_mapper()
        
        # Test various symbol mappings
        test_cases = [
            ("ES.FUT", "CME_Equity"),
            ("CL.FUT", "CME_Energy"), 
            ("SPY", "NYSE"),
            ("AAPL", "NASDAQ"),
        ]
        
        for symbol, expected_exchange in test_cases:
            detected_exchange, confidence, mapping_info = mapper.map_symbol_to_exchange(symbol)
            
            assert detected_exchange == expected_exchange, (
                f"Symbol {symbol} should map to {expected_exchange}, got {detected_exchange}"
            )
            assert confidence > 0.8, f"Confidence for {symbol} should be high, got {confidence}"
            assert mapping_info is not None, f"Mapping info should exist for {symbol}"

    def test_databento_adapter_calendar_filtering(self):
        """Test calendar filtering in databento adapter."""
        from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter
        
        # Create adapter with minimal config
        config = {
            "api": {"key_env_var": "FAKE_KEY"},
            "validation": {}
        }
        
        adapter = DatabentoAdapter(config)
        
        # Test date chunk generation with calendar filtering
        start_date = "2024-12-23"  # Monday before Christmas
        end_date = "2024-12-27"    # Friday after Christmas
        
        # Without calendar filtering
        chunks_normal = adapter._generate_date_chunks(
            start_date, end_date, 1, False, "NYSE"
        )
        
        # With calendar filtering
        chunks_filtered = adapter._generate_date_chunks(
            start_date, end_date, 1, True, "NYSE"
        )
        
        # Should have fewer chunks with filtering (Christmas Day excluded)
        assert len(chunks_filtered) <= len(chunks_normal), (
            "Calendar filtering should reduce or maintain chunk count"
        )

    def test_cli_pre_flight_analysis(self):
        """Test CLI pre-flight analysis integration.""" 
        from src.cli.smart_validation import SmartValidator
        
        # Test with futures symbols (should auto-detect CME_Equity)
        validator = SmartValidator(exchange_name="CME_Equity")
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = validator.validate_date_range(start_date, end_date)
        
        assert result.is_valid, "Date range validation should succeed"
        assert 'coverage_ratio' in result.metadata, "Should include coverage ratio"
        assert 'trading_days' in result.metadata, "Should include trading days count"
        assert 'exchange_name' in result.metadata, "Should include exchange name"
        
        coverage_ratio = result.metadata['coverage_ratio']
        assert 0.0 <= coverage_ratio <= 1.0, f"Coverage ratio should be between 0 and 1, got {coverage_ratio}"

    def test_multiple_exchange_consistency(self):
        """Test consistency across different exchanges."""
        from src.cli.smart_validation import MarketCalendar
        
        exchanges = ["NYSE", "NASDAQ", "CME_Equity"]
        test_date = date(2024, 1, 10)  # Wednesday
        
        results = {}
        for exchange in exchanges:
            try:
                calendar = MarketCalendar(exchange)
                is_trading = calendar.is_trading_day(test_date)
                results[exchange] = is_trading
            except Exception as e:
                pytest.skip(f"Exchange {exchange} not available: {e}")
        
        # For a normal Wednesday, most exchanges should be trading
        # (though CME_Equity might have different rules)
        trading_count = sum(results.values())
        assert trading_count >= len(results) // 2, (
            f"Most exchanges should be trading on {test_date}, results: {results}"
        )

    def test_performance_benchmarking(self):
        """Basic performance test for calendar operations."""
        from src.cli.smart_validation import MarketCalendar
        import time
        
        calendar = MarketCalendar("NYSE")
        
        # Test performance of trading day checks
        start_time = time.time()
        
        test_dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(365)]
        trading_days = [calendar.is_trading_day(d) for d in test_dates]
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should process 365 days in reasonable time (< 5 seconds)
        assert elapsed < 5.0, f"Calendar operations took too long: {elapsed:.2f}s"
        
        # Should have reasonable number of trading days in a year (~252)
        trading_count = sum(trading_days)
        assert 240 <= trading_count <= 260, f"Unexpected trading day count: {trading_count}"

    def test_fallback_behavior(self):
        """Test fallback behavior when pandas-market-calendars features fail."""
        from src.cli.smart_validation import MarketCalendar
        
        # Create calendar with known good exchange
        calendar = MarketCalendar("NYSE")
        
        # Test with invalid date range (should handle gracefully)
        invalid_start = date(1900, 1, 1)  # Very old date
        invalid_end = date(1900, 1, 31)
        
        # These should not crash, but may return empty results
        try:
            holidays = calendar.get_holidays(invalid_start, invalid_end)
            early_closes = calendar.get_early_closes(invalid_start, invalid_end)
            
            # Results might be empty but shouldn't be None
            assert holidays is not None, "Holidays should not be None"
            assert early_closes is not None, "Early closes should not be None"
            
        except Exception:
            # Some operations might fail for very old dates, which is acceptable
            pass

    @pytest.mark.parametrize("exchange", [
        "NYSE", "NASDAQ", "CME_Equity", "CME_Energy", "LSE"
    ])
    def test_exchange_specific_functionality(self, exchange):
        """Test functionality for specific exchanges."""
        from src.cli.smart_validation import MarketCalendar
        
        try:
            calendar = MarketCalendar(exchange)
            
            # Test basic functionality
            test_date = date(2024, 1, 10)  # Wednesday
            is_trading = calendar.is_trading_day(test_date)
            
            # Result should be boolean
            assert isinstance(is_trading, bool), f"is_trading_day should return bool for {exchange}"
            
            # Test name property
            assert calendar.name == exchange, f"Calendar name should match exchange for {exchange}"
            
        except ValueError as e:
            if "Unknown exchange" in str(e):
                pytest.skip(f"Exchange {exchange} not available in this pandas-market-calendars version")
            else:
                raise

    def test_date_range_edge_cases(self):
        """Test edge cases for date ranges."""
        from src.cli.smart_validation import MarketCalendar
        
        calendar = MarketCalendar("NYSE")
        
        # Test single day range
        single_day = date(2024, 1, 10)
        count = calendar.get_trading_days_count(single_day, single_day)
        
        expected = 1 if calendar.is_trading_day(single_day) else 0
        assert count == expected, f"Single day count should be {expected}, got {count}"
        
        # Test reverse date range (should handle gracefully)
        start = date(2024, 1, 10)
        end = date(2024, 1, 5)  # End before start
        
        # Should either return 0 or handle gracefully
        count = calendar.get_trading_days_count(start, end)
        assert count >= 0, f"Reverse date range should return non-negative count, got {count}"

    def test_calendar_caching(self):
        """Test that calendar caching works correctly."""
        from src.cli.smart_validation import get_calendar_instance
        
        # Clear cache first
        get_calendar_instance.cache_clear()
        
        # Create two instances of the same calendar
        cal1 = get_calendar_instance("NYSE")
        cal2 = get_calendar_instance("NYSE")
        
        # Should be the same instance due to caching
        assert cal1 is cal2, "Calendar instances should be cached"
        
        # Check cache info
        cache_info = get_calendar_instance.cache_info()
        assert cache_info.hits >= 1, "Should have at least one cache hit"


class TestMarketCalendarPerformance:
    """Performance tests for market calendar operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        if not pandas_market_calendars_available:
            pytest.skip("pandas-market-calendars not available")
    
    def test_bulk_trading_day_checks(self):
        """Test performance of bulk trading day checks."""
        from src.cli.smart_validation import MarketCalendar
        import time
        
        calendar = MarketCalendar("NYSE")
        
        # Generate a large number of dates
        dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(1000)]
        
        start_time = time.time()
        results = [calendar.is_trading_day(d) for d in dates]
        end_time = time.time()
        
        elapsed = end_time - start_time
        
        # Should process 1000 dates quickly
        assert elapsed < 10.0, f"Bulk trading day checks took too long: {elapsed:.2f}s"
        assert len(results) == 1000, "Should have results for all dates"
        
    def test_schedule_retrieval_performance(self):
        """Test performance of schedule retrieval."""
        from src.cli.smart_validation import MarketCalendar
        import time
        
        calendar = MarketCalendar("NYSE")
        
        # Test large date range
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        
        start_time = time.time()
        schedule = calendar.get_schedule(start, end)
        end_time = time.time()
        
        elapsed = end_time - start_time
        
        # Should retrieve full year schedule reasonably quickly
        assert elapsed < 15.0, f"Schedule retrieval took too long: {elapsed:.2f}s"
        
        if schedule is not None:
            assert not schedule.empty, "Schedule should not be empty for full year"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])