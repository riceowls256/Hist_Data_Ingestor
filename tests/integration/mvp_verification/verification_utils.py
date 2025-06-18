"""
Shared utilities for MVP verification tests.

This module provides common functionality used across all MVP verification scripts,
including database connections, logging setup, result formatting, and utility functions.
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.exc import SQLAlchemyError
import structlog

# Configure structured logging
logger = structlog.get_logger(__name__)


@dataclass
class MVPVerificationResult:
    """Standard result format for MVP verification tests."""
    test_name: str
    status: str  # "PASS", "FAIL", "WARNING", "ERROR"
    execution_time: float
    details: Dict[str, Any]
    recommendations: List[str]
    timestamp: str
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class VerificationUtils:
    """Utility class for MVP verification operations."""
    
    # MVP target symbols from PRD
    MVP_SYMBOLS = ["CL.c.0", "SPY", "ES.c.0", "NG.c.0", "HO.c.0", "RB.c.0"]
    
    # Performance targets from NFRs
    QUERY_PERFORMANCE_TARGET = 5.0  # seconds
    INTEGRITY_TARGET = 0.01  # <1% failure rate
    STABILITY_TARGET = 0.95  # 95% operational stability
    MINIMUM_DATA_DAYS = 30  # minimum days of data required
    
    def __init__(self):
        self.logger = structlog.get_logger(self.__class__.__name__)
        self._engine: Optional[Engine] = None
    
    @property
    def engine(self) -> Engine:
        """Get or create database engine."""
        if self._engine is None:
            self._engine = self.create_db_engine()
        return self._engine
    
    def create_db_engine(self) -> Engine:
        """Create SQLAlchemy engine for TimescaleDB connection."""
        try:
            # Get database configuration from environment
            db_config = {
                'host': os.getenv('TIMESCALEDB_HOST', 'localhost'),
                'port': os.getenv('TIMESCALEDB_PORT', '5432'),
                'database': os.getenv('TIMESCALEDB_DB', 'hist_data_ingestor'),
                'user': os.getenv('TIMESCALEDB_USER', 'postgres'),
                'password': os.getenv('TIMESCALEDB_PASSWORD', 'password')
            }
            
            connection_string = (
                f"postgresql://{db_config['user']}:{db_config['password']}"
                f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
            )
            
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=False
            )
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.logger.info("Database connection established", **db_config)
            return engine
            
        except Exception as e:
            self.logger.error("Failed to create database engine", error=str(e))
            raise
    
    @contextmanager
    def get_db_connection(self):
        """Context manager for database connections."""
        connection = self.engine.connect()
        try:
            yield connection
        finally:
            connection.close()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute SQL query and return results as list of dictionaries."""
        try:
            with self.get_db_connection() as conn:
                result = conn.execute(text(query), params or {})
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result.fetchall()]
        except SQLAlchemyError as e:
            self.logger.error("Query execution failed", query=query, error=str(e))
            raise
    
    def measure_execution_time(self, func, *args, **kwargs) -> tuple[Any, float]:
        """Measure execution time of a function."""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            return result, execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(
                "Function execution failed", 
                function=func.__name__, 
                execution_time=execution_time,
                error=str(e)
            )
            raise
    
    def check_data_availability(self, symbols: List[str], days_back: int = 30) -> Dict[str, Any]:
        """Check if data is available for specified symbols in recent period."""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        query = """
        SELECT 
            security_symbol,
            data_source,
            COUNT(*) as record_count,
            MIN(event_timestamp) as earliest_date,
            MAX(event_timestamp) as latest_date,
            COUNT(DISTINCT DATE(event_timestamp)) as days_with_data
        FROM financial_time_series_data 
        WHERE security_symbol = ANY(:symbols)
            AND data_source = 'Databento'
            AND event_timestamp >= :cutoff_date
        GROUP BY security_symbol, data_source
        ORDER BY security_symbol;
        """
        
        try:
            results = self.execute_query(query, {
                'symbols': symbols,
                'cutoff_date': cutoff_date
            })
            
            availability_summary = {
                'symbols_found': len(results),
                'symbols_expected': len(symbols),
                'total_records': sum(r['record_count'] for r in results),
                'date_range_start': cutoff_date.isoformat(),
                'date_range_end': datetime.now().isoformat(),
                'details': results
            }
            
            return availability_summary
            
        except Exception as e:
            self.logger.error("Data availability check failed", error=str(e))
            raise
    
    def validate_performance_target(self, execution_time: float, target: float = None) -> bool:
        """Check if execution time meets performance target."""
        target = target or self.QUERY_PERFORMANCE_TARGET
        return execution_time <= target
    
    def calculate_success_rate(self, successful: int, total: int) -> float:
        """Calculate success rate as percentage."""
        if total == 0:
            return 0.0
        return successful / total
    
    def generate_recommendations(self, test_name: str, status: str, details: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on test results."""
        recommendations = []
        
        if test_name == "data_availability" and status == "FAIL":
            missing_symbols = details.get('missing_symbols', [])
            if missing_symbols:
                recommendations.append(f"Ingest missing symbols: {', '.join(missing_symbols)}")
            if details.get('insufficient_data_days', False):
                recommendations.append("Increase data retention period or ingest historical data")
        
        elif test_name == "performance_benchmark" and status == "FAIL":
            avg_time = details.get('average_execution_time', 0)
            if avg_time > self.QUERY_PERFORMANCE_TARGET:
                recommendations.append("Optimize database indexes for query performance")
                recommendations.append("Consider query result caching for frequently accessed data")
                recommendations.append("Review TimescaleDB hypertable partitioning strategy")
        
        elif test_name == "data_integrity" and status == "FAIL":
            failure_rate = details.get('failure_rate', 0)
            if failure_rate > self.INTEGRITY_TARGET:
                recommendations.append("Review data validation rules and thresholds")
                recommendations.append("Investigate common causes of quarantined records")
                recommendations.append("Consider data quality monitoring alerts")
        
        elif test_name == "operational_stability" and status == "FAIL":
            stability_rate = details.get('stability_rate', 0)
            if stability_rate < self.STABILITY_TARGET:
                recommendations.append("Investigate ingestion failures and implement robust error handling")
                recommendations.append("Set up automated monitoring and alerting for ingestion processes")
                recommendations.append("Review and improve retry logic for transient failures")
        
        return recommendations
    
    def save_results_to_file(self, results: List[MVPVerificationResult], filename: str = None) -> str:
        """Save verification results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mvp_verification_results_{timestamp}.json"
        
        filepath = os.path.join("logs", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        results_data = {
            'execution_timestamp': datetime.now(timezone.utc).isoformat(),
            'total_tests': len(results),
            'passed_tests': len([r for r in results if r.status == "PASS"]),
            'failed_tests': len([r for r in results if r.status == "FAIL"]),
            'warning_tests': len([r for r in results if r.status == "WARNING"]),
            'error_tests': len([r for r in results if r.status == "ERROR"]),
            'results': [r.to_dict() for r in results]
        }
        
        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        self.logger.info("Results saved to file", filepath=filepath)
        return filepath
    
    def create_executive_summary(self, results: List[MVPVerificationResult]) -> Dict[str, Any]:
        """Create executive summary of MVP verification results."""
        total_tests = len(results)
        passed_tests = len([r for r in results if r.status == "PASS"])
        failed_tests = len([r for r in results if r.status == "FAIL"])
        
        mvp_ready = failed_tests == 0
        
        summary = {
            'mvp_readiness': 'READY' if mvp_ready else 'NOT READY',
            'overall_score': f"{passed_tests}/{total_tests}",
            'pass_rate': f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            'critical_issues': [
                r.test_name for r in results if r.status == "FAIL"
            ],
            'recommendations': [
                rec for r in results for rec in r.recommendations
            ][:10],  # Top 10 recommendations
            'execution_summary': {
                'total_execution_time': sum(r.execution_time for r in results),
                'longest_test': max(results, key=lambda r: r.execution_time).test_name if results else None,
                'test_timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
        
        return summary 