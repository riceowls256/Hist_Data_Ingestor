"""
QueryBuilder for TimescaleDB financial data retrieval.

This module provides a comprehensive querying interface for retrieving financial
data from TimescaleDB using SQLAlchemy Core. It supports all Databento schemas
and provides optimized query construction with symbol resolution.
"""

import structlog
import os
from contextlib import contextmanager
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional, Union, Iterator
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, select, and_, or_, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .table_definitions import (
    SCHEMA_TABLES, INDEX_COLUMNS, definitions_data,
    daily_ohlcv_data, trades_data, tbbo_data, statistics_data
)
from .exceptions import QueryExecutionError, SymbolResolutionError

logger = structlog.get_logger(__name__)


class QueryBuilder:
    """
    Main query builder for TimescaleDB financial data retrieval.

    Provides methods to query all supported schemas with symbol resolution,
    date range filtering, and performance optimization for TimescaleDB.
    """

    def __init__(self, connection_params: Optional[Dict[str, Any]] = None):
        """
        Initialize the QueryBuilder.

        Args:
            connection_params: Database connection parameters, if None uses environment
        """
        self.connection_params = connection_params or self._get_connection_params()
        self.engine = self._create_engine()

    def _get_connection_params(self) -> Dict[str, Any]:
        """Get database connection parameters from environment variables."""
        return {
            'host': os.getenv('TIMESCALEDB_HOST', 'localhost'),
            'port': int(os.getenv('TIMESCALEDB_PORT', '5432')),
            'database': os.getenv('TIMESCALEDB_DBNAME', 'hist_data'),
            'user': os.getenv('TIMESCALEDB_USER', 'postgres'),
            'password': os.getenv('TIMESCALEDB_PASSWORD', ''),
        }

    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with connection pooling."""
        params = self.connection_params
        password = quote_plus(params['password']) if params['password'] else ''

        connection_string = (
            f"postgresql://{params['user']}:{password}@"
            f"{params['host']}:{params['port']}/{params['database']}"
        )

        return create_engine(
            connection_string,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False  # Set to True for SQL debugging
        )

    @contextmanager
    def get_connection(self):
        """Get a database connection with proper cleanup."""
        connection = None
        try:
            connection = self.engine.connect()
            yield connection
        except Exception as e:
            # Don't wrap SymbolResolutionError - let it bubble up for fallback handling
            if isinstance(e, SymbolResolutionError):
                raise e
            logger.error(f"Database connection error: {e}")
            raise QueryExecutionError(f"Failed to connect to database: {e}")
        finally:
            if connection:
                connection.close()

    def _resolve_symbols_to_instrument_ids(
        self,
        symbols: Union[str, List[str]]
    ) -> List[int]:
        """
        Resolve security symbols to instrument_ids via definitions_data table.

        Args:
            symbols: Single symbol string or list of symbol strings

        Returns:
            List of instrument_ids corresponding to the symbols

        Raises:
            SymbolResolutionError: If symbols cannot be resolved
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        if not symbols:
            return []

        try:
            with self.get_connection() as conn:
                # First check if definitions_data table exists
                table_exists = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'definitions_data'
                    );
                """)).fetchone()[0]

                if not table_exists:
                    logger.info("definitions_data table not found, using fallback symbol resolution")
                    raise SymbolResolutionError("definitions_data table does not exist")

                # Query to resolve symbols to instrument_ids
                query = select(definitions_data.c.instrument_id, definitions_data.c.raw_symbol).where(
                    definitions_data.c.raw_symbol.in_(symbols)
                ).distinct()

                result = conn.execute(query)
                rows = result.fetchall()

                if not rows:
                    raise SymbolResolutionError(f"No instrument_ids found for symbols: {symbols}")

                # Check if all symbols were resolved
                found_symbols = {row.raw_symbol for row in rows}
                missing_symbols = set(symbols) - found_symbols

                if missing_symbols:
                    logger.warning(f"Could not resolve symbols: {missing_symbols}")
                    # Continue with found symbols rather than failing completely

                instrument_ids = [row.instrument_id for row in rows]
                logger.info(f"Resolved {len(symbols)} symbols to {len(instrument_ids)} instrument_ids")

                return instrument_ids

        except SQLAlchemyError as e:
            logger.error(f"Database error during symbol resolution: {e}")
            raise SymbolResolutionError(f"Failed to resolve symbols: {e}")

    def _query_ohlcv_by_symbols_direct(
        self,
        symbols: Union[str, List[str]],
        start_date: Optional[Union[date, datetime]] = None,
        end_date: Optional[Union[date, datetime]] = None,
        granularity: str = '1d',
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query OHLCV data directly by symbols without requiring definitions table.

        This is a fallback method when definitions_data table is not available.

        Args:
            symbols: Single symbol string or list of symbol strings
            start_date: Start date for time range filter
            end_date: End date for time range filter
            granularity: Time granularity (default: '1d')
            limit: Maximum number of records to return

        Returns:
            List of dictionaries containing OHLCV data with symbols

        Raises:
            QueryExecutionError: If query fails
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        if not symbols:
            return []

        try:
            with self.get_connection() as conn:
                # Build query conditions
                conditions = [
                    daily_ohlcv_data.c.symbol.in_(symbols),
                    daily_ohlcv_data.c.granularity == granularity
                ]

                # Add date range filters
                if start_date:
                    conditions.append(daily_ohlcv_data.c.ts_event >= start_date)
                if end_date:
                    conditions.append(daily_ohlcv_data.c.ts_event <= end_date)

                # Build query
                query = select(daily_ohlcv_data).where(and_(*conditions))
                query = query.order_by(daily_ohlcv_data.c.symbol, daily_ohlcv_data.c.ts_event.desc())

                # Apply limit if specified
                if limit:
                    query = query.limit(limit)

                result = conn.execute(query)
                rows = result.fetchall()

                # Convert to list of dictionaries
                results = []
                for row in rows:
                    row_dict = dict(row._mapping)
                    results.append(row_dict)

                logger.info(f"Retrieved {len(results)} OHLCV records for {len(symbols)} symbols")
                return results

        except SQLAlchemyError as e:
            logger.error(f"Database error during direct OHLCV query: {e}")
            raise QueryExecutionError(f"Failed to query OHLCV data: {e}")

    def _build_base_query(
        self,
        table,
        instrument_ids: List[int],
        start_date: Optional[Union[date, datetime]] = None,
        end_date: Optional[Union[date, datetime]] = None,
        additional_filters: Optional[List] = None,
        limit: Optional[int] = None
    ):
        """
        Build base query with common filters for optimal index usage.

        Args:
            table: SQLAlchemy table object
            instrument_ids: List of instrument IDs to filter by
            start_date: Start date for time range filter
            end_date: End date for time range filter
            additional_filters: Additional WHERE conditions
            limit: Maximum number of records to return

        Returns:
            SQLAlchemy select query object
        """
        # Start with base select
        query = select(table)

        # Build WHERE conditions for optimal index usage
        conditions = []

        # Always filter by instrument_id first (primary key component)
        if instrument_ids:
            conditions.append(table.c.instrument_id.in_(instrument_ids))

        # Add date range filters (leverages time-based partitioning)
        if start_date:
            conditions.append(table.c.ts_event >= start_date)
        if end_date:
            conditions.append(table.c.ts_event <= end_date)

        # Add any additional filters
        if additional_filters:
            conditions.extend(additional_filters)

        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))

        # Order by index columns for optimal performance
        query = query.order_by(table.c.instrument_id, table.c.ts_event.desc())

        # Apply limit if specified
        if limit:
            query = query.limit(limit)

        return query

    def _execute_query_with_symbol_resolution(
        self,
        table,
        symbols: Union[str, List[str]],
        start_date: Optional[Union[date, datetime]] = None,
        end_date: Optional[Union[date, datetime]] = None,
        additional_filters: Optional[List] = None,
        limit: Optional[int] = None,
        include_symbol_names: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute query with automatic symbol resolution and return formatted results.

        Args:
            table: SQLAlchemy table object
            symbols: Symbol(s) to query for
            start_date: Start date for filtering
            end_date: End date for filtering
            additional_filters: Additional WHERE conditions
            limit: Maximum records to return
            include_symbol_names: Whether to include resolved symbol names in results

        Returns:
            List of dictionaries containing query results
        """
        try:
            # Resolve symbols to instrument_ids
            instrument_ids = self._resolve_symbols_to_instrument_ids(symbols)

            if not instrument_ids:
                logger.info("No instrument_ids resolved, returning empty result")
                return []

            # Build and execute query
            query = self._build_base_query(
                table, instrument_ids, start_date, end_date, additional_filters, limit
            )

            with self.get_connection() as conn:
                start_time = datetime.now()
                result = conn.execute(query)
                rows = result.fetchall()
                execution_time = (datetime.now() - start_time).total_seconds()

                logger.info(f"Query executed in {execution_time:.3f}s, returned {len(rows)} rows")

                # Convert to list of dictionaries
                results = [dict(row._mapping) for row in rows]

                # Add symbol names if requested
                if include_symbol_names and results:
                    results = self._add_symbol_names_to_results(results)

                return results

        except SymbolResolutionError:
            # Re-raise SymbolResolutionError for fallback handling
            raise
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryExecutionError(f"Failed to execute query: {e}")

    def _add_symbol_names_to_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add symbol names to query results by looking up instrument_ids.

        Args:
            results: List of query result dictionaries

        Returns:
            Results with 'symbol' field added
        """
        if not results:
            return results

        # Get unique instrument_ids from results
        instrument_ids = list(set(row['instrument_id'] for row in results))

        try:
            with self.get_connection() as conn:
                # Query for symbol mappings
                symbol_query = select(
                    definitions_data.c.instrument_id,
                    definitions_data.c.raw_symbol
                ).where(
                    definitions_data.c.instrument_id.in_(instrument_ids)
                ).distinct()

                symbol_result = conn.execute(symbol_query)
                symbol_mapping = {
                    row.instrument_id: row.raw_symbol
                    for row in symbol_result.fetchall()
                }

                # Add symbol names to results
                for row in results:
                    row['symbol'] = symbol_mapping.get(row['instrument_id'], 'UNKNOWN')

                return results

        except Exception as e:
            logger.warning(f"Failed to add symbol names: {e}")
            # Return results without symbol names rather than failing
            return results

    def query_daily_ohlcv(
        self,
        symbols: Union[str, List[str]],
        start_date: Optional[Union[date, datetime]] = None,
        end_date: Optional[Union[date, datetime]] = None,
        granularity: str = '1d',
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query daily OHLCV data for specified symbols and date range.

        This method tries to use the definitions table for symbol resolution,
        but falls back to direct symbol queries if the definitions table is not available.

        Args:
            symbols: Symbol(s) to query for
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            granularity: Data granularity (default: '1d')
            limit: Maximum number of records to return

        Returns:
            List of dictionaries containing OHLCV data

        Raises:
            QueryExecutionError: If database query fails

        Example:
            >>> qb = QueryBuilder()
            >>> results = qb.query_daily_ohlcv(
            ...     symbols=['ES.c.0'],
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 1, 31),
            ...     limit=100
            ... )
            >>> print(f"Found {len(results)} OHLCV records")
        """
        try:
            # Try the standard approach using definitions table
            additional_filters = [daily_ohlcv_data.c.granularity == granularity]

            return self._execute_query_with_symbol_resolution(
                daily_ohlcv_data, symbols, start_date, end_date,
                additional_filters, limit
            )

        except SymbolResolutionError as e:
            # If symbol resolution fails (e.g., definitions table doesn't exist),
            # fall back to direct symbol query
            logger.info(f"Symbol resolution failed, using direct symbol query: {e}")

            return self._query_ohlcv_by_symbols_direct(
                symbols, start_date, end_date, granularity, limit
            )

    def query_trades(
        self,
        symbols: Union[str, List[str]],
        start_date: Optional[Union[date, datetime]] = None,
        end_date: Optional[Union[date, datetime]] = None,
        side: Optional[str] = None,
        limit: Optional[int] = 10000  # Default limit for high-volume data
    ) -> List[Dict[str, Any]]:
        """
        Query trades data for specified symbols and date range.

        Args:
            symbols: Symbol(s) to query for
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            side: Trade side filter ('B' for buy, 'S' for sell)
            limit: Maximum number of records to return (default: 10000)

        Returns:
            List of dictionaries containing trades data
        """
        additional_filters = []
        if side:
            additional_filters.append(trades_data.c.side == side)

        return self._execute_query_with_symbol_resolution(
            trades_data, symbols, start_date, end_date,
            additional_filters, limit
        )

    def query_tbbo(
        self,
        symbols: Union[str, List[str]],
        start_date: Optional[Union[date, datetime]] = None,
        end_date: Optional[Union[date, datetime]] = None,
        limit: Optional[int] = 10000  # Default limit for high-volume data
    ) -> List[Dict[str, Any]]:
        """
        Query TBBO (Top of Book) data for specified symbols and date range.

        Args:
            symbols: Symbol(s) to query for
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            limit: Maximum number of records to return (default: 10000)

        Returns:
            List of dictionaries containing TBBO data
        """
        return self._execute_query_with_symbol_resolution(
            tbbo_data, symbols, start_date, end_date,
            None, limit
        )

    def query_statistics(
        self,
        symbols: Union[str, List[str]],
        start_date: Optional[Union[date, datetime]] = None,
        end_date: Optional[Union[date, datetime]] = None,
        stat_type: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query statistics data for specified symbols and date range.

        Args:
            symbols: Symbol(s) to query for
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            stat_type: Statistics type filter
            limit: Maximum number of records to return

        Returns:
            List of dictionaries containing statistics data
        """
        additional_filters = []
        if stat_type is not None:
            additional_filters.append(statistics_data.c.stat_type == stat_type)

        return self._execute_query_with_symbol_resolution(
            statistics_data, symbols, start_date, end_date,
            additional_filters, limit
        )

    def query_definitions(
        self,
        symbols: Optional[Union[str, List[str]]] = None,
        asset: Optional[str] = None,
        exchange: Optional[str] = None,
        instrument_class: Optional[str] = None,
        limit: Optional[int] = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query instrument definitions data.

        Args:
            symbols: Symbol(s) to query for (optional)
            asset: Asset filter (e.g., 'ES', 'CL')
            exchange: Exchange filter
            instrument_class: Instrument class filter (e.g., 'FUT', 'OPT')
            limit: Maximum number of records to return

        Returns:
            List of dictionaries containing definitions data
        """
        additional_filters = []

        if asset:
            additional_filters.append(definitions_data.c.asset == asset)
        if exchange:
            additional_filters.append(definitions_data.c.exchange == exchange)
        if instrument_class:
            additional_filters.append(definitions_data.c.instrument_class == instrument_class)

        if symbols:
            return self._execute_query_with_symbol_resolution(
                definitions_data, symbols, None, None,
                additional_filters, limit, include_symbol_names=False
            )
        else:
            # Query without symbol resolution
            try:
                query = self._build_base_query(
                    definitions_data, [], None, None, additional_filters, limit
                )

                with self.get_connection() as conn:
                    result = conn.execute(query)
                    rows = result.fetchall()

                    return [dict(row._mapping) for row in rows]

            except Exception as e:
                logger.error(f"Definitions query failed: {e}")
                raise QueryExecutionError(f"Failed to query definitions: {e}")

    def to_dataframe(self, results: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert query results to Pandas DataFrame.

        Args:
            results: List of dictionaries from query methods

        Returns:
            Pandas DataFrame with query results
        """
        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)

        # Convert timestamp columns to datetime
        timestamp_columns = ['ts_event', 'ts_recv', 'ts_ref', 'expiration', 'activation']
        for col in timestamp_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])

        # Convert decimal columns to float for easier analysis
        decimal_columns = [col for col in df.columns if 'price' in col.lower() or col in ['vwap']]
        for col in decimal_columns:
            if col in df.columns and df[col].dtype == 'object':
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def get_available_symbols(
        self,
        asset: Optional[str] = None,
        exchange: Optional[str] = None,
        limit: int = 100
    ) -> List[str]:
        """
        Get list of available symbols in the database.

        Args:
            asset: Filter by asset
            exchange: Filter by exchange
            limit: Maximum number of symbols to return

        Returns:
            List of available symbol strings
        """
        try:
            additional_filters = []
            if asset:
                additional_filters.append(definitions_data.c.asset == asset)
            if exchange:
                additional_filters.append(definitions_data.c.exchange == exchange)

            query = select(definitions_data.c.raw_symbol).distinct()

            if additional_filters:
                query = query.where(and_(*additional_filters))

            query = query.order_by(definitions_data.c.raw_symbol).limit(limit)

            with self.get_connection() as conn:
                result = conn.execute(query)
                return [row.raw_symbol for row in result.fetchall()]

        except Exception as e:
            logger.error(f"Failed to get available symbols: {e}")
            return []
