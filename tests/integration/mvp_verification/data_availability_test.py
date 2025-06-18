"""
Data Availability Verification Test (AC1)

This test verifies that data is available for MVP target symbols from Databento
for a recent period across key schemas, confirming minimum 30 days coverage.

MVP Target Symbols (from PRD Section 5):
- CL (Crude Oil futures) 
- SPY or /ES (S&P 500)
- NG (Natural Gas)
- HO (Heating Oil)  
- RB (RBOB Gasoline)
"""

import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
import structlog

from .verification_utils import VerificationUtils, MVPVerificationResult


class DataAvailabilityTest:
    """Test data availability for MVP target symbols across key schemas."""
    
    def __init__(self):
        self.utils = VerificationUtils()
        self.logger = structlog.get_logger(self.__class__.__name__)
        
        # Key schemas to verify (based on story technical guidance)
        self.key_schemas = [
            'ohlcv-1d',
            'trades', 
            'tbbo',
            'statistics',
            'definitions'
        ]
    
    def run_test(self) -> MVPVerificationResult:
        """Execute the complete data availability verification test."""
        self.logger.info("Starting data availability verification test")
        
        start_time = time.time()
        
        try:
            # Perform all data availability checks
            symbol_availability = self._check_symbol_availability()
            schema_coverage = self._check_schema_coverage() 
            data_recency = self._check_data_recency()
            data_continuity = self._check_data_continuity()
            
            # Aggregate results
            test_details = {
                'symbol_availability': symbol_availability,
                'schema_coverage': schema_coverage,
                'data_recency': data_recency,
                'data_continuity': data_continuity,
                'verification_criteria': {
                    'minimum_symbols': len(self.utils.MVP_SYMBOLS),
                    'minimum_days': self.utils.MINIMUM_DATA_DAYS,
                    'required_schemas': self.key_schemas,
                    'data_source': 'Databento'
                }
            }
            
            # Determine overall test status
            status = self._determine_test_status(test_details)
            recommendations = self.utils.generate_recommendations(
                'data_availability', status, test_details
            )
            
            execution_time = time.time() - start_time
            
            result = MVPVerificationResult(
                test_name="data_availability",
                status=status,
                execution_time=execution_time,
                details=test_details,
                recommendations=recommendations,
                timestamp=""
            )
            
            self.logger.info(
                "Data availability test completed",
                status=status,
                execution_time=execution_time
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error("Data availability test failed", error=str(e))
            
            return MVPVerificationResult(
                test_name="data_availability",
                status="ERROR",
                execution_time=execution_time,
                details={'error': str(e)},
                recommendations=['Fix database connectivity and retry test'],
                timestamp=""
            )
    
    def _check_symbol_availability(self) -> Dict[str, Any]:
        """Check if all MVP target symbols have data available."""
        self.logger.info("Checking symbol availability")
        
        query = """
        SELECT DISTINCT 
            security_symbol,
            data_source,
            COUNT(*) OVER (PARTITION BY security_symbol) as total_records,
            MIN(event_timestamp) OVER (PARTITION BY security_symbol) as earliest_record,
            MAX(event_timestamp) OVER (PARTITION BY security_symbol) as latest_record
        FROM financial_time_series_data 
        WHERE security_symbol = ANY(:symbols)
            AND data_source = 'Databento'
            AND event_timestamp >= :cutoff_date
        ORDER BY security_symbol;
        """
        
        cutoff_date = datetime.now() - timedelta(days=self.utils.MINIMUM_DATA_DAYS)
        
        try:
            results = self.utils.execute_query(query, {
                'symbols': self.utils.MVP_SYMBOLS,
                'cutoff_date': cutoff_date
            })
            
            symbols_found = set(r['security_symbol'] for r in results)
            symbols_expected = set(self.utils.MVP_SYMBOLS)
            missing_symbols = symbols_expected - symbols_found
            
            return {
                'symbols_expected': list(symbols_expected),
                'symbols_found': list(symbols_found),
                'missing_symbols': list(missing_symbols),
                'symbols_with_data': len(symbols_found),
                'total_symbols_required': len(symbols_expected),
                'coverage_percentage': (len(symbols_found) / len(symbols_expected)) * 100,
                'symbol_details': results
            }
            
        except Exception as e:
            self.logger.error("Symbol availability check failed", error=str(e))
            raise
    
    def _check_schema_coverage(self) -> Dict[str, Any]:
        """Check data availability across different schemas/table types."""
        self.logger.info("Checking schema coverage")
        
        # Query to check table existence and record counts
        table_check_query = """
        SELECT 
            table_name,
            CASE 
                WHEN table_name = 'financial_time_series_data' THEN 'PRIMARY'
                ELSE 'SECONDARY'
            END as table_type
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
            AND table_name IN (
                'financial_time_series_data',
                'daily_ohlcv_data', 
                'trades_data',
                'tbbo_data',
                'statistics_data',
                'definitions_data'
            );
        """
        
        try:
            table_results = self.utils.execute_query(table_check_query)
            tables_found = [r['table_name'] for r in table_results]
            
            # Check record counts for existing tables
            schema_details = {}
            cutoff_date = datetime.now() - timedelta(days=self.utils.MINIMUM_DATA_DAYS)
            
            for table in tables_found:
                if table == 'financial_time_series_data':
                    # Primary table with symbol filtering
                    count_query = f"""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(DISTINCT security_symbol) as unique_symbols,
                        MIN(event_timestamp) as earliest_date,
                        MAX(event_timestamp) as latest_date
                    FROM {table}
                    WHERE data_source = 'Databento'
                        AND event_timestamp >= :cutoff_date
                        AND security_symbol = ANY(:symbols);
                    """
                    
                    result = self.utils.execute_query(count_query, {
                        'cutoff_date': cutoff_date,
                        'symbols': self.utils.MVP_SYMBOLS
                    })
                else:
                    # Secondary tables - basic count
                    count_query = f"""
                    SELECT 
                        COUNT(*) as total_records,
                        MIN(ts_event) as earliest_date,
                        MAX(ts_event) as latest_date
                    FROM {table}
                    WHERE ts_event >= :cutoff_date;
                    """
                    
                    result = self.utils.execute_query(count_query, {
                        'cutoff_date': cutoff_date
                    })
                
                schema_details[table] = result[0] if result else {'total_records': 0}
            
            return {
                'tables_found': tables_found,
                'schema_details': schema_details,
                'primary_table_available': 'financial_time_series_data' in tables_found,
                'total_tables_found': len(tables_found)
            }
            
        except Exception as e:
            self.logger.error("Schema coverage check failed", error=str(e))
            raise
    
    def _check_data_recency(self) -> Dict[str, Any]:
        """Check if data is recent enough for MVP requirements."""
        self.logger.info("Checking data recency")
        
        query = """
        SELECT 
            security_symbol,
            MAX(event_timestamp) as latest_record,
            EXTRACT(EPOCH FROM (NOW() - MAX(event_timestamp)))/86400 as days_since_latest
        FROM financial_time_series_data 
        WHERE security_symbol = ANY(:symbols)
            AND data_source = 'Databento'
        GROUP BY security_symbol
        ORDER BY latest_record DESC;
        """
        
        try:
            results = self.utils.execute_query(query, {
                'symbols': self.utils.MVP_SYMBOLS
            })
            
            max_staleness_days = 7  # Data should be no more than 7 days old
            stale_symbols = [
                r for r in results 
                if r['days_since_latest'] > max_staleness_days
            ]
            
            return {
                'symbol_recency': results,
                'stale_symbols': stale_symbols,
                'max_allowed_staleness_days': max_staleness_days,
                'all_symbols_fresh': len(stale_symbols) == 0
            }
            
        except Exception as e:
            self.logger.error("Data recency check failed", error=str(e))
            raise
    
    def _check_data_continuity(self) -> Dict[str, Any]:
        """Check for data continuity and gaps in the time series."""
        self.logger.info("Checking data continuity")
        
        # Check for gaps in daily data for each symbol
        gap_analysis_query = """
        WITH daily_data AS (
            SELECT 
                security_symbol,
                DATE(event_timestamp) as data_date,
                COUNT(*) as records_per_day
            FROM financial_time_series_data 
            WHERE security_symbol = ANY(:symbols)
                AND data_source = 'Databento'
                AND event_timestamp >= :cutoff_date
            GROUP BY security_symbol, DATE(event_timestamp)
        ),
        date_range AS (
            SELECT 
                security_symbol,
                MIN(data_date) as start_date,
                MAX(data_date) as end_date,
                COUNT(*) as days_with_data,
                (MAX(data_date) - MIN(data_date) + 1) as expected_days
            FROM daily_data
            GROUP BY security_symbol
        )
        SELECT 
            security_symbol,
            start_date,
            end_date,
            days_with_data,
            expected_days,
            (expected_days - days_with_data) as missing_days,
            ROUND((days_with_data::DECIMAL / expected_days) * 100, 2) as continuity_percentage
        FROM date_range
        ORDER BY security_symbol;
        """
        
        cutoff_date = datetime.now() - timedelta(days=self.utils.MINIMUM_DATA_DAYS)
        
        try:
            results = self.utils.execute_query(gap_analysis_query, {
                'symbols': self.utils.MVP_SYMBOLS,
                'cutoff_date': cutoff_date
            })
            
            min_continuity_threshold = 90.0  # 90% continuity required
            symbols_with_gaps = [
                r for r in results 
                if r['continuity_percentage'] < min_continuity_threshold
            ]
            
            return {
                'continuity_analysis': results,
                'symbols_with_gaps': symbols_with_gaps,
                'min_continuity_threshold': min_continuity_threshold,
                'average_continuity': sum(r['continuity_percentage'] for r in results) / len(results) if results else 0
            }
            
        except Exception as e:
            self.logger.error("Data continuity check failed", error=str(e))
            raise
    
    def _determine_test_status(self, details: Dict[str, Any]) -> str:
        """Determine overall test status based on all checks."""
        symbol_availability = details['symbol_availability']
        schema_coverage = details['schema_coverage']
        data_recency = details['data_recency']
        data_continuity = details['data_continuity']
        
        # Critical failures
        if len(symbol_availability['missing_symbols']) > 0:
            return "FAIL"
        
        if not schema_coverage['primary_table_available']:
            return "FAIL"
        
        if not data_recency['all_symbols_fresh']:
            return "FAIL"
        
        # Warning conditions
        if symbol_availability['coverage_percentage'] < 100:
            return "WARNING"
        
        if data_continuity['average_continuity'] < 95.0:
            return "WARNING"
        
        # Success conditions
        return "PASS"
    
    def generate_detailed_report(self, result: MVPVerificationResult) -> str:
        """Generate a detailed text report of the data availability test."""
        details = result.details
        
        report = []
        report.append("=== MVP DATA AVAILABILITY VERIFICATION REPORT ===")
        report.append(f"Test Status: {result.status}")
        report.append(f"Execution Time: {result.execution_time:.2f} seconds")
        report.append(f"Timestamp: {result.timestamp}")
        report.append("")
        
        # Symbol availability section
        symbol_info = details['symbol_availability']
        report.append("SYMBOL AVAILABILITY:")
        report.append(f"  Expected symbols: {len(symbol_info['symbols_expected'])}")
        report.append(f"  Found symbols: {len(symbol_info['symbols_found'])}")
        report.append(f"  Coverage: {symbol_info['coverage_percentage']:.1f}%")
        
        if symbol_info['missing_symbols']:
            report.append(f"  Missing symbols: {', '.join(symbol_info['missing_symbols'])}")
        
        report.append("")
        
        # Schema coverage section
        schema_info = details['schema_coverage']
        report.append("SCHEMA COVERAGE:")
        report.append(f"  Tables found: {len(schema_info['tables_found'])}")
        report.append(f"  Primary table available: {schema_info['primary_table_available']}")
        
        report.append("")
        
        # Data recency section
        recency_info = details['data_recency']
        report.append("DATA RECENCY:")
        report.append(f"  All symbols fresh: {recency_info['all_symbols_fresh']}")
        
        if recency_info['stale_symbols']:
            report.append("  Stale symbols:")
            for symbol in recency_info['stale_symbols']:
                report.append(f"    {symbol['security_symbol']}: {symbol['days_since_latest']:.1f} days old")
        
        report.append("")
        
        # Recommendations
        if result.recommendations:
            report.append("RECOMMENDATIONS:")
            for rec in result.recommendations:
                report.append(f"  - {rec}")
        
        return "\n".join(report) 