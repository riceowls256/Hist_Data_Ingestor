"""
Tests for Phase 2: LiveStatusDashboard and OperationMonitor components.

Comprehensive test coverage for real-time status monitoring functionality
including dashboard layouts, operation tracking, and system metrics.
"""

import pytest
import json
import tempfile
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cli.progress_utils import (
    LiveStatusDashboard, OperationMonitor, format_duration
)


class TestOperationMonitor:
    """Test suite for OperationMonitor class."""
    
    def setup_method(self):
        """Set up test environment with temporary state directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.temp_dir) / "test_hdi_state"
        self.monitor = OperationMonitor(state_dir=self.state_dir)
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_initialization(self):
        """Test OperationMonitor initialization."""
        assert self.monitor.state_dir == self.state_dir
        assert self.state_dir.exists()
        assert isinstance(self.monitor.operations, dict)
        
    def test_register_operation(self):
        """Test operation registration."""
        config = {
            'description': 'Test operation',
            'total_items': 1000,
            'schema': 'ohlcv-1d'
        }
        
        op_id = self.monitor.register_operation('test_op_1', config)
        
        assert op_id == 'test_op_1'
        assert 'test_op_1' in self.monitor.operations
        
        operation = self.monitor.operations['test_op_1']
        assert operation['id'] == 'test_op_1'
        assert operation['config'] == config
        assert operation['status'] == 'starting'
        assert operation['progress'] == 0
        assert operation['total'] == 1000
        assert operation['pid'] == os.getpid()
        assert isinstance(operation['errors'], list)
        assert len(operation['errors']) == 0
        
        # Check persistence
        operation_file = self.state_dir / "test_op_1.json"
        assert operation_file.exists()
        
    def test_update_operation(self):
        """Test operation updates."""
        # Register operation first
        config = {'description': 'Test operation'}
        self.monitor.register_operation('test_op_1', config)
        
        # Update operation
        self.monitor.update_operation(
            'test_op_1',
            status='running',
            progress=50,
            metrics={'records_processed': 500, 'throughput': 100.5}
        )
        
        operation = self.monitor.operations['test_op_1']
        assert operation['status'] == 'running'
        assert operation['progress'] == 50
        assert operation['metrics']['records_processed'] == 500
        assert operation['metrics']['throughput'] == 100.5
        
        # Test error handling
        self.monitor.update_operation(
            'test_op_1',
            errors=['Connection timeout', 'Retry failed']
        )
        
        assert len(operation['errors']) == 2
        assert 'Connection timeout' in operation['errors']
        
    def test_complete_operation(self):
        """Test operation completion."""
        # Register and run operation
        config = {'description': 'Test operation', 'total_items': 100}
        self.monitor.register_operation('test_op_1', config)
        self.monitor.update_operation('test_op_1', status='running', progress=50)
        
        # Complete operation
        final_metrics = {'total_time': 120.5, 'avg_throughput': 95.2}
        self.monitor.complete_operation('test_op_1', 'completed', final_metrics)
        
        operation = self.monitor.operations['test_op_1']
        assert operation['status'] == 'completed'
        assert operation['progress'] == 100  # Should be set to total
        assert 'end_time' in operation
        assert 'duration_seconds' in operation
        assert operation['metrics']['total_time'] == 120.5
        
    def test_get_active_operations(self):
        """Test active operations filtering."""
        # Register multiple operations with different statuses
        self.monitor.register_operation('op_1', {'description': 'Active op 1'})
        self.monitor.register_operation('op_2', {'description': 'Completed op'})
        self.monitor.register_operation('op_3', {'description': 'Active op 2'})
        
        # Update statuses
        self.monitor.update_operation('op_1', status='running')
        self.monitor.complete_operation('op_2', 'completed')
        self.monitor.update_operation('op_3', status='in_progress')
        
        active_ops = self.monitor.get_active_operations()
        
        # Should only return active operations (running/in_progress)
        active_ids = [op['id'] for op in active_ops]
        assert 'op_1' in active_ids
        assert 'op_3' in active_ids
        assert 'op_2' not in active_ids
        
    def test_get_operation_history(self):
        """Test operation history retrieval."""
        # Create operations with different timestamps
        for i in range(15):
            op_id = f'op_{i}'
            self.monitor.register_operation(op_id, {'description': f'Operation {i}'})
            self.monitor.complete_operation(op_id, 'completed')
            time.sleep(0.001)  # Ensure different timestamps
            
        # Get history with limit
        history = self.monitor.get_operation_history(limit=10)
        
        assert len(history) == 10
        # Should be sorted by start time, most recent first
        for i in range(len(history) - 1):
            assert history[i]['start_time'] >= history[i + 1]['start_time']
            
    def test_cleanup_old_operations(self):
        """Test cleanup of old operations."""
        # Create old operation (simulate by modifying end_time)
        self.monitor.register_operation('old_op', {'description': 'Old operation'})
        self.monitor.complete_operation('old_op', 'completed')
        
        # Manually set old end_time
        old_time = (datetime.now() - timedelta(days=10)).isoformat()
        self.monitor.operations['old_op']['end_time'] = old_time
        self.monitor._persist_operation('old_op', self.monitor.operations['old_op'])
        
        # Create recent operation
        self.monitor.register_operation('recent_op', {'description': 'Recent operation'})
        self.monitor.complete_operation('recent_op', 'completed')
        
        # Cleanup operations older than 7 days
        self.monitor.cleanup_old_operations(days_old=7)
        
        assert 'old_op' not in self.monitor.operations
        assert 'recent_op' in self.monitor.operations
        
        # Check file was removed
        old_file = self.state_dir / "old_op.json"
        assert not old_file.exists()
        
    def test_persistence_and_loading(self):
        """Test operation persistence and loading across instances."""
        # Create operations
        self.monitor.register_operation('op_1', {'description': 'Persistent op 1'})
        self.monitor.register_operation('op_2', {'description': 'Persistent op 2'})
        self.monitor.update_operation('op_1', status='running', progress=25)
        
        # Create new monitor instance (simulates restart)
        new_monitor = OperationMonitor(state_dir=self.state_dir)
        
        assert len(new_monitor.operations) == 2
        assert 'op_1' in new_monitor.operations
        assert 'op_2' in new_monitor.operations
        assert new_monitor.operations['op_1']['status'] == 'running'
        assert new_monitor.operations['op_1']['progress'] == 25
        
    @patch('psutil.pid_exists')
    def test_dead_process_detection(self, mock_pid_exists):
        """Test detection of dead processes."""
        # Mock process as not existing
        mock_pid_exists.return_value = False
        
        # Register operation with fake PID
        config = {'description': 'Dead process operation'}
        self.monitor.register_operation('dead_op', config)
        self.monitor.update_operation('dead_op', status='running')
        
        # Get active operations (should detect dead process)
        active_ops = self.monitor.get_active_operations()
        
        assert len(active_ops) == 0  # Should be empty
        assert self.monitor.operations['dead_op']['status'] == 'failed'
        assert 'Process terminated unexpectedly' in self.monitor.operations['dead_op']['errors']


class TestLiveStatusDashboard:
    """Test suite for LiveStatusDashboard class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.temp_dir) / "test_hdi_state"
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    @patch('cli.progress_utils.OperationMonitor')
    def test_initialization(self, mock_monitor_class):
        """Test LiveStatusDashboard initialization."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        dashboard = LiveStatusDashboard(
            title="Test Dashboard",
            show_system_metrics=True,
            show_operation_queue=True,
            refresh_rate=1.0
        )
        
        assert dashboard.title == "Test Dashboard"
        assert dashboard.show_system_metrics is True
        assert dashboard.show_operation_queue is True
        assert dashboard.refresh_rate == 1.0
        assert dashboard.current_status == "Ready"
        assert dashboard.current_status_style == "cyan"
        
    @patch('cli.progress_utils.OperationMonitor')
    def test_layout_creation(self, mock_monitor_class):
        """Test dashboard layout creation."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        # Test with full features
        dashboard = LiveStatusDashboard(
            show_system_metrics=True,
            show_operation_queue=True
        )
        
        layout = dashboard._create_layout()
        assert layout is not None
        
        # Test with minimal features
        dashboard_minimal = LiveStatusDashboard(
            show_system_metrics=False,
            show_operation_queue=False
        )
        
        layout_minimal = dashboard_minimal._create_layout()
        assert layout_minimal is not None
        
    @patch('cli.progress_utils.OperationMonitor')
    def test_status_updates(self, mock_monitor_class):
        """Test status updates."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        dashboard = LiveStatusDashboard()
        
        # Test status update
        dashboard.update_status("Processing data", "yellow")
        assert dashboard.current_status == "Processing data"
        assert dashboard.current_status_style == "yellow"
        
    @patch('cli.progress_utils.OperationMonitor')
    def test_operation_management(self, mock_monitor_class):
        """Test operation addition and completion."""
        mock_monitor = Mock()
        mock_monitor.register_operation.return_value = 'test_op_1'
        mock_monitor.get_active_operations.return_value = []
        mock_monitor.get_operation_history.return_value = []
        mock_monitor_class.return_value = mock_monitor
        
        dashboard = LiveStatusDashboard()
        
        # Test adding operation
        config = {'description': 'Test operation', 'total_items': 1000}
        op_id = dashboard.add_operation('test_op_1', config)
        
        assert op_id == 'test_op_1'
        mock_monitor.register_operation.assert_called_once_with('test_op_1', config)
        
        # Test updating operation progress
        dashboard.update_operation_progress('test_op_1', progress=50, status='running')
        mock_monitor.update_operation.assert_called_once_with('test_op_1', progress=50, status='running')
        
        # Test completing operation
        final_metrics = {'duration': 120}
        dashboard.complete_operation('test_op_1', 'completed', final_metrics)
        mock_monitor.complete_operation.assert_called_once_with('test_op_1', 'completed', final_metrics)
        
    @patch('cli.progress_utils.OperationMonitor')
    @patch('psutil.Process')
    def test_system_metrics_collection(self, mock_process_class, mock_monitor_class):
        """Test system metrics collection."""
        # Mock psutil Process
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 45.2
        mock_memory_info = Mock()
        mock_memory_info.rss = 512 * 1024 * 1024  # 512 MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process_class.return_value = mock_process
        
        # Mock psutil net_io_counters
        with patch('psutil.net_io_counters') as mock_net_io:
            mock_net_stats = Mock()
            mock_net_stats.bytes_sent = 1024 * 1024  # 1 MB
            mock_net_stats.bytes_recv = 2048 * 1024  # 2 MB
            mock_net_io.return_value = mock_net_stats
            
            mock_monitor = Mock()
            mock_monitor_class.return_value = mock_monitor
            
            dashboard = LiveStatusDashboard()
            dashboard._collect_system_metrics()
            
            # Check metrics were collected
            assert dashboard.system_metrics['cpu_percent'] == 45.2
            assert dashboard.system_metrics['memory_mb'] == 512.0
            
    @patch('cli.progress_utils.OperationMonitor')
    def test_operations_panel_creation(self, mock_monitor_class):
        """Test operations panel creation with mock data."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        # Mock active operations
        mock_operations = [
            {
                'id': 'op_1',
                'config': {'description': 'OHLCV ingestion for ES.c.0'},
                'status': 'running',
                'progress': 750,
                'total': 1000,
                'start_time': datetime.now().isoformat(),
                'metrics': {
                    'records_processed': 7500,
                    'throughput': 125.5,
                    'errors': 2
                }
            },
            {
                'id': 'op_2', 
                'config': {'description': 'Trades data processing'},
                'status': 'in_progress',
                'progress': 250,
                'total': 500,
                'start_time': (datetime.now() - timedelta(minutes=5)).isoformat(),
                'metrics': {
                    'records_processed': 2500
                }
            }
        ]
        
        dashboard = LiveStatusDashboard()
        dashboard.current_operations = mock_operations
        
        panel = dashboard._create_operations_panel()
        assert panel is not None
        
        # Test with no operations
        dashboard.current_operations = []
        dashboard._update_main_panel()  # Should not raise exception


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_format_duration(self):
        """Test duration formatting function."""
        assert format_duration(30) == "30.0s"
        assert format_duration(90) == "1m 30s"
        assert format_duration(3661) == "1h 1m"
        assert format_duration(7320) == "2h 2m"
        
    def test_format_duration_edge_cases(self):
        """Test edge cases for duration formatting."""
        assert format_duration(0) == "0.0s"
        assert format_duration(59.9) == "59.9s"
        assert format_duration(60) == "1m 0s"
        assert format_duration(3600) == "1h 0m"


class TestIntegration:
    """Integration tests for Phase 2 components."""
    
    def setup_method(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.temp_dir) / "test_hdi_state"
        
    def teardown_method(self):
        """Clean up integration test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_end_to_end_operation_lifecycle(self):
        """Test complete operation lifecycle through monitor and dashboard."""
        # Create monitor and dashboard
        monitor = OperationMonitor(state_dir=self.state_dir)
        
        with patch('cli.progress_utils.OperationMonitor') as mock_monitor_class:
            mock_monitor_class.return_value = monitor
            dashboard = LiveStatusDashboard()
            
            # Register operation
            config = {
                'description': 'E2E Test Operation',
                'total_items': 1000,
                'schema': 'ohlcv-1d'
            }
            
            op_id = dashboard.add_operation('e2e_test_op', config)
            assert op_id == 'e2e_test_op'
            
            # Verify operation is active
            active_ops = monitor.get_active_operations()
            assert len(active_ops) == 1
            assert active_ops[0]['id'] == 'e2e_test_op'
            
            # Update progress multiple times
            for progress in [100, 250, 500, 750, 1000]:
                dashboard.update_operation_progress(
                    'e2e_test_op',
                    progress=progress,
                    status='running',
                    metrics={
                        'records_processed': progress * 10,
                        'throughput': 50 + (progress / 10)
                    }
                )
                
            # Complete operation
            final_metrics = {
                'total_records': 10000,
                'avg_throughput': 125.5,
                'duration_seconds': 80.2
            }
            
            dashboard.complete_operation('e2e_test_op', 'completed', final_metrics)
            
            # Verify completion
            operation = monitor.operations['e2e_test_op']
            assert operation['status'] == 'completed'
            assert operation['progress'] == 1000
            assert 'duration_seconds' in operation
            assert operation['metrics']['avg_throughput'] == 125.5
            
            # Verify no longer in active operations
            active_ops = monitor.get_active_operations()
            assert len(active_ops) == 0
            
            # Verify in history
            history = monitor.get_operation_history()
            assert len(history) == 1
            assert history[0]['id'] == 'e2e_test_op'
            
    def test_persistence_across_sessions(self):
        """Test that operations persist across monitor sessions."""
        # Create first monitor session
        monitor1 = OperationMonitor(state_dir=self.state_dir)
        
        # Register multiple operations
        for i in range(3):
            config = {'description': f'Persistent operation {i}'}
            monitor1.register_operation(f'persist_op_{i}', config)
            monitor1.update_operation(f'persist_op_{i}', status='running', progress=i * 100)
            
        # Complete one operation
        monitor1.complete_operation('persist_op_0', 'completed')
        
        # Create second monitor session (simulates restart)
        monitor2 = OperationMonitor(state_dir=self.state_dir)
        
        # Verify all operations loaded
        assert len(monitor2.operations) == 3
        for i in range(3):
            assert f'persist_op_{i}' in monitor2.operations
            
        assert monitor2.operations['persist_op_0']['status'] == 'completed'
        assert monitor2.operations['persist_op_1']['status'] == 'running'
        assert monitor2.operations['persist_op_1']['progress'] == 100
        
        # Verify file persistence
        for i in range(3):
            op_file = self.state_dir / f"persist_op_{i}.json"
            assert op_file.exists()
            
            with open(op_file) as f:
                data = json.load(f)
                assert data['id'] == f'persist_op_{i}'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])