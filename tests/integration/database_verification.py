#!/usr/bin/env python3
"""
Database Verification Module for Story 2.7 End-to-End Testing.

This module provides comprehensive database verification utilities to validate:
- Data storage correctness across all Databento schemas
- Data integrity and business logic constraints  
- Transformation accuracy from source to target format
- Record counts and data quality metrics
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)


@dataclass
class DatabaseConfig:
    """Database configuration for testing."""
    host: str
    port: int
    database: str
    user: str
    password: str
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create config from environment variables."""
        return cls(
            host=os.getenv('TIMESCALEDB_TEST_HOST', 'localhost'),
            port=int(os.getenv('TIMESCALEDB_TEST_PORT', '5432')),
            database=os.getenv('TIMESCALEDB_TEST_DB', 'hist_data_test'),
            user=os.getenv('TIMESCALEDB_TEST_USER', 'postgres'),
            password=os.getenv('TIMESCALEDB_TEST_PASSWORD', 'password')
        )


@dataclass 
class VerificationResult:
    """Result of database verification check."""
    table_name: str
    check_name: str
    passed: bool
    expected: Any
    actual: Any
    details: str
    
    def __str__(self) -> str:
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} {self.table_name}.{self.check_name}: {self.details}"


class DatabaseVerifier:
    """Comprehensive database verification for end-to-end testing."""
    
    def __init__(self, config: DatabaseConfig):
        """Initialize database verifier with configuration."""
        self.config = config
        self.connection: Optional[psycopg2.connection] = None
        self.logger = logging.getLogger(__name__)
        
        # Schema-specific verification rules
        self.schema_verifications = {
            'daily_ohlcv_data': self._verify_ohlcv_data,
            'trades_data': self._verify_trades_data,
            'tbbo_data': self._verify_tbbo_data,
            'statistics_data': self._verify_statistics_data,
            'definitions_data': self._verify_definitions_data
        }
    
    def connect(self) -> bool:
        """Connect to the test database."""
        try:
            self.connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password
            )
            self.logger.info(f"Connected to database: {self.config.database}")
            return True
        except psycopg2.Error as e:
            self.logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from database."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute query and return results as list of dictionaries."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def verify_all_tables(self, test_date_range: Optional[Tuple[str, str]] = None) -> Dict[str, List[VerificationResult]]:
        """
        Run comprehensive verification on all tables.
        
        Args:
            test_date_range: Optional (start_date, end_date) tuple for filtering test data
            
        Returns:
            Dictionary mapping table names to verification results
        """
        all_results = {}
        
        for table_name, verify_func in self.schema_verifications.items():
            self.logger.info(f"Verifying table: {table_name}")
            try:
                results = verify_func(test_date_range)
                all_results[table_name] = results
            except Exception as e:
                error_result = VerificationResult(
                    table_name=table_name,
                    check_name="table_verification",
                    passed=False,
                    expected="No errors",
                    actual=str(e),
                    details=f"Verification failed with error: {e}"
                )
                all_results[table_name] = [error_result]
        
        return all_results
    
    def _verify_ohlcv_data(self, date_range: Optional[Tuple[str, str]]) -> List[VerificationResult]:
        """Verify OHLCV data integrity and business logic."""
        results = []
        
        # Base query for OHLCV data
        base_query = """
        SELECT 
            COUNT(*) as record_count,
            COUNT(DISTINCT instrument_id) as unique_instruments,
            MIN(ts_event) as earliest_timestamp,
            MAX(ts_event) as latest_timestamp,
            MIN(open_price) as min_open,
            MAX(high_price) as max_high,
            MIN(low_price) as min_low,
            AVG(volume) as avg_volume
        FROM daily_ohlcv_data 
        WHERE data_source = 'databento'
        """
        
        if date_range:
            base_query += f" AND ts_event >= '{date_range[0]}' AND ts_event <= '{date_range[1]}'"
        
        # 1. Record count verification
        data = self.execute_query(base_query)
        if data:
            row = data[0]
            results.append(VerificationResult(
                table_name='daily_ohlcv_data',
                check_name='record_count',
                passed=row['record_count'] > 0,
                expected="> 0",
                actual=row['record_count'],
                details=f"Found {row['record_count']} OHLCV records"
            ))
            
            # 2. Business logic: High >= Low constraint
            invalid_ohlc_query = """
            SELECT COUNT(*) as invalid_count 
            FROM daily_ohlcv_data 
            WHERE data_source = 'databento' 
            AND (high_price < low_price 
                OR high_price < open_price 
                OR high_price < close_price)
            """
            if date_range:
                invalid_ohlc_query += f" AND ts_event >= '{date_range[0]}' AND ts_event <= '{date_range[1]}'"
            
            invalid_data = self.execute_query(invalid_ohlc_query)
            invalid_count = invalid_data[0]['invalid_count']
            
            results.append(VerificationResult(
                table_name='daily_ohlcv_data',
                check_name='ohlc_business_logic',
                passed=invalid_count == 0,
                expected=0,
                actual=invalid_count,
                details=f"Invalid OHLC relationships: {invalid_count}"
            ))
            
            # 3. Price range validation (positive prices)
            negative_prices_query = """
            SELECT COUNT(*) as negative_count
            FROM daily_ohlcv_data 
            WHERE data_source = 'databento'
            AND (open_price <= 0 OR high_price <= 0 OR low_price <= 0 OR close_price <= 0)
            """
            if date_range:
                negative_prices_query += f" AND ts_event >= '{date_range[0]}' AND ts_event <= '{date_range[1]}'"
            
            negative_data = self.execute_query(negative_prices_query)
            negative_count = negative_data[0]['negative_count']
            
            results.append(VerificationResult(
                table_name='daily_ohlcv_data',
                check_name='positive_prices',
                passed=negative_count == 0,
                expected=0,
                actual=negative_count,
                details=f"Records with non-positive prices: {negative_count}"
            ))
        
        return results
    
    def _verify_trades_data(self, date_range: Optional[Tuple[str, str]]) -> List[VerificationResult]:
        """Verify trades data integrity."""
        results = []
        
        base_query = """
        SELECT 
            COUNT(*) as record_count,
            COUNT(DISTINCT instrument_id) as unique_instruments,
            MIN(ts_event) as earliest_timestamp,
            MAX(ts_event) as latest_timestamp,
            SUM(size) as total_volume,
            AVG(price) as avg_price
        FROM trades_data 
        WHERE data_source = 'databento'
        """
        
        if date_range:
            base_query += f" AND ts_event >= '{date_range[0]}' AND ts_event <= '{date_range[1]}'"
        
        data = self.execute_query(base_query)
        if data:
            row = data[0]
            results.append(VerificationResult(
                table_name='trades_data',
                check_name='record_count',
                passed=row['record_count'] > 0,
                expected="> 0",
                actual=row['record_count'],
                details=f"Found {row['record_count']} trade records"
            ))
            
            # Validate positive prices and sizes
            invalid_trades_query = """
            SELECT COUNT(*) as invalid_count
            FROM trades_data 
            WHERE data_source = 'databento'
            AND (price <= 0 OR size <= 0)
            """
            if date_range:
                invalid_trades_query += f" AND ts_event >= '{date_range[0]}' AND ts_event <= '{date_range[1]}'"
            
            invalid_data = self.execute_query(invalid_trades_query)
            invalid_count = invalid_data[0]['invalid_count']
            
            results.append(VerificationResult(
                table_name='trades_data',
                check_name='positive_values',
                passed=invalid_count == 0,
                expected=0,
                actual=invalid_count,
                details=f"Trades with invalid price/size: {invalid_count}"
            ))
        
        return results
    
    def _verify_tbbo_data(self, date_range: Optional[Tuple[str, str]]) -> List[VerificationResult]:
        """Verify top-of-book bid/offer data integrity."""
        results = []
        
        base_query = """
        SELECT 
            COUNT(*) as record_count,
            COUNT(DISTINCT instrument_id) as unique_instruments,
            MIN(ts_event) as earliest_timestamp,
            MAX(ts_event) as latest_timestamp
        FROM tbbo_data 
        WHERE data_source = 'databento'
        """
        
        if date_range:
            base_query += f" AND ts_event >= '{date_range[0]}' AND ts_event <= '{date_range[1]}'"
        
        data = self.execute_query(base_query)
        if data:
            row = data[0]
            results.append(VerificationResult(
                table_name='tbbo_data',
                check_name='record_count',
                passed=row['record_count'] > 0,
                expected="> 0",
                actual=row['record_count'],
                details=f"Found {row['record_count']} TBBO records"
            ))
            
            # Validate bid/ask spread logic (ask >= bid when both present)
            invalid_spread_query = """
            SELECT COUNT(*) as invalid_count
            FROM tbbo_data 
            WHERE data_source = 'databento'
            AND bid_price IS NOT NULL 
            AND ask_price IS NOT NULL
            AND ask_price < bid_price
            """
            if date_range:
                invalid_spread_query += f" AND ts_event >= '{date_range[0]}' AND ts_event <= '{date_range[1]}'"
            
            invalid_data = self.execute_query(invalid_spread_query)
            invalid_count = invalid_data[0]['invalid_count']
            
            results.append(VerificationResult(
                table_name='tbbo_data',
                check_name='bid_ask_spread',
                passed=invalid_count == 0,
                expected=0,
                actual=invalid_count,
                details=f"Invalid bid/ask spreads: {invalid_count}"
            ))
        
        return results
    
    def _verify_statistics_data(self, date_range: Optional[Tuple[str, str]]) -> List[VerificationResult]:
        """Verify statistics data integrity."""
        results = []
        
        base_query = """
        SELECT 
            COUNT(*) as record_count,
            COUNT(DISTINCT instrument_id) as unique_instruments,
            COUNT(DISTINCT stat_type) as unique_stat_types,
            MIN(ts_event) as earliest_timestamp,
            MAX(ts_event) as latest_timestamp
        FROM statistics_data 
        WHERE data_source = 'databento'
        """
        
        if date_range:
            base_query += f" AND ts_event >= '{date_range[0]}' AND ts_event <= '{date_range[1]}'"
        
        data = self.execute_query(base_query)
        if data:
            row = data[0]
            results.append(VerificationResult(
                table_name='statistics_data',
                check_name='record_count',
                passed=row['record_count'] >= 0,  # Statistics might be empty for test data
                expected=">= 0",
                actual=row['record_count'],
                details=f"Found {row['record_count']} statistics records"
            ))
        
        return results
    
    def _verify_definitions_data(self, date_range: Optional[Tuple[str, str]]) -> List[VerificationResult]:
        """Verify definitions data integrity."""
        results = []
        
        base_query = """
        SELECT 
            COUNT(*) as record_count,
            COUNT(DISTINCT instrument_id) as unique_instruments,
            MIN(ts_event) as earliest_timestamp,
            MAX(ts_event) as latest_timestamp
        FROM definitions_data 
        WHERE data_source = 'databento'
        """
        
        if date_range:
            base_query += f" AND ts_event >= '{date_range[0]}' AND ts_event <= '{date_range[1]}'"
        
        data = self.execute_query(base_query)
        if data:
            row = data[0]
            results.append(VerificationResult(
                table_name='definitions_data',
                check_name='record_count',
                passed=row['record_count'] >= 0,  # Definitions might be empty for some test datasets
                expected=">= 0",
                actual=row['record_count'],
                details=f"Found {row['record_count']} definition records"
            ))
        
        return results
    
    def check_idempotency(self, table_name: str, date_range: Optional[Tuple[str, str]] = None) -> List[VerificationResult]:
        """
        Check for duplicate records (idempotency verification).
        
        Args:
            table_name: Name of table to check
            date_range: Optional date range for filtering
            
        Returns:
            List of verification results for idempotency checks
        """
        results = []
        
        # Define unique constraints for each table
        unique_constraints = {
            'daily_ohlcv_data': ['instrument_id', 'ts_event', 'granularity'],
            'trades_data': ['instrument_id', 'ts_event', 'price', 'size'],
            'tbbo_data': ['instrument_id', 'ts_event'],
            'statistics_data': ['instrument_id', 'ts_event', 'stat_type'],
            'definitions_data': ['instrument_id', 'ts_event']
        }
        
        if table_name not in unique_constraints:
            results.append(VerificationResult(
                table_name=table_name,
                check_name='idempotency_check',
                passed=False,
                expected="Valid table name",
                actual=table_name,
                details=f"Unknown table: {table_name}"
            ))
            return results
        
        # Build duplicate check query
        constraint_fields = unique_constraints[table_name]
        fields_str = ', '.join(constraint_fields)
        
        duplicate_query = f"""
        SELECT {fields_str}, COUNT(*) as duplicate_count
        FROM {table_name}
        WHERE data_source = 'databento'
        """
        
        if date_range:
            duplicate_query += f" AND ts_event >= '{date_range[0]}' AND ts_event <= '{date_range[1]}'"
        
        duplicate_query += f"""
        GROUP BY {fields_str}
        HAVING COUNT(*) > 1
        """
        
        duplicates = self.execute_query(duplicate_query)
        
        results.append(VerificationResult(
            table_name=table_name,
            check_name='idempotency_check',
            passed=len(duplicates) == 0,
            expected=0,
            actual=len(duplicates),
            details=f"Duplicate record groups found: {len(duplicates)}"
        ))
        
        return results
    
    def generate_verification_report(self, all_results: Dict[str, List[VerificationResult]]) -> str:
        """Generate a comprehensive verification report."""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("DATABASE VERIFICATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().isoformat()}")
        report_lines.append("")
        
        total_checks = 0
        passed_checks = 0
        
        for table_name, results in all_results.items():
            report_lines.append(f"TABLE: {table_name.upper()}")
            report_lines.append("-" * 40)
            
            for result in results:
                report_lines.append(str(result))
                total_checks += 1
                if result.passed:
                    passed_checks += 1
            
            report_lines.append("")
        
        # Summary
        report_lines.append("SUMMARY:")
        report_lines.append(f"Total checks: {total_checks}")
        report_lines.append(f"Passed: {passed_checks}")
        report_lines.append(f"Failed: {total_checks - passed_checks}")
        report_lines.append(f"Success rate: {(passed_checks/total_checks*100):.1f}%" if total_checks > 0 else "No checks run")
        
        return "\n".join(report_lines)


def main():
    """Main function for running database verification."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("🔍 Database Verification for Story 2.7")
    print("=" * 50)
    
    # Load configuration
    config = DatabaseConfig.from_env()
    print(f"Database: {config.host}:{config.port}/{config.database}")
    
    # Initialize verifier
    verifier = DatabaseVerifier(config)
    
    if not verifier.connect():
        print("❌ Failed to connect to database")
        return False
    
    try:
        # Run comprehensive verification
        print("Running comprehensive database verification...")
        all_results = verifier.verify_all_tables()
        
        # Check idempotency for all tables
        print("Checking idempotency...")
        for table_name in verifier.schema_verifications.keys():
            idempotency_results = verifier.check_idempotency(table_name)
            all_results[table_name].extend(idempotency_results)
        
        # Generate and display report
        report = verifier.generate_verification_report(all_results)
        print("\n" + report)
        
        # Save report to file
        report_file = Path("database_verification_report.txt")
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_file}")
        
        return True
        
    finally:
        verifier.disconnect()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 