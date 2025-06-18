"""
TimescaleDB data loader for Databento definition records.

This module provides functionality to load and store Databento definition records
into TimescaleDB with proper schema management and error handling.
"""

import structlog
from contextlib import contextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
import os

from storage.models import DatabentoDefinitionRecord

logger = structlog.get_logger(__name__)


class TimescaleDefinitionLoader:
    """
    Loader for Databento definition records into TimescaleDB.

    Handles bulk insertion of definition records into the definitions_data hypertable
    with proper type conversion and error handling.
    """

    def __init__(self, connection_params: Optional[Dict[str, Any]] = None):
        """
        Initialize the TimescaleDB loader.

        Args:
            connection_params: Database connection parameters, if None uses environment
        """
        self.connection_params = connection_params or self._get_connection_params()

    def _get_connection_params(self) -> Dict[str, Any]:
        """Get database connection parameters from environment variables."""
        return {
            'host': os.getenv('TIMESCALEDB_HOST', 'localhost'),
            'port': int(os.getenv('TIMESCALEDB_PORT', '5432')),
            'database': os.getenv('TIMESCALEDB_DBNAME', 'hist_data'),
            'user': os.getenv('TIMESCALEDB_USER', 'postgres'),
            'password': os.getenv('TIMESCALEDB_PASSWORD', ''),
        }

    @contextmanager
    def get_connection(self):
        """Get a database connection with proper cleanup."""
        connection = None
        try:
            connection = psycopg2.connect(**self.connection_params)
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                connection.close()

    def create_schema_if_not_exists(self) -> bool:
        """
        Create the definitions_data schema if it doesn't exist.

        Returns:
            bool: True if schema was created or already exists
        """
        schema_sql_path = os.path.join(
            os.path.dirname(__file__),
            'schema_definitions',
            'definitions_data_table.sql'
        )

        if not os.path.exists(schema_sql_path):
            logger.error(f"Schema SQL file not found: {schema_sql_path}")
            return False

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Check if table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = 'definitions_data'
                        );
                    """)
                    table_exists = cursor.fetchone()[0]

                    if not table_exists:
                        logger.info("Creating definitions_data schema...")
                        with open(schema_sql_path, 'r') as schema_file:
                            schema_sql = schema_file.read()
                            cursor.execute(schema_sql)
                        conn.commit()
                        logger.info("Successfully created definitions_data schema")
                    else:
                        logger.info("definitions_data table already exists")

                    return True

        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            return False

    def insert_definition_records(
        self,
        records: List[DatabentoDefinitionRecord],
        batch_size: int = 1000
    ) -> Dict[str, int]:
        """
        Insert definition records into the definitions_data table.

        Args:
            records: List of validated DatabentoDefinitionRecord instances
            batch_size: Number of records to insert in each batch

        Returns:
            Dict with statistics: {'inserted': int, 'errors': int}
        """
        if not records:
            return {'inserted': 0, 'errors': 0}

        insert_sql = self._build_insert_sql()
        stats = {'inserted': 0, 'errors': 0}

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Process records in batches
                    for i in range(0, len(records), batch_size):
                        batch = records[i:i + batch_size]
                        batch_data = []

                        for record in batch:
                            try:
                                row_data = self._record_to_tuple(record)
                                batch_data.append(row_data)
                            except Exception as e:
                                logger.warning(f"Failed to convert record: {e}")
                                stats['errors'] += 1
                                continue

                        if batch_data:
                            cursor.executemany(insert_sql, batch_data)
                            stats['inserted'] += len(batch_data)
                            logger.info(f"Inserted batch of {len(batch_data)} records")

                conn.commit()
                logger.info(f"Successfully inserted {stats['inserted']} definition records")

        except Exception as e:
            logger.error(f"Failed to insert definition records: {e}")
            stats['errors'] += len(records) - stats['inserted']

        return stats

    def _build_insert_sql(self) -> str:
        """Build the INSERT SQL statement for definition records."""
        columns = [
            'ts_event', 'ts_recv', 'rtype', 'publisher_id', 'instrument_id',
            'raw_symbol', 'security_update_action', 'instrument_class',
            'min_price_increment', 'display_factor', 'expiration', 'activation',
            'high_limit_price', 'low_limit_price', 'max_price_variation',
            'unit_of_measure_qty', 'min_price_increment_amount', 'price_ratio',
            'inst_attrib_value', 'underlying_id', 'raw_instrument_id',
            'market_depth_implied', 'market_depth', 'market_segment_id',
            'max_trade_vol', 'min_lot_size', 'min_lot_size_block',
            'min_lot_size_round_lot', 'min_trade_vol', 'contract_multiplier',
            'decay_quantity', 'original_contract_size', 'appl_id',
            'maturity_year', 'decay_start_date', 'channel_id',
            'currency', 'settl_currency', 'secsubtype', 'group_code',
            'exchange', 'asset', 'cfi', 'security_type', 'unit_of_measure',
            'underlying', 'strike_price_currency', 'strike_price',
            'match_algorithm', 'main_fraction', 'price_display_format',
            'sub_fraction', 'underlying_product', 'maturity_month',
            'maturity_day', 'maturity_week', 'user_defined_instrument',
            'contract_multiplier_unit', 'flow_schedule_type', 'tick_rule',
            'leg_count', 'leg_index', 'leg_instrument_id', 'leg_raw_symbol',
            'leg_instrument_class', 'leg_side', 'leg_price', 'leg_delta',
            'leg_ratio_price_numerator', 'leg_ratio_price_denominator',
            'leg_ratio_qty_numerator', 'leg_ratio_qty_denominator',
            'leg_underlying_id'
        ]

        placeholders = ', '.join(['%s'] * len(columns))
        column_list = ', '.join(columns)

        return f"""
            INSERT INTO definitions_data ({column_list})
            VALUES ({placeholders})
            ON CONFLICT (instrument_id, ts_event)
            DO UPDATE SET
                updated_at = NOW(),
                security_update_action = EXCLUDED.security_update_action,
                high_limit_price = EXCLUDED.high_limit_price,
                low_limit_price = EXCLUDED.low_limit_price
        """

    def _record_to_tuple(self, record: DatabentoDefinitionRecord) -> tuple:
        """Convert a DatabentoDefinitionRecord to tuple for database insertion."""
        return (
            record.ts_event,
            record.ts_recv,
            record.rtype,
            record.publisher_id,
            record.instrument_id,
            record.raw_symbol,
            record.security_update_action,
            record.instrument_class,
            record.min_price_increment,
            record.display_factor,
            record.expiration,
            record.activation,
            record.high_limit_price,
            record.low_limit_price,
            record.max_price_variation,
            record.unit_of_measure_qty,
            record.min_price_increment_amount,
            record.price_ratio,
            record.inst_attrib_value,
            record.underlying_id,
            record.raw_instrument_id,
            record.market_depth_implied,
            record.market_depth,
            record.market_segment_id,
            record.max_trade_vol,
            record.min_lot_size,
            record.min_lot_size_block,
            record.min_lot_size_round_lot,
            record.min_trade_vol,
            record.contract_multiplier,
            record.decay_quantity,
            record.original_contract_size,
            record.appl_id,
            record.maturity_year,
            record.decay_start_date,
            record.channel_id,
            record.currency,
            record.settl_currency,
            record.secsubtype,
            record.group,
            record.exchange,
            record.asset,
            record.cfi,
            record.security_type,
            record.unit_of_measure,
            record.underlying,
            record.strike_price_currency,
            record.strike_price,
            record.match_algorithm,
            record.main_fraction,
            record.price_display_format,
            record.sub_fraction,
            record.underlying_product,
            record.maturity_month,
            record.maturity_day,
            record.maturity_week,
            record.user_defined_instrument,
            record.contract_multiplier_unit,
            record.flow_schedule_type,
            record.tick_rule,
            record.leg_count,
            record.leg_index,
            record.leg_instrument_id,
            record.leg_raw_symbol,
            record.leg_instrument_class,
            record.leg_side,
            record.leg_price,
            record.leg_delta,
            record.leg_ratio_price_numerator,
            record.leg_ratio_price_denominator,
            record.leg_ratio_qty_numerator,
            record.leg_ratio_qty_denominator,
            record.leg_underlying_id
        )

    def get_definition_records(
        self,
        asset: Optional[str] = None,
        instrument_class: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Retrieve definition records from the database.

        Args:
            asset: Filter by asset (e.g., 'ES', 'CL')
            instrument_class: Filter by instrument class (e.g., 'FUT', 'OPT')
            limit: Maximum number of records to return

        Returns:
            List of definition records as dictionaries
        """
        query = """
            SELECT * FROM definitions_data
            WHERE 1=1
        """
        params = []

        if asset:
            query += " AND asset = %s"
            params.append(asset)

        if instrument_class:
            query += " AND instrument_class = %s"
            params.append(instrument_class)

        query += " ORDER BY ts_event DESC LIMIT %s"
        params.append(limit)

        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to retrieve definition records: {e}")
            return []
