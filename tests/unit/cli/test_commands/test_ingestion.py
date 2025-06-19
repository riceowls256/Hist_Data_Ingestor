"""
Unit tests for CLI ingestion commands module.

Tests all ingestion-related commands including the main ingest command
and backfill operations with comprehensive parameter validation.
"""

from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from datetime import datetime, date, timedelta

import pytest
from typer.testing import CliRunner
from rich.console import Console

from src.cli.commands.ingestion import app as ingestion_app, validate_date_format, parse_symbols, validate_symbol_stype_combination


class TestIngestionCommands:
    """Comprehensive test suite for ingestion commands."""
    
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
    
    def test_parse_symbols(self):
        """Test symbol parsing functionality."""
        assert parse_symbols("ES.FUT,CL.FUT") == ["ES.FUT", "CL.FUT"]
        assert parse_symbols("ES.FUT, CL.FUT ") == ["ES.FUT", "CL.FUT"]
        assert parse_symbols("ES.FUT") == ["ES.FUT"]
        assert parse_symbols("") == []
    
    def test_validate_symbol_stype_combination_valid(self):
        """Test valid symbol-stype combinations."""
        # Continuous contracts
        errors = validate_symbol_stype_combination(["ES.c.0", "CL.c.0"], "continuous")
        assert len(errors) == 0
        
        # Parent symbols
        errors = validate_symbol_stype_combination(["ES.FUT", "CL.FUT"], "parent")
        assert len(errors) == 0
        
        # Native symbols
        errors = validate_symbol_stype_combination(["SPY", "AAPL"], "native")
        assert len(errors) == 0
        
        # ALL_SYMBOLS special case
        errors = validate_symbol_stype_combination(["ALL_SYMBOLS"], "parent")
        assert len(errors) == 0
    
    def test_validate_symbol_stype_combination_invalid(self):
        """Test invalid symbol-stype combinations."""
        # Wrong format for continuous
        errors = validate_symbol_stype_combination(["ES.FUT"], "continuous")
        assert len(errors) > 0
        assert "Invalid symbols for stype_in='continuous'" in errors[0]
        
        # Wrong format for parent
        errors = validate_symbol_stype_combination(["ES.c.0"], "parent")
        assert len(errors) > 0
        assert "Invalid symbols for stype_in='parent'" in errors[0]
        
        # Invalid stype_in
        errors = validate_symbol_stype_combination(["ES.FUT"], "invalid_type")
        assert len(errors) > 0
        assert "Invalid stype_in 'invalid_type'" in errors[0]


class TestIngestCommand:
    """Test suite for the ingest command."""
    
    def setup_method(self):
        """Set up test fixtures for ingest command tests."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.ingestion.PipelineOrchestrator')
    @patch('src.cli.commands.ingestion.get_config_manager')
    def test_ingest_command_with_job(self, mock_config_manager, mock_orchestrator):
        """Test ingest command using predefined job configuration."""
        # Mock config manager
        mock_manager = Mock()
        mock_config_manager.return_value = mock_manager
        mock_manager.get_job_config.return_value = {
            "dataset": "GLBX.MDP3",
            "schema": "ohlcv-1d",
            "symbols": "ES.FUT,CL.FUT",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "stype_in": "parent"
        }
        
        # Mock orchestrator
        mock_pipeline = Mock()
        mock_orchestrator.return_value = mock_pipeline
        mock_pipeline.execute_pipeline.return_value = {
            "status": "success",
            "records_processed": 1000,
            "duration": 30.5
        }
        
        # Test command execution
        result = self.runner.invoke(ingestion_app, [
            "ingest",
            "--api", "databento",
            "--job", "test_job",
            "--force"  # Skip confirmation
        ])
        
        assert result.exit_code == 0
        mock_manager.get_job_config.assert_called_once_with("databento", "test_job")
        mock_pipeline.execute_pipeline.assert_called_once()
    
    @patch('src.cli.commands.ingestion.PipelineOrchestrator')
    def test_ingest_command_custom_parameters(self, mock_orchestrator):
        """Test ingest command with custom parameters."""
        # Mock orchestrator
        mock_pipeline = Mock()
        mock_orchestrator.return_value = mock_pipeline
        mock_pipeline.execute_pipeline.return_value = {
            "status": "success",
            "records_processed": 500,
            "duration": 15.2
        }
        
        # Test command execution
        result = self.runner.invoke(ingestion_app, [
            "ingest",
            "--api", "databento",
            "--dataset", "GLBX.MDP3",
            "--schema", "trades",
            "--symbols", "ES.c.0,CL.c.0",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02",
            "--stype-in", "continuous",
            "--force"
        ])
        
        assert result.exit_code == 0
        mock_pipeline.execute_pipeline.assert_called_once()
        
        # Verify job config parameters
        call_args = mock_pipeline.execute_pipeline.call_args[0][0]
        assert call_args["api"] == "databento"
        assert call_args["dataset"] == "GLBX.MDP3"
        assert call_args["schema"] == "trades"
        assert call_args["symbols"] == ["ES.c.0", "CL.c.0"]
        assert call_args["stype_in"] == "continuous"
    
    def test_ingest_command_missing_parameters(self):
        """Test ingest command with missing required parameters."""
        result = self.runner.invoke(ingestion_app, [
            "ingest",
            "--api", "databento"
            # Missing other required parameters
        ])
        
        assert result.exit_code == 1
        assert "Missing required parameters" in result.stdout
    
    def test_ingest_command_invalid_dates(self):
        """Test ingest command with invalid date formats."""
        result = self.runner.invoke(ingestion_app, [
            "ingest",
            "--api", "databento",
            "--dataset", "GLBX.MDP3",
            "--schema", "ohlcv-1d",
            "--symbols", "ES.FUT",
            "--start-date", "invalid-date",
            "--end-date", "2024-01-31",
            "--force"
        ])
        
        assert result.exit_code == 1
        assert "Invalid start_date format" in result.stdout
    
    def test_ingest_command_equal_dates(self):
        """Test ingest command with equal start and end dates."""
        result = self.runner.invoke(ingestion_app, [
            "ingest",
            "--api", "databento",
            "--dataset", "GLBX.MDP3",
            "--schema", "ohlcv-1d",
            "--symbols", "ES.FUT",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-01",
            "--force"
        ])
        
        assert result.exit_code == 1
        assert "Start date cannot equal end date" in result.stdout
    
    def test_ingest_command_invalid_schema(self):
        """Test ingest command with invalid schema."""
        result = self.runner.invoke(ingestion_app, [
            "ingest",
            "--api", "databento",
            "--dataset", "GLBX.MDP3",
            "--schema", "invalid_schema",
            "--symbols", "ES.FUT",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02",
            "--force"
        ])
        
        assert result.exit_code == 1
        assert "Invalid schema: invalid_schema" in result.stdout
    
    def test_ingest_command_all_supported_schemas(self):
        """Test ingest command with all supported schema types."""
        from src.cli.common.constants import SUPPORTED_SCHEMAS
        
        # Test each supported schema
        supported_schemas = SUPPORTED_SCHEMAS + ["ohlcv"]  # Include alias
        
        for schema in supported_schemas:
            # Test dry run for each schema to verify validation passes
            result = self.runner.invoke(ingestion_app, [
                "ingest",
                "--api", "databento",
                "--dataset", "GLBX.MDP3",
                "--schema", schema,
                "--symbols", "ES.FUT",
                "--start-date", "2024-01-01",
                "--end-date", "2024-01-02",
                "--dry-run"
            ])
            
            # Should not fail on schema validation
            assert result.exit_code == 0, f"Schema {schema} should be valid but failed validation"
            assert "DRY RUN MODE" in result.stdout
    
    def test_ingest_command_dry_run(self):
        """Test ingest command in dry run mode."""
        result = self.runner.invoke(ingestion_app, [
            "ingest",
            "--api", "databento",
            "--dataset", "GLBX.MDP3",
            "--schema", "ohlcv-1d",
            "--symbols", "ES.FUT",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02",
            "--dry-run"
        ])
        
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.stdout
        assert "Configuration validation passed" in result.stdout
    
    @patch('src.cli.commands.ingestion.GuidedMode')
    @patch('src.cli.commands.ingestion.PipelineOrchestrator')
    def test_ingest_command_guided_mode(self, mock_orchestrator, mock_guided_mode):
        """Test ingest command in guided mode."""
        # Mock guided mode
        mock_guided_mode.run_ingestion_wizard.return_value = {
            "api": "databento",
            "dataset": "GLBX.MDP3",
            "schema": "ohlcv-1d",
            "symbols": "ES.FUT",
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
            "stype_in": "parent"
        }
        
        # Mock orchestrator
        mock_pipeline = Mock()
        mock_orchestrator.return_value = mock_pipeline
        mock_pipeline.execute_pipeline.return_value = {
            "status": "success",
            "records_processed": 100,
            "duration": 5.0
        }
        
        result = self.runner.invoke(ingestion_app, [
            "ingest",
            "--guided",
            "--force"
        ])
        
        assert result.exit_code == 0
        mock_guided_mode.run_ingestion_wizard.assert_called_once()
        mock_pipeline.execute_pipeline.assert_called_once()
    
    @patch('src.cli.commands.ingestion.PipelineOrchestrator')
    def test_ingest_command_pipeline_failure(self, mock_orchestrator):
        """Test ingest command handling pipeline failures."""
        # Mock orchestrator with failure
        mock_pipeline = Mock()
        mock_orchestrator.return_value = mock_pipeline
        mock_pipeline.execute_pipeline.return_value = {
            "status": "failure",
            "error": "Database connection failed"
        }
        
        result = self.runner.invoke(ingestion_app, [
            "ingest",
            "--api", "databento",
            "--dataset", "GLBX.MDP3",
            "--schema", "ohlcv-1d",
            "--symbols", "ES.FUT",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02",
            "--force"
        ])
        
        assert result.exit_code == 1
        assert "Ingestion failed" in result.stdout
        assert "Database connection failed" in result.stdout


class TestBackfillCommand:
    """Test suite for the backfill command."""
    
    def setup_method(self):
        """Set up test fixtures for backfill command tests."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.ingestion.SymbolGroupManager')
    @patch('src.cli.commands.ingestion.PipelineOrchestrator')
    def test_backfill_command_predefined_group(self, mock_orchestrator, mock_symbol_manager):
        """Test backfill command with predefined symbol group."""
        # Mock symbol manager
        mock_manager = Mock()
        mock_symbol_manager.return_value = mock_manager
        mock_manager.get_predefined_groups.return_value = ["SP500_SAMPLE"]
        mock_manager.get_group_symbols.return_value = ["SPY", "QQQ", "IWM"]
        
        # Mock orchestrator
        mock_pipeline = Mock()
        mock_orchestrator.return_value = mock_pipeline
        mock_pipeline.execute_pipeline.return_value = {
            "status": "success",
            "records_processed": 100,
            "duration": 5.0
        }
        
        result = self.runner.invoke(ingestion_app, [
            "backfill",
            "SP500_SAMPLE",
            "--lookback", "1w",
            "--force"
        ])
        
        assert result.exit_code == 0
        mock_manager.get_group_symbols.assert_called_once_with("SP500_SAMPLE")
        # Should call execute_pipeline for each symbol/schema combination
        assert mock_pipeline.execute_pipeline.call_count == 3  # 3 symbols * 1 schema
    
    @patch('src.cli.commands.ingestion.SymbolGroupManager')
    @patch('src.cli.commands.ingestion.PipelineOrchestrator')
    def test_backfill_command_custom_symbols(self, mock_orchestrator, mock_symbol_manager):
        """Test backfill command with custom symbol list."""
        # Mock symbol manager (custom group not found)
        mock_manager = Mock()
        mock_symbol_manager.return_value = mock_manager
        mock_manager.get_predefined_groups.return_value = ["SP500_SAMPLE"]
        
        # Mock orchestrator
        mock_pipeline = Mock()
        mock_orchestrator.return_value = mock_pipeline
        mock_pipeline.execute_pipeline.return_value = {
            "status": "success",
            "records_processed": 100,
            "duration": 5.0
        }
        
        result = self.runner.invoke(ingestion_app, [
            "backfill",
            "ES.FUT,CL.FUT",
            "--lookback", "1m",
            "--force"
        ])
        
        assert result.exit_code == 0
        # Should call execute_pipeline for each symbol/schema combination
        assert mock_pipeline.execute_pipeline.call_count == 2  # 2 symbols * 1 schema
    
    @patch('src.cli.commands.ingestion.SymbolGroupManager')
    @patch('src.cli.commands.ingestion.PipelineOrchestrator')
    def test_backfill_command_multiple_schemas(self, mock_orchestrator, mock_symbol_manager):
        """Test backfill command with multiple schemas."""
        # Mock symbol manager
        mock_manager = Mock()
        mock_symbol_manager.return_value = mock_manager
        mock_manager.get_predefined_groups.return_value = []
        
        # Mock orchestrator
        mock_pipeline = Mock()
        mock_orchestrator.return_value = mock_pipeline
        mock_pipeline.execute_pipeline.return_value = {
            "status": "success",
            "records_processed": 100,
            "duration": 5.0
        }
        
        result = self.runner.invoke(ingestion_app, [
            "backfill",
            "ES.FUT,CL.FUT",
            "--schemas", "ohlcv-1d,trades",
            "--lookback", "1w",
            "--force"
        ])
        
        assert result.exit_code == 0
        # Should call execute_pipeline for each symbol/schema combination
        assert mock_pipeline.execute_pipeline.call_count == 4  # 2 symbols * 2 schemas
    
    def test_backfill_command_invalid_lookback(self):
        """Test backfill command with invalid lookback period."""
        result = self.runner.invoke(ingestion_app, [
            "backfill",
            "ES.FUT",
            "--lookback", "invalid_period",
            "--force"
        ])
        
        assert result.exit_code == 1
        assert "Invalid lookback period" in result.stdout
    
    @patch('src.cli.commands.ingestion.SymbolGroupManager')
    def test_backfill_command_empty_group(self, mock_symbol_manager):
        """Test backfill command with empty symbol group."""
        # Mock symbol manager with empty group
        mock_manager = Mock()
        mock_symbol_manager.return_value = mock_manager
        mock_manager.get_predefined_groups.return_value = ["EMPTY_GROUP"]
        mock_manager.get_group_symbols.return_value = []
        
        result = self.runner.invoke(ingestion_app, [
            "backfill",
            "EMPTY_GROUP",
            "--force"
        ])
        
        assert result.exit_code == 1
        assert "No symbols found for group" in result.stdout
    
    @patch('src.cli.commands.ingestion.SymbolGroupManager')
    @patch('src.cli.commands.ingestion.PipelineOrchestrator')
    def test_backfill_command_dry_run(self, mock_orchestrator, mock_symbol_manager):
        """Test backfill command in dry run mode."""
        # Mock symbol manager
        mock_manager = Mock()
        mock_symbol_manager.return_value = mock_manager
        mock_manager.get_predefined_groups.return_value = []
        
        result = self.runner.invoke(ingestion_app, [
            "backfill",
            "ES.FUT",
            "--dry-run"
        ])
        
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.stdout
        assert "Operation plan validated" in result.stdout
        # Should not call execute_pipeline in dry run mode
        mock_orchestrator.assert_not_called()
    
    @patch('src.cli.commands.ingestion.SymbolGroupManager')
    @patch('src.cli.commands.ingestion.PipelineOrchestrator')
    def test_backfill_command_with_failures(self, mock_orchestrator, mock_symbol_manager):
        """Test backfill command handling some failures."""
        # Mock symbol manager
        mock_manager = Mock()
        mock_symbol_manager.return_value = mock_manager
        mock_manager.get_predefined_groups.return_value = []
        
        # Mock orchestrator with mixed results
        mock_pipeline = Mock()
        mock_orchestrator.return_value = mock_pipeline
        
        # First call succeeds, second fails
        mock_pipeline.execute_pipeline.side_effect = [
            {"status": "success", "records_processed": 100},
            {"status": "failure", "error": "Network timeout"}
        ]
        
        result = self.runner.invoke(ingestion_app, [
            "backfill",
            "ES.FUT,CL.FUT",
            "--lookback", "1d",
            "--retry-failed", "false",  # Disable retry for test
            "--force"
        ])
        
        assert result.exit_code == 1  # Should exit with error due to failures
        assert "Failed operations" in result.stdout
        assert "Network timeout" in result.stdout
    
    @patch('src.cli.commands.ingestion.SymbolGroupManager')
    @patch('src.cli.commands.ingestion.PipelineOrchestrator')
    def test_backfill_command_retry_logic(self, mock_orchestrator, mock_symbol_manager):
        """Test backfill command retry logic for failures."""
        # Mock symbol manager
        mock_manager = Mock()
        mock_symbol_manager.return_value = mock_manager
        mock_manager.get_predefined_groups.return_value = []
        
        # Mock orchestrator with failure then success on retry
        mock_pipeline = Mock()
        mock_orchestrator.return_value = mock_pipeline
        
        # First call fails, second call (retry) succeeds
        mock_pipeline.execute_pipeline.side_effect = [
            {"status": "failure", "error": "Temporary error"},
            {"status": "success", "records_processed": 100}
        ]
        
        result = self.runner.invoke(ingestion_app, [
            "backfill",
            "ES.FUT",
            "--lookback", "1d",
            "--retry-failed", "true",
            "--force"
        ])
        
        assert result.exit_code == 0  # Should succeed after retry
        assert mock_pipeline.execute_pipeline.call_count == 2  # Original + retry
        assert "retry" in result.stdout


class TestIngestionCommandsPerformance:
    """Performance tests for ingestion commands."""
    
    def setup_method(self):
        """Set up performance test fixtures."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.ingestion.PipelineOrchestrator')
    def test_ingest_command_performance(self, mock_orchestrator):
        """Test ingest command executes within performance threshold."""
        # Mock orchestrator
        mock_pipeline = Mock()
        mock_orchestrator.return_value = mock_pipeline
        mock_pipeline.execute_pipeline.return_value = {
            "status": "success",
            "records_processed": 1000,
            "duration": 10.0
        }
        
        import time
        start_time = time.time()
        
        result = self.runner.invoke(ingestion_app, [
            "ingest",
            "--api", "databento",
            "--dataset", "GLBX.MDP3",
            "--schema", "ohlcv-1d",
            "--symbols", "ES.FUT",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02",
            "--force"
        ])
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert result.exit_code == 0
        assert execution_time < 2.0  # Should execute setup/validation in less than 2 seconds
    
    @patch('src.cli.commands.ingestion.SymbolGroupManager')
    @patch('src.cli.commands.ingestion.PipelineOrchestrator')
    def test_backfill_command_performance(self, mock_orchestrator, mock_symbol_manager):
        """Test backfill command setup performance with large symbol groups."""
        # Mock symbol manager with large symbol group
        mock_manager = Mock()
        mock_symbol_manager.return_value = mock_manager
        mock_manager.get_predefined_groups.return_value = ["LARGE_GROUP"]
        mock_manager.get_group_symbols.return_value = [f"SYMBOL_{i}" for i in range(100)]
        
        # Mock orchestrator
        mock_pipeline = Mock()
        mock_orchestrator.return_value = mock_pipeline
        mock_pipeline.execute_pipeline.return_value = {
            "status": "success",
            "records_processed": 100,
            "duration": 1.0
        }
        
        import time
        start_time = time.time()
        
        result = self.runner.invoke(ingestion_app, [
            "backfill",
            "LARGE_GROUP",
            "--dry-run"  # Use dry run to test setup performance only
        ])
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert result.exit_code == 0
        assert execution_time < 3.0  # Should handle large groups in less than 3 seconds


class TestIngestionCommandsErrorHandling:
    """Test error handling for ingestion commands."""
    
    def setup_method(self):
        """Set up error handling test fixtures."""
        self.runner = CliRunner()
    
    @patch('src.cli.commands.ingestion.PipelineOrchestrator')
    def test_ingest_command_pipeline_exception(self, mock_orchestrator):
        """Test ingest command handling PipelineError exceptions."""
        from core.pipeline_orchestrator import PipelineError
        
        # Mock orchestrator to raise PipelineError
        mock_orchestrator.side_effect = PipelineError("Database connection failed")
        
        result = self.runner.invoke(ingestion_app, [
            "ingest",
            "--api", "databento",
            "--dataset", "GLBX.MDP3",
            "--schema", "ohlcv-1d",
            "--symbols", "ES.FUT",
            "--start-date", "2024-01-01",
            "--end-date", "2024-01-02",
            "--force"
        ])
        
        assert result.exit_code == 1
        assert "Pipeline error" in result.stdout
        assert "Database connection failed" in result.stdout
    
    @patch('src.cli.commands.ingestion.SymbolGroupManager')
    def test_backfill_command_exception_handling(self, mock_symbol_manager):
        """Test backfill command handling unexpected exceptions."""
        # Mock symbol manager to raise exception
        mock_symbol_manager.side_effect = Exception("Unexpected error occurred")
        
        result = self.runner.invoke(ingestion_app, [
            "backfill",
            "ES.FUT",
            "--force"
        ])
        
        assert result.exit_code == 1
        assert "Backfill operation failed" in result.stdout
        assert "Unexpected error occurred" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])