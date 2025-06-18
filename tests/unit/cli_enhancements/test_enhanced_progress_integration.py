"""
Test suite for enhanced progress integration with PipelineOrchestrator.

This module tests the Phase 1.1 implementation of enhanced progress tracking
to ensure proper integration between PipelineOrchestrator and EnhancedProgress.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, Any, List

from core.pipeline_orchestrator import PipelineOrchestrator, PipelineStats
from cli.progress_utils import EnhancedProgress


class TestEnhancedProgressIntegration:
    """Test the integration of enhanced progress tracking."""

    def test_orchestrator_accepts_progress_callback(self):
        """Test that PipelineOrchestrator accepts and stores progress callback."""
        # Create a mock callback
        mock_callback = Mock()
        
        # Create orchestrator with callback
        orchestrator = PipelineOrchestrator(progress_callback=mock_callback)
        
        # Verify callback is stored
        assert orchestrator.progress_callback is not None
        assert orchestrator.progress_callback == mock_callback

    def test_orchestrator_works_without_progress_callback(self):
        """Test that PipelineOrchestrator works without progress callback."""
        # Create orchestrator without callback
        orchestrator = PipelineOrchestrator()
        
        # Verify default no-op callback is set
        assert orchestrator.progress_callback is not None
        # Call it to ensure it doesn't raise
        orchestrator.progress_callback(description="test", completed=1, total=10)

    @patch('core.pipeline_orchestrator.logger')
    def test_progress_callback_called_during_pipeline_stages(self, mock_logger):
        """Test that progress callback is called at each pipeline stage."""
        # Create mock callback to track calls
        progress_calls = []
        def mock_callback(**kwargs):
            progress_calls.append(kwargs)
        
        # Create orchestrator with callback
        orchestrator = PipelineOrchestrator(progress_callback=mock_callback)
        
        # Mock the stage methods to return test data
        test_chunks = [
            [{'id': 1}, {'id': 2}, {'id': 3}],  # Chunk 1 with 3 records
            [{'id': 4}, {'id': 5}],              # Chunk 2 with 2 records
        ]
        
        orchestrator._stage_data_extraction = Mock(return_value=test_chunks)
        orchestrator._stage_data_transformation = Mock(side_effect=lambda x, *args: x)
        orchestrator._stage_data_validation = Mock(side_effect=lambda x, *args: (x, []))
        orchestrator._stage_data_storage = Mock(return_value=True)
        
        # Execute pipeline stages
        job_config = {'name': 'test_job', 'schema': 'ohlcv-1d'}
        orchestrator._execute_pipeline_stages(job_config)
        
        # Verify progress callbacks were made
        assert len(progress_calls) > 0
        
        # Check for initial fetch callback
        fetch_calls = [c for c in progress_calls if 'Fetching data' in c.get('description', '')]
        assert len(fetch_calls) > 0
        
        # Check for processing callbacks
        processing_calls = [c for c in progress_calls if 'Processing' in c.get('description', '')]
        assert len(processing_calls) > 0
        
        # Check for stage callbacks
        stage_calls = [c for c in progress_calls if 'stage' in c]
        assert len(stage_calls) > 0
        assert any(c['stage'] == 'transformation' for c in stage_calls)
        assert any(c['stage'] == 'validation' for c in stage_calls)
        assert any(c['stage'] == 'storage' for c in stage_calls)
        
        # Check for completion callback
        completion_calls = [c for c in progress_calls if 'completed' in c.get('description', '')]
        assert len(completion_calls) > 0

    def test_progress_callback_reports_correct_totals(self):
        """Test that progress callback reports correct record totals."""
        progress_updates = []
        def track_progress(**kwargs):
            progress_updates.append(kwargs)
        
        orchestrator = PipelineOrchestrator(progress_callback=track_progress)
        
        # Mock data with known sizes
        test_chunks = [
            [{'id': i} for i in range(100)],  # 100 records
            [{'id': i} for i in range(50)],   # 50 records
            [{'id': i} for i in range(75)],   # 75 records
        ]
        total_records = 225
        
        orchestrator._stage_data_extraction = Mock(return_value=test_chunks)
        orchestrator._stage_data_transformation = Mock(side_effect=lambda x, *args: x)
        orchestrator._stage_data_validation = Mock(side_effect=lambda x, *args: (x, []))
        orchestrator._stage_data_storage = Mock(return_value=True)
        
        # Execute pipeline
        job_config = {'name': 'test_job'}
        orchestrator._execute_pipeline_stages(job_config)
        
        # Find the initial processing update
        processing_updates = [u for u in progress_updates if 'Processing' in u.get('description', '') and 'records' in u.get('description', '')]
        assert len(processing_updates) > 0
        
        # Verify total is correct
        first_processing = processing_updates[0]
        assert first_processing['total'] == total_records
        assert f"{total_records:,} records" in first_processing['description']

    def test_progress_callback_handles_errors(self):
        """Test that progress callback properly reports errors."""
        error_updates = []
        def track_errors(**kwargs):
            if kwargs.get('error'):
                error_updates.append(kwargs)
        
        orchestrator = PipelineOrchestrator(progress_callback=track_errors)
        
        # Mock extraction to raise an error
        orchestrator._stage_data_extraction = Mock(side_effect=Exception("Test error"))
        
        # Execute pipeline (should fail)
        job_config = {'name': 'test_job'}
        result = orchestrator._execute_pipeline_stages(job_config)
        
        # Verify failure
        assert result is False
        
        # Verify error was reported through progress callback
        assert len(error_updates) > 0
        assert error_updates[0]['error'] is True
        assert 'Test error' in error_updates[0]['description']

    def test_main_py_progress_integration(self):
        """Test the integration pattern used in main.py."""
        from cli.progress_utils import EnhancedProgress
        
        # Simulate the progress callback pattern from main.py
        metrics_updates = []
        stage_updates = []
        
        class MockProgress:
            def update_main(self, **kwargs):
                pass
            
            def update_metrics(self, metrics):
                metrics_updates.append(metrics)
            
            def update_stage(self, stage, description):
                stage_updates.append((stage, description))
            
            def set_status(self, status):
                pass
        
        mock_progress = MockProgress()
        
        # Create the callback as done in main.py
        def progress_callback(**kwargs):
            description = kwargs.get('description', '')
            completed = kwargs.get('completed', 0)
            total = kwargs.get('total', 0)
            
            if total > 0:
                mock_progress.update_main(
                    completed=completed,
                    total=total,
                    description=description
                )
            
            if 'records_stored' in kwargs:
                mock_progress.update_metrics({
                    'records_stored': kwargs['records_stored'],
                    'records_quarantined': kwargs.get('records_quarantined', 0),
                    'chunks_processed': kwargs.get('chunks_processed', 0)
                })
            
            if 'stage' in kwargs:
                mock_progress.update_stage(kwargs['stage'], description)
        
        # Test the callback with sample data
        progress_callback(
            description="Processing chunk 1/3",
            completed=100,
            total=300,
            records_stored=100,
            records_quarantined=5,
            chunks_processed=1,
            stage="storage"
        )
        
        # Verify metrics were updated
        assert len(metrics_updates) == 1
        assert metrics_updates[0]['records_stored'] == 100
        assert metrics_updates[0]['records_quarantined'] == 5
        assert metrics_updates[0]['chunks_processed'] == 1
        
        # Verify stage was updated
        assert len(stage_updates) == 1
        assert stage_updates[0] == ("storage", "Processing chunk 1/3")


@pytest.mark.integration
class TestEnhancedProgressE2E:
    """End-to-end tests for enhanced progress functionality."""

    @patch('core.pipeline_orchestrator.ComponentFactory.create_adapter')
    @patch('core.pipeline_orchestrator.RuleEngine')
    @patch('core.pipeline_orchestrator.TimescaleOHLCVLoader')
    def test_full_pipeline_with_progress(self, mock_loader, mock_rule_engine, mock_adapter_factory):
        """Test full pipeline execution with progress tracking."""
        # Track all progress updates
        all_updates = []
        def capture_progress(**kwargs):
            all_updates.append(kwargs)
        
        # Setup mocks
        mock_adapter = Mock()
        mock_adapter.validate_config.return_value = True
        mock_adapter.connect.return_value = None
        mock_adapter.fetch_historical_data.return_value = [
            Mock(ts_event=123, symbol='TEST', open_price=100, high_price=101, low_price=99, close_price=100.5)
            for _ in range(10)
        ]
        mock_adapter_factory.return_value = mock_adapter
        
        # Create orchestrator with progress tracking
        orchestrator = PipelineOrchestrator(progress_callback=capture_progress)
        
        # Execute a simple ingestion
        job_config = {
            'name': 'test_job',
            'dataset': 'TEST',
            'schema': 'ohlcv-1d',
            'symbols': ['TEST'],
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'stype_in': 'parent',
            'processing_batch_size': 5  # Small batch size for testing
        }
        
        # Initialize components (mocked)
        orchestrator.adapter = mock_adapter
        orchestrator.ohlcv_loader = mock_loader
        
        # Execute pipeline stages
        result = orchestrator._execute_pipeline_stages(job_config)
        
        # Verify execution succeeded
        assert result is True
        
        # Analyze progress updates
        descriptions = [u.get('description', '') for u in all_updates]
        
        # Verify we got updates for all major stages
        assert any('Fetching data' in d for d in descriptions)
        assert any('Processing' in d and 'records' in d for d in descriptions)
        assert any('chunk' in d for d in descriptions)
        assert any('Pipeline completed' in d for d in descriptions)
        
        # Verify we got stage updates
        stages = [u.get('stage') for u in all_updates if 'stage' in u]
        assert 'transformation' in stages
        assert 'validation' in stages
        assert 'storage' in stages
        
        # Verify final stats were included
        final_updates = [u for u in all_updates if 'final_stats' in u]
        assert len(final_updates) > 0