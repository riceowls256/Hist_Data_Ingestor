"""
TimescaleDB TBBO (Top of Book Bid/Offer) Data Loader

This module provides the TimescaleTBBOLoader class for storing top-of-book bid/offer
quote records in TimescaleDB. It handles the creation of hypertables and efficient
batch insertion of TBBO data.
"""

import os
from contextlib import contextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

import psycopg2
import psycopg2.errors
from psycopg2.extras import RealDictCursor

from storage.models import DatabentoTBBORecord
from utils.custom_logger import get_logger

logger = get_logger(__name__)


class TimescaleTBBOLoader:
    """
    Loader for TBBO (Top of Book) data into TimescaleDB.

    This class handles the storage of TBBO records in the tbbo_data table,
    including hypertable creation and batch insertion operations.
    """

    def __init__(self, connection_params: Optional[Dict[str, Any]] = None):
        """
        Initialize the TimescaleTBBOLoader.

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
        Create the TBBO table and hypertable if they don't exist.
        Executes the SQL schema file for tbbo_data table.

        Returns:
            True if schema creation succeeded, False otherwise
        """
        from pathlib import Path
        
        # Get the schema file path
        schema_file = Path(__file__).parent / 'schema_definitions' / 'tbbo_data_table.sql'
        
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False
            
        # Read and parse the SQL schema file
        with open(schema_file, 'r') as f:
            sql_content = f.read()
        
        # Split the SQL file into individual statements
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
            if 'CREATE TABLE' in stmt_upper and 'tbbo_data' in stmt:
                # Replace CREATE TABLE with CREATE TABLE IF NOT EXISTS
                create_table_sql = stmt.replace('CREATE TABLE tbbo_data', 
                                               'CREATE TABLE IF NOT EXISTS tbbo_data')
                create_table_sql = create_table_sql.replace('DROP TABLE IF EXISTS tbbo_data CASCADE;', '')
            elif 'CREATE_HYPERTABLE' in stmt_upper:
                create_hypertable_sql = stmt
            elif 'CREATE INDEX' in stmt_upper:
                # Ensure all indexes use IF NOT EXISTS
                if 'IF NOT EXISTS' not in stmt:
                    stmt = stmt.replace('CREATE INDEX', 'CREATE INDEX IF NOT EXISTS')
                create_indexes_sql.append(stmt)
        
        if not create_table_sql:
            logger.error("Could not extract CREATE TABLE statement from schema file")
            return False

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create table
                    try:
                        cursor.execute(create_table_sql)
                        logger.info("TBBO table created successfully")
                    except psycopg2.errors.DuplicateTable:
                        logger.info("TBBO table already exists, skipping creation")
                    except Exception as e:
                        logger.error(f"Failed to create TBBO table: {e}")
                        raise

                    # Create hypertable
                    if create_hypertable_sql:
                        try:
                            cursor.execute(create_hypertable_sql)
                            logger.info("TBBO hypertable created or already exists")
                        except Exception as e:
                            # Hypertable creation with if_not_exists=TRUE should not fail
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
                    logger.info("TBBO indexes created or verified")

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to create TBBO schema: {e}")
            return False

    def insert_tbbo_records(self,
                          records: List[DatabentoTBBORecord],
                          batch_size: int = 1000,
                          data_source: str = 'databento') -> Dict[str, int]:
        """
        Insert TBBO records into the database.

        Args:
            records: List of DatabentoTBBORecord instances to insert
            batch_size: Number of records to insert per batch
            data_source: Source of the data (default: 'databento')

        Returns:
            Dictionary with insertion statistics
        """
        if not records:
            logger.info("No TBBO records to insert")
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
                                # Convert Pydantic model to tuple
                                data = self._record_to_tuple(record, data_source)
                                batch_data.append(data)
                            except Exception as e:
                                logger.error(f"Failed to convert record: {e}")
                                stats['errors'] += 1
                                continue

                        if batch_data:
                            try:
                                cursor.executemany(insert_sql, batch_data)
                                stats['inserted'] += len(batch_data)
                                logger.debug(f"Inserted batch of {len(batch_data)} TBBO records")
                            except Exception as e:
                                logger.error(f"Failed to insert batch: {e}")
                                stats['errors'] += len(batch_data)
                                conn.rollback()
                                continue

                    conn.commit()
                    logger.info(f"Successfully inserted {stats['inserted']} TBBO records")

        except Exception as e:
            logger.error(f"Database error during TBBO insertion: {e}")
            raise

        return stats

    def _build_insert_sql(self) -> str:
        """Build the INSERT SQL statement for TBBO."""
        return """
            INSERT INTO tbbo_data (
                ts_event, instrument_id, bid_px, ask_px, bid_sz, ask_sz,
                bid_ct, ask_ct, sequence, ts_recv, symbol, data_source, is_crossed
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

    def _record_to_tuple(self, record: DatabentoTBBORecord, data_source: str) -> tuple:
        """Convert a DatabentoTBBORecord to a tuple for insertion."""
        # Calculate if this is a crossed market
        is_crossed = False
        if record.bid_px is not None and record.ask_px is not None:
            if record.bid_px > record.ask_px:
                is_crossed = True
        
        return (
            record.ts_event,
            record.instrument_id,
            float(record.bid_px) if isinstance(record.bid_px, Decimal) else record.bid_px,
            float(record.ask_px) if isinstance(record.ask_px, Decimal) else record.ask_px,
            record.bid_sz,
            record.ask_sz,
            record.bid_ct,
            record.ask_ct,
            record.sequence,
            record.ts_recv,
            record.symbol,
            data_source,
            is_crossed  # Add the crossed market flag
        )