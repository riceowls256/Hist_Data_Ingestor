"""
Pipeline Orchestrator for Historical Data Ingestion.

This module provides the central orchestration logic for coordinating data ingestion
pipelines across different API sources. It manages component initialization,
execution sequencing, error handling, and progress tracking.
"""

import os
import yaml
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

import structlog
from pydantic import BaseModel, ValidationError
from tenacity import RetryError

from src.core.config_manager import ConfigManager
from src.ingestion.api_adapters.base_adapter import BaseAdapter
from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter
from src.transformation.rule_engine import RuleEngine, TransformationError
from src.storage.timescale_loader import TimescaleDefinitionLoader
from src.storage.timescale_ohlcv_loader import TimescaleOHLCVLoader
from src.utils.custom_logger import get_logger

logger = get_logger(__name__)


class PipelineError(Exception):
    """Base exception for pipeline-related errors."""
    pass


class UnsupportedAPIError(PipelineError):
    """Raised when an unsupported API type is requested."""
    pass


class ComponentInitializationError(PipelineError):
    """Raised when a pipeline component fails to initialize."""
    pass


class PipelineExecutionError(PipelineError):
    """Raised when pipeline execution encounters an unrecoverable error."""
    pass


class ComponentFactory:
    """Factory for creating pipeline components based on API type."""

    # Registry of available API adapters
    _adapters: Dict[str, Type[BaseAdapter]] = {
        "databento": DatabentoAdapter,
    }

    @classmethod
    def register_adapter(cls, api_type: str, adapter_class: Type[BaseAdapter]) -> None:
        """Register a new API adapter.

        Args:
            api_type: String identifier for the API type
            adapter_class: BaseAdapter subclass for this API
        """
        cls._adapters[api_type] = adapter_class
        logger.info("Registered new API adapter", api_type=api_type, adapter_class=adapter_class.__name__)

    @classmethod
    def create_adapter(cls, api_type: str, config: Dict[str, Any]) -> BaseAdapter:
        """Create an API adapter instance.

        Args:
            api_type: Type of API adapter to create
            config: Configuration for the adapter

        Returns:
            Initialized adapter instance

        Raises:
            UnsupportedAPIError: If API type is not supported
            ComponentInitializationError: If adapter initialization fails
        """
        if api_type not in cls._adapters:
            available_apis = list(cls._adapters.keys())
            raise UnsupportedAPIError(
                f"Unsupported API type: {api_type}. Available: {available_apis}"
            )

        adapter_class = cls._adapters[api_type]
        try:
            adapter = adapter_class(config)
            logger.info("Created API adapter", api_type=api_type, adapter_class=adapter_class.__name__)
            return adapter
        except Exception as e:
            logger.error("Failed to create API adapter", api_type=api_type, error=str(e))
            raise ComponentInitializationError(f"Failed to initialize {api_type} adapter: {e}") from e


class PipelineStats:
    """Statistics tracking for pipeline execution."""

    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.records_fetched: int = 0
        self.records_transformed: int = 0
        self.records_validated: int = 0
        self.records_stored: int = 0
        self.records_quarantined: int = 0
        self.chunks_processed: int = 0
        self.errors_encountered: int = 0

    def start(self) -> None:
        """Mark the start of pipeline execution."""
        self.start_time = datetime.now(UTC)
        logger.info("Pipeline statistics tracking started", start_time=self.start_time.isoformat())

    def finish(self) -> None:
        """Mark the end of pipeline execution."""
        self.end_time = datetime.now(UTC)
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0

        logger.info(
            "Pipeline execution completed",
            end_time=self.end_time.isoformat(),
            duration_seconds=duration,
            records_fetched=self.records_fetched,
            records_transformed=self.records_transformed,
            records_validated=self.records_validated,
            records_stored=self.records_stored,
            records_quarantined=self.records_quarantined,
            chunks_processed=self.chunks_processed,
            errors_encountered=self.errors_encountered
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for logging/reporting."""
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": duration,
            "records_fetched": self.records_fetched,
            "records_transformed": self.records_transformed,
            "records_validated": self.records_validated,
            "records_stored": self.records_stored,
            "records_quarantined": self.records_quarantined,
            "chunks_processed": self.chunks_processed,
            "errors_encountered": self.errors_encountered
        }


class PipelineOrchestrator:
    """
    Central orchestrator for data ingestion pipelines.

    Coordinates the execution of data ingestion workflows by:
    1. Loading and validating configurations
    2. Initializing appropriate components based on API type
    3. Executing the ETL pipeline sequence
    4. Managing error handling and retry logic
    5. Tracking progress and performance metrics
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None, progress_callback: Optional[callable] = None):
        """
        Initialize the pipeline orchestrator.

        Args:
            config_manager: Optional ConfigManager instance. If None, creates a new one.
            progress_callback: Optional callback function for progress updates. 
                              Signature: progress_callback(description: str, completed: int = 0, 
                                                        total: int = 0, **kwargs)
        """
        self.config_manager = config_manager or ConfigManager()
        self.system_config = self.config_manager.get()
        self.stats = PipelineStats()
        self.progress_callback = progress_callback or (lambda **kwargs: None)

        # Component instances (initialized per pipeline run)
        self.adapter: Optional[BaseAdapter] = None
        self.rule_engine: Optional[RuleEngine] = None
        self.storage_loader: Optional[TimescaleDefinitionLoader] = None
        self.ohlcv_loader: Optional[TimescaleOHLCVLoader] = None
        self.trades_loader = None  # Optional[TimescaleTradesLoader]
        self.tbbo_loader = None    # Optional[TimescaleTBBOLoader]
        self.statistics_loader = None  # Optional[TimescaleStatisticsLoader]

        logger.info("PipelineOrchestrator initialized", has_progress_callback=bool(progress_callback))

    def load_api_config(self, api_type: str) -> Dict[str, Any]:
        """
        Load API-specific configuration file.

        Args:
            api_type: Type of API (e.g., 'databento')

        Returns:
            Parsed configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config format is invalid
            yaml.YAMLError: If YAML parsing fails

        Example:
            >>> orchestrator = PipelineOrchestrator()
            >>> config = orchestrator.load_api_config('databento')
            >>> print(config['jobs'][0]['name'])
            'ohlcv_1d'
        """
        config_path = Path(__file__).parent.parent.parent / "configs" / "api_specific" / f"{api_type}_config.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"API config file not found: {config_path}")

        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            logger.info("Loaded API configuration", api_type=api_type, config_path=str(config_path))
            return config
        except yaml.YAMLError as e:
            logger.error("Failed to parse API configuration", api_type=api_type, error=str(e))
            raise ValidationError(f"Invalid YAML in {config_path}: {e}") from e

    def validate_job_config(self, job_config: Dict[str, Any], api_type: str) -> bool:
        """
        Validate job configuration for the specified API type.

        Args:
            job_config: Job configuration dictionary
            api_type: Type of API

        Returns:
            True if valid, False otherwise
        """
        required_fields = {
            "databento": ["name", "dataset", "schema", "symbols", "start_date", "end_date", "stype_in"]
        }

        if api_type not in required_fields:
            logger.error("Unknown API type for validation", api_type=api_type)
            return False

        missing_fields = []
        for field in required_fields[api_type]:
            if field not in job_config:
                missing_fields.append(field)

        if missing_fields:
            logger.error(
                "Job configuration missing required fields",
                api_type=api_type,
                missing_fields=missing_fields,
                job_config=job_config
            )
            return False

        logger.debug("Job configuration validated successfully", api_type=api_type, job_name=job_config.get("name"))
        return True

    def initialize_components(self, api_type: str, api_config: Dict[str, Any]) -> None:
        """
        Initialize pipeline components for the specified API type.

        Args:
            api_type: Type of API (e.g., 'databento')
            api_config: API-specific configuration

        Raises:
            ComponentInitializationError: If any component fails to initialize
        """
        try:
            # Initialize API adapter
            logger.info("Initializing API adapter", api_type=api_type)
            self.adapter = ComponentFactory.create_adapter(api_type, api_config)

            # Validate adapter configuration
            if not self.adapter.validate_config():
                raise ComponentInitializationError(f"Invalid configuration for {api_type} adapter")

            # Connect to API
            self.adapter.connect()

            # Initialize transformation engine
            transformation_config = api_config.get("transformation", {})
            mapping_config_path = transformation_config.get("mapping_config_path")

            if mapping_config_path:
                logger.info("Initializing RuleEngine", mapping_config_path=mapping_config_path)
                self.rule_engine = RuleEngine(mapping_config_path)
            else:
                logger.warning("No mapping configuration specified, transformation will be skipped")
                self.rule_engine = None

            # Initialize storage loaders
            logger.info("Initializing storage loaders")

            # Check for test environment variables first, fallback to regular config
            if os.getenv('TIMESCALEDB_TEST_HOST'):
                # Use test database configuration
                connection_params = {
                    'host': os.getenv('TIMESCALEDB_TEST_HOST'),
                    'port': int(os.getenv('TIMESCALEDB_TEST_PORT', 5432)),
                    'database': os.getenv('TIMESCALEDB_TEST_DB'),
                    'user': os.getenv('TIMESCALEDB_TEST_USER'),
                    'password': os.getenv('TIMESCALEDB_TEST_PASSWORD')
                }
                logger.info("Using test database configuration")
            else:
                # Use regular configuration
                db_config = self.system_config.db
                connection_params = {
                    'host': db_config.host,
                    'port': db_config.port,
                    'database': db_config.dbname,
                    'user': db_config.user,
                    'password': db_config.password
                }
                logger.info("Using regular database configuration")

            # Initialize all storage loaders
            self.storage_loader = TimescaleDefinitionLoader(connection_params)
            self.ohlcv_loader = TimescaleOHLCVLoader(connection_params)
            
            # Import and initialize new loaders
            from src.storage.timescale_trades_loader import TimescaleTradesLoader
            from src.storage.timescale_tbbo_loader import TimescaleTBBOLoader
            from src.storage.timescale_statistics_loader import TimescaleStatisticsLoader
            
            self.trades_loader = TimescaleTradesLoader(connection_params)
            self.tbbo_loader = TimescaleTBBOLoader(connection_params)
            self.statistics_loader = TimescaleStatisticsLoader(connection_params)

            # Create schemas if they don't exist
            self.ohlcv_loader.create_schema_if_not_exists()
            self.trades_loader.create_schema_if_not_exists()
            self.tbbo_loader.create_schema_if_not_exists()
            self.statistics_loader.create_schema_if_not_exists()
            self.storage_loader.create_schema_if_not_exists()  # Create definitions table

            logger.info("All pipeline components initialized successfully", api_type=api_type)

        except Exception as e:
            logger.error("Failed to initialize pipeline components", api_type=api_type, error=str(e))
            raise ComponentInitializationError(f"Component initialization failed: {e}") from e

    def cleanup_components(self) -> None:
        """Clean up and disconnect pipeline components."""
        if self.adapter:
            try:
                self.adapter.disconnect()
                logger.debug("API adapter disconnected")
            except Exception as e:
                logger.warning("Failed to disconnect adapter", error=str(e))

        if self.storage_loader:
            try:
                # TimescaleDefinitionLoader uses context managers, no explicit close needed
                logger.debug("Storage loader cleanup completed")
            except Exception as e:
                logger.warning("Failed to cleanup storage loader", error=str(e))

        # Reset component references
        self.adapter = None
        self.rule_engine = None
        self.storage_loader = None
        self.ohlcv_loader = None

        logger.info("Pipeline components cleaned up")

    def execute_databento_pipeline(self, job_config: Dict[str, Any]) -> bool:
        """
        Execute the complete Databento data ingestion pipeline.

        This method orchestrates the following sequence:
        1. Fetch data from Databento API (with Pydantic validation)
        2. Transform data using RuleEngine
        3. Validate transformed data
        4. Store data in TimescaleDB
        5. Track progress and handle errors

        Args:
            job_config: Job configuration dictionary

        Returns:
            True if pipeline completed successfully, False otherwise
        """
        job_name = job_config.get("name", "unnamed_job")

        try:
            self.stats.start()
            logger.info("Starting Databento pipeline execution", job_name=job_name, job_config=job_config)

            # Validate job configuration
            if not self.validate_job_config(job_config, "databento"):
                raise PipelineExecutionError("Invalid job configuration")

            # Check component initialization
            if not all([self.adapter, self.storage_loader]):
                raise PipelineExecutionError("Pipeline components not properly initialized")

            # Execute pipeline stages
            success = self._execute_pipeline_stages(job_config)

            if success:
                logger.info("Databento pipeline completed successfully", job_name=job_name)
                return True
            else:
                logger.error("Databento pipeline failed", job_name=job_name)
                return False

        except Exception as e:
            self.stats.errors_encountered += 1
            logger.error(
                "Databento pipeline execution failed",
                job_name=job_name,
                error=str(e),
                error_type=type(e).__name__
            )
            return False
        finally:
            self.stats.finish()

    def _execute_pipeline_stages(self, job_config: Dict[str, Any]) -> bool:
        """
        Execute the core pipeline stages for data processing.

        Args:
            job_config: Job configuration dictionary

        Returns:
            True if all stages completed successfully
        """
        job_name = job_config.get("name", "unnamed_job")

        try:
            # Stage 1: Data Extraction
            logger.info("Pipeline Stage 1: Data Extraction", job_name=job_name)
            self.progress_callback(description=f"Fetching data for {job_name}...")
            data_chunks = self._stage_data_extraction(job_config)
            
            total_chunks = len(data_chunks)
            if total_chunks == 0:
                self.progress_callback(description="No data to process", completed=1, total=1)
                return True
                
            # Calculate total records for progress tracking
            total_records = sum(len(chunk) if hasattr(chunk, '__len__') else 0 for chunk in data_chunks)
            self.progress_callback(
                description=f"Processing {total_records:,} records in {total_chunks} chunks",
                completed=0,
                total=total_records
            )

            records_processed = 0
            for chunk_idx, raw_data_chunk in enumerate(data_chunks):
                chunk_size = len(raw_data_chunk) if hasattr(raw_data_chunk, '__len__') else 0
                
                logger.info(
                    "Processing data chunk",
                    job_name=job_name,
                    chunk_index=chunk_idx,
                    chunk_size=chunk_size
                )
                
                # Update progress for chunk start
                self.progress_callback(
                    description=f"Processing chunk {chunk_idx + 1}/{total_chunks}",
                    completed=records_processed,
                    total=total_records,
                    chunk_progress=0,
                    chunk_total=chunk_size
                )

                # Stage 2: Data Transformation
                logger.debug("Pipeline Stage 2: Data Transformation", job_name=job_name, chunk_index=chunk_idx)
                self.progress_callback(
                    description=f"Transforming chunk {chunk_idx + 1}/{total_chunks}",
                    completed=records_processed,
                    total=total_records,
                    stage="transformation"
                )
                transformed_data = self._stage_data_transformation(raw_data_chunk, job_config, chunk_idx)

                # Stage 3: Data Validation (Post-transformation)
                logger.debug("Pipeline Stage 3: Data Validation", job_name=job_name, chunk_index=chunk_idx)
                self.progress_callback(
                    description=f"Validating chunk {chunk_idx + 1}/{total_chunks}",
                    completed=records_processed,
                    total=total_records,
                    stage="validation"
                )
                validated_data, quarantined_data = self._stage_data_validation(transformed_data, job_name, chunk_idx)

                # Stage 4: Data Storage
                logger.debug("Pipeline Stage 4: Data Storage", job_name=job_name, chunk_index=chunk_idx)
                self.progress_callback(
                    description=f"Storing chunk {chunk_idx + 1}/{total_chunks}",
                    completed=records_processed,
                    total=total_records,
                    stage="storage"
                )
                storage_success = self._stage_data_storage(validated_data, job_name, chunk_idx, job_config)

                if not storage_success:
                    logger.error("Storage stage failed", job_name=job_name, chunk_index=chunk_idx)
                    return False

                # Update statistics and progress
                self.stats.chunks_processed += 1
                self.stats.records_quarantined += len(quarantined_data) if quarantined_data else 0
                records_processed += chunk_size
                
                # Update progress for chunk completion
                self.progress_callback(
                    description=f"Completed chunk {chunk_idx + 1}/{total_chunks}",
                    completed=records_processed,
                    total=total_records,
                    records_stored=self.stats.records_stored,
                    records_quarantined=self.stats.records_quarantined,
                    chunks_processed=self.stats.chunks_processed
                )

                logger.info(
                    "Chunk processing completed",
                    job_name=job_name,
                    chunk_index=chunk_idx,
                    records_stored=len(validated_data) if validated_data else 0,
                    records_quarantined=len(quarantined_data) if quarantined_data else 0
                )

            # Final progress update
            self.progress_callback(
                description=f"Pipeline completed for {job_name}",
                completed=total_records,
                total=total_records,
                final_stats=self.stats.to_dict()
            )

            return True

        except Exception as e:
            logger.error(
                "Pipeline stage execution failed",
                job_name=job_name,
                error=str(e),
                error_type=type(e).__name__
            )
            self.stats.errors_encountered += 1
            self.progress_callback(
                description=f"Pipeline failed: {str(e)}",
                error=True
            )
            return False

    def _stage_data_extraction(self, job_config: Dict[str, Any]) -> List[List[BaseModel]]:
        """
        Stage 1: Extract data from the API with Pydantic validation.

        Args:
            job_config: Job configuration dictionary

        Returns:
            List of data chunks (each chunk is a List[BaseModel])

        Raises:
            PipelineExecutionError: If data extraction fails
        """
        job_name = job_config.get("name", "unnamed_job")

        try:
            # Fetch data using the adapter (includes Pydantic validation)
            # The adapter yields individual BaseModel instances, so we need to collect them into batches
            raw_records = list(self.adapter.fetch_historical_data(job_config))

            # Group records into chunks for processing
            # For now, we'll use a simple batching strategy
            chunk_size = job_config.get("processing_batch_size", 1000)  # Default 1000 records per chunk
            raw_data_chunks = []

            for i in range(0, len(raw_records), chunk_size):
                chunk = raw_records[i:i + chunk_size]
                raw_data_chunks.append(chunk)

            total_records = len(raw_records)
            self.stats.records_fetched = total_records

            logger.info(
                "Data extraction completed",
                job_name=job_name,
                chunks_count=len(raw_data_chunks),
                total_records=total_records,
                chunk_size=chunk_size
            )

            return raw_data_chunks

        except Exception as e:
            logger.error("Data extraction stage failed", job_name=job_name, error=str(e))
            raise PipelineExecutionError(f"Data extraction failed: {e}") from e

    def _stage_data_transformation(self, raw_data: Any, job_config: Dict[str, Any], chunk_idx: int) -> Any:
        """
        Stage 2: Transform data using the RuleEngine.

        Args:
            raw_data: Raw data chunk from extraction stage
            job_config: Job configuration dictionary
            chunk_idx: Chunk index for logging

        Returns:
            Transformed data or original data if no transformation configured
        """
        job_name = job_config.get("name", "unnamed_job")

        try:
            if self.rule_engine:
                # Get schema name from job config
                schema_name = job_config.get("schema", "ohlcv-1d")  # Default fallback
                transformed_data = self.rule_engine.transform_batch(raw_data, schema_name)

                record_count = len(transformed_data) if hasattr(transformed_data, '__len__') else 1
                self.stats.records_transformed += record_count

                logger.debug(
                    "Data transformation completed",
                    job_name=job_name,
                    chunk_index=chunk_idx,
                    records_transformed=record_count
                )

                return transformed_data
            else:
                logger.debug(
                    "No transformation engine configured, skipping transformation",
                    job_name=job_name,
                    chunk_index=chunk_idx
                )
                return raw_data

        except TransformationError as e:
            logger.error(
                "Data transformation failed",
                job_name=job_name,
                chunk_index=chunk_idx,
                error=str(e)
            )
            self.stats.errors_encountered += 1
            # Return original data to allow pipeline to continue
            return raw_data
        except Exception as e:
            logger.error(
                "Unexpected error in transformation stage",
                job_name=job_name,
                chunk_index=chunk_idx,
                error=str(e),
                error_type=type(e).__name__
            )
            self.stats.errors_encountered += 1
            # Return original data to allow pipeline to continue
            return raw_data

    def _stage_data_validation(self, data: Any, job_name: str, chunk_idx: int) -> tuple[Any, Any]:
        """
        Stage 3: Validate transformed data and handle quarantine.

        Args:
            data: Transformed data to validate
            job_name: Job name for logging
            chunk_idx: Chunk index for logging

        Returns:
            Tuple of (validated_data, quarantined_data)
        """
        try:
            # For now, we'll assume validation happens within the adapter
            # Future implementation can add post-transformation validation here

            record_count = len(data) if hasattr(data, '__len__') else 1
            self.stats.records_validated += record_count

            logger.debug(
                "Data validation completed",
                job_name=job_name,
                chunk_index=chunk_idx,
                records_validated=record_count,
                records_quarantined=0
            )

            return data, []

        except Exception as e:
            logger.error(
                "Data validation failed",
                job_name=job_name,
                chunk_index=chunk_idx,
                error=str(e),
                error_type=type(e).__name__
            )
            self.stats.errors_encountered += 1
            # Return original data and empty quarantine list
            return data, []

    def _validate_and_repair_record_dict(self, record_dict: Dict[str, Any], schema: str, job_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate and attempt to repair record dictionary before Pydantic model creation."""
        
        # Make a copy to avoid modifying the original
        repaired_dict = record_dict.copy()
        
        # Apply field name mapping for definition records
        if schema == 'definition':
            repaired_dict = self._apply_definition_field_mapping(repaired_dict)
        
        # Check for required symbol field
        if 'symbol' not in repaired_dict or not repaired_dict['symbol']:
            # Attempt to repair symbol field
            symbols = job_config.get('symbols')
            if symbols:
                if isinstance(symbols, list) and len(symbols) == 1:
                    repaired_dict['symbol'] = symbols[0]
                elif isinstance(symbols, str):
                    repaired_dict['symbol'] = symbols
                else:
                    # Multi-symbol case - use instrument_id or fallback
                    if 'instrument_id' in repaired_dict:
                        repaired_dict['symbol'] = f"INSTRUMENT_{repaired_dict['instrument_id']}"
                    else:
                        repaired_dict['symbol'] = "UNKNOWN_SYMBOL"
                
                logger.info("Repaired missing symbol field", 
                           symbol=repaired_dict['symbol'], 
                           original_symbols=symbols)
            else:
                logger.error("Cannot repair missing symbol field - no symbols in job config", 
                            record_dict=repaired_dict)
                return None
        
        # Validate other required fields based on schema
        required_fields = self._get_required_fields_for_schema(schema)
        missing_fields = [field for field in required_fields if field not in repaired_dict]
        
        if missing_fields:
            logger.error("Cannot repair missing required fields", 
                        missing_fields=missing_fields, 
                        schema=schema,
                        record_dict=repaired_dict)
            return None
        
        return repaired_dict
    
    def _apply_definition_field_mapping(self, record_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply field name mapping for definition records to match Pydantic model field names."""
        
        # Field mappings from transformed dict field names to Pydantic model field names
        field_mappings = {
            'record_type': 'rtype',
            'update_action': 'security_update_action', 
            'instrument_attributes': 'inst_attrib_value',
            'max_trade_volume': 'max_trade_vol',
            'min_block_size': 'min_lot_size_block',
            'min_round_lot_size': 'min_lot_size_round_lot',
            'min_trade_volume': 'min_trade_vol',
            'security_group': 'group',
            'underlying_asset': 'asset',
            'underlying_instrument_id': 'underlying_id',
            'settlement_currency': 'settl_currency',
            'security_subtype': 'secsubtype',
            'cfi_code': 'cfi',
            'underlying_symbol': 'underlying',
            'strike_currency': 'strike_price_currency',
            'matching_algorithm': 'match_algorithm',
            'underlying_product_code': 'underlying_product',
            'is_user_defined': 'user_defined_instrument',
            'application_id': 'appl_id'
        }
        
        mapped_dict = {}
        
        # Copy all fields, applying mappings where needed
        for key, value in record_dict.items():
            mapped_key = field_mappings.get(key, key)
            mapped_dict[mapped_key] = value
        
        # Ensure required fields have default values if missing
        required_defaults = {
            'rtype': 19,
            'security_update_action': 'A',
            'inst_attrib_value': 0,
            'max_trade_vol': 0,
            'min_lot_size_block': 0,
            'min_lot_size_round_lot': 0,
            'min_trade_vol': 0,
            'group': '',
            'asset': ''
        }
        
        for field, default_value in required_defaults.items():
            if field not in mapped_dict:
                mapped_dict[field] = default_value
        
        return mapped_dict

    def _get_required_fields_for_schema(self, schema: str) -> List[str]:
        """Get list of required fields for each schema type."""
        required_fields = {
            'trades': ['ts_event', 'instrument_id', 'price', 'size', 'symbol'],
            'tbbo': ['ts_event', 'instrument_id', 'symbol'],
            'ohlcv': ['ts_event', 'instrument_id', 'symbol', 'open_price', 'high_price', 'low_price', 'close_price'],
            'statistics': ['ts_event', 'instrument_id', 'symbol', 'stat_type']
        }
        
        schema_base = schema.split('-')[0] if '-' in schema else schema
        return required_fields.get(schema_base, ['ts_event', 'symbol'])

    def _normalize_schema_name_for_storage(self, schema_name: str) -> str:
        """
        Normalize schema names for consistent storage routing.
        Uses the same mapping as the databento adapter.
        """
        schema_aliases = {
            "definitions": "definition",
            "stats": "statistics", 
            "ohlcv": "ohlcv-1d",
        }
        return schema_aliases.get(schema_name, schema_name)

    def _stage_data_storage(self, data: Any, job_name: str, chunk_idx: int, job_config: Dict[str, Any]) -> bool:
        """
        Stage 4: Store validated data in TimescaleDB using appropriate loader.

        Args:
            data: Validated data to store
            job_name: Job name for logging
            job_config: Job configuration containing schema and other metadata
            chunk_idx: Chunk index for logging

        Returns:
            True if storage succeeded, False otherwise
        """
        # Bind context for storage operations
        storage_logger = logger.bind(
            job_name=job_name,
            chunk_index=chunk_idx,
            operation="data_storage"
        )

        try:
            if not data:
                storage_logger.debug("No data to store")
                return True

            # Determine record type and use appropriate storage loader
            records_list = data if isinstance(data, list) else [data]

            if not records_list:
                return True

            # Check the type of the first record to determine storage strategy
            first_record = records_list[0]

            from src.storage.models import (
                DatabentoOHLCVRecord, 
                DatabentoDefinitionRecord, 
                DatabentoStatisticsRecord,
                DatabentoTradeRecord,
                DatabentoTBBORecord
            )

            # First check if records are Pydantic models (no transformation applied)
            if isinstance(first_record, DatabentoOHLCVRecord):
                # Use OHLCV loader for OHLCV records
                storage_logger = storage_logger.bind(storage_type="ohlcv", table="daily_ohlcv_data")
                storage_logger.debug("Storing OHLCV records")
                # Extract granularity from schema (e.g., 'ohlcv-1d' -> '1d')
                schema = job_config.get('schema', 'ohlcv-1d')
                granularity = schema.split('-')[-1] if '-' in schema else '1d'
                data_source = job_config.get('api', 'databento')
                
                self.ohlcv_loader.insert_ohlcv_records(
                    records_list, 
                    granularity=granularity,
                    data_source=data_source
                )
            elif isinstance(first_record, DatabentoTradeRecord):
                # Use Trades loader for trade records
                storage_logger = storage_logger.bind(storage_type="trades", table="trades_data")
                storage_logger.debug("Storing Trade records")
                data_source = job_config.get('api', 'databento')
                
                stats = self.trades_loader.insert_trades_records(
                    records_list,
                    data_source=data_source
                )
                self.stats.records_stored += stats['inserted']
                if stats['errors'] > 0:
                    storage_logger.warning(f"Failed to store {stats['errors']} trade records")
                return True
            elif isinstance(first_record, DatabentoTBBORecord):
                # Use TBBO loader for TBBO records
                storage_logger = storage_logger.bind(storage_type="tbbo", table="tbbo_data")
                storage_logger.debug("Storing TBBO records")
                data_source = job_config.get('api', 'databento')
                
                stats = self.tbbo_loader.insert_tbbo_records(
                    records_list,
                    data_source=data_source
                )
                self.stats.records_stored += stats['inserted']
                if stats['errors'] > 0:
                    storage_logger.warning(f"Failed to store {stats['errors']} TBBO records")
                return True
            elif isinstance(first_record, DatabentoStatisticsRecord):
                # Use Statistics loader for statistics records
                storage_logger = storage_logger.bind(storage_type="statistics", table="statistics_data")
                storage_logger.debug("Storing Statistics records")
                data_source = job_config.get('api', 'databento')
                
                stats = self.statistics_loader.insert_statistics_records(
                    records_list,
                    data_source=data_source
                )
                self.stats.records_stored += stats['inserted']
                if stats['errors'] > 0:
                    storage_logger.warning(f"Failed to store {stats['errors']} statistics records")
                return True
            elif isinstance(first_record, DatabentoDefinitionRecord):
                # Use Definition loader for Definition records
                storage_logger = storage_logger.bind(storage_type="definition", table="definitions")
                storage_logger.debug("Storing Definition records")
                stats = self.storage_loader.insert_definition_records(records_list)
                if isinstance(stats, dict):
                    self.stats.records_stored += stats.get('inserted', 0)
                    if stats.get('errors', 0) > 0:
                        storage_logger.warning(f"Failed to store {stats['errors']} definition records")
                else:
                    # Fallback for loaders that don't return stats dict
                    self.stats.records_stored += len(records_list)
                
                storage_logger.debug(
                    "Data storage completed",
                    records_stored=len(records_list),
                    record_type=type(first_record).__name__
                )
                return True
            elif isinstance(first_record, dict):
                # Records have been transformed to dictionaries - use schema from job config
                raw_schema = job_config.get('schema', '').lower()
                # Normalize schema name for consistent storage routing
                schema = self._normalize_schema_name_for_storage(raw_schema)
                data_source = job_config.get('api', 'databento')
                
                if 'ohlcv' in schema:
                    # Use OHLCV loader for transformed OHLCV records
                    storage_logger = storage_logger.bind(storage_type="ohlcv", table="daily_ohlcv_data")
                    storage_logger.debug("Storing transformed OHLCV records")
                    granularity = schema.split('-')[-1] if '-' in schema else '1d'
                    
                    # Convert dicts back to Pydantic models for the loader with validation and repair
                    pydantic_records = []
                    repair_stats = {'repaired': 0, 'failed_repair': 0, 'conversion_errors': 0}
                    
                    for record_dict in records_list:
                        # Pre-validate and repair if needed
                        validated_dict = self._validate_and_repair_record_dict(record_dict, schema, job_config)
                        
                        if validated_dict is None:
                            repair_stats['failed_repair'] += 1
                            self.stats.errors_encountered += 1
                            continue
                        
                        if validated_dict != record_dict:
                            repair_stats['repaired'] += 1
                        
                        try:
                            pydantic_record = DatabentoOHLCVRecord(**validated_dict)
                            pydantic_records.append(pydantic_record)
                        except ValidationError as e:
                            repair_stats['conversion_errors'] += 1
                            storage_logger.error("Failed to convert validated dict to OHLCV model", 
                                               error=str(e),
                                               validated_dict=validated_dict,
                                               original_dict=record_dict)
                            self.stats.errors_encountered += 1
                    
                    # Log repair statistics
                    if any(repair_stats.values()):
                        storage_logger.info("Record repair statistics", **repair_stats)
                    
                    if pydantic_records:
                        self.ohlcv_loader.insert_ohlcv_records(
                            pydantic_records, 
                            granularity=granularity,
                            data_source=data_source
                        )
                        self.stats.records_stored += len(pydantic_records)
                elif schema == 'trades':
                    # Use Trades loader for transformed trade records
                    storage_logger = storage_logger.bind(storage_type="trades", table="trades_data")
                    storage_logger.debug("Storing transformed Trade records")
                    
                    # Convert dicts back to Pydantic models for the loader with validation and repair
                    pydantic_records = []
                    repair_stats = {'repaired': 0, 'failed_repair': 0, 'conversion_errors': 0}
                    
                    for record_dict in records_list:
                        # Pre-validate and repair if needed
                        validated_dict = self._validate_and_repair_record_dict(record_dict, schema, job_config)
                        
                        if validated_dict is None:
                            repair_stats['failed_repair'] += 1
                            self.stats.errors_encountered += 1
                            continue
                        
                        if validated_dict != record_dict:
                            repair_stats['repaired'] += 1
                        
                        try:
                            pydantic_record = DatabentoTradeRecord(**validated_dict)
                            pydantic_records.append(pydantic_record)
                        except ValidationError as e:
                            repair_stats['conversion_errors'] += 1
                            storage_logger.error("Failed to convert validated dict to Trade model", 
                                               error=str(e),
                                               validated_dict=validated_dict,
                                               original_dict=record_dict)
                            self.stats.errors_encountered += 1
                    
                    # Log repair statistics
                    if any(repair_stats.values()):
                        storage_logger.info("Record repair statistics", **repair_stats)
                    
                    if pydantic_records:
                        stats = self.trades_loader.insert_trades_records(
                            pydantic_records,
                            data_source=data_source
                        )
                        self.stats.records_stored += stats['inserted']
                        if stats['errors'] > 0:
                            storage_logger.warning(f"Failed to store {stats['errors']} trade records")
                elif schema == 'tbbo':
                    # Use TBBO loader for transformed TBBO records
                    storage_logger = storage_logger.bind(storage_type="tbbo", table="tbbo_data")
                    storage_logger.debug("Storing transformed TBBO records")
                    
                    # Convert dicts back to Pydantic models for the loader with validation and repair
                    pydantic_records = []
                    repair_stats = {'repaired': 0, 'failed_repair': 0, 'conversion_errors': 0}
                    
                    for record_dict in records_list:
                        # Pre-validate and repair if needed
                        validated_dict = self._validate_and_repair_record_dict(record_dict, schema, job_config)
                        
                        if validated_dict is None:
                            repair_stats['failed_repair'] += 1
                            self.stats.errors_encountered += 1
                            continue
                        
                        if validated_dict != record_dict:
                            repair_stats['repaired'] += 1
                        
                        try:
                            pydantic_record = DatabentoTBBORecord(**validated_dict)
                            pydantic_records.append(pydantic_record)
                        except ValidationError as e:
                            repair_stats['conversion_errors'] += 1
                            storage_logger.error("Failed to convert validated dict to TBBO model", 
                                               error=str(e),
                                               validated_dict=validated_dict,
                                               original_dict=record_dict)
                            self.stats.errors_encountered += 1
                    
                    # Log repair statistics
                    if any(repair_stats.values()):
                        storage_logger.info("Record repair statistics", **repair_stats)
                    
                    if pydantic_records:
                        stats = self.tbbo_loader.insert_tbbo_records(
                            pydantic_records,
                            data_source=data_source
                        )
                        self.stats.records_stored += stats['inserted']
                        if stats['errors'] > 0:
                            storage_logger.warning(f"Failed to store {stats['errors']} TBBO records")
                elif schema == 'statistics':
                    # Use Statistics loader for transformed statistics records
                    storage_logger = storage_logger.bind(storage_type="statistics", table="statistics_data")
                    storage_logger.debug("Storing transformed Statistics records")
                    
                    # Convert dicts back to Pydantic models for the loader with validation and repair
                    pydantic_records = []
                    repair_stats = {'repaired': 0, 'failed_repair': 0, 'conversion_errors': 0}
                    
                    for record_dict in records_list:
                        # Create a new dict with proper field mappings
                        # The transformation maps stat_value to price, but the model expects stat_value
                        model_dict = record_dict.copy()
                        if 'price' in model_dict and 'stat_value' not in model_dict:
                            model_dict['stat_value'] = model_dict.pop('price')
                        
                        # Pre-validate and repair if needed
                        validated_dict = self._validate_and_repair_record_dict(model_dict, schema, job_config)
                        
                        if validated_dict is None:
                            repair_stats['failed_repair'] += 1
                            self.stats.errors_encountered += 1
                            continue
                        
                        if validated_dict != model_dict:
                            repair_stats['repaired'] += 1
                        
                        try:
                            pydantic_record = DatabentoStatisticsRecord(**validated_dict)
                            pydantic_records.append(pydantic_record)
                        except ValidationError as e:
                            repair_stats['conversion_errors'] += 1
                            storage_logger.error("Failed to convert validated dict to Statistics model", 
                                               error=str(e),
                                               validated_dict=validated_dict,
                                               original_dict=record_dict)
                            self.stats.errors_encountered += 1
                    
                    # Log repair statistics
                    if any(repair_stats.values()):
                        storage_logger.info("Record repair statistics", **repair_stats)
                    
                    if pydantic_records:
                        stats = self.statistics_loader.insert_statistics_records(
                            pydantic_records,
                            data_source=data_source
                        )
                        self.stats.records_stored += stats['inserted']
                        if stats['errors'] > 0:
                            storage_logger.warning(f"Failed to store {stats['errors']} statistics records")
                elif schema == 'definition':
                    # Use Definition loader for transformed definition records
                    storage_logger = storage_logger.bind(storage_type="definition", table="definitions_data")
                    storage_logger.debug("Storing transformed Definition records")
                    
                    # Convert dicts back to Pydantic models for the loader with validation and repair
                    pydantic_records = []
                    repair_stats = {'repaired': 0, 'failed_repair': 0, 'conversion_errors': 0}
                    
                    for record_dict in records_list:
                        # Pre-validate and repair if needed
                        validated_dict = self._validate_and_repair_record_dict(record_dict, schema, job_config)
                        
                        if validated_dict is None:
                            repair_stats['failed_repair'] += 1
                            self.stats.errors_encountered += 1
                            continue
                        
                        if validated_dict != record_dict:
                            repair_stats['repaired'] += 1
                        
                        try:
                            pydantic_record = DatabentoDefinitionRecord(**validated_dict)
                            pydantic_records.append(pydantic_record)
                        except ValidationError as e:
                            repair_stats['conversion_errors'] += 1
                            storage_logger.error("Failed to convert validated dict to Definition model", 
                                               error=str(e),
                                               validated_dict=validated_dict,
                                               original_dict=record_dict)
                            self.stats.errors_encountered += 1
                    
                    # Log repair statistics
                    if any(repair_stats.values()):
                        storage_logger.info("Record repair statistics", **repair_stats)
                    
                    if pydantic_records:
                        stats = self.storage_loader.insert_definition_records(pydantic_records)
                        if isinstance(stats, dict):
                            self.stats.records_stored += stats.get('inserted', 0)
                            if stats.get('errors', 0) > 0:
                                storage_logger.warning(f"Failed to store {stats['errors']} definition records")
                        else:
                            # Fallback for loaders that don't return stats dict
                            self.stats.records_stored += len(pydantic_records)
                else:
                    # Unknown schema type
                    storage_logger.error(
                        "Unknown schema type for dictionary records",
                        schema=schema,
                        record_dict=first_record
                    )
                    return False
                
                return True
            else:
                # Unknown record type
                storage_logger = storage_logger.bind(storage_type="unknown", table="unknown")
                storage_logger.error(
                    "Unknown record type, cannot store",
                    record_type=type(first_record).__name__,
                    record_dict=first_record if isinstance(first_record, dict) else None
                )
                return False

            record_count = len(records_list)
            self.stats.records_stored += record_count

            storage_logger.debug(
                "Data storage completed",
                records_stored=record_count,
                record_type=type(first_record).__name__
            )

            return True

        except Exception as e:
            storage_logger.error(
                "Data storage failed",
                error=str(e),
                error_type=type(e).__name__
            )
            self.stats.errors_encountered += 1
            return False

    def execute_ingestion(
        self,
        api_type: str,
        job_name: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Execute a complete data ingestion pipeline.

        This is the main entry point for pipeline execution. It loads configuration,
        initializes components, and executes the appropriate pipeline based on API type.

        Args:
            api_type: Type of API to use (e.g., 'databento')
            job_name: Name of predefined job in config, or None for custom job
            overrides: Optional parameter overrides for the job

        Returns:
            True if pipeline completed successfully, False otherwise

        Raises:
            UnsupportedAPIError: If API type is not supported
            ComponentInitializationError: If component initialization fails
            PipelineExecutionError: If pipeline execution fails
            FileNotFoundError: If configuration files are missing

        Example:
            >>> orchestrator = PipelineOrchestrator()
            >>> # Execute predefined job
            >>> success = orchestrator.execute_ingestion('databento', 'ohlcv_1d')
            >>>
            >>> # Execute custom job with overrides
            >>> overrides = {
            ...     'dataset': 'GLBX.MDP3',
            ...     'schema': 'ohlcv-1d',
            ...     'symbols': ['ES.FUT'],
            ...     'start_date': '2024-01-01',
            ...     'end_date': '2024-01-31'
            ... }
            >>> success = orchestrator.execute_ingestion('databento', overrides=overrides)
        """
        try:
            logger.info(
                "Starting ingestion pipeline",
                api_type=api_type,
                job_name=job_name,
                overrides=overrides
            )

            # Load API-specific configuration
            api_config = self.load_api_config(api_type)

            # Get job configuration
            if job_name:
                job_config = self._get_predefined_job_config(api_config, job_name)
            else:
                job_config = self._build_job_config_from_overrides(overrides or {})

            # Apply any overrides
            if overrides:
                job_config.update(overrides)

            # Initialize pipeline components
            self.initialize_components(api_type, api_config)

            # Execute the appropriate pipeline
            if api_type == "databento":
                success = self.execute_databento_pipeline(job_config)
            else:
                raise UnsupportedAPIError(f"Pipeline execution not implemented for API type: {api_type}")

            return success

        except Exception as e:
            logger.error(
                "Ingestion pipeline failed",
                api_type=api_type,
                job_name=job_name,
                error=str(e),
                error_type=type(e).__name__
            )
            return False
        finally:
            self.cleanup_components()

    def _get_predefined_job_config(self, api_config: Dict[str, Any], job_name: str) -> Dict[str, Any]:
        """Get a predefined job configuration by name."""
        jobs = api_config.get("jobs", [])

        for job in jobs:
            if job.get("name") == job_name:
                logger.info("Found predefined job configuration", job_name=job_name)
                return job.copy()

        available_jobs = [job.get("name") for job in jobs if job.get("name")]
        raise ValueError(f"Job '{job_name}' not found. Available jobs: {available_jobs}")

    def _build_job_config_from_overrides(self, overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Build job configuration from override parameters."""
        # Create a job config with a default name if not provided
        job_config = overrides.copy()
        
        # Add a default name based on schema and symbols if not provided
        if 'name' not in job_config:
            schema = job_config.get('schema', 'custom')
            symbols = job_config.get('symbols', [])
            symbol_str = '_'.join(symbols[:2]) if symbols else 'data'  # Use first 2 symbols for brevity
            job_config['name'] = f"cli_{schema}_{symbol_str}"
        
        logger.info("Building job configuration from overrides", job_config=job_config)
        return job_config
