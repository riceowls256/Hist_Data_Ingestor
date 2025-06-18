"""
Tests for ThrottledProgressUpdater and StreamingProgressTracker classes.

Tests the throttling behavior, adaptive intervals, and memory efficiency
of the Phase 5 progress tracking enhancements.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json

from src.cli.progress_utils import (
    ThrottledProgressUpdater, 
    StreamingProgressTracker,
    EnhancedProgress
)


class TestThrottledProgressUpdater:
    """Test suite for ThrottledProgressUpdater."""
    
    def test_initialization(self):
        """Test throttler initialization with default parameters."""
        throttler = ThrottledProgressUpdater()
        
        assert throttler.min_interval == 0.1
        assert throttler.max_interval == 1.0
        assert throttler.adaptive is True
        assert throttler.max_queue_size == 1000
        assert throttler.running is False
        assert throttler.progress_instance is None
        assert throttler.update_method == "update_main"
        
    def test_initialization_with_custom_params(self):
        """Test throttler initialization with custom parameters."""
        throttler = ThrottledProgressUpdater(
            min_interval=0.05,
            max_interval=2.0,
            adaptive=False,
            max_queue_size=500
        )
        
        assert throttler.min_interval == 0.05
        assert throttler.max_interval == 2.0
        assert throttler.adaptive is False
        assert throttler.max_queue_size == 500
        
    def test_set_target(self):
        """Test setting target progress instance."""
        throttler = ThrottledProgressUpdater()
        mock_progress = Mock()
        
        throttler.set_target(mock_progress, "custom_update")
        
        assert throttler.progress_instance == mock_progress
        assert throttler.update_method == "custom_update"
        
    def test_start_stop_lifecycle(self):
        """Test starting and stopping the throttler."""
        throttler = ThrottledProgressUpdater()
        
        # Initially not running
        assert not throttler.running
        assert throttler.update_thread is None
        
        # Start throttler
        throttler.start()
        assert throttler.running
        assert throttler.update_thread is not None
        assert throttler.update_thread.is_alive()
        
        # Stop throttler
        throttler.stop()
        assert not throttler.running
        
        # Give thread time to finish
        time.sleep(0.2)
        assert not throttler.update_thread.is_alive()
        
    def test_update_queuing(self):
        """Test that updates are queued correctly."""
        throttler = ThrottledProgressUpdater(min_interval=0.05)
        mock_progress = Mock()
        mock_progress._direct_update_main = Mock()
        
        throttler.set_target(mock_progress)
        throttler.start()
        
        try:
            # Send multiple rapid updates
            for i in range(5):
                throttler.update("main", completed=i * 10, total=100)
                time.sleep(0.01)  # Very fast updates
            
            # Give throttler time to process
            time.sleep(0.2)
            
            # Should have called the update method (possibly throttled)
            assert mock_progress._direct_update_main.called
            
        finally:
            throttler.stop()
            
    def test_adaptive_interval_calculation(self):
        """Test adaptive interval calculation based on update frequency."""
        throttler = ThrottledProgressUpdater(adaptive=True)
        
        # No history - should return min interval
        interval = throttler._calculate_update_interval()
        assert interval == throttler.min_interval
        
        # Add some update frequency history
        current_time = time.time()
        for i in range(10):
            throttler.update_frequency_history.append(current_time + i * 0.01)
            
        # Should calculate adaptive interval
        interval = throttler._calculate_update_interval()
        assert isinstance(interval, float)
        assert throttler.min_interval <= interval <= throttler.max_interval
        
    def test_non_adaptive_interval(self):
        """Test that non-adaptive mode always returns min interval."""
        throttler = ThrottledProgressUpdater(adaptive=False, min_interval=0.2)
        
        # Add update history that would normally increase interval
        current_time = time.time()
        for i in range(50):
            throttler.update_frequency_history.append(current_time + i * 0.001)
            
        interval = throttler._calculate_update_interval()
        assert interval == 0.2  # Should always be min_interval
        
    def test_context_manager(self):
        """Test using throttler as context manager."""
        throttler = ThrottledProgressUpdater()
        mock_progress = Mock()
        mock_progress._direct_update_main = Mock()
        
        throttler.set_target(mock_progress)
        
        with throttler:
            assert throttler.running
            throttler.update("main", completed=50, total=100)
            time.sleep(0.1)
            
        # Should be stopped after context exit
        assert not throttler.running
        
    def test_get_stats(self):
        """Test getting throttling statistics."""
        throttler = ThrottledProgressUpdater(min_interval=0.1, max_interval=0.5)
        
        stats = throttler.get_stats()
        
        assert 'running' in stats
        assert 'pending_updates' in stats
        assert 'min_interval' in stats
        assert 'max_interval' in stats
        assert 'adaptive' in stats
        assert 'current_interval' in stats
        
        assert stats['running'] is False
        assert stats['min_interval'] == 0.1
        assert stats['max_interval'] == 0.5
        assert stats['adaptive'] is True
        
    def test_flush_updates_without_target(self):
        """Test that flush_updates handles missing target gracefully."""
        throttler = ThrottledProgressUpdater()
        throttler.pending_updates = {"main": {"completed": 50}}
        
        # Should not raise exception
        throttler._flush_updates()
        assert len(throttler.pending_updates) == 0
        
    def test_update_frequency_tracking(self):
        """Test that update frequency is tracked correctly."""
        throttler = ThrottledProgressUpdater()
        
        # Initially empty
        assert len(throttler.update_frequency_history) == 0
        
        # Add some updates
        for i in range(5):
            throttler.update("main", completed=i * 10)
            time.sleep(0.01)
            
        # Should have tracked update times
        assert len(throttler.update_frequency_history) == 5
        
    def test_high_frequency_update_handling(self):
        """Test handling of very high frequency updates."""
        throttler = ThrottledProgressUpdater(min_interval=0.01, adaptive=True)
        mock_progress = Mock()
        mock_progress._direct_update_main = Mock()
        
        throttler.set_target(mock_progress)
        throttler.start()
        
        try:
            # Send 100 rapid updates
            for i in range(100):
                throttler.update("main", completed=i, total=100)
                
            # Give time for processing
            time.sleep(0.2)
            
            # Should have throttled the updates (fewer actual calls than requested)
            actual_calls = mock_progress._direct_update_main.call_count
            assert actual_calls < 100  # Should be throttled
            assert actual_calls > 0    # But some updates should have gone through
            
        finally:
            throttler.stop()


class TestStreamingProgressTracker:
    """Test suite for StreamingProgressTracker."""
    
    def test_initialization(self):
        """Test tracker initialization."""
        tracker = StreamingProgressTracker(max_history=500, checkpoint_interval=50)
        
        assert tracker.max_history == 500
        assert tracker.checkpoint_interval == 50
        assert tracker.compression_enabled is True
        assert len(tracker.metrics_buffer) == 0
        assert len(tracker.checkpoints) == 0
        assert tracker.total_processed == 0
        
    def test_record_metric_compressed(self):
        """Test recording metrics with compression enabled."""
        tracker = StreamingProgressTracker(max_history=100)
        
        # Record some metrics
        tracker.record_metric("throughput", 1500.123456, metadata={"symbol": "ES.c.0"})
        tracker.record_metric("error_rate", 0.05)
        
        assert len(tracker.metrics_buffer) == 2
        
        # Check compression
        metric = tracker.metrics_buffer[0]
        assert 't' in metric  # Compressed timestamp
        assert 'v' in metric  # Compressed value
        assert 'm' in metric  # Compressed type
        assert metric['v'] == 1500.123  # Precision limited
        assert metric['m'] == "throughp"  # Type truncated
        
    def test_record_metric_uncompressed(self):
        """Test recording metrics without compression."""
        tracker = StreamingProgressTracker()
        tracker.compression_enabled = False
        
        tracker.record_metric("throughput", 1500.123456, metadata={"symbol": "ES.c.0"})
        
        metric = tracker.metrics_buffer[0]
        assert 'timestamp' in metric
        assert 'value' in metric
        assert 'type' in metric
        assert 'metadata' in metric
        assert metric['value'] == 1500.123456
        assert metric['type'] == "throughput"
        
    def test_circular_buffer_behavior(self):
        """Test that metrics buffer respects max size."""
        tracker = StreamingProgressTracker(max_history=5)
        
        # Add more metrics than max_history
        for i in range(10):
            tracker.record_metric("test", i)
            
        # Should only keep the last 5
        assert len(tracker.metrics_buffer) == 5
        
        # Check that it kept the most recent ones
        values = [m['v'] for m in tracker.metrics_buffer]
        assert values == [5, 6, 7, 8, 9]
        
    def test_automatic_checkpointing(self):
        """Test automatic checkpoint creation."""
        tracker = StreamingProgressTracker(checkpoint_interval=3)
        
        # Record metrics to trigger checkpoints
        for i in range(10):
            tracker.record_metric("test", i)
            
        # Should have created checkpoints
        expected_checkpoints = 10 // 3  # 3 checkpoints
        assert len(tracker.checkpoints) == expected_checkpoints
        
        # Check checkpoint names
        checkpoint_names = list(tracker.checkpoints.keys())
        assert "auto_1" in checkpoint_names
        assert "auto_2" in checkpoint_names
        assert "auto_3" in checkpoint_names
        
    def test_manual_checkpoint_creation(self):
        """Test manual checkpoint creation."""
        tracker = StreamingProgressTracker()
        tracker.total_processed = 1000
        
        custom_data = {"operation": "backfill", "symbols": ["ES.c.0"]}
        tracker.create_checkpoint("manual_test", custom_data)
        
        assert "manual_test" in tracker.checkpoints
        checkpoint = tracker.checkpoints["manual_test"]
        
        assert checkpoint['total_processed'] == 1000
        assert checkpoint['custom'] == custom_data
        assert 'timestamp' in checkpoint
        assert 'current_metrics' in checkpoint
        
    def test_checkpoint_cleanup(self):
        """Test that old checkpoints are cleaned up."""
        tracker = StreamingProgressTracker()
        
        # Create more than 20 checkpoints
        for i in range(25):
            tracker.create_checkpoint(f"test_{i}")
            time.sleep(0.001)  # Ensure different timestamps
            
        # Should only keep 20 most recent
        assert len(tracker.checkpoints) == 20
        
        # Should have kept the most recent ones
        checkpoint_names = list(tracker.checkpoints.keys())
        assert "test_24" in checkpoint_names
        assert "test_23" in checkpoint_names
        assert "test_4" not in checkpoint_names  # Old ones removed
        
    def test_get_current_metrics(self):
        """Test getting current aggregated metrics."""
        tracker = StreamingProgressTracker()
        tracker.total_processed = 5000
        
        # Add some throughput data
        current_time = time.time()
        tracker.throughput_buffer.extend([
            (current_time - 30, 1000),
            (current_time - 20, 1200),
            (current_time - 10, 1100)
        ])
        
        # Add some error data
        tracker.error_buffer.extend([
            {'time': current_time - 100, 'value': 1, 'type': 'validation_error'},
            {'time': current_time - 50, 'value': 1, 'type': 'network_error'}
        ])
        
        metrics = tracker.get_current_metrics()
        
        assert 'elapsed_time' in metrics
        assert 'total_processed' in metrics
        assert 'recent_throughput' in metrics
        assert 'error_rate' in metrics
        assert 'memory_usage_mb' in metrics
        
        assert metrics['total_processed'] == 5000
        assert metrics['recent_throughput'] > 0
        
    def test_get_streaming_stats(self):
        """Test getting streaming statistics for a time window."""
        tracker = StreamingProgressTracker()
        current_time = time.time()
        
        # Add metrics across different time periods
        for i in range(10):
            timestamp = current_time - (10 - i) * 10  # 10 seconds apart
            tracker.record_metric("throughput", 1000 + i * 100, timestamp)
            
        # Get stats for 60-second window
        stats = tracker.get_streaming_stats(window_seconds=60)
        
        assert stats['window_seconds'] == 60
        assert stats['metrics_count'] > 0
        assert 'throughp_count' in stats  # Compressed metric name
        assert 'throughp_avg' in stats
        assert 'throughp_min' in stats
        assert 'throughp_max' in stats
        
    def test_memory_usage_estimation(self):
        """Test memory usage estimation."""
        tracker = StreamingProgressTracker(max_history=1000)
        
        # Add various data
        for i in range(100):
            tracker.record_metric("throughput", i)
            
        memory_mb = tracker._estimate_memory_usage()
        
        assert isinstance(memory_mb, float)
        assert memory_mb > 0
        assert memory_mb < 10  # Should be reasonable for test data
        
    def test_clear_history(self):
        """Test clearing old metrics to free memory."""
        tracker = StreamingProgressTracker()
        current_time = time.time()
        
        # Add metrics with different timestamps
        for i in range(10):
            timestamp = current_time - (10 - i) * 60  # 1 minute apart
            tracker.record_metric("test", i, timestamp)
            
        # Clear history keeping only last 5 minutes
        tracker.clear_history(keep_recent_seconds=300)
        
        # Should have fewer metrics
        assert len(tracker.metrics_buffer) < 10
        
        # Should have kept only recent metrics
        for metric in tracker.metrics_buffer:
            if tracker.compression_enabled:
                metric_time = tracker.start_time + (metric['t'] / 1000)
            else:
                metric_time = metric['timestamp']
            assert (current_time - metric_time) <= 300
            
    def test_export_metrics_json(self):
        """Test exporting metrics to JSON format."""
        tracker = StreamingProgressTracker()
        tracker.total_processed = 1000
        
        # Add some test data
        for i in range(5):
            tracker.record_metric("test", i)
            
        tracker.create_checkpoint("test_checkpoint")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
            
        try:
            tracker.export_metrics(temp_path, format="json", include_checkpoints=True)
            
            # Verify export
            assert temp_path.exists()
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
                
            assert 'metadata' in data
            assert 'metrics' in data
            assert 'checkpoints' in data
            assert 'current_stats' in data
            
            assert data['metadata']['total_processed'] == 1000
            assert len(data['metrics']) == 5
            assert 'test_checkpoint' in data['checkpoints']
            
        finally:
            if temp_path.exists():
                temp_path.unlink()
                
    def test_export_metrics_csv(self):
        """Test exporting metrics to CSV format."""
        tracker = StreamingProgressTracker()
        
        # Add some test data
        for i in range(3):
            tracker.record_metric("test_metric", i * 100)
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = Path(f.name)
            
        try:
            tracker.export_metrics(temp_path, format="csv")
            
            # Verify export
            assert temp_path.exists()
            
            with open(temp_path, 'r') as f:
                lines = f.readlines()
                
            # Should have header + data rows
            assert len(lines) == 4  # 1 header + 3 data rows
            assert 'timestamp_ms' in lines[0]  # Compressed format header
            assert 'value' in lines[0]
            assert 'type' in lines[0]
            
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestEnhancedProgressWithThrottling:
    """Test EnhancedProgress with throttling enabled."""
    
    def test_throttling_initialization(self):
        """Test EnhancedProgress initialization with throttling."""
        progress = EnhancedProgress(
            "Test progress",
            use_throttling=True,
            throttle_min_interval=0.05
        )
        
        assert progress.use_throttling is True
        assert progress.throttler is not None
        assert progress.throttler.min_interval == 0.05
        
    def test_throttling_disabled_by_default(self):
        """Test that throttling is disabled by default."""
        progress = EnhancedProgress("Test progress")
        
        assert progress.use_throttling is False
        assert progress.throttler is None
        
    def test_context_manager_with_throttling(self):
        """Test context manager behavior with throttling enabled."""
        progress = EnhancedProgress(
            "Test progress",
            use_throttling=True,
            throttle_min_interval=0.01
        )
        
        with progress:
            assert progress.throttler.running
            
            # Test updates go through throttler
            progress.update_main(completed=50, total=100)
            time.sleep(0.05)
            
        # Throttler should be stopped after context exit
        assert not progress.throttler.running
        
    def test_direct_update_methods(self):
        """Test that direct update methods work correctly."""
        progress = EnhancedProgress("Test progress", use_throttling=True)
        
        with progress:
            # Test direct main update
            progress._direct_update_main(completed=25, total=100)
            
            # Test direct subtask update
            task_name = progress.add_subtask("test_task", "Test subtask", total=50)
            progress._direct_update_subtask(task_name, completed=10)
            
            # Should not raise exceptions
            assert True
            
    def test_throttled_vs_direct_updates(self):
        """Test difference between throttled and direct updates."""
        progress = EnhancedProgress("Test progress", use_throttling=True)
        
        with patch.object(progress.progress, 'update') as mock_update:
            with progress:
                # Throttled update should go through throttler
                progress.update_main(completed=50, total=100)
                
                # Give throttler time to process
                time.sleep(0.1)
                
                # Direct update should call immediately
                progress._direct_update_main(completed=75, total=100)
                
                # Direct call should have happened immediately
                mock_update.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])