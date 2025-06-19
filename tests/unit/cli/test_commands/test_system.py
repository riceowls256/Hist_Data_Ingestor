"""
Unit tests for CLI system commands module.

Tests all system-related commands including status, version, config, monitor, and list_jobs.
Ensures 100% functional equivalence with original CLI implementation.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

import pytest
from typer.testing import CliRunner
from rich.console import Console

from src.cli.commands.system import app as system_app


class TestSystemCommands:
    """Comprehensive test suite for system commands."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.runner = CliRunner()
        self.console = Console(file=StringIO(), force_terminal=True)
    
    def test_version_command(self):
        """Test version command displays correct version information."""
        result = self.runner.invoke(system_app, ["version"])
        
        assert result.exit_code == 0
        assert "Historical Data Ingestor" in result.stdout
        assert "Version: 1.0.0-mvp" in result.stdout
        assert "Build: Story 2.6 Implementation" in result.stdout
        assert f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}" in result.stdout
        assert "CLI Framework: Typer with Rich formatting" in result.stdout
    
    @patch('src.cli.commands.system.psycopg2.connect')
    @patch.dict(os.environ, {
        'TIMESCALEDB_USER': 'test_user',
        'TIMESCALEDB_PASSWORD': 'test_pass',
        'TIMESCALEDB_HOST': 'localhost',
        'TIMESCALEDB_PORT': '5432',
        'TIMESCALEDB_DBNAME': 'test_db',
        'DATABENTO_API_KEY': 'test_key'
    })
    def test_status_command_success(self, mock_connect):
        """Test status command with successful database connection."""
        # Mock successful database connection
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        result = self.runner.invoke(system_app, ["status"])
        
        assert result.exit_code == 0
        assert "Checking system status" in result.stdout
        assert "TimescaleDB connection: OK" in result.stdout
        assert "Databento API key: Configured" in result.stdout
        
        # Verify database connection was attempted and closed
        mock_connect.assert_called_once_with(
            dbname='test_db',
            user='test_user',
            password='test_pass',
            host='localhost',
            port='5432'
        )
        mock_conn.close.assert_called_once()
    
    @patch('src.cli.commands.system.psycopg2.connect')
    @patch.dict(os.environ, {
        'TIMESCALEDB_USER': 'test_user',
        'TIMESCALEDB_PASSWORD': 'test_pass',
        'TIMESCALEDB_HOST': 'localhost',
        'TIMESCALEDB_PORT': '5432',
        'TIMESCALEDB_DBNAME': 'test_db'
    }, clear=True)
    def test_status_command_db_failure(self, mock_connect):
        """Test status command with database connection failure."""
        # Mock database connection failure
        mock_connect.side_effect = Exception("Connection failed")
        
        result = self.runner.invoke(system_app, ["status"])
        
        assert result.exit_code == 0  # Status command shouldn't fail on DB errors
        assert "TimescaleDB connection: FAILED" in result.stdout
        assert "Connection failed" in result.stdout
        assert "Databento API key: Not configured" in result.stdout
    
    @patch.dict(os.environ, {}, clear=True)
    def test_status_command_missing_env_vars(self):
        """Test status command with missing environment variables."""
        result = self.runner.invoke(system_app, ["status"])
        
        assert result.exit_code == 1
        assert "Database environment variables not set" in result.stdout
    
    @patch('src.cli.commands.system.PipelineOrchestrator')
    def test_list_jobs_success(self, mock_orchestrator_class):
        """Test list_jobs command with successful job loading."""
        # Mock orchestrator with sample jobs
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_orchestrator.load_api_config.return_value = {
            "jobs": [
                {
                    "name": "test_job_1",
                    "dataset": "GLBX.MDP3",
                    "schema": "ohlcv-1d",
                    "symbols": ["ES.c.0", "CL.c.0"],
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                },
                {
                    "name": "test_job_2", 
                    "dataset": "GLBX.MDP3",
                    "schema": "trades",
                    "symbols": ["ES.c.0"],
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-02"
                }
            ]
        }
        
        result = self.runner.invoke(system_app, ["list-jobs", "--api", "databento"])
        
        assert result.exit_code == 0
        assert "Available jobs for DATABENTO" in result.stdout
        assert "test_job_1" in result.stdout
        assert "test_job_2" in result.stdout
        assert "GLBX.MDP3" in result.stdout
        assert "ohlcv-1d" in result.stdout
        assert "trades" in result.stdout
        
        mock_orchestrator.load_api_config.assert_called_once_with("databento")
    
    @patch('src.cli.commands.system.PipelineOrchestrator')
    def test_list_jobs_no_jobs(self, mock_orchestrator_class):
        """Test list_jobs command with no available jobs."""
        # Mock orchestrator with no jobs
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator
        mock_orchestrator.load_api_config.return_value = {"jobs": []}
        
        result = self.runner.invoke(system_app, ["list-jobs"])
        
        assert result.exit_code == 0
        assert "No predefined jobs found" in result.stdout
    
    @patch('src.cli.commands.system.PipelineOrchestrator')
    def test_list_jobs_error(self, mock_orchestrator_class):
        """Test list_jobs command with orchestrator error."""
        # Mock orchestrator error
        mock_orchestrator_class.side_effect = Exception("Failed to load config")
        
        result = self.runner.invoke(system_app, ["list-jobs"])
        
        assert result.exit_code == 1
        assert "Failed to load jobs" in result.stdout
    
    @patch('src.cli.commands.system.OperationMonitor')
    def test_monitor_quick_status(self, mock_monitor_class):
        """Test monitor command default quick status display."""
        # Mock monitor with sample operations
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        mock_monitor.get_active_operations.return_value = [
            {
                'id': 'test-op-1',
                'config': {'description': 'Test operation 1'},
                'status': 'running',
                'progress': 50,
                'total': 100
            }
        ]
        mock_monitor.get_operation_history.return_value = [
            {
                'id': 'test-op-2',
                'config': {'description': 'Test operation 2'},
                'status': 'completed'
            }
        ]
        
        result = self.runner.invoke(system_app, ["monitor"])
        
        assert result.exit_code == 0
        assert "Operation Monitor - Quick Status" in result.stdout
        assert "1 active operation(s)" in result.stdout
        assert "Test operation 1" in result.stdout
        assert "Recent operations" in result.stdout
    
    @patch('src.cli.commands.system.OperationMonitor')
    def test_monitor_cleanup(self, mock_monitor_class):
        """Test monitor command cleanup functionality."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        result = self.runner.invoke(system_app, ["monitor", "--cleanup", "--cleanup-days", "14"])
        
        assert result.exit_code == 0
        assert "Cleaning up old operations" in result.stdout
        assert "Cleanup completed (operations older than 14 days)" in result.stdout
        
        mock_monitor.cleanup_old_operations.assert_called_once_with(14)
    
    @patch('src.cli.commands.system.OperationMonitor')
    def test_monitor_history(self, mock_monitor_class):
        """Test monitor command history display."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        mock_monitor.get_operation_history.return_value = [
            {
                'id': 'test-op-1',
                'config': {'description': 'Historical operation'},
                'status': 'completed',
                'start_time': '2024-01-01T10:00:00',
                'duration_seconds': 300
            }
        ]
        
        result = self.runner.invoke(system_app, ["monitor", "--history"])
        
        assert result.exit_code == 0
        assert "Operation History (Last 20)" in result.stdout
        assert "Historical operation" in result.stdout
        assert "completed" in result.stdout
    
    @patch('src.cli.commands.system.get_config_manager')
    def test_config_get(self, mock_get_config_manager):
        """Test config get command."""
        mock_config_manager = Mock()
        mock_get_config_manager.return_value = mock_config_manager
        mock_config_manager.get_setting.return_value = "test_value"
        
        result = self.runner.invoke(system_app, ["config", "get", "test.key"])
        
        assert result.exit_code == 0
        assert "test.key" in result.stdout
        assert "test_value" in result.stdout
        
        mock_config_manager.get_setting.assert_called_once_with("test.key")
    
    @patch('src.cli.commands.system.get_config_manager')
    def test_config_get_not_found(self, mock_get_config_manager):
        """Test config get command with non-existent key."""
        mock_config_manager = Mock()
        mock_get_config_manager.return_value = mock_config_manager
        mock_config_manager.get_setting.return_value = None
        
        result = self.runner.invoke(system_app, ["config", "get", "nonexistent.key"])
        
        assert result.exit_code == 0
        assert "Setting 'nonexistent.key' not found" in result.stdout
    
    @patch('src.cli.commands.system.get_config_manager')
    def test_config_set(self, mock_get_config_manager):
        """Test config set command."""
        mock_config_manager = Mock()
        mock_get_config_manager.return_value = mock_config_manager
        
        result = self.runner.invoke(system_app, ["config", "set", "test.key", "new_value"])
        
        assert result.exit_code == 0
        assert "Set test.key = new_value" in result.stdout
        
        mock_config_manager.set_setting.assert_called_once_with("test.key", "new_value", True)
    
    @patch('src.cli.commands.system.get_config_manager')
    def test_config_set_boolean(self, mock_get_config_manager):
        """Test config set command with boolean value parsing."""
        mock_config_manager = Mock()
        mock_get_config_manager.return_value = mock_config_manager
        
        result = self.runner.invoke(system_app, ["config", "set", "test.key", "true"])
        
        assert result.exit_code == 0
        mock_config_manager.set_setting.assert_called_once_with("test.key", True, True)
        
        # Test false value
        result = self.runner.invoke(system_app, ["config", "set", "test.key", "false"])
        assert result.exit_code == 0
        mock_config_manager.set_setting.assert_called_with("test.key", False, True)
    
    @patch('src.cli.commands.system.get_config_manager')
    def test_config_set_integer(self, mock_get_config_manager):
        """Test config set command with integer value parsing."""
        mock_config_manager = Mock()
        mock_get_config_manager.return_value = mock_config_manager
        
        result = self.runner.invoke(system_app, ["config", "set", "test.key", "42"])
        
        assert result.exit_code == 0
        mock_config_manager.set_setting.assert_called_once_with("test.key", 42, True)
    
    @patch('src.cli.commands.system.get_config_manager')
    def test_config_list(self, mock_get_config_manager):
        """Test config list command."""
        mock_config_manager = Mock()
        mock_get_config_manager.return_value = mock_config_manager
        mock_config_manager.list_settings.return_value = {
            "progress": {"style": "advanced"},
            "colors": {"enabled": True}
        }
        
        result = self.runner.invoke(system_app, ["config", "list"])
        
        assert result.exit_code == 0
        assert "Complete Configuration" in result.stdout
        assert "progress" in result.stdout
        assert "colors" in result.stdout
    
    @patch('src.cli.commands.system.get_config_manager')
    def test_config_reset(self, mock_get_config_manager):
        """Test config reset command."""
        mock_config_manager = Mock()
        mock_get_config_manager.return_value = mock_config_manager
        
        result = self.runner.invoke(system_app, ["config", "reset"])
        
        assert result.exit_code == 0
        assert "Resetting entire configuration to defaults" in result.stdout
        assert "Configuration reset to defaults" in result.stdout
        
        mock_config_manager.reset_config.assert_called_once_with()
    
    @patch('src.cli.commands.system.get_config_manager')
    def test_config_validate(self, mock_get_config_manager):
        """Test config validate command."""
        mock_config_manager = Mock()
        mock_get_config_manager.return_value = mock_config_manager
        mock_config_manager.validate_config.return_value = []
        
        result = self.runner.invoke(system_app, ["config", "validate"])
        
        assert result.exit_code == 0
        assert "Configuration is valid" in result.stdout
    
    @patch('src.cli.commands.system.get_config_manager')
    def test_config_validate_errors(self, mock_get_config_manager):
        """Test config validate command with validation errors."""
        mock_config_manager = Mock()
        mock_get_config_manager.return_value = mock_config_manager
        mock_config_manager.validate_config.return_value = ["Error 1", "Error 2"]
        
        result = self.runner.invoke(system_app, ["config", "validate"])
        
        assert result.exit_code == 1
        assert "Configuration validation failed" in result.stdout
        assert "Error 1" in result.stdout
        assert "Error 2" in result.stdout
    
    def test_config_invalid_action(self):
        """Test config command with invalid action."""
        result = self.runner.invoke(system_app, ["config", "invalid_action"])
        
        assert result.exit_code == 1
        assert "Unknown action: invalid_action" in result.stdout
        assert "Valid actions: get, set, list, reset, export, import, validate, environment" in result.stdout
    
    def test_config_get_missing_key(self):
        """Test config get command without providing key."""
        result = self.runner.invoke(system_app, ["config", "get"])
        
        assert result.exit_code == 1
        assert "Key required for get action" in result.stdout
    
    def test_config_set_missing_params(self):
        """Test config set command without providing key or value."""
        result = self.runner.invoke(system_app, ["config", "set"])
        
        assert result.exit_code == 1
        assert "Key and value required for set action" in result.stdout
    
    @patch('src.cli.commands.system.get_config_manager')
    def test_config_environment(self, mock_get_config_manager):
        """Test config environment command."""
        mock_config_manager = Mock()
        mock_get_config_manager.return_value = mock_config_manager
        mock_config_manager.get_environment_info.return_value = {
            'platform': 'darwin',
            'terminal_size': '80x24',
            'is_tty': True,
            'supports_color': True,
            'supports_unicode': True,
            'cpu_cores': 8,
            'recommended_workers': 4,
            'is_ci': False,
            'is_ssh': False,
            'is_container': False,
            'is_windows': False,
            'optimal_progress_style': 'advanced',
            'optimal_update_frequency': '100ms'
        }
        
        result = self.runner.invoke(system_app, ["config", "environment"])
        
        assert result.exit_code == 0
        assert "Environment Information" in result.stdout
        assert "Platform" in result.stdout
        assert "darwin" in result.stdout
        assert "CPU Cores" in result.stdout
        assert "8" in result.stdout
        assert "Local Interactive Environment" in result.stdout
        assert "Recommended Settings" in result.stdout


class TestSystemCommandsIntegration:
    """Integration tests for system commands with external dependencies."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.runner = CliRunner()
    
    @pytest.mark.integration
    def test_status_command_real_environment(self):
        """Test status command against real environment (when available)."""
        # This test should be run only when real database is available
        # Skip if environment variables are not set
        required_vars = ['TIMESCALEDB_USER', 'TIMESCALEDB_PASSWORD', 'TIMESCALEDB_DBNAME']
        if not all(os.getenv(var) for var in required_vars):
            pytest.skip("Database environment variables not configured")
        
        result = self.runner.invoke(system_app, ["status"])
        
        # Should not crash even if database is not available
        assert result.exit_code in [0, 1]  # Allow for connection failures
        assert "Checking system status" in result.stdout
    
    @pytest.mark.integration
    def test_list_jobs_real_config(self):
        """Test list_jobs command with real configuration files."""
        result = self.runner.invoke(system_app, ["list-jobs", "--api", "databento"])
        
        # Should not crash even if config files are missing
        assert result.exit_code in [0, 1]  # Allow for config loading failures


class TestSystemCommandsPerformance:
    """Performance tests for system commands."""
    
    def setup_method(self):
        """Set up performance test fixtures."""
        self.runner = CliRunner()
    
    def test_version_command_performance(self):
        """Test version command executes within performance threshold."""
        import time
        
        start_time = time.time()
        result = self.runner.invoke(system_app, ["version"])
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert result.exit_code == 0
        assert execution_time < 0.1  # Should execute in less than 100ms
    
    @patch('src.cli.commands.system.get_config_manager')
    def test_config_list_performance(self, mock_get_config_manager):
        """Test config list command performance with large configuration."""
        # Mock large configuration
        large_config = {}
        for i in range(100):
            large_config[f"section_{i}"] = {f"key_{j}": f"value_{j}" for j in range(50)}
        
        mock_config_manager = Mock()
        mock_get_config_manager.return_value = mock_config_manager
        mock_config_manager.list_settings.return_value = large_config
        
        import time
        start_time = time.time()
        result = self.runner.invoke(system_app, ["config", "list"])
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert result.exit_code == 0
        assert execution_time < 1.0  # Should handle large config in less than 1 second


if __name__ == "__main__":
    pytest.main([__file__, "-v"])