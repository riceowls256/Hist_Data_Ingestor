"""
Unit tests for DatabentoAdapter.

Tests the DatabentoAdapter class functionality including configuration validation,
connection establishment, data fetching with retries, and error handling.
"""

import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pytest
from pydantic import ValidationError

import databento
from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter
from src.storage.models import DatabentoOHLCVRecord, DatabentoTradeRecord


class TestDatabentoAdapter:
    """Test cases for DatabentoAdapter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.valid_config = {
            "api": {
                "key_env_var": "DATABENTO_API_KEY",
                "base_url": "https://hist.databento.com",
                "timeout": 30
            },
            "retry_policy": {
                "max_retries": 3,
                "base_delay": 1.0,
                "max_delay": 60.0,
                "backoff_multiplier": 2.0
            }
        }
        
        self.job_config = {
            "name": "test_job",
            "dataset": "GLBX.MDP3",
            "schema": "ohlcv-1m",
            "symbols": ["ES.FUT", "CL.FUT"],
            "stype_in": "continuous",
            "start_date": "2023-01-01",
            "end_date": "2023-01-02",
            "date_chunk_interval_days": 1
        }

    def test_init_with_valid_config(self):
        """Test adapter initialization with valid configuration."""
        adapter = DatabentoAdapter(self.valid_config)
        
        assert adapter.config == self.valid_config
        assert adapter.max_retries == 3
        assert adapter.base_delay == 1.0
        assert adapter.max_delay == 60.0
        assert adapter.backoff_multiplier == 2.0
        assert adapter._client is None

    def test_init_with_default_retry_config(self):
        """Test adapter initialization with default retry configuration."""
        config = {"api": {"key_env_var": "DATABENTO_API_KEY"}}
        adapter = DatabentoAdapter(config)
        
        assert adapter.max_retries == 3
        assert adapter.base_delay == 1.0
        assert adapter.max_delay == 60.0
        assert adapter.backoff_multiplier == 2.0

    @patch.dict(os.environ, {"DATABENTO_API_KEY": "test_key"})
    def test_validate_config_success(self):
        """Test successful configuration validation."""
        adapter = DatabentoAdapter(self.valid_config)
        assert adapter.validate_config() is True

    def test_validate_config_missing_key_env_var(self):
        """Test configuration validation with missing key_env_var."""
        config = {"api": {}}
        adapter = DatabentoAdapter(config)
        assert adapter.validate_config() is False

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_config_missing_env_var(self):
        """Test configuration validation with missing environment variable."""
        adapter = DatabentoAdapter(self.valid_config)
        assert adapter.validate_config() is False

    @patch.dict(os.environ, {"DATABENTO_API_KEY": "test_key"})
    @patch('src.ingestion.api_adapters.databento_adapter.databento.Historical')
    def test_connect_success(self, mock_historical_class):
        """Test successful connection to Databento API."""
        mock_client = Mock()
        mock_historical_class.return_value = mock_client
        
        adapter = DatabentoAdapter(self.valid_config)
        adapter.connect()
        
        mock_historical_class.assert_called_once_with(key="test_key")
        assert adapter._client == mock_client

    def test_connect_invalid_config(self):
        """Test connection with invalid configuration."""
        config = {"api": {}}
        adapter = DatabentoAdapter(config)
        
        with pytest.raises(ValueError, match="Invalid configuration"):
            adapter.connect()

    @patch.dict(os.environ, {"DATABENTO_API_KEY": "test_key"})
    @patch('src.ingestion.api_adapters.databento_adapter.databento.Historical')
    def test_connect_client_initialization_error(self, mock_historical_class):
        """Test connection failure during client initialization."""
        mock_historical_class.side_effect = Exception("API error")
        
        adapter = DatabentoAdapter(self.valid_config)
        
        with pytest.raises(ConnectionError, match="Could not establish connection"):
            adapter.connect()

    def test_generate_date_chunks_no_chunking(self):
        """Test date chunk generation without chunking."""
        adapter = DatabentoAdapter(self.valid_config)
        
        chunks = adapter._generate_date_chunks("2023-01-01", "2023-01-31", None)
        
        assert len(chunks) == 1
        assert chunks[0] == ("2023-01-01", "2023-01-31")

    def test_generate_date_chunks_with_chunking(self):
        """Test date chunk generation with chunking."""
        adapter = DatabentoAdapter(self.valid_config)
        
        chunks = adapter._generate_date_chunks("2023-01-01", "2023-01-05", 2)
        
        # 2023-01-01 to 2023-01-05 with 2-day chunks should create 2 chunks:
        # Chunk 1: 2023-01-01 to 2023-01-03 (2 days)
        # Chunk 2: 2023-01-03 to 2023-01-05 (2 days)
        assert len(chunks) == 2
        assert chunks[0][0] == "2023-01-01T00:00:00"
        assert chunks[1][1] == "2023-01-05T00:00:00"

    @patch.dict(os.environ, {"DATABENTO_API_KEY": "test_key"})
    @patch('src.ingestion.api_adapters.databento_adapter.databento.Historical')
    def test_fetch_data_chunk_success(self, mock_historical_class):
        """Test successful data chunk fetching."""
        mock_client = Mock()
        mock_dbn_store = Mock()
        mock_client.timeseries.get_range.return_value = mock_dbn_store
        mock_historical_class.return_value = mock_client
        
        adapter = DatabentoAdapter(self.valid_config)
        adapter.connect()
        
        result = adapter._fetch_data_chunk(
            dataset="GLBX.MDP3",
            schema="ohlcv-1m",
            symbols=["ES.FUT"],
            stype_in="continuous",
            start_date="2023-01-01",
            end_date="2023-01-02"
        )
        
        assert result == mock_dbn_store
        mock_client.timeseries.get_range.assert_called_once_with(
            dataset="GLBX.MDP3",
            symbols=["ES.FUT"],
            schema="ohlcv-1m",
            start="2023-01-01",
            end="2023-01-02",
            stype_in="continuous"
        )

    def test_fetch_data_chunk_not_connected(self):
        """Test data chunk fetching when client is not connected."""
        adapter = DatabentoAdapter(self.valid_config)
        
        with pytest.raises(ConnectionError, match="Client not connected"):
            adapter._fetch_data_chunk(
                dataset="GLBX.MDP3",
                schema="ohlcv-1m",
                symbols=["ES.FUT"],
                stype_in="continuous",
                start_date="2023-01-01",
                end_date="2023-01-02"
            )

    @patch.dict(os.environ, {"DATABENTO_API_KEY": "test_key"})
    @patch('src.ingestion.api_adapters.databento_adapter.databento.Historical')
    def test_fetch_historical_data_success(self, mock_historical_class):
        """Test successful historical data fetching."""
        # Mock the client and data
        mock_client = Mock()
        mock_historical_class.return_value = mock_client
        
        # Create mock records
        mock_record1 = Mock()
        mock_record1.as_dict.return_value = {
            "ts_event": datetime(2023, 1, 1, 12, 0),
            "ts_init": None,
            "instrument_id": 12345,
            "symbol": "ES.FUT",
            "open": "4000.50",
            "high": "4010.25",
            "low": "3995.75",
            "close": "4005.00",
            "volume": 1000,
            "vwap": None,
            "count": None
        }
        
        mock_record2 = Mock()
        mock_record2.as_dict.return_value = {
            "ts_event": datetime(2023, 1, 1, 12, 1),
            "ts_init": None,
            "instrument_id": 12345,
            "symbol": "ES.FUT",
            "open": "4005.00",
            "high": "4015.50",
            "low": "4000.25",
            "close": "4012.75",
            "volume": 1200,
            "vwap": None,
            "count": None
        }
        
        mock_dbn_store = Mock()
        mock_dbn_store.__iter__ = Mock(return_value=iter([mock_record1, mock_record2]))
        mock_client.timeseries.get_range.return_value = mock_dbn_store
        
        adapter = DatabentoAdapter(self.valid_config)
        adapter.connect()
        
        # Test data fetching
        records = list(adapter.fetch_historical_data(self.job_config))
        
        assert len(records) == 2
        assert all(isinstance(record, DatabentoOHLCVRecord) for record in records)
        assert records[0].symbol == "ES.FUT"
        assert records[0].open == 4000.50

    def test_fetch_historical_data_not_connected(self):
        """Test historical data fetching when client is not connected."""
        adapter = DatabentoAdapter(self.valid_config)
        
        with pytest.raises(ConnectionError, match="Client not connected"):
            list(adapter.fetch_historical_data(self.job_config))

    def test_fetch_historical_data_missing_parameters(self):
        """Test historical data fetching with missing parameters."""
        adapter = DatabentoAdapter(self.valid_config)
        adapter._client = Mock()  # Mock connection
        
        incomplete_config = {"schema": "ohlcv-1m"}
        
        with pytest.raises(ValueError, match="Missing required job configuration"):
            list(adapter.fetch_historical_data(incomplete_config))

    def test_fetch_historical_data_unsupported_schema(self):
        """Test historical data fetching with unsupported schema."""
        adapter = DatabentoAdapter(self.valid_config)
        adapter._client = Mock()  # Mock connection
        
        invalid_job_config = self.job_config.copy()
        invalid_job_config["schema"] = "unsupported_schema"
        
        with pytest.raises(ValueError, match="Unsupported schema"):
            list(adapter.fetch_historical_data(invalid_job_config))

    @patch.dict(os.environ, {"DATABENTO_API_KEY": "test_key"})
    @patch('src.ingestion.api_adapters.databento_adapter.databento.Historical')
    def test_fetch_historical_data_validation_error(self, mock_historical_class):
        """Test handling of Pydantic validation errors during data fetching."""
        mock_client = Mock()
        mock_historical_class.return_value = mock_client
        
        # Create mock record with invalid data
        mock_record = Mock()
        mock_record.as_dict.return_value = {
            "ts_event": "invalid_datetime",  # Invalid datetime
            "symbol": "ES.FUT",
            "open": "not_a_number"  # Invalid decimal
        }
        
        mock_dbn_store = Mock()
        mock_dbn_store.__iter__ = Mock(return_value=iter([mock_record]))
        mock_client.timeseries.get_range.return_value = mock_dbn_store
        
        adapter = DatabentoAdapter(self.valid_config)
        adapter.connect()
        
        # Should handle validation errors gracefully
        records = list(adapter.fetch_historical_data(self.job_config))
        
        # No records should be yielded due to validation failures
        assert len(records) == 0

    def test_disconnect(self):
        """Test disconnection from Databento API."""
        adapter = DatabentoAdapter(self.valid_config)
        adapter._client = Mock()
        
        adapter.disconnect()
        
        assert adapter._client is None

    def test_context_manager(self):
        """Test using adapter as context manager."""
        with patch.dict(os.environ, {"DATABENTO_API_KEY": "test_key"}):
            with patch('src.ingestion.api_adapters.databento_adapter.databento.Historical') as mock_historical:
                mock_client = Mock()
                mock_historical.return_value = mock_client
                
                with DatabentoAdapter(self.valid_config) as adapter:
                    assert adapter._client == mock_client
                
                # Client should be disconnected after context exit
                assert adapter._client is None 