"""
Data Integrity Rate Analysis (AC3)

This script analyzes ingestion logs and quarantine data to calculate the percentage
of records that failed validation vs. were stored successfully. Reports PASS if 
integrity rate meets <1% failure target (NFR 3).

Analyzes:
- Application logs for success/failure patterns
- Quarantine/DLQ files for failed records
- Database record counts for successful ingestion
"""

import time
import os
import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import structlog

from .verification_utils import VerificationUtils, MVPVerificationResult


class DataIntegrityAnalysis:
    """Analyze data integrity rates from logs and quarantine data."""
    
    def __init__(self):
        self.utils = VerificationUtils()
        self.logger = structlog.get_logger(self.__class__.__name__)
        
        # File paths for analysis
        self.log_directory = Path("logs")
        self.dlq_directory = Path("dlq")
        
        # Integrity thresholds
        self.max_failure_rate = 0.01  # <1% failure rate target
        
        # Log parsing patterns
        self.log_patterns = {
            'successful_ingestion': [
                r'Successfully stored (\d+) records',
                r'Ingestion completed.*(\d+) records processed',
                r'Batch ingestion successful.*(\d+) records'
            ],
            'failed_records': [
                r'Validation failed for (\d+) records',
                r'Quarantined (\d+) records',
                r'Failed to process (\d+) records'
            ],
            'error_patterns': [
                r'ERROR.*validation.*failed',
                r'ERROR.*ingestion.*failed',
                r'CRITICAL.*data.*integrity'
            ]
        }
    
    def run_test(self) -> MVPVerificationResult:
        """Execute the complete data integrity analysis."""
        self.logger.info("Starting data integrity analysis")
        
        start_time = time.time()
        
        try:
            # Perform integrity analysis
            log_analysis = self._analyze_application_logs()
            dlq_analysis = self._analyze_quarantine_data()
            database_validation = self._validate_database_integrity()
            trend_analysis = self._analyze_integrity_trends()
            
            # Aggregate results
            integrity_details = {
                'log_analysis': log_analysis,
                'dlq_analysis': dlq_analysis,
                'database_validation': database_validation,
                'trend_analysis': trend_analysis,
                'integrity_thresholds': {
                    'max_failure_rate': self.max_failure_rate,
                    'target_description': 'Less than 1% of records fail validation'
                }
            }
            
            # Calculate overall integrity rate
            overall_integrity = self._calculate_overall_integrity(integrity_details)
            integrity_details['overall_integrity'] = overall_integrity
            
            # Determine test status
            status = self._determine_test_status(integrity_details)
            recommendations = self.utils.generate_recommendations(
                'data_integrity', status, integrity_details
            )
            
            execution_time = time.time() - start_time
            
            result = MVPVerificationResult(
                test_name="data_integrity",
                status=status,
                execution_time=execution_time,
                details=integrity_details,
                recommendations=recommendations,
                timestamp=""
            )
            
            self.logger.info(
                "Data integrity analysis completed",
                status=status,
                execution_time=execution_time,
                failure_rate=overall_integrity.get('failure_rate', 0)
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error("Data integrity analysis failed", error=str(e))
            
            return MVPVerificationResult(
                test_name="data_integrity",
                status="ERROR",
                execution_time=execution_time,
                details={'error': str(e)},
                recommendations=['Fix log access permissions and retry analysis'],
                timestamp=""
            )
    
    def _analyze_application_logs(self) -> Dict[str, Any]:
        """Analyze application logs for ingestion success/failure patterns."""
        self.logger.info("Analyzing application logs")
        
        log_files = []
        if self.log_directory.exists():
            log_files = list(self.log_directory.glob("*.log"))
        
        if not log_files:
            self.logger.warning("No log files found", directory=str(self.log_directory))
            return {
                'files_analyzed': 0,
                'log_files': [],
                'total_successful_records': 0,
                'total_failed_records': 0,
                'parsing_errors': ['No log files found']
            }
        
        total_successful = 0
        total_failed = 0
        parsing_errors = []
        file_summaries = []
        
        for log_file in log_files:
            try:
                file_summary = self._parse_log_file(log_file)
                file_summaries.append(file_summary)
                total_successful += file_summary['successful_records']
                total_failed += file_summary['failed_records']
                
            except Exception as e:
                error_msg = f"Failed to parse {log_file.name}: {str(e)}"
                parsing_errors.append(error_msg)
                self.logger.warning("Log file parsing failed", file=str(log_file), error=str(e))
        
        return {
            'files_analyzed': len(file_summaries),
            'log_files': [f['filename'] for f in file_summaries],
            'file_summaries': file_summaries,
            'total_successful_records': total_successful,
            'total_failed_records': total_failed,
            'total_processed_records': total_successful + total_failed,
            'log_failure_rate': total_failed / (total_successful + total_failed) if (total_successful + total_failed) > 0 else 0,
            'parsing_errors': parsing_errors
        }
    
    def _parse_log_file(self, log_file: Path) -> Dict[str, Any]:
        """Parse a single log file for ingestion metrics."""
        successful_records = 0
        failed_records = 0
        error_entries = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Search for successful ingestion patterns
            for pattern in self.log_patterns['successful_ingestion']:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    try:
                        successful_records += int(match)
                    except ValueError:
                        continue
            
            # Search for failed record patterns
            for pattern in self.log_patterns['failed_records']:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    try:
                        failed_records += int(match)
                    except ValueError:
                        continue
            
            # Search for error patterns
            for pattern in self.log_patterns['error_patterns']:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                error_entries.extend(matches[:10])  # Limit to first 10 errors
            
            return {
                'filename': log_file.name,
                'file_size': log_file.stat().st_size,
                'modification_time': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat(),
                'successful_records': successful_records,
                'failed_records': failed_records,
                'error_count': len(error_entries),
                'sample_errors': error_entries
            }
            
        except Exception as e:
            self.logger.error("Failed to parse log file", file=str(log_file), error=str(e))
            raise
    
    def _analyze_quarantine_data(self) -> Dict[str, Any]:
        """Analyze quarantine/DLQ directory for failed records."""
        self.logger.info("Analyzing quarantine data")
        
        if not self.dlq_directory.exists():
            return {
                'dlq_directory_exists': False,
                'quarantined_files': 0,
                'quarantined_records': 0,
                'analysis': 'DLQ directory not found'
            }
        
        dlq_files = list(self.dlq_directory.glob("*"))
        quarantined_records = 0
        file_analysis = []
        
        for dlq_file in dlq_files:
            if dlq_file.is_file():
                try:
                    file_info = self._analyze_dlq_file(dlq_file)
                    file_analysis.append(file_info)
                    quarantined_records += file_info['record_count']
                    
                except Exception as e:
                    self.logger.warning("Failed to analyze DLQ file", file=str(dlq_file), error=str(e))
        
        return {
            'dlq_directory_exists': True,
            'quarantined_files': len(file_analysis),
            'quarantined_records': quarantined_records,
            'file_analysis': file_analysis,
            'recent_quarantine_activity': self._check_recent_quarantine_activity(file_analysis)
        }
    
    def _analyze_dlq_file(self, dlq_file: Path) -> Dict[str, Any]:
        """Analyze a single quarantine file."""
        file_stats = dlq_file.stat()
        record_count = 0
        
        try:
            if dlq_file.suffix.lower() == '.json':
                # JSON format - count array elements or lines
                with open(dlq_file, 'r') as f:
                    content = f.read().strip()
                    if content.startswith('['):
                        # JSON array
                        data = json.loads(content)
                        record_count = len(data) if isinstance(data, list) else 1
                    else:
                        # JSONL format
                        record_count = len(content.split('\n')) if content else 0
            
            elif dlq_file.suffix.lower() == '.csv':
                # CSV format - count lines minus header
                with open(dlq_file, 'r') as f:
                    lines = f.readlines()
                    record_count = max(0, len(lines) - 1)  # Subtract header
            
            else:
                # Generic text file - count non-empty lines
                with open(dlq_file, 'r') as f:
                    lines = f.readlines()
                    record_count = len([line for line in lines if line.strip()])
        
        except Exception as e:
            self.logger.warning("Failed to count records in DLQ file", file=str(dlq_file), error=str(e))
        
        return {
            'filename': dlq_file.name,
            'file_size': file_stats.st_size,
            'modification_time': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            'record_count': record_count,
            'file_extension': dlq_file.suffix.lower()
        }
    
    def _check_recent_quarantine_activity(self, file_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check for recent quarantine activity (last 7 days)."""
        recent_cutoff = datetime.now() - timedelta(days=7)
        
        recent_files = []
        recent_records = 0
        
        for file_info in file_analysis:
            mod_time = datetime.fromisoformat(file_info['modification_time'])
            if mod_time >= recent_cutoff:
                recent_files.append(file_info)
                recent_records += file_info['record_count']
        
        return {
            'recent_files_count': len(recent_files),
            'recent_quarantined_records': recent_records,
            'cutoff_date': recent_cutoff.isoformat(),
            'recent_files': recent_files
        }
    
    def _validate_database_integrity(self) -> Dict[str, Any]:
        """Validate data integrity at the database level."""
        self.logger.info("Validating database integrity")
        
        try:
            # Check for duplicate records
            duplicate_check = self._check_for_duplicates()
            
            # Check for data consistency
            consistency_check = self._check_data_consistency()
            
            # Check for invalid data patterns
            validation_check = self._check_data_validation()
            
            return {
                'duplicate_analysis': duplicate_check,
                'consistency_analysis': consistency_check,
                'validation_analysis': validation_check,
                'database_accessible': True
            }
            
        except Exception as e:
            self.logger.error("Database integrity validation failed", error=str(e))
            return {
                'database_accessible': False,
                'error': str(e)
            }
    
    def _check_for_duplicates(self) -> Dict[str, Any]:
        """Check for duplicate records in the database."""
        query = """
        SELECT 
            security_symbol,
            event_timestamp,
            COUNT(*) as duplicate_count
        FROM financial_time_series_data
        WHERE data_source = 'Databento'
            AND event_timestamp >= :cutoff_date
        GROUP BY security_symbol, event_timestamp
        HAVING COUNT(*) > 1
        LIMIT 100;
        """
        
        cutoff_date = datetime.now() - timedelta(days=30)
        
        try:
            results = self.utils.execute_query(query, {'cutoff_date': cutoff_date})
            
            total_duplicates = sum(r['duplicate_count'] - 1 for r in results)  # Subtract 1 to get extra copies
            
            return {
                'duplicate_groups_found': len(results),
                'total_duplicate_records': total_duplicates,
                'sample_duplicates': results[:10]
            }
            
        except Exception as e:
            self.logger.error("Duplicate check failed", error=str(e))
            raise
    
    def _check_data_consistency(self) -> Dict[str, Any]:
        """Check for data consistency issues."""
        # Check for records with invalid price/volume data
        consistency_query = """
        SELECT 
            security_symbol,
            COUNT(*) as total_records,
            COUNT(CASE WHEN open_price <= 0 THEN 1 END) as invalid_open_price,
            COUNT(CASE WHEN close_price <= 0 THEN 1 END) as invalid_close_price,
            COUNT(CASE WHEN volume < 0 THEN 1 END) as invalid_volume,
            COUNT(CASE WHEN high_price < low_price THEN 1 END) as invalid_high_low
        FROM financial_time_series_data
        WHERE data_source = 'Databento'
            AND event_timestamp >= :cutoff_date
            AND security_symbol = ANY(:symbols)
        GROUP BY security_symbol;
        """
        
        cutoff_date = datetime.now() - timedelta(days=30)
        
        try:
            results = self.utils.execute_query(consistency_query, {
                'cutoff_date': cutoff_date,
                'symbols': self.utils.MVP_SYMBOLS
            })
            
            total_records = sum(r['total_records'] for r in results)
            total_inconsistencies = sum(
                r['invalid_open_price'] + r['invalid_close_price'] + 
                r['invalid_volume'] + r['invalid_high_low']
                for r in results
            )
            
            return {
                'total_records_checked': total_records,
                'total_inconsistencies': total_inconsistencies,
                'inconsistency_rate': total_inconsistencies / total_records if total_records > 0 else 0,
                'symbol_analysis': results
            }
            
        except Exception as e:
            self.logger.error("Consistency check failed", error=str(e))
            raise
    
    def _check_data_validation(self) -> Dict[str, Any]:
        """Check for validation rule compliance."""
        # Check for missing required fields
        validation_query = """
        SELECT 
            security_symbol,
            COUNT(*) as total_records,
            COUNT(CASE WHEN event_timestamp IS NULL THEN 1 END) as missing_timestamp,
            COUNT(CASE WHEN security_symbol IS NULL OR security_symbol = '' THEN 1 END) as missing_symbol,
            COUNT(CASE WHEN data_source IS NULL OR data_source = '' THEN 1 END) as missing_source
        FROM financial_time_series_data
        WHERE event_timestamp >= :cutoff_date
            AND security_symbol = ANY(:symbols)
        GROUP BY security_symbol;
        """
        
        cutoff_date = datetime.now() - timedelta(days=30)
        
        try:
            results = self.utils.execute_query(validation_query, {
                'cutoff_date': cutoff_date,
                'symbols': self.utils.MVP_SYMBOLS
            })
            
            total_records = sum(r['total_records'] for r in results)
            total_validation_failures = sum(
                r['missing_timestamp'] + r['missing_symbol'] + r['missing_source']
                for r in results
            )
            
            return {
                'total_records_validated': total_records,
                'total_validation_failures': total_validation_failures,
                'validation_failure_rate': total_validation_failures / total_records if total_records > 0 else 0,
                'validation_details': results
            }
            
        except Exception as e:
            self.logger.error("Validation check failed", error=str(e))
            raise
    
    def _analyze_integrity_trends(self) -> Dict[str, Any]:
        """Analyze integrity trends over time."""
        self.logger.info("Analyzing integrity trends")
        
        # Query daily integrity metrics for the last 30 days
        trend_query = """
        SELECT 
            DATE(event_timestamp) as ingestion_date,
            COUNT(*) as total_records,
            security_symbol,
            COUNT(CASE WHEN open_price <= 0 OR close_price <= 0 THEN 1 END) as invalid_records
        FROM financial_time_series_data
        WHERE data_source = 'Databento'
            AND event_timestamp >= :cutoff_date
            AND security_symbol = ANY(:symbols)
        GROUP BY DATE(event_timestamp), security_symbol
        ORDER BY ingestion_date DESC, security_symbol;
        """
        
        cutoff_date = datetime.now() - timedelta(days=30)
        
        try:
            results = self.utils.execute_query(trend_query, {
                'cutoff_date': cutoff_date,
                'symbols': self.utils.MVP_SYMBOLS
            })
            
            # Aggregate by date
            daily_metrics = {}
            for record in results:
                date = record['ingestion_date']
                if date not in daily_metrics:
                    daily_metrics[date] = {'total_records': 0, 'invalid_records': 0}
                
                daily_metrics[date]['total_records'] += record['total_records']
                daily_metrics[date]['invalid_records'] += record['invalid_records']
            
            # Calculate daily failure rates
            daily_failure_rates = []
            for date, metrics in daily_metrics.items():
                failure_rate = metrics['invalid_records'] / metrics['total_records'] if metrics['total_records'] > 0 else 0
                daily_failure_rates.append({
                    'date': date.isoformat() if hasattr(date, 'isoformat') else str(date),
                    'total_records': metrics['total_records'],
                    'invalid_records': metrics['invalid_records'],
                    'failure_rate': failure_rate
                })
            
            # Calculate trend statistics
            failure_rates = [d['failure_rate'] for d in daily_failure_rates]
            avg_failure_rate = sum(failure_rates) / len(failure_rates) if failure_rates else 0
            
            return {
                'analysis_period_days': 30,
                'days_with_data': len(daily_failure_rates),
                'daily_failure_rates': daily_failure_rates,
                'average_daily_failure_rate': avg_failure_rate,
                'max_daily_failure_rate': max(failure_rates) if failure_rates else 0,
                'trend_improving': len(failure_rates) > 1 and failure_rates[-1] < failure_rates[0]
            }
            
        except Exception as e:
            self.logger.error("Trend analysis failed", error=str(e))
            return {'error': str(e)}
    
    def _calculate_overall_integrity(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall integrity metrics."""
        log_analysis = details['log_analysis']
        dlq_analysis = details['dlq_analysis']
        database_validation = details['database_validation']
        
        # Primary calculation from logs
        total_processed = log_analysis['total_processed_records']
        total_failed = log_analysis['total_failed_records'] + dlq_analysis['quarantined_records']
        log_failure_rate = log_analysis['log_failure_rate']
        
        # Database consistency issues
        db_inconsistencies = 0
        if database_validation.get('consistency_analysis'):
            db_inconsistencies = database_validation['consistency_analysis']['total_inconsistencies']
        
        # Calculate comprehensive failure rate
        total_failures = total_failed + db_inconsistencies
        comprehensive_failure_rate = total_failures / total_processed if total_processed > 0 else 0
        
        # Determine pass/fail status
        meets_target = comprehensive_failure_rate <= self.max_failure_rate
        
        return {
            'total_processed_records': total_processed,
            'total_failed_records': total_failures,
            'failure_rate': comprehensive_failure_rate,
            'failure_percentage': comprehensive_failure_rate * 100,
            'target_failure_rate': self.max_failure_rate,
            'target_failure_percentage': self.max_failure_rate * 100,
            'meets_target': meets_target,
            'failure_breakdown': {
                'log_failures': log_analysis['total_failed_records'],
                'quarantined_records': dlq_analysis['quarantined_records'],
                'database_inconsistencies': db_inconsistencies
            }
        }
    
    def _determine_test_status(self, details: Dict[str, Any]) -> str:
        """Determine overall test status based on integrity analysis."""
        overall_integrity = details['overall_integrity']
        
        # Critical failure - cannot access data sources
        if not details['log_analysis']['files_analyzed'] and not details['dlq_analysis']['dlq_directory_exists']:
            return "FAIL"
        
        # Primary success criteria - meets failure rate target
        if overall_integrity['meets_target']:
            return "PASS"
        
        # Warning - close to target or minor issues
        if overall_integrity['failure_rate'] <= self.max_failure_rate * 1.5:  # Within 50% of target
            return "WARNING"
        
        # Failure - exceeds target significantly
        return "FAIL"
    
    def generate_detailed_report(self, result: MVPVerificationResult) -> str:
        """Generate a detailed text report of the data integrity analysis."""
        details = result.details
        
        report = []
        report.append("=== MVP DATA INTEGRITY VERIFICATION REPORT ===")
        report.append(f"Test Status: {result.status}")
        report.append(f"Execution Time: {result.execution_time:.2f} seconds")
        report.append(f"Timestamp: {result.timestamp}")
        report.append("")
        
        # Overall integrity summary
        overall = details['overall_integrity']
        report.append("INTEGRITY SUMMARY:")
        report.append(f"  Target: <{overall['target_failure_percentage']:.1f}% failure rate")
        report.append(f"  Actual: {overall['failure_percentage']:.2f}% failure rate")
        report.append(f"  Status: {'PASS' if overall['meets_target'] else 'FAIL'}")
        report.append(f"  Total Records Processed: {overall['total_processed_records']:,}")
        report.append(f"  Total Failed Records: {overall['total_failed_records']:,}")
        report.append("")
        
        # Failure breakdown
        breakdown = overall['failure_breakdown']
        report.append("FAILURE BREAKDOWN:")
        report.append(f"  Log Failures: {breakdown['log_failures']:,}")
        report.append(f"  Quarantined Records: {breakdown['quarantined_records']:,}")
        report.append(f"  Database Inconsistencies: {breakdown['database_inconsistencies']:,}")
        report.append("")
        
        # Log analysis summary
        log_analysis = details['log_analysis']
        report.append("LOG ANALYSIS:")
        report.append(f"  Files Analyzed: {log_analysis['files_analyzed']}")
        report.append(f"  Successful Records: {log_analysis['total_successful_records']:,}")
        report.append(f"  Failed Records: {log_analysis['total_failed_records']:,}")
        report.append("")
        
        # DLQ analysis summary
        dlq_analysis = details['dlq_analysis']
        report.append("QUARANTINE ANALYSIS:")
        report.append(f"  DLQ Directory Exists: {dlq_analysis['dlq_directory_exists']}")
        report.append(f"  Quarantined Files: {dlq_analysis['quarantined_files']}")
        report.append(f"  Quarantined Records: {dlq_analysis['quarantined_records']:,}")
        report.append("")
        
        # Recommendations
        if result.recommendations:
            report.append("RECOMMENDATIONS:")
            for rec in result.recommendations:
                report.append(f"  - {rec}")
        
        return "\n".join(report) 