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
from src.transformation.validators.databento_validators import validate_dataframe
from src.utils.file_io import QuarantineManager

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

    def _normalize_schema(self, schema: str) -> str:
        """
        Normalize user-friendly or CLI schema aliases to their canonical Databento API schema names.
        Raises an error if the schema is not recognized.

        Args:
            schema (str): User-provided or config-provided schema name.

        Returns:
            str: Canonical Databento API schema name.

        Raises:
            ValueError: If the schema is not recognized
        """
        aliases = {
            # Definitions
            "definitions": "definition",

            # OHLCV Aliases
            "ohlcv-daily": "ohlcv-1d",
            "ohlcv-eod": "ohlcv-1d",
            "ohlcv-d": "ohlcv-1d",
            "ohlcv-h": "ohlcv-1h",
            "ohlcv-m": "ohlcv-1m",
            "ohlcv-s": "ohlcv-1s",

            # Market Depth
            "top-of-book": "tbbo",
            "quotes": "tbbo",

            # Statistics shorthand
            "stats": "statistics",

            # Other common shorthands
            "order-book": "mbp-1",
            "book": "mbp-1",
            "best-book": "mbp-1",
            "trd": "trades",
            "bbo": "tbbo",
        }

        valid_schemas = {
            "mbo", "mbp-1", "mbp-10", "tbbo", "trades",
            "ohlcv-1s", "ohlcv-1m", "ohlcv-1h", "ohlcv-1d",
            "definition", "statistics", "status", "imbalance",
            "ohlcv-eod", "cmbp-1", "cbbo-1s", "cbbo-1m", "tcbbo",
            "bbo-1s", "bbo-1m"
        }

        input_schema = schema.lower()
        canonical_schema = aliases.get(input_schema, input_schema)

        if canonical_schema not in valid_schemas:
            logger.error("Unrecognized schema passed to normalize", input=input_schema)
            raise ValueError(
                f"Schema '{schema}' is not recognized. "
                f"Use one of: {sorted(valid_schemas)} or valid alias."
            )

        if input_schema != canonical_schema:
            logger.debug("Normalized schema alias", input_schema=schema, normalized_schema=canonical_schema)

        return canonical_schema

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
        # Normalize the schema to canonical name
        normalized_schema = self._normalize_schema(schema)
        
        # Bind context for this specific API call
        api_logger = logger.bind(
            schema_name=normalized_schema,
            original_schema=schema if schema != normalized_schema else None,
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
                schema=normalized_schema,
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
        chunk_interval_days: Optional[int],
        enable_market_calendar: bool = False,
        exchange_name: str = "NYSE"
    ) -> List[tuple[str, str]]:
        """
        Generate date chunks for processing large date ranges with optional market calendar filtering.

        Args:
            start_date: Start date in ISO format
            end_date: End date in ISO format
            chunk_interval_days: Number of days per chunk, None for no chunking
            enable_market_calendar: Whether to filter chunks based on trading days
            exchange_name: Exchange name for market calendar (e.g., NYSE, CME_Equity)

        Returns:
            List of (start_date, end_date) tuples for each chunk, optionally filtered for trading days
        """
        if not chunk_interval_days:
            chunks = [(start_date, end_date)]
        else:
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

        # Apply market calendar filtering if enabled
        if enable_market_calendar:
            try:
                from src.cli.smart_validation import MarketCalendar, PANDAS_MARKET_CALENDARS_AVAILABLE
                
                if PANDAS_MARKET_CALENDARS_AVAILABLE:
                    calendar = MarketCalendar(exchange_name)
                    filtered_chunks = []
                    
                    for chunk_start, chunk_end in chunks:
                        # Parse chunk dates
                        start_dt = datetime.fromisoformat(chunk_start.replace('Z', '+00:00')).date()
                        end_dt = datetime.fromisoformat(chunk_end.replace('Z', '+00:00')).date()
                        
                        # Check if chunk contains any trading days
                        trading_days_count = calendar.get_trading_days_count(start_dt, end_dt)
                        
                        if trading_days_count > 0:
                            filtered_chunks.append((chunk_start, chunk_end))
                            logger.debug(f"Including chunk {start_dt} to {end_dt} - {trading_days_count} trading days")
                        else:
                            logger.info(f"Skipping chunk {start_dt} to {end_dt} - no trading days ({exchange_name})")
                    
                    original_count = len(chunks)
                    filtered_count = len(filtered_chunks)
                    
                    if filtered_count < original_count:
                        savings_pct = ((original_count - filtered_count) / original_count) * 100
                        logger.info(f"Market calendar filtering: {original_count} → {filtered_count} chunks "
                                  f"({savings_pct:.1f}% API cost reduction)",
                                  exchange=exchange_name, 
                                  original_chunks=original_count,
                                  filtered_chunks=filtered_count)
                    
                    chunks = filtered_chunks
                else:
                    logger.warning("Market calendar filtering requested but pandas-market-calendars not available")
                    
            except Exception as e:
                logger.warning(f"Market calendar filtering failed: {e}", 
                             exchange=exchange_name, 
                             error=str(e))
                logger.info("Continuing with original chunks (no filtering applied)")

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


    def _clean_string_field(self, value: Any) -> str:
        """
        Clean string fields by removing NUL characters and handling encoding.
        
        Args:
            value: The raw value from the API
            
        Returns:
            Cleaned string value safe for PostgreSQL
        """
        if value is None:
            return ''
        
        # Handle bytes
        if isinstance(value, bytes):
            try:
                # Decode and remove NUL terminators
                cleaned = value.decode('utf-8').rstrip('\x00')
            except UnicodeDecodeError:
                # Fallback to latin-1 if utf-8 fails
                cleaned = value.decode('latin-1').rstrip('\x00')
        else:
            # Convert to string and remove NUL characters
            cleaned = str(value).rstrip('\x00')
        
        # Remove any embedded NUL characters that might cause PostgreSQL issues
        cleaned = cleaned.replace('\x00', '')
        
        return cleaned

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

        # Check if this is a definition record (rtype = 19)
        if hasattr(record, 'rtype') and record.rtype == 19:
            # Add comprehensive field mappings for definition records
            field_mappings.update({
                # Core definition fields - handle char types - API field name to mapping
                'raw_symbol': lambda x: self._clean_string_field(x),
                'update_action': lambda x: chr(x) if isinstance(x, int) else str(x),  # API field name
                'instrument_class': lambda x: chr(x) if isinstance(x, int) else str(x),
                'min_price_increment': lambda x: Decimal(str(x / 1_000_000_000)),
                'display_factor': lambda x: Decimal(str(x / 1_000_000_000)),
                'expiration': lambda x: datetime.fromtimestamp(x / 1_000_000_000, tz=UTC),
                'activation': lambda x: datetime.fromtimestamp(x / 1_000_000_000, tz=UTC),
                'high_limit_price': lambda x: Decimal(str(x / 1_000_000_000)),
                'low_limit_price': lambda x: Decimal(str(x / 1_000_000_000)),
                'max_price_variation': lambda x: Decimal(str(x / 1_000_000_000)),
                'unit_of_measure_qty': lambda x: Decimal(str(x / 1_000_000_000)),
                'min_price_increment_amount': lambda x: Decimal(str(x / 1_000_000_000)),
                'price_ratio': lambda x: Decimal(str(x / 1_000_000_000)),
                'inst_attrib_value': lambda x: x,  # API field name
                'underlying_instrument_id': lambda x: x if x != 0 else None,  # API field name  
                'raw_instrument_id': lambda x: x if x != 0 else None,
                'market_depth_implied': lambda x: x,
                'market_depth': lambda x: x,
                'market_segment_id': lambda x: x,
                'max_trade_volume': lambda x: x,  # API field name
                'min_lot_size': lambda x: x,
                'min_block_size': lambda x: x,  # API field name
                'min_round_lot_size': lambda x: x,  # API field name  
                'min_trade_volume': lambda x: x,  # API field name
                'contract_multiplier': lambda x: x if x != 0 else None,
                'decay_quantity': lambda x: x if x != 0 else None,
                'original_contract_size': lambda x: x if x != 0 else None,
                'application_id': lambda x: x if x != 0 else None,  # API field name
                'maturity_year': lambda x: x if x != 0 else None,
                'decay_start_date': lambda x: datetime.fromtimestamp((x - 719163) * 86400, tz=UTC).date() if x != 0 else None,  # Excel date to Python date
                'channel_id': lambda x: x,
                'currency': lambda x: self._clean_string_field(x),
                'settlement_currency': lambda x: self._clean_string_field(x) if x else None,  # API field name
                'security_subtype': lambda x: self._clean_string_field(x) if x else None,  # API field name
                'security_group': lambda x: self._clean_string_field(x),  # API field name
                'exchange': lambda x: self._clean_string_field(x),
                'underlying_asset': lambda x: self._clean_string_field(x),  # API field name
                'cfi_code': lambda x: self._clean_string_field(x) if x else None,  # API field name
                'security_type': lambda x: self._clean_string_field(x) if x else None,
                'unit_of_measure': lambda x: self._clean_string_field(x) if x else None,
                'underlying_symbol': lambda x: self._clean_string_field(x) if x else None,  # API field name
                'strike_currency': lambda x: self._clean_string_field(x) if x else None,  # API field name
                'strike_price': lambda x: Decimal(str(x / 1_000_000_000)) if x != 0 else None,
                'matching_algorithm': lambda x: chr(x) if isinstance(x, int) else str(x) if x else None,  # API field name
                'main_fraction': lambda x: x if x != 0 else None,
                'price_display_format': lambda x: x if x != 0 else None,
                'sub_fraction': lambda x: x if x != 0 else None,
                'underlying_product_code': lambda x: x if x != 0 else None,  # API field name
                'maturity_month': lambda x: x if x != 0 else None,
                'maturity_day': lambda x: x if x != 0 else None,
                'maturity_week': lambda x: x if x != 0 else None,
                'is_user_defined': lambda x: chr(x) if isinstance(x, int) else str(x) if x else None,  # API field name
                'contract_multiplier_unit': lambda x: x if x != 0 else None,
                'flow_schedule_type': lambda x: x if x != 0 else None,
                'tick_rule': lambda x: x if x != 0 else None,
                'leg_count': lambda x: x,
                'leg_index': lambda x: x if x not in (255, 65535) else None,  # 255 and 65535 are null values
                'leg_instrument_id': lambda x: x if x != 0 else None,
                'leg_raw_symbol': lambda x: x.decode('utf-8') if isinstance(x, bytes) else str(x).rstrip('\x00') if x else None,
                'leg_instrument_class': lambda x: chr(x) if isinstance(x, int) and x not in (255, 127) else str(x) if x and x not in (255, 127) else None,
                'leg_side': lambda x: chr(x) if isinstance(x, int) and x not in (255, 127) else str(x) if x and x not in (255, 127) else None,
                'leg_price': lambda x: Decimal(str(x / 1_000_000_000)) if x != 0 else None,
                'leg_delta': lambda x: Decimal(str(x / 1_000_000_000)) if x != 0 else None,
                'leg_ratio_price_numerator': lambda x: x if x != 0 else None,
                'leg_ratio_price_denominator': lambda x: x if x != 0 else None,
                'leg_ratio_qty_numerator': lambda x: x if x != 0 else None,
                'leg_ratio_qty_denominator': lambda x: x if x != 0 else None,
                'leg_underlying_id': lambda x: x if x != 0 else None,
            })

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
                        # Definition record field name mappings - API field names to Pydantic model field names
                        elif field == 'rtype':
                            record_dict['rtype'] = converter(value)
                        elif field == 'update_action' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['security_update_action'] = converter(value)
                        elif field == 'inst_attrib_value' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['inst_attrib_value'] = converter(value)
                        elif field == 'max_trade_volume' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['max_trade_vol'] = converter(value)
                        elif field == 'min_block_size' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['min_lot_size_block'] = converter(value)
                        elif field == 'min_round_lot_size' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['min_lot_size_round_lot'] = converter(value)
                        elif field == 'min_trade_volume' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['min_trade_vol'] = converter(value)
                        elif field == 'security_group' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['group'] = converter(value)
                        elif field == 'underlying_asset' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['asset'] = converter(value)
                        elif field == 'underlying_instrument_id' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['underlying_id'] = converter(value)
                        elif field == 'settlement_currency' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['settl_currency'] = converter(value)
                        elif field == 'security_subtype' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['secsubtype'] = converter(value)
                        elif field == 'cfi_code' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['cfi'] = converter(value)
                        elif field == 'underlying_symbol' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['underlying'] = converter(value)
                        elif field == 'strike_currency' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['strike_price_currency'] = converter(value)
                        elif field == 'matching_algorithm' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['match_algorithm'] = converter(value)
                        elif field == 'underlying_product_code' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['underlying_product'] = converter(value)
                        elif field == 'is_user_defined' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['user_defined_instrument'] = converter(value)
                        elif field == 'application_id' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['appl_id'] = converter(value)
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
                        # Definition record field name mappings for None values
                        elif field == 'update_action' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['security_update_action'] = None
                        elif field == 'inst_attrib_value' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['inst_attrib_value'] = None
                        elif field == 'max_trade_volume' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['max_trade_vol'] = None
                        elif field == 'min_block_size' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['min_lot_size_block'] = None
                        elif field == 'min_round_lot_size' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['min_lot_size_round_lot'] = None
                        elif field == 'min_trade_volume' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['min_trade_vol'] = None
                        elif field == 'security_group' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['group'] = None
                        elif field == 'underlying_asset' and hasattr(record, 'rtype') and record.rtype == 19:
                            record_dict['asset'] = None
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
                    # Definition record field name mappings for error cases
                    elif field == 'update_action' and hasattr(record, 'rtype') and record.rtype == 19:
                        record_dict['security_update_action'] = None
                    elif field == 'inst_attrib_value' and hasattr(record, 'rtype') and record.rtype == 19:
                        record_dict['inst_attrib_value'] = None
                    elif field == 'max_trade_volume' and hasattr(record, 'rtype') and record.rtype == 19:
                        record_dict['max_trade_vol'] = None
                    elif field == 'min_block_size' and hasattr(record, 'rtype') and record.rtype == 19:
                        record_dict['min_lot_size_block'] = None
                    elif field == 'min_round_lot_size' and hasattr(record, 'rtype') and record.rtype == 19:
                        record_dict['min_lot_size_round_lot'] = None
                    elif field == 'min_trade_volume' and hasattr(record, 'rtype') and record.rtype == 19:
                        record_dict['min_trade_vol'] = None
                    elif field == 'security_group' and hasattr(record, 'rtype') and record.rtype == 19:
                        record_dict['group'] = None
                    elif field == 'underlying_asset' and hasattr(record, 'rtype') and record.rtype == 19:
                        record_dict['asset'] = None
                    else:
                        record_dict[field] = None

        # Ensure symbol field is always present using robust mapping logic
        record_dict = self._ensure_symbol_field(record_dict, symbols, record)

        # For OHLCV records that don't have ts_recv, use ts_event as fallback
        if 'ts_event' in record_dict and 'ts_recv' not in record_dict:
            record_dict['ts_recv'] = record_dict['ts_event']

        # For definition records, ensure required fields have default values if missing from API
        if hasattr(record, 'rtype') and record.rtype == 19:
            # Provide default values for required fields that might be missing from API
            if 'security_update_action' not in record_dict:
                record_dict['security_update_action'] = 'A'  # Default to Add
            if 'max_trade_vol' not in record_dict:
                record_dict['max_trade_vol'] = 0  # Default value
            if 'min_lot_size_block' not in record_dict:
                record_dict['min_lot_size_block'] = 0  # Default value
            if 'min_lot_size_round_lot' not in record_dict:
                record_dict['min_lot_size_round_lot'] = 0  # Default value
            if 'min_trade_vol' not in record_dict:
                record_dict['min_trade_vol'] = 0  # Default value
            if 'group' not in record_dict:
                record_dict['group'] = ''  # Default to empty string
            if 'asset' not in record_dict:
                record_dict['asset'] = ''  # Default to empty string

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

        # Normalize schema first to handle aliases
        normalized_schema = self._normalize_schema(schema)
        
        # Extract market calendar settings from job config 
        enable_market_calendar = job_config.get("enable_market_calendar_filtering", False)
        exchange_name = job_config.get("exchange_name")
        
        # Intelligent exchange detection if not explicitly provided
        if enable_market_calendar and not exchange_name:
            try:
                from src.cli.exchange_mapping import map_symbols_to_exchange
                symbol_list = symbols if isinstance(symbols, list) else [symbols]
                exchange_name, confidence = map_symbols_to_exchange(symbol_list, "NYSE")
                fetch_logger.info(f"Auto-detected exchange for calendar filtering",
                                exchange=exchange_name, 
                                confidence=confidence,
                                symbols=symbol_list)
            except Exception as e:
                fetch_logger.warning(f"Failed to auto-detect exchange: {e}")
                exchange_name = "NYSE"
        elif not exchange_name:
            exchange_name = "NYSE"
        
        date_chunks = self._generate_date_chunks(start_date, end_date, chunk_interval_days, 
                                                enable_market_calendar, exchange_name)

        model_cls = DATABENTO_SCHEMA_MODEL_MAPPING.get(normalized_schema)
        if not model_cls:
            fetch_logger.error("No Pydantic model found for schema", 
                              original_schema=schema, 
                              normalized_schema=normalized_schema)
            return

        validation_stats = {"total_records": 0, "failed_validation": 0}

        for start, end in date_chunks:
            data_chunk = self._fetch_data_chunk(dataset, normalized_schema, symbols, stype_in, start, end)

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
