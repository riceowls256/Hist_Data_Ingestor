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
from utils.custom_logger import get_logger

from ingestion.api_adapters.base_adapter import BaseAdapter
from storage.models import DATABENTO_SCHEMA_MODEL_MAPPING
from transformation.validators.databento_validators import validate_dataframe
from utils.file_io import QuarantineManager

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
        self.validation_config = self.config.get("validation", {})
        self.strict_mode = self.validation_config.get("strict_mode", True)
        self.quarantine_manager = QuarantineManager(
            enabled=self.validation_config.get("quarantine_enabled", True)
        )

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
            logger.error("Missing key_env_var in api configuration")
            return False

        api_key = os.getenv(key_env_var)
        if not api_key:
            logger.error("API key not found in environment", env_var=key_env_var)
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
        symbols: Any,  # Can be List[str] or str for parent symbology
        stype_in: str,
        start_date: str,
        end_date: str
    ) -> databento.DBNStore:
        """
        Fetch a single chunk of data from the Databento API with retry logic.

        Args:
            dataset: Dataset identifier (e.g., 'GLBX.MDP3')
            schema: Schema type (e.g., 'ohlcv-1d', 'trades', 'tbbo')
            symbols: List of symbols or single symbol string
            stype_in: Symbol type ('continuous', 'native', 'parent')
            start_date: Start date in ISO format
            end_date: End date in ISO format

        Returns:
            DBNStore containing the fetched data

        Raises:
            RuntimeError: If API call fails after all retries
        """
        # Bind context for this specific API call
        api_logger = logger.bind(
            schema_name=schema,
            dataset=dataset,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            operation="api_call"
        )

        retry_decorator = self._create_retry_decorator()

        @retry_decorator
        def _make_api_call():
            api_logger.info("Fetching data chunk from Databento API")
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
            api_logger.error(
                "Failed to fetch data after all retries",
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

        while current_start <= final_end:
            current_end = min(
                current_start + timedelta(days=chunk_interval_days),
                final_end
            )
            chunks.append((
                current_start.isoformat(),
                current_end.isoformat()
            ))
            current_start = current_end

            # Prevent infinite loop when start equals end
            if current_start == final_end:
                break

        logger.info(f"Generated {len(chunks)} date chunks", chunks=len(chunks))
        return chunks

    def _ensure_symbol_field(self, record_dict: Dict[str, Any], symbols=None, record=None) -> Dict[str, Any]:
        """Ensure symbol field is always present with appropriate fallback logic."""
        
        # Priority 1: Use provided symbols parameter
        if symbols:
            if isinstance(symbols, list) and len(symbols) == 1:
                record_dict['symbol'] = symbols[0]
                return record_dict
            elif isinstance(symbols, str):
                record_dict['symbol'] = symbols
                return record_dict
            elif isinstance(symbols, list) and len(symbols) > 1:
                # For multi-symbol, try to resolve from instrument_id or use first symbol
                if 'instrument_id' in record_dict:
                    # TODO: Implement instrument_id to symbol mapping if needed
                    record_dict['symbol'] = symbols[0]  # Fallback to first symbol
                else:
                    record_dict['symbol'] = symbols[0]
                return record_dict
        
        # Priority 2: Extract from record if available
        if record and hasattr(record, 'raw_symbol'):
            record_dict['symbol'] = getattr(record, 'raw_symbol')
            return record_dict
        
        # Priority 3: Use instrument_id based naming if available
        if 'instrument_id' in record_dict:
            record_dict['symbol'] = f"INSTRUMENT_{record_dict['instrument_id']}"
            return record_dict
        
        # Priority 4: Use a default fallback
        record_dict['symbol'] = "UNKNOWN_SYMBOL"
        logger.warning("Symbol field set to default fallback", record_data=record_dict)
        return record_dict

    def _validate_required_fields(self, record_dict: Dict[str, Any], schema: str) -> bool:
        """Validate that required fields are present for the given schema."""
        required_fields = {
            'trades': ['ts_event', 'instrument_id', 'price', 'size'],
            'tbbo': ['ts_event', 'instrument_id'],
            'ohlcv': ['ts_event', 'instrument_id', 'open_price', 'high_price', 'low_price', 'close_price'],
            'statistics': ['ts_event', 'instrument_id', 'stat_type']
        }
        
        schema_base = schema.split('-')[0] if '-' in schema else schema
        fields = required_fields.get(schema_base, [])
        
        missing_fields = [field for field in fields if field not in record_dict or record_dict[field] is None]
        
        if missing_fields:
            logger.warning(f"Missing required fields for {schema}: {missing_fields}", record_data=record_dict)
            return False
        
        return True


    def _record_to_dict(self, record, symbols=None) -> Dict[str, Any]:
        """
        Convert a Databento record to dictionary using direct attribute access.

        This method handles the conversion from Databento record objects to dictionaries,
        using direct attribute access and proper data preprocessing for Pydantic validation.

        Args:
            record: Databento record object (OHLCVMsg, TradeMsg, etc.)
            symbols: Original symbols from job config for proper symbol mapping

        Returns:
            Dictionary representation of the record with properly converted types
        """
        from datetime import datetime, UTC
        from decimal import Decimal

        record_dict = {}

        # Define fields we want to extract and their conversions
        field_mappings = {
            'ts_event': lambda x: datetime.fromtimestamp(x / 1_000_000_000, tz=UTC),  # Convert nanoseconds to datetime
            # Receive timestamp (optional)
            'ts_recv': lambda x: datetime.fromtimestamp(x / 1_000_000_000, tz=UTC) if x is not None else None,
            # Initial timestamp for OHLCV
            'ts_init': lambda x: datetime.fromtimestamp(x / 1_000_000_000, tz=UTC) if x is not None else None,
            'instrument_id': lambda x: x,
            'rtype': lambda x: x,  # Record type (32=OHLCV-1s, 33=OHLCV-1m, 34=OHLCV-1h, 35=OHLCV-1d)
            'publisher_id': lambda x: x,  # Publisher ID from Databento
            'open': lambda x: Decimal(str(x / 1_000_000_000)),  # Convert to decimal (prices are in nanounits)
            'high': lambda x: Decimal(str(x / 1_000_000_000)),
            'low': lambda x: Decimal(str(x / 1_000_000_000)),
            'close': lambda x: Decimal(str(x / 1_000_000_000)),
            'volume': lambda x: x,
            'count': lambda x: x,  # Number of trades in OHLCV bar
            'price': lambda x: Decimal(str(x / 1_000_000_000)),  # For trades
            'size': lambda x: x,  # For trades
            'stat_type': lambda x: x.value if hasattr(x, 'value') else x,  # For statistics
            'price': lambda x: Decimal(str(x / 1_000_000_000)) if x is not None else None,  # Raw field name from API
            'stat_value': lambda x: Decimal(str(x / 1_000_000_000)) if x is not None else None
        }

        # Special handling for TBBO records (MBP1Msg format)
        # Extract bid/ask data from levels[0] if available
        if hasattr(record, 'levels') and record.levels:
            first_level = record.levels[0]
            # Extract bid/ask data from the first level
            if hasattr(first_level, 'bid_px'):
                record_dict['bid_px'] = Decimal(str(first_level.bid_px / 1_000_000_000))
            if hasattr(first_level, 'ask_px'):
                record_dict['ask_px'] = Decimal(str(first_level.ask_px / 1_000_000_000))
            if hasattr(first_level, 'bid_sz'):
                record_dict['bid_sz'] = first_level.bid_sz
            if hasattr(first_level, 'ask_sz'):
                record_dict['ask_sz'] = first_level.ask_sz
            if hasattr(first_level, 'bid_ct'):
                record_dict['bid_ct'] = first_level.bid_ct
            if hasattr(first_level, 'ask_ct'):
                record_dict['ask_ct'] = first_level.ask_ct

        # Extract fields using mappings
        for field, converter in field_mappings.items():
            if hasattr(record, field):
                try:
                    value = getattr(record, field)
                    if value is not None:
                        # Map API field names to model field names for OHLCV
                        if field == 'open':
                            record_dict['open_price'] = converter(value)
                        elif field == 'high':
                            record_dict['high_price'] = converter(value)
                        elif field == 'low':
                            record_dict['low_price'] = converter(value)
                        elif field == 'close':
                            record_dict['close_price'] = converter(value)
                        elif field == 'count':
                            record_dict['trade_count'] = converter(value)
                        elif field == 'price' and hasattr(record, 'stat_type'):
                            # For statistics records, map 'price' field to 'stat_value'
                            record_dict['stat_value'] = converter(value)
                        else:
                            record_dict[field] = converter(value)
                    else:
                        # Map field names for None values too
                        if field == 'open':
                            record_dict['open_price'] = None
                        elif field == 'high':
                            record_dict['high_price'] = None
                        elif field == 'low':
                            record_dict['low_price'] = None
                        elif field == 'close':
                            record_dict['close_price'] = None
                        elif field == 'count':
                            record_dict['trade_count'] = None
                        elif field == 'price' and hasattr(record, 'stat_type'):
                            # For statistics records, map 'price' field to 'stat_value'
                            record_dict['stat_value'] = None
                        else:
                            record_dict[field] = None
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"Failed to convert field {field}: {e}")
                    # Map field names for error cases too
                    if field == 'open':
                        record_dict['open_price'] = None
                    elif field == 'high':
                        record_dict['high_price'] = None
                    elif field == 'low':
                        record_dict['low_price'] = None
                    elif field == 'close':
                        record_dict['close_price'] = None
                    elif field == 'count':
                        record_dict['trade_count'] = None
                    elif field == 'price' and hasattr(record, 'stat_type'):
                        # For statistics records, map 'price' field to 'stat_value'
                        record_dict['stat_value'] = None
                    else:
                        record_dict[field] = None

        # Ensure symbol field is always present using robust mapping logic
        record_dict = self._ensure_symbol_field(record_dict, symbols, record)

        # For OHLCV records that don't have ts_recv, use ts_event as fallback
        if 'ts_event' in record_dict and 'ts_recv' not in record_dict:
            record_dict['ts_recv'] = record_dict['ts_event']

        return record_dict

    def fetch_historical_data(self, job_config: Dict[str, Any]) -> Iterator[BaseModel]:
        """
        Fetches historical data from the Databento API based on the job configuration.

        This method handles date chunking, data fetching, Pydantic validation,
        and quarantining of invalid records.

        Args:
            job_config: Configuration for the specific data ingestion job containing:
                - dataset: Dataset identifier (e.g., 'GLBX.MDP3')
                - schema: Schema type (e.g., 'ohlcv-1d', 'trades', 'tbbo')
                - symbols: List of symbols or single symbol string
                - stype_in: Symbol type ('continuous', 'native', 'parent')
                - start_date: Start date in ISO format
                - end_date: End date in ISO format
                - date_chunk_interval_days: Optional chunking interval

        Yields:
            Iterator of validated Pydantic model instances (DatabentoOHLCVRecord, etc.)

        Raises:
            ConnectionError: If client is not connected
            RuntimeError: If API calls fail after retries
            ValidationError: If schema is not supported

        Example:
            >>> adapter = DatabentoAdapter(config)
            >>> adapter.connect()
            >>> job_config = {
            ...     'dataset': 'GLBX.MDP3',
            ...     'schema': 'ohlcv-1d',
            ...     'symbols': ['ES.FUT'],
            ...     'stype_in': 'continuous',
            ...     'start_date': '2024-01-01',
            ...     'end_date': '2024-01-31'
            ... }
            >>> for record in adapter.fetch_historical_data(job_config):
            ...     print(f"OHLCV: {record.symbol} - Close: {record.close}")
        """
        dataset = job_config["dataset"]
        schema = job_config["schema"]
        symbols = job_config["symbols"]
        stype_in = job_config["stype_in"]
        start_date = job_config["start_date"]
        end_date = job_config["end_date"]
        chunk_interval_days = job_config.get("date_chunk_interval_days")

        # Bind context for all operations in this fetch session
        fetch_logger = logger.bind(
            schema_name=schema,
            dataset=dataset,
            symbols=symbols,
            operation="fetch_historical_data"
        )

        date_chunks = self._generate_date_chunks(start_date, end_date, chunk_interval_days)

        model_cls = DATABENTO_SCHEMA_MODEL_MAPPING.get(schema)
        if not model_cls:
            fetch_logger.error("No Pydantic model found for schema")
            return

        validation_stats = {"total_records": 0, "failed_validation": 0}

        for start, end in date_chunks:
            data_chunk = self._fetch_data_chunk(dataset, schema, symbols, stype_in, start, end)

            for record in data_chunk:
                validation_stats["total_records"] += 1
                try:
                    # Convert record to dictionary using direct attribute access
                    record_dict = self._record_to_dict(record, symbols)

                    # Stage 1 Validation: Pydantic model instantiation
                    model_instance = model_cls.model_validate(
                        record_dict,
                        strict=self.strict_mode
                    )
                    yield model_instance
                except ValidationError as e:
                    validation_stats["failed_validation"] += 1
                    record_dict = self._record_to_dict(record, symbols)
                    fetch_logger.warning(
                        "Pydantic validation failed for record",
                        error=str(e),
                        record_data=record_dict
                    )
                    self.quarantine_manager.quarantine_record(
                        schema,
                        "pydantic_validation",
                        str(e),
                        original_record=record_dict
                    )

        fetch_logger.info(
            "Data fetching and validation complete",
            stats=validation_stats
        )

    def disconnect(self) -> None:
        """Disconnects the client. For Databento, this is a no-op."""
        self.client = None
        logger.info("Databento client disconnected.")
