"""
Databento API Adapter for historical data extraction.

This module implements the DatabentoAdapter class that connects to the Databento API
using the official databento-python client library to fetch historical market data.
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, Iterator, List, Optional

import databento
import structlog
from pydantic import BaseModel, ValidationError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)
from src.utils.custom_logger import get_logger

from src.ingestion.api_adapters.base_adapter import BaseAdapter
from src.storage.models import DATABENTO_SCHEMA_MODEL_MAPPING

logger = get_logger(__name__)

class DatabentoAdapter(BaseAdapter):
    """
    API Adapter for Databento that fetches historical market data.
    
    This adapter uses the official databento-python client library to connect to
    the Databento API, fetch data for configured symbols and schemas, and convert
    DBN records into validated Pydantic models.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the DatabentoAdapter with configuration.
        
        Args:
            config: Configuration dictionary containing API settings and retry policy
        """
        super().__init__(config)
        self.client = None
        
        # Extract retry policy from config
        retry_config = self.config.get("retry_policy", {})
        self.max_retries = retry_config.get("max_retries", 3)
        self.base_delay = retry_config.get("base_delay", 1.0)
        self.max_delay = retry_config.get("max_delay", 60.0)
        self.backoff_multiplier = retry_config.get("backoff_multiplier", 2.0)

    def validate_config(self) -> bool:
        """
        Validate the adapter configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        api_config = self.config.get("api", {})
        key_env_var = api_config.get("key_env_var")
        
        if not key_env_var:
            self.log.error("Missing key_env_var in api configuration")
            return False
            
        api_key = os.getenv(key_env_var)
        if not api_key:
            self.log.error("API key not found in environment", env_var=key_env_var)
            return False
            
        return True

    def connect(self) -> None:
        """
        Connects to the Databento API.
        It can be configured with a direct 'key' or a 'key_env_var' to read from the environment.
        """
        api_config = self.config.get('api', {})
        api_key = api_config.get('key')

        if not api_key:
            key_env_var = api_config.get('key_env_var')
            if not key_env_var:
                logger.error("API config must contain either 'key' or 'key_env_var'")
                raise ValueError("Invalid configuration: Missing API key source.")
            
            api_key = os.getenv(key_env_var)
            if not api_key:
                logger.error(f"Environment variable '{key_env_var}' not set for Databento API key.")
                raise ValueError(f"Missing API key in environment variable {key_env_var}")

        try:
            self.client = databento.Historical(key=api_key)
            logger.info("Successfully connected to Databento API")
        except Exception as e:
            logger.error(f"Failed to connect to Databento API: {e}")
            raise

    def _create_retry_decorator(self):
        """Create a retry decorator with current configuration."""
        return retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(
                multiplier=self.backoff_multiplier,
                min=self.base_delay,
                max=self.max_delay
            ),
            retry=retry_if_exception_type((
                databento.BentoError,
                ConnectionError,
                TimeoutError,
            )),
            reraise=True
        )

    def _fetch_data_chunk(
        self,
        dataset: str,
        schema: str,
        symbols: List[str],
        stype_in: str,
        start_date: str,
        end_date: str
    ) -> databento.DBNStore:
        """
        Fetch a single chunk of data from Databento API with retry logic.
        
        Args:
            dataset: Dataset identifier (e.g., "GLBX.MDP3")
            schema: Schema type (e.g., "ohlcv-1m", "trades")
            symbols: List of symbols to fetch
            stype_in: Symbol type (e.g., "continuous", "native")
            start_date: Start date in ISO format
            end_date: End date in ISO format
            
        Returns:
            DBNStore: Raw data store from Databento API
            
        Raises:
            ConnectionError: If client is not connected
            RuntimeError: If API call fails after retries
        """
        if not self.client:
            raise ConnectionError("Client not connected. Call connect() first.")
            
        retry_decorator = self._create_retry_decorator()
        
        @retry_decorator
        def _make_api_call():
            logger.info(
                "Fetching data chunk from Databento API",
                dataset=dataset,
                schema=schema,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date
            )
            return self.client.timeseries.get_range(
                dataset=dataset,
                symbols=symbols,
                schema=schema,
                start=start_date,
                end=end_date,
                stype_in=stype_in
            )
        
        try:
            return _make_api_call()
        except RetryError as e:
            logger.error(
                "Failed to fetch data after all retries",
                dataset=dataset,
                schema=schema,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                error=str(e)
            )
            raise RuntimeError("Failed to fetch data from Databento API") from e

    def _generate_date_chunks(
        self,
        start_date: str,
        end_date: str,
        chunk_interval_days: Optional[int]
    ) -> List[tuple[str, str]]:
        """
        Generate date chunks for processing large date ranges.
        
        Args:
            start_date: Start date in ISO format
            end_date: End date in ISO format  
            chunk_interval_days: Number of days per chunk, None for no chunking
            
        Returns:
            List of (start_date, end_date) tuples for each chunk
        """
        if not chunk_interval_days:
            return [(start_date, end_date)]
            
        chunks = []
        current_start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        final_end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        while current_start < final_end:
            current_end = min(
                current_start + timedelta(days=chunk_interval_days),
                final_end
            )
            chunks.append((
                current_start.isoformat(),
                current_end.isoformat()
            ))
            current_start = current_end
            
        logger.info(f"Generated {len(chunks)} date chunks", chunks=len(chunks))
        return chunks

    def fetch_historical_data(self, job_config: Dict[str, Any]) -> Iterator[BaseModel]:
        """
        Fetch historical data based on job configuration.
        
        Args:
            job_config: Job configuration containing dataset, schema, symbols, date range, etc.
            
        Yields:
            BaseModel: Validated Pydantic model instances containing the fetched data
            
        Raises:
            ValueError: If job configuration is invalid
            ConnectionError: If API connection fails
            RuntimeError: If data fetching fails
        """
        if not self.client:
            raise ConnectionError("Client not connected. Call connect() first.")
            
        # Extract job parameters
        dataset = job_config.get("dataset")
        schema = job_config.get("schema")
        symbols = job_config.get("symbols", [])
        stype_in = job_config.get("stype_in", "continuous")
        start_date = job_config.get("start_date")
        end_date = job_config.get("end_date")
        chunk_interval_days = job_config.get("date_chunk_interval_days")
        
        # Validate required parameters
        if not all([dataset, schema, symbols, start_date, end_date]):
            raise ValueError("Missing required job configuration parameters")
            
        # Get the appropriate Pydantic model for this schema
        pydantic_model = DATABENTO_SCHEMA_MODEL_MAPPING.get(schema)
        if not pydantic_model:
            raise ValueError(f"Unsupported schema: {schema}")
            
        logger.info(
            "Starting data fetch job",
            dataset=dataset,
            schema=schema,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            chunk_interval_days=chunk_interval_days
        )
        
        # Generate date chunks
        date_chunks = self._generate_date_chunks(
            start_date, end_date, chunk_interval_days
        )
        
        total_records = 0
        validation_errors = 0
        
        # Process each date chunk
        for chunk_start, chunk_end in date_chunks:
            try:
                # Fetch data for this chunk
                data_store = self._fetch_data_chunk(
                    dataset=dataset,
                    schema=schema,
                    symbols=symbols,
                    stype_in=stype_in,
                    start_date=chunk_start,
                    end_date=chunk_end
                )
                
                # Process each record in the data store
                chunk_records = 0
                for record in data_store:
                    try:
                        # Convert databento record to dictionary
                        # Use direct attribute access for databento records
                        record_dict = {}
                        for attr in dir(record):
                            if not attr.startswith('_') and not callable(getattr(record, attr)):
                                # Skip helper/metadata fields, focus on actual data
                                if attr not in ['hd', 'publisher_id', 'rtype', 'size_hint', 'record_size']:
                                    record_dict[attr] = getattr(record, attr)
                        
                        # Validate with Pydantic model
                        validated_record = pydantic_model.model_validate(record_dict)
                        yield validated_record
                        
                        chunk_records += 1
                        total_records += 1
                        
                    except ValidationError as e:
                        validation_errors += 1
                        logger.warning(
                            "Pydantic validation failed for record",
                            schema=schema,
                            error=str(e),
                            record_sample=str(record)[:200]
                        )
                        # Continue processing other records
                        continue
                    except Exception as e:
                        logger.error(
                            "Failed to process record",
                            error=str(e),
                            record_type=type(record).__name__
                        )
                        continue
                        
                logger.info(
                    "Completed chunk processing",
                    chunk_start=chunk_start,
                    chunk_end=chunk_end,
                    records_processed=chunk_records
                )
                
            except Exception as e:
                logger.error(
                    "Failed to process date chunk",
                    chunk_start=chunk_start,
                    chunk_end=chunk_end,
                    error=str(e)
                )
                # Continue with next chunk rather than failing entire job
                continue
                
        logger.info(
            "Data fetch job completed",
            total_records=total_records,
            validation_errors=validation_errors,
            job_name=job_config.get("name", "unknown")
        )

    def disconnect(self) -> None:
        """
        Close connection to the API.
        
        For Databento, this is a no-op as the client is stateless.
        """
        if self.client:
            self.client = None
            logger.info("Databento client disconnected")