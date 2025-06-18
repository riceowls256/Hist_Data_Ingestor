"""
Unit tests for PipelineOrchestrator.

Tests the core orchestration logic including component initialization,
pipeline execution, error handling, and CLI integration.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime
from typing import Dict, Any

from src.core.pipeline_orchestrator import (
    PipelineOrchestrator,
    ComponentFactory,
    PipelineStats,
    PipelineError,
    UnsupportedAPIError,
    ComponentInitializationError,
    PipelineExecutionError
)
from src.core.config_manager import ConfigManager


class TestComponentFactory:
    """Test the ComponentFactory class."""
    
    def test_register_adapter(self):
        """Test adapter registration."""
        mock_adapter = Mock()
        mock_adapter.__name__ = "MockAdapter"
        ComponentFactory.register_adapter("test_api", mock_adapter)
        
        assert "test_api" in ComponentFactory._adapters
        assert ComponentFactory._adapters["test_api"] == mock_adapter
    
    def test_create_adapter_success(self):
        """Test successful adapter creation."""
        mock_adapter_class = Mock()
        mock_adapter_class.__name__ = "MockAdapter"  # Add __name__ attribute
        mock_adapter_instance = Mock()
        mock_adapter_class.return_value = mock_adapter_instance
        
        ComponentFactory._adapters["test_api"] = mock_adapter_class
        
        config = {"key": "value"}
        result = ComponentFactory.create_adapter("test_api", config)
        
        mock_adapter_class.assert_called_once_with(config)
        assert result == mock_adapter_instance
    
    def test_create_adapter_unsupported_api(self):
        """Test adapter creation with unsupported API type."""
        with pytest.raises(UnsupportedAPIError) as exc_info:
            ComponentFactory.create_adapter("unsupported_api", {})
        
        assert "Unsupported API type: unsupported_api" in str(exc_info.value)
    
    def test_create_adapter_initialization_error(self):
        """Test adapter creation when initialization fails."""
        mock_adapter_class = Mock()
        mock_adapter_class.side_effect = Exception("Init failed")
        
        ComponentFactory._adapters["failing_api"] = mock_adapter_class
        
        with pytest.raises(ComponentInitializationError) as exc_info:
            ComponentFactory.create_adapter("failing_api", {})
        
        assert "Failed to initialize failing_api adapter" in str(exc_info.value)


class TestPipelineStats:
    """Test the PipelineStats class."""
    
    def test_initialization(self):
        """Test stats initialization."""
        stats = PipelineStats()
        
        assert stats.start_time is None
        assert stats.end_time is None
        assert stats.records_fetched == 0
        assert stats.records_transformed == 0
        assert stats.records_validated == 0
        assert stats.records_stored == 0
        assert stats.records_quarantined == 0
        assert stats.chunks_processed == 0
        assert stats.errors_encountered == 0
    
    def test_start_tracking(self):
        """Test starting statistics tracking."""
        stats = PipelineStats()
        
        with patch('src.core.pipeline_orchestrator.datetime') as mock_datetime:
            mock_time = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_time
            
            stats.start()
            
            assert stats.start_time == mock_time
    
    def test_finish_tracking(self):
        """Test finishing statistics tracking."""
        stats = PipelineStats()
        
        with patch('src.core.pipeline_orchestrator.datetime') as mock_datetime:
            start_time = datetime(2023, 1, 1, 12, 0, 0)
            end_time = datetime(2023, 1, 1, 12, 5, 0)
            
            mock_datetime.now.side_effect = [start_time, end_time]
            
            stats.start()
            stats.finish()
            
            assert stats.start_time == start_time
            assert stats.end_time == end_time
    
    def test_to_dict(self):
        """Test converting stats to dictionary."""
        stats = PipelineStats()
        stats.records_fetched = 100
        stats.records_stored = 95
        stats.records_quarantined = 5
        
        result = stats.to_dict()
        
        assert result["records_fetched"] == 100
        assert result["records_stored"] == 95
        assert result["records_quarantined"] == 5
        assert "start_time" in result
        assert "end_time" in result
        assert "duration_seconds" in result


class TestPipelineOrchestrator:
    """Test the PipelineOrchestrator class."""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Mock ConfigManager fixture."""
        mock_config = Mock()
        mock_config.db = Mock()
        mock_config.db.host = "localhost"
        mock_config.db.port = 5432
        mock_config.db.dbname = "test_db"
        mock_config.db.user = "test_user"
        mock_config.db.password = "test_pass"
        
        mock_config_manager = Mock(spec=ConfigManager)
        mock_config_manager.get.return_value = mock_config
        
        return mock_config_manager
    
    @pytest.fixture
    def orchestrator(self, mock_config_manager):
        """PipelineOrchestrator fixture."""
        return PipelineOrchestrator(config_manager=mock_config_manager)
    
    def test_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.config_manager is not None
        assert orchestrator.system_config is not None
        assert isinstance(orchestrator.stats, PipelineStats)
        assert orchestrator.adapter is None
        assert orchestrator.rule_engine is None
        assert orchestrator.storage_loader is None
    
    @patch('src.core.pipeline_orchestrator.yaml.safe_load')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_api_config_success(self, mock_open_func, mock_yaml_load, orchestrator):
        """Test successful API config loading."""
        mock_config = {"api": {"key": "value"}}
        mock_yaml_load.return_value = mock_config
        
        # Create a proper mock for the config path that supports exists()
        mock_config_path = Mock()
        mock_config_path.exists.return_value = True
        
        # Mock Path to return our config path mock when called
        with patch('src.core.pipeline_orchestrator.Path') as mock_path_class:
            # Create a mock that handles the division operator chain
            mock_configs = Mock()
            mock_api_specific = Mock()
            mock_databento_config = mock_config_path
            
            # Set up the chain: parent.parent.parent / "configs" / "api_specific" / "databento_config.yaml"
            mock_parent3 = Mock()
            mock_parent3.__truediv__ = Mock(side_effect=lambda x: mock_configs if x == "configs" else None)
            mock_configs.__truediv__ = Mock(side_effect=lambda x: mock_api_specific if x == "api_specific" else None)
            mock_api_specific.__truediv__ = Mock(side_effect=lambda x: mock_databento_config if x == "databento_config.yaml" else None)
            
            mock_parent2 = Mock()
            mock_parent2.parent = mock_parent3
            
            mock_parent1 = Mock()
            mock_parent1.parent = mock_parent2
            
            mock_path_instance = Mock()
            mock_path_instance.parent = mock_parent1
            
            mock_path_class.return_value = mock_path_instance
            
            result = orchestrator.load_api_config("databento")
            
            assert result == mock_config
            mock_open_func.assert_called_once_with(mock_config_path, 'r')
            mock_yaml_load.assert_called_once()
    
    def test_load_api_config_file_not_found(self, orchestrator):
        """Test API config loading when file doesn't exist."""
        # Create a mock config path that doesn't exist
        mock_config_path = Mock()
        mock_config_path.exists.return_value = False
        
        with patch('src.core.pipeline_orchestrator.Path') as mock_path_class:
            # Create a mock that handles the division operator chain
            mock_configs = Mock()
            mock_api_specific = Mock()
            mock_nonexistent_config = mock_config_path
            
            # Set up the chain: parent.parent.parent / "configs" / "api_specific" / "nonexistent_config.yaml"
            mock_parent3 = Mock()
            mock_parent3.__truediv__ = Mock(side_effect=lambda x: mock_configs if x == "configs" else None)
            mock_configs.__truediv__ = Mock(side_effect=lambda x: mock_api_specific if x == "api_specific" else None)
            mock_api_specific.__truediv__ = Mock(side_effect=lambda x: mock_nonexistent_config if x == "nonexistent_config.yaml" else None)
            
            mock_parent2 = Mock()
            mock_parent2.parent = mock_parent3
            
            mock_parent1 = Mock()
            mock_parent1.parent = mock_parent2
            
            mock_path_instance = Mock()
            mock_path_instance.parent = mock_parent1
            
            mock_path_class.return_value = mock_path_instance
            
            with pytest.raises(FileNotFoundError):
                orchestrator.load_api_config("nonexistent")
    
    def test_validate_job_config_success(self, orchestrator):
        """Test successful job config validation."""
        job_config = {
            "name": "test_job",
            "dataset": "GLBX.MDP3",
            "schema": "ohlcv-1d",
            "symbols": ["CL.FUT"],
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "stype_in": "continuous"
        }
        
        result = orchestrator.validate_job_config(job_config, "databento")
        
        assert result is True
    
    def test_validate_job_config_missing_fields(self, orchestrator):
        """Test job config validation with missing fields."""
        job_config = {
            "name": "test_job",
            "dataset": "GLBX.MDP3"
            # Missing required fields
        }
        
        result = orchestrator.validate_job_config(job_config, "databento")
        
        assert result is False
    
    def test_validate_job_config_unknown_api(self, orchestrator):
        """Test job config validation with unknown API type."""
        job_config = {"name": "test_job"}
        
        result = orchestrator.validate_job_config(job_config, "unknown_api")
        
        assert result is False
    
    @patch('src.core.pipeline_orchestrator.ComponentFactory.create_adapter')
    @patch('src.core.pipeline_orchestrator.RuleEngine')
    @patch('src.core.pipeline_orchestrator.TimescaleDefinitionLoader')
    def test_initialize_components_success(
        self, 
        mock_timescale_definition_loader, 
        mock_rule_engine, 
        mock_create_adapter,
        orchestrator
    ):
        """Test successful component initialization."""
        # Setup mocks
        mock_adapter = Mock()
        mock_adapter.validate_config.return_value = True
        mock_create_adapter.return_value = mock_adapter
        
        mock_rule_engine_instance = Mock()
        mock_rule_engine.return_value = mock_rule_engine_instance
        
        mock_storage_instance = Mock()
        mock_timescale_definition_loader.return_value = mock_storage_instance
        
        api_config = {
            "transformation": {
                "mapping_config_path": "test_mapping.yaml"
            }
        }
        
        orchestrator.initialize_components("databento", api_config)
        
        # Verify components were initialized
        assert orchestrator.adapter == mock_adapter
        assert orchestrator.rule_engine == mock_rule_engine_instance
        assert orchestrator.storage_loader == mock_storage_instance
        
        # Verify calls
        mock_adapter.validate_config.assert_called_once()
        mock_adapter.connect.assert_called_once()
        mock_rule_engine.assert_called_once_with("test_mapping.yaml")
        mock_timescale_definition_loader.assert_called_once()
    
    @patch('src.core.pipeline_orchestrator.ComponentFactory.create_adapter')
    def test_initialize_components_invalid_config(self, mock_create_adapter, orchestrator):
        """Test component initialization with invalid adapter config."""
        mock_adapter = Mock()
        mock_adapter.validate_config.return_value = False
        mock_create_adapter.return_value = mock_adapter
        
        with pytest.raises(ComponentInitializationError):
            orchestrator.initialize_components("databento", {})
    
    def test_cleanup_components(self, orchestrator):
        """Test component cleanup."""
        # Setup mock components
        mock_adapter = Mock()
        mock_storage = Mock()
        
        orchestrator.adapter = mock_adapter
        orchestrator.storage_loader = mock_storage
        
        orchestrator.cleanup_components()
        
        # Verify cleanup calls
        mock_adapter.disconnect.assert_called_once()
        # Note: TimescaleDefinitionLoader doesn't have a close method, so we don't check for it
        
        # Verify components are reset
        assert orchestrator.adapter is None
        assert orchestrator.storage_loader is None
    
    def test_get_predefined_job_config_success(self, orchestrator):
        """Test getting predefined job config."""
        api_config = {
            "jobs": [
                {"name": "job1", "dataset": "DS1"},
                {"name": "job2", "dataset": "DS2"}
            ]
        }
        
        result = orchestrator._get_predefined_job_config(api_config, "job2")
        
        assert result == {"name": "job2", "dataset": "DS2"}
    
    def test_get_predefined_job_config_not_found(self, orchestrator):
        """Test getting predefined job config when job doesn't exist."""
        api_config = {
            "jobs": [
                {"name": "job1", "dataset": "DS1"}
            ]
        }
        
        with pytest.raises(ValueError) as exc_info:
            orchestrator._get_predefined_job_config(api_config, "nonexistent")
        
        assert "Job 'nonexistent' not found" in str(exc_info.value)
    
    def test_build_job_config_from_overrides(self, orchestrator):
        """Test building job config from overrides."""
        overrides = {
            "dataset": "GLBX.MDP3",
            "schema": "ohlcv-1d",
            "symbols": ["CL.FUT"]
        }
        
        result = orchestrator._build_job_config_from_overrides(overrides)
        
        # Should include all original overrides
        for key, value in overrides.items():
            assert result[key] == value
        
        # Should automatically add a name field
        assert "name" in result
        assert result["name"] == "cli_ohlcv-1d_CL.FUT"
    
    @patch.object(PipelineOrchestrator, 'validate_job_config')
    @patch.object(PipelineOrchestrator, '_execute_pipeline_stages')
    def test_execute_databento_pipeline_success(
        self, 
        mock_execute_stages, 
        mock_validate_config,
        orchestrator
    ):
        """Test successful Databento pipeline execution."""
        # Setup mocks
        mock_validate_config.return_value = True
        mock_execute_stages.return_value = True
        
        # Setup orchestrator components
        orchestrator.adapter = Mock()
        orchestrator.storage_loader = Mock()
        
        job_config = {"name": "test_job"}
        
        result = orchestrator.execute_databento_pipeline(job_config)
        
        assert result is True
        mock_validate_config.assert_called_once_with(job_config, "databento")
        mock_execute_stages.assert_called_once_with(job_config)
    
    @patch.object(PipelineOrchestrator, 'validate_job_config')
    def test_execute_databento_pipeline_invalid_config(
        self, 
        mock_validate_config,
        orchestrator
    ):
        """Test Databento pipeline execution with invalid config."""
        mock_validate_config.return_value = False
        
        job_config = {"name": "test_job"}
        
        result = orchestrator.execute_databento_pipeline(job_config)
        
        assert result is False
    
    def test_execute_databento_pipeline_components_not_initialized(self, orchestrator):
        """Test Databento pipeline execution when components aren't initialized."""
        job_config = {"name": "test_job"}
        
        with patch.object(orchestrator, 'validate_job_config', return_value=True):
            result = orchestrator.execute_databento_pipeline(job_config)
        
        assert result is False


class TestPipelineIntegration:
    """Integration tests for pipeline execution flow."""
    
    @patch('src.core.pipeline_orchestrator.ConfigManager')
    @patch.object(PipelineOrchestrator, 'load_api_config')
    @patch.object(PipelineOrchestrator, 'initialize_components')
    @patch.object(PipelineOrchestrator, 'execute_databento_pipeline')
    @patch.object(PipelineOrchestrator, 'cleanup_components')
    def test_execute_ingestion_with_job_name(
        self,
        mock_cleanup,
        mock_execute_databento,
        mock_initialize,
        mock_load_config,
        mock_config_manager_class
    ):
        """Test complete ingestion execution with predefined job."""
        # Setup mocks
        mock_config_manager = Mock()
        mock_config_manager_class.return_value = mock_config_manager
        
        mock_api_config = {
            "jobs": [{"name": "test_job", "dataset": "DS1"}]
        }
        mock_load_config.return_value = mock_api_config
        mock_execute_databento.return_value = True
        
        orchestrator = PipelineOrchestrator()
        
        result = orchestrator.execute_ingestion(
            api_type="databento",
            job_name="test_job"
        )
        
        assert result is True
        mock_load_config.assert_called_once_with("databento")
        mock_initialize.assert_called_once_with("databento", mock_api_config)
        mock_execute_databento.assert_called_once()
        mock_cleanup.assert_called_once()
    
    @patch('src.core.pipeline_orchestrator.ConfigManager')
    @patch.object(PipelineOrchestrator, 'load_api_config')
    def test_execute_ingestion_unsupported_api(
        self,
        mock_load_config,
        mock_config_manager_class
    ):
        """Test ingestion execution with unsupported API type."""
        mock_config_manager = Mock()
        mock_config_manager_class.return_value = mock_config_manager
        
        mock_load_config.return_value = {}
        
        orchestrator = PipelineOrchestrator()
        
        result = orchestrator.execute_ingestion(
            api_type="unsupported_api",
            job_name="test_job"
        )
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__]) 