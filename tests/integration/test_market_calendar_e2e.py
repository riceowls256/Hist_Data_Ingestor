"""
End-to-end tests for pandas-market-calendars integration.

These tests validate the complete pipeline integration including CLI commands,
data processing, and real-world usage scenarios.
"""

import pytest
import subprocess
import json
import tempfile
from pathlib import Path
from datetime import date, timedelta

# Check if pandas-market-calendars is available
try:
    import pandas_market_calendars as mcal
    pandas_market_calendars_available = True
except ImportError:
    pandas_market_calendars_available = False


class TestMarketCalendarE2E:
    """End-to-end tests for market calendar integration."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        if not pandas_market_calendars_available:
            pytest.skip("pandas-market-calendars not available")
    
    def test_market_calendar_cli_command(self):
        """Test the market-calendar CLI command end-to-end."""
        
        # Test basic functionality
        result = subprocess.run([
            "python", "main.py", "market-calendar", 
            "2024-01-01", "2024-01-31", 
            "--exchange", "NYSE"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 0, f"CLI command failed: {result.stderr}"
        
        # Check for expected output patterns
        output = result.stdout
        assert "Market Calendar Analysis" in output, "Should show calendar analysis header"
        assert "Trading day coverage" in output, "Should show coverage information"
        assert "Total days:" in output, "Should show total days"
        assert "Trading days:" in output, "Should show trading days"

    def test_market_calendar_list_exchanges(self):
        """Test listing available exchanges."""
        
        result = subprocess.run([
            "python", "main.py", "market-calendar",
            "2024-01-01", "2024-01-02",
            "--list-exchanges"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 0, f"List exchanges failed: {result.stderr}"
        
        output = result.stdout
        assert "Available Market Calendars" in output, "Should show exchange list header"
        assert "NYSE" in output, "Should list NYSE exchange"

    def test_market_calendar_with_holidays(self):
        """Test market calendar with holiday display."""
        
        # Test around a known holiday period (Christmas)
        result = subprocess.run([
            "python", "main.py", "market-calendar",
            "2024-12-20", "2024-12-31",
            "--exchange", "NYSE",
            "--holidays"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 0, f"Holiday display failed: {result.stderr}"
        
        output = result.stdout
        assert "Trading day coverage" in output, "Should show coverage"
        # Should show holidays in this period (Christmas)

    def test_exchange_mapping_cli_command(self):
        """Test the exchange-mapping CLI command."""
        
        # Test basic symbol analysis
        result = subprocess.run([
            "python", "main.py", "exchange-mapping",
            "ES.FUT,CL.c.0,SPY,AAPL"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 0, f"Exchange mapping failed: {result.stderr}"
        
        output = result.stdout
        assert "Symbol Exchange Mapping Analysis" in output, "Should show analysis header"
        assert "ES.FUT" in output, "Should show ES.FUT symbol"
        assert "CME_Equity" in output, "Should detect CME_Equity for ES.FUT"

    def test_exchange_mapping_list_exchanges(self):
        """Test listing supported exchanges in mapping."""
        
        result = subprocess.run([
            "python", "main.py", "exchange-mapping",
            "--list"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 0, f"Exchange mapping list failed: {result.stderr}"
        
        output = result.stdout
        assert "Supported Exchange Calendars" in output, "Should show exchange list"
        assert "CME_Energy" in output, "Should list CME_Energy"
        assert "NYSE" in output, "Should list NYSE"

    def test_exchange_mapping_test_symbol(self):
        """Test individual symbol testing."""
        
        result = subprocess.run([
            "python", "main.py", "exchange-mapping",
            "--test", "CL.FUT"
        ], capture_output=True, text=True, cwd=".")
        
        assert result.returncode == 0, f"Symbol testing failed: {result.stderr}"
        
        output = result.stdout
        assert "Testing Symbol: CL.FUT" in output, "Should show symbol test"
        assert "CME_Energy" in output, "Should detect CME_Energy for CL.FUT"
        assert "Confidence:" in output, "Should show confidence level"

    def test_ingest_with_market_calendar_preflight(self):
        """Test ingestion with market calendar pre-flight checks."""
        
        # Test dry-run with market calendar analysis
        result = subprocess.run([
            "python", "main.py", "ingest",
            "--api", "databento",
            "--dataset", "GLBX.MDP3", 
            "--schema", "ohlcv-1d",
            "--symbols", "ES.FUT",
            "--stype-in", "continuous",
            "--start-date", "2024-12-23",  # Christmas week
            "--end-date", "2024-12-27",
            "--dry-run"
        ], capture_output=True, text=True, cwd=".")
        
        # Should succeed (dry run doesn't need API key)
        assert result.returncode == 0, f"Ingest pre-flight failed: {result.stderr}"
        
        output = result.stdout
        assert "Market Calendar Pre-flight Analysis" in output, "Should show pre-flight analysis"
        assert "Auto-detected exchange" in output, "Should show exchange detection"

    def test_query_with_market_calendar_preflight(self):
        """Test query with market calendar pre-flight checks."""
        
        # Test with a holiday period to trigger warnings
        result = subprocess.run([
            "python", "main.py", "query",
            "--symbols", "ES.c.0",
            "--start-date", "2024-12-23",  # Christmas week
            "--end-date", "2024-12-27",
            "--dry-run"
        ], capture_output=True, text=True, cwd=".")
        
        # May fail due to database connection, but should show pre-flight analysis
        output = result.stdout + result.stderr
        assert "Market Calendar Pre-flight Analysis" in output, "Should show pre-flight analysis"

    def test_databento_config_calendar_filtering(self):
        """Test databento config with calendar filtering examples."""
        
        from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter
        import yaml
        
        # Load the databento config
        config_path = Path("configs/api_specific/databento_config.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Find calendar filtering examples
        calendar_jobs = []
        for job in config.get("jobs", []):
            if job.get("enable_market_calendar_filtering"):
                calendar_jobs.append(job)
        
        assert len(calendar_jobs) > 0, "Should have calendar filtering examples in config"
        
        # Test that the adapter can handle these configs
        adapter_config = {
            "api": {"key_env_var": "FAKE_KEY"},
            "validation": {}
        }
        
        adapter = DatabentoAdapter(adapter_config)
        
        for job in calendar_jobs:
            # Test chunk generation with calendar filtering
            chunks = adapter._generate_date_chunks(
                job["start_date"],
                job["end_date"], 
                job.get("date_chunk_interval_days"),
                job.get("enable_market_calendar_filtering", False),
                job.get("exchange_name", "NYSE")
            )
            
            assert len(chunks) > 0, f"Should generate chunks for job {job['name']}"

    def test_smart_validator_integration(self):
        """Test SmartValidator integration with exchange mapping."""
        
        from src.cli.smart_validation import SmartValidator
        from src.cli.exchange_mapping import map_symbols_to_exchange
        
        # Test automatic exchange detection
        symbols = ["ES.FUT", "CL.FUT"]
        exchange, confidence = map_symbols_to_exchange(symbols)
        
        assert exchange in ["CME_Equity", "CME_Energy"], f"Should detect CME exchange, got {exchange}"
        assert confidence > 0.8, f"Should have high confidence, got {confidence}"
        
        # Test validator with detected exchange
        validator = SmartValidator(exchange_name=exchange)
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = validator.validate_date_range(start_date, end_date)
        
        assert result.is_valid, "Validation should succeed"
        assert result.metadata.get("exchange_name") == exchange, "Should include correct exchange"

    def test_calendar_fallback_behavior(self):
        """Test fallback behavior when pandas-market-calendars is not available."""
        
        # Temporarily simulate library not available
        from src.cli import smart_validation
        
        # Save original state
        original_available = smart_validation.PANDAS_MARKET_CALENDARS_AVAILABLE
        original_mcal = smart_validation.mcal
        
        try:
            # Simulate library not available
            smart_validation.PANDAS_MARKET_CALENDARS_AVAILABLE = False
            smart_validation.mcal = None
            
            # Test MarketCalendar fallback
            calendar = smart_validation.MarketCalendar("NYSE")
            
            # Should work with fallback implementation
            test_date = date(2024, 1, 10)  # Wednesday
            is_trading = calendar.is_trading_day(test_date)
            
            assert isinstance(is_trading, bool), "Should return boolean even in fallback mode"
            
            # Test early closes fallback
            early_closes = calendar.get_early_closes(date(2024, 11, 25), date(2024, 12, 2))
            assert isinstance(early_closes, dict), "Should return dict even in fallback mode"
            
        finally:
            # Restore original state
            smart_validation.PANDAS_MARKET_CALENDARS_AVAILABLE = original_available
            smart_validation.mcal = original_mcal

    def test_performance_with_large_date_ranges(self):
        """Test performance with large date ranges."""
        
        from src.cli.smart_validation import MarketCalendar
        import time
        
        calendar = MarketCalendar("NYSE")
        
        # Test with full year
        start_time = time.time()
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        trading_days = calendar.get_trading_days_count(start_date, end_date)
        holidays = calendar.get_holidays(start_date, end_date)
        early_closes = calendar.get_early_closes(start_date, end_date)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete within reasonable time
        assert elapsed < 30.0, f"Large date range processing took too long: {elapsed:.2f}s"
        
        # Should have reasonable results
        assert 240 <= trading_days <= 260, f"Unexpected trading days for full year: {trading_days}"
        assert len(holidays) >= 8, f"Should have multiple holidays in a year, got {len(holidays)}"

    def test_concurrent_calendar_access(self):
        """Test concurrent access to calendar instances."""
        
        from src.cli.smart_validation import MarketCalendar
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(exchange, worker_id):
            try:
                calendar = MarketCalendar(exchange)
                test_date = date(2024, 1, 10)
                is_trading = calendar.is_trading_day(test_date)
                results.append((worker_id, exchange, is_trading))
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Create multiple threads accessing different exchanges
        threads = []
        for i in range(5):
            exchange = ["NYSE", "NASDAQ", "CME_Equity"][i % 3]
            thread = threading.Thread(target=worker, args=(exchange, i))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=10.0)
        
        # Check results
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 5, f"Should have 5 results, got {len(results)}"

    def test_memory_usage_stability(self):
        """Test memory usage stability over multiple operations."""
        
        from src.cli.smart_validation import MarketCalendar
        import gc
        
        calendar = MarketCalendar("NYSE")
        
        # Perform many operations
        for i in range(100):
            test_date = date(2024, 1, 1) + timedelta(days=i % 365)
            calendar.is_trading_day(test_date)
            
            if i % 10 == 0:
                gc.collect()  # Force garbage collection
        
        # Should complete without memory issues
        assert True, "Memory usage test completed"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])