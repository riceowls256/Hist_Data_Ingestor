"""
TimescaleDB OHLCV Data Loader

This module provides the TimescaleOHLCVLoader class for storing OHLCV (Open, High, Low, Close, Volume)
records in TimescaleDB. It handles the creation of hypertables and efficient batch insertion
of OHLCV data.
"""

import os
from contextlib import contextmanager
from typing import Dict, Any, List, Optional

import psycopg2
import psycopg2.errors
from psycopg2.extras import RealDictCursor
import structlog

from storage.models import DatabentoOHLCVRecord
from utils.custom_logger import get_logger

logger = get_logger(__name__)


class TimescaleOHLCVLoader:
    """
    Loader for OHLCV data into TimescaleDB.

    This class handles the storage of OHLCV records in the daily_ohlcv_data table,
    including hypertable creation and batch insertion operations.
    """

    def __init__(self, connection_params: Optional[Dict[str, Any]] = None):
        """
        Initialize the TimescaleOHLCVLoader.

        Args:
            connection_params: Database connection parameters. If None, will load from environment.
        """
        self.connection_params = connection_params or self._get_connection_params()

    def _get_connection_params(self) -> Dict[str, Any]:
        """Get database connection parameters from environment variables."""
        return {
            'host': os.getenv('TIMESCALEDB_HOST', 'localhost'),
            'port': int(os.getenv('TIMESCALEDB_PORT', 5432)),
            'database': os.getenv('TIMESCALEDB_DBNAME', 'hist_data'),
            'user': os.getenv('TIMESCALEDB_USER', 'postgres'),
            'password': os.getenv('TIMESCALEDB_PASSWORD', 'postgres')
        }

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def create_schema_if_not_exists(self) -> bool:
        """
        Create the OHLCV table and hypertable if they don't exist.
        Executes the SQL schema file for daily_ohlcv_data table.

        Returns:
            True if schema creation succeeded, False otherwise
        """
        import os
        from pathlib import Path
        
        # Get the schema file path
        schema_file = Path(__file__).parent / 'schema_definitions' / 'daily_ohlcv_data_table.sql'
        
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            # Fallback to hardcoded schema for backward compatibility
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS daily_ohlcv_data (
                    ts_event TIMESTAMPTZ NOT NULL,
                    instrument_id INTEGER NOT NULL,
                    open_price DECIMAL(20,8) NOT NULL,
                    high_price DECIMAL(20,8) NOT NULL,
                    low_price DECIMAL(20,8) NOT NULL,
                    close_price DECIMAL(20,8) NOT NULL,
                    volume BIGINT NOT NULL,
                    trade_count INTEGER,
                    vwap DECIMAL(20,8),
                    granularity VARCHAR(10) NOT NULL DEFAULT '1d',
                    data_source VARCHAR(50) NOT NULL DEFAULT 'databento',
                    symbol VARCHAR(50),
                    ts_recv TIMESTAMPTZ,
                    rtype INTEGER,
                    publisher_id INTEGER,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    CONSTRAINT chk_price_relationships CHECK (
                        high_price >= low_price AND 
                        high_price >= open_price AND 
                        high_price >= close_price AND
                        low_price <= open_price AND 
                        low_price <= close_price
                    ),
                    CONSTRAINT chk_vwap_range CHECK (
                        vwap IS NULL OR (vwap >= low_price AND vwap <= high_price)
                    ),
                    CONSTRAINT uq_daily_ohlcv_unique UNIQUE (ts_event, instrument_id, granularity, data_source)
                );
            """
            
            create_hypertable_sql = """
                SELECT create_hypertable('daily_ohlcv_data', 'ts_event',
                                       chunk_time_interval => INTERVAL '1 day',
                                       if_not_exists => TRUE);
            """
            
            create_indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_daily_ohlcv_instrument_time ON daily_ohlcv_data (instrument_id, ts_event DESC);",
                "CREATE INDEX IF NOT EXISTS idx_daily_ohlcv_symbol ON daily_ohlcv_data (symbol);",
                "CREATE INDEX IF NOT EXISTS idx_daily_ohlcv_source ON daily_ohlcv_data (data_source);",
                "CREATE INDEX IF NOT EXISTS idx_daily_ohlcv_granularity ON daily_ohlcv_data (granularity);",
                "CREATE INDEX IF NOT EXISTS idx_daily_ohlcv_symbol_gran_time ON daily_ohlcv_data (symbol, granularity, ts_event DESC);",
                "CREATE INDEX IF NOT EXISTS idx_daily_ohlcv_volume ON daily_ohlcv_data (volume) WHERE volume > 0;"
            ]
        else:
            # Read and parse the SQL schema file
            with open(schema_file, 'r') as f:
                sql_content = f.read()
            
            # Split the SQL file into individual statements
            # Remove comments and split by semicolons
            sql_statements = []
            current_statement = []
            
            for line in sql_content.split('\n'):
                # Skip pure comment lines
                if line.strip().startswith('--') or line.strip().startswith('\\'):
                    continue
                    
                current_statement.append(line)
                
                # Check if this line ends a statement
                if line.rstrip().endswith(';'):
                    statement = '\n'.join(current_statement).strip()
                    if statement and not statement.startswith('--'):
                        sql_statements.append(statement)
                    current_statement = []
            
            # Extract relevant statements
            create_table_sql = None
            create_hypertable_sql = None
            create_indexes_sql = []
            
            for stmt in sql_statements:
                stmt_upper = stmt.upper()
                if 'CREATE TABLE' in stmt_upper and 'daily_ohlcv_data' in stmt:
                    # Replace CREATE TABLE with CREATE TABLE IF NOT EXISTS
                    create_table_sql = stmt.replace('CREATE TABLE daily_ohlcv_data', 
                                                   'CREATE TABLE IF NOT EXISTS daily_ohlcv_data')
                    create_table_sql = create_table_sql.replace('DROP TABLE IF EXISTS daily_ohlcv_data CASCADE;', '')
                elif 'CREATE_HYPERTABLE' in stmt_upper:
                    create_hypertable_sql = stmt
                elif 'CREATE INDEX' in stmt_upper:
                    # Ensure all indexes use IF NOT EXISTS
                    if 'IF NOT EXISTS' not in stmt:
                        stmt = stmt.replace('CREATE INDEX', 'CREATE INDEX IF NOT EXISTS')
                    create_indexes_sql.append(stmt)
            
            # Use the extracted statements
            if not create_table_sql:
                logger.error("Could not extract CREATE TABLE statement from schema file")
                return False

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create table
                    try:
                        cursor.execute(create_table_sql)
                        logger.info("OHLCV table created successfully")
                    except psycopg2.errors.DuplicateTable:
                        logger.info("OHLCV table already exists, skipping creation")
                    except Exception as e:
                        logger.error(f"Failed to create OHLCV table: {e}")
                        raise

                    # Create hypertable
                    try:
                        cursor.execute(create_hypertable_sql)
                        logger.info("OHLCV hypertable created or already exists")
                    except Exception as e:
                        # Hypertable creation with if_not_exists=TRUE should not fail
                        # but log warning if it does
                        logger.warning(f"Hypertable creation notice: {e}")

                    # Create indexes
                    for index_sql in create_indexes_sql:
                        try:
                            cursor.execute(index_sql)
                        except psycopg2.errors.DuplicateObject:
                            # Index already exists, continue
                            pass
                        except Exception as e:
                            logger.warning(f"Index creation notice: {e}")
                    logger.info("OHLCV indexes created or verified")

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to create OHLCV schema: {e}")
            return False

    def insert_ohlcv_records(self,
                             records: List[DatabentoOHLCVRecord],
                             batch_size: int = 1000,
                             granularity: str = '1d',
                             data_source: str = 'databento') -> Dict[str, int]:
        """
        Insert OHLCV records into the database.

        Args:
            records: List of DatabentoOHLCVRecord instances to insert
            batch_size: Number of records to insert per batch
            granularity: Time granularity of the data (e.g., '1d', '1h', '5m')
            data_source: Source of the data (default: 'databento')

        Returns:
            Dictionary with insertion statistics
        """
        if not records:
            logger.info("No OHLCV records to insert")
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
                                row_data = self._record_to_tuple(record, granularity, data_source)
                                batch_data.append(row_data)
                            except Exception as e:
                                logger.warning(f"Failed to convert OHLCV record: {e}")
                                stats['errors'] += 1
                                continue

                        if batch_data:
                            cursor.executemany(insert_sql, batch_data)
                            stats['inserted'] += len(batch_data)
                            logger.info(f"Inserted batch of {len(batch_data)} OHLCV records")

                conn.commit()
                logger.info(f"Successfully inserted {stats['inserted']} OHLCV records")

        except Exception as e:
            logger.error(f"Failed to insert OHLCV records: {e}")
            stats['errors'] += len(records) - stats['inserted']

        return stats

    def _build_insert_sql(self) -> str:
        """Build the INSERT SQL statement for OHLCV records."""
        columns = [
            'ts_event', 'ts_recv', 'instrument_id', 'symbol',
            'open_price', 'high_price', 'low_price', 'close_price', 'volume',
            'trade_count', 'vwap', 'granularity', 'data_source',
            'rtype', 'publisher_id'
        ]

        placeholders = ', '.join(['%s'] * len(columns))
        column_list = ', '.join(columns)

        return f"""
            INSERT INTO daily_ohlcv_data ({column_list})
            VALUES ({placeholders})
            ON CONFLICT (ts_event, instrument_id, granularity, data_source)
            DO UPDATE SET
                updated_at = NOW(),
                symbol = EXCLUDED.symbol,
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                volume = EXCLUDED.volume,
                trade_count = EXCLUDED.trade_count,
                vwap = EXCLUDED.vwap,
                ts_recv = EXCLUDED.ts_recv,
                rtype = EXCLUDED.rtype,
                publisher_id = EXCLUDED.publisher_id
        """

    def _record_to_tuple(self, record: DatabentoOHLCVRecord, granularity: str = '1d', data_source: str = 'databento') -> tuple:
        """Convert a DatabentoOHLCVRecord to tuple for database insertion.
        
        Args:
            record: The OHLCV record to convert
            granularity: Time granularity of the data
            data_source: Source of the data
        """
        return (
            record.ts_event,
            record.ts_recv,
            record.instrument_id,
            record.symbol,
            record.open_price,
            record.high_price,
            record.low_price,
            record.close_price,
            record.volume,
            record.trade_count,  # trade_count
            record.vwap,
            granularity,  # granularity from parameter
            data_source,  # data_source from parameter
            record.rtype,
            record.publisher_id
        )

    def get_ohlcv_records(self,
                          symbol: Optional[str] = None,
                          instrument_id: Optional[int] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Retrieve OHLCV records from the database.

        Args:
            symbol: Filter by symbol
            instrument_id: Filter by instrument ID
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            limit: Maximum number of records to return

        Returns:
            List of OHLCV records as dictionaries
        """
        query = """
            SELECT * FROM daily_ohlcv_data
            WHERE 1=1
        """
        params = []

        if symbol:
            query += " AND symbol = %s"
            params.append(symbol)

        if instrument_id:
            query += " AND instrument_id = %s"
            params.append(instrument_id)

        if start_date:
            query += " AND ts_event >= %s"
            params.append(start_date)

        if end_date:
            query += " AND ts_event <= %s"
            params.append(end_date)

        query += " ORDER BY ts_event DESC LIMIT %s"
        params.append(limit)

        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to retrieve OHLCV records: {e}")
            return []
