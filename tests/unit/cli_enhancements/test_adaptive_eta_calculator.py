"""
Test suite for AdaptiveETACalculator implementation.

This module tests the Phase 1.2 implementation of adaptive ETA calculation
with historical performance tracking.
"""

import pytest
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile

from cli.progress_utils import AdaptiveETACalculator, AdaptiveETAColumn


class TestAdaptiveETACalculator:
    """Test the AdaptiveETACalculator functionality."""

    def test_initialization(self):
        """Test calculator initialization."""
        calc = AdaptiveETACalculator(window_size=50)
        
        assert calc.window_size == 50
        assert len(calc.throughput_history) == 0
        assert len(calc.operation_times) == 0
        assert calc.current_operation_start is None
        assert calc.items_at_start == 0

    def test_throughput_tracking(self):
        """Test throughput history tracking."""
        calc = AdaptiveETACalculator(window_size=5)
        
        # Add some throughput data
        calc.update("test_op", 100, 10.0)  # 10 items/sec
        calc.update("test_op", 200, 10.0)  # 20 items/sec
        calc.update("test_op", 150, 10.0)  # 15 items/sec
        
        assert len(calc.throughput_history) == 3
        assert 10.0 in calc.throughput_history
        assert 20.0 in calc.throughput_history
        assert 15.0 in calc.throughput_history

    def test_window_size_limit(self):
        """Test that window size is respected."""
        calc = AdaptiveETACalculator(window_size=3)
        
        # Add more than window size
        for i in range(5):
            calc.update("test_op", 100, 10.0)
            
        assert len(calc.throughput_history) == 3  # Limited by window size

    def test_operation_specific_tracking(self):
        """Test operation-specific timing tracking."""
        calc = AdaptiveETACalculator()
        
        # Track different operations
        calc.update("op1", 100, 10.0)
        calc.update("op2", 200, 5.0)
        calc.update("op1", 150, 15.0)
        
        assert "op1" in calc.operation_times
        assert "op2" in calc.operation_times
        assert len(calc.operation_times["op1"]) == 2
        assert len(calc.operation_times["op2"]) == 1

    def test_estimate_with_current_operation(self):
        """Test ETA estimation using current operation data."""
        calc = AdaptiveETACalculator()
        
        # Simulate current operation progress
        eta = calc.estimate_remaining_time(
            "test_op",
            items_remaining=500,
            items_completed=100,
            time_elapsed=10.0  # 10 items/sec
        )
        
        assert eta is not None
        assert abs(eta - 50.0) < 1.0  # Should be ~50 seconds

    def test_estimate_with_historical_data(self):
        """Test ETA estimation using historical data."""
        calc = AdaptiveETACalculator()
        
        # Add historical data
        calc.update("test_op", 100, 10.0)  # 10 items/sec
        calc.update("test_op", 100, 10.0)  # 10 items/sec
        calc.update("test_op", 100, 10.0)  # 10 items/sec
        
        # Estimate without current operation data
        eta = calc.estimate_remaining_time(
            "test_op",
            items_remaining=500,
            items_completed=0,
            time_elapsed=0
        )
        
        assert eta is not None
        assert abs(eta - 50.0) < 1.0  # Should be ~50 seconds

    def test_blended_estimate(self):
        """Test blended ETA using current and historical data."""
        calc = AdaptiveETACalculator()
        
        # Add historical data (slower)
        for _ in range(5):
            calc.update("test_op", 100, 20.0)  # 5 items/sec
        
        # Current operation is faster
        eta = calc.estimate_remaining_time(
            "test_op",
            items_remaining=1000,
            items_completed=200,
            time_elapsed=10.0  # 20 items/sec currently
        )
        
        # Should blend 70% current (20/sec) + 30% historical (5/sec)
        # Blended = 0.7 * 20 + 0.3 * 5 = 15.5 items/sec
        # ETA = 1000 / 15.5 ≈ 64.5 seconds
        assert eta is not None
        assert 60 < eta < 70

    def test_confidence_levels(self):
        """Test confidence level calculation."""
        calc = AdaptiveETACalculator()
        
        # No data
        assert calc.get_confidence_level("unknown_op") == "none"
        
        # Add some data
        for i in range(25):
            calc.update("test_op", 100, 10.0)
            
        assert calc.get_confidence_level("test_op") == "high"
        
        # Medium confidence
        calc2 = AdaptiveETACalculator()
        for i in range(7):
            calc2.update("test_op", 100, 10.0)
        assert calc2.get_confidence_level("test_op") == "medium"
        
        # Low confidence
        calc3 = AdaptiveETACalculator()
        calc3.update("test_op", 100, 10.0)
        assert calc3.get_confidence_level("test_op") == "low"

    def test_start_operation_tracking(self):
        """Test operation start tracking."""
        calc = AdaptiveETACalculator()
        
        with patch('time.time', return_value=1000.0):
            calc.start_operation("test_op", items_completed=50)
            
        assert calc.current_operation_start == 1000.0
        assert calc.items_at_start == 50
        
        # Test update using start tracking
        with patch('time.time', return_value=1010.0):
            calc.update("test_op", 150, None)  # 100 items in 10 seconds
            
        assert len(calc.throughput_history) == 1
        assert calc.throughput_history[0] == 10.0  # 10 items/sec

    def test_persistence(self):
        """Test history persistence to disk."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = Path(f.name)
            
        try:
            # Create calculator with custom history file
            calc1 = AdaptiveETACalculator(history_file=temp_file)
            
            # Add some data
            calc1.update("op1", 100, 10.0)
            calc1.update("op2", 200, 20.0)
            calc1._save_history()
            
            # Create new calculator and load history
            calc2 = AdaptiveETACalculator(history_file=temp_file)
            
            # Verify data was loaded
            assert "op1" in calc2.operation_times
            assert "op2" in calc2.operation_times
            assert len(calc2.throughput_history) > 0
            
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_median_based_fallback(self):
        """Test median-based calculation for stability."""
        calc = AdaptiveETACalculator()
        
        # Add varied throughput data
        throughputs = [5, 10, 15, 20, 100]  # 100 is an outlier
        for tp in throughputs:
            calc.update("generic", int(tp * 10), 10.0)
            
        # Estimate should use median for stability
        eta = calc.estimate_remaining_time(
            "unknown_op",  # Force fallback to general history
            items_remaining=150,
            items_completed=0,
            time_elapsed=0
        )
        
        # Median of recent values should be around 15 items/sec
        # So 150 items / 15 items/sec = 10 seconds
        assert eta is not None
        assert 8 < eta < 12  # Should be close to 10


class TestAdaptiveETAColumn:
    """Test the AdaptiveETAColumn integration."""

    def test_column_initialization(self):
        """Test column initialization."""
        calc = AdaptiveETACalculator()
        column = AdaptiveETAColumn(calculator=calc)
        
        assert column.calculator is calc
        assert len(column.last_update_time) == 0
        assert len(column.last_completed) == 0

    def test_render_with_no_data(self):
        """Test rendering with no ETA data."""
        column = AdaptiveETAColumn()
        
        # Mock task
        task = Mock()
        task.total = 100
        task.completed = 0
        task.started = time.time()
        task.fields = {}
        task.time_remaining = None
        
        result = column.render(task)
        assert result.plain == "--:--"

    def test_render_with_estimate(self):
        """Test rendering with ETA estimate."""
        calc = AdaptiveETACalculator()
        # Pre-populate with data
        for _ in range(10):
            calc.update("test_op", 100, 10.0)  # 10 items/sec
            
        column = AdaptiveETAColumn(calculator=calc)
        
        # Mock task
        task = Mock()
        task.total = 1000
        task.completed = 500
        task.started = time.time() - 50  # 50 seconds ago
        task.fields = {'operation_type': 'test_op'}
        task.time_remaining = None
        
        result = column.render(task)
        # Should show ~50s remaining
        assert "50s" in result.plain or "49s" in result.plain or "51s" in result.plain

    def test_confidence_indicators(self):
        """Test confidence level indicators in output."""
        calc = AdaptiveETACalculator()
        column = AdaptiveETAColumn(calculator=calc)
        
        # Mock task
        task = Mock()
        task.total = 1000
        task.completed = 100
        task.started = time.time() - 10
        task.fields = {'operation_type': 'new_op'}
        task.time_remaining = None
        
        # Low confidence - should show ? prefix
        calc.update("new_op", 100, 10.0)  # Just one sample
        result = column.render(task)
        assert result.plain.startswith("?") or result.plain.startswith("~")

    def test_operation_type_tracking(self):
        """Test that operation types are properly tracked."""
        column = AdaptiveETAColumn()
        
        # Mock tasks for different operations
        task1 = Mock()
        task1.total = 100
        task1.completed = 50
        task1.started = time.time()
        task1.fields = {'operation_type': 'databento_ohlcv'}
        task1.time_remaining = None
        
        task2 = Mock() 
        task2.total = 100
        task2.completed = 50
        task2.started = time.time()
        task2.fields = {'operation_type': 'databento_trades'}
        task2.time_remaining = None
        
        # Render both
        column.render(task1)
        column.render(task2)
        
        # Both operations should be tracked
        assert id(task1) in column.last_update_time
        assert id(task2) in column.last_update_time