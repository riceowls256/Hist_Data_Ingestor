#!/usr/bin/env python3
"""
Idempotency Testing Module for Story 2.7.

This module tests that running the same data ingestion job multiple times
does not create duplicate records in the database, ensuring proper idempotency
behavior through the DownloadProgressTracker and database constraints.
"""

import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)


@dataclass
class IdempotencyTestResult:
    """Result of an idempotency test run."""
    test_name: str
    run_number: int
    execution_time: float
    records_before: Dict[str, int]
    records_after: Dict[str, int]
    duplicates_found: Dict[str, int]
    pipeline_success: bool
    error_message: Optional[str] = None


class IdempotencyTester:
    """Tests idempotency behavior of the Databento pipeline."""
    
    def __init__(self, db_config: Dict[str, str]):
        """Initialize the idempotency tester."""
        self.db_config = db_config
        self.connection: Optional[psycopg2.connection] = None
        self.logger = logging.getLogger(__name__)
        
        # Tables to monitor for idempotency
        self.monitored_tables = [
            'daily_ohlcv_data',
            'trades_data', 
            'tbbo_data',
            'statistics_data',
            'definitions_data'
        ]
        
        # Unique constraint definitions for duplicate detection
        self.unique_constraints = {
            'daily_ohlcv_data': ['instrument_id', 'ts_event', 'granularity'],
            'trades_data': ['instrument_id', 'ts_event', 'price', 'size'],
            'tbbo_data': ['instrument_id', 'ts_event'],
            'statistics_data': ['instrument_id', 'ts_event', 'stat_type'],
            'definitions_data': ['instrument_id', 'ts_event']
        }
    
    def connect_database(self) -> bool:
        """Connect to the test database."""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.logger.info("Connected to test database")
            return True
        except psycopg2.Error as e:
            self.logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect_database(self) -> None:
        """Disconnect from the database."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_table_record_counts(self) -> Dict[str, int]:
        """Get current record counts for all monitored tables."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        counts = {}
        with self.connection.cursor() as cursor:
            for table in self.monitored_tables:
                cursor.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE data_source = 'databento'"
                )
                counts[table] = cursor.fetchone()[0]
        
        return counts
    
    def check_for_duplicates(self) -> Dict[str, int]:
        """Check for duplicate records in all monitored tables."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        duplicates = {}
        with self.connection.cursor() as cursor:
            for table, constraint_fields in self.unique_constraints.items():
                fields_str = ', '.join(constraint_fields)
                
                query = f"""
                SELECT COUNT(*) as duplicate_groups
                FROM (
                    SELECT {fields_str}
                    FROM {table}
                    WHERE data_source = 'databento'
                    GROUP BY {fields_str}
                    HAVING COUNT(*) > 1
                ) duplicates
                """
                
                cursor.execute(query)
                duplicates[table] = cursor.fetchone()[0]
        
        return duplicates
    
    def run_pipeline_job(self, job_name: str) -> Tuple[bool, float, Optional[str]]:
        """
        Run a pipeline job and measure execution time.
        
        Args:
            job_name: Name of the job configuration to run
            
        Returns:
            Tuple of (success, execution_time_seconds, error_message)
        """
        start_time = time.time()
        
        try:
            # Run the pipeline via CLI
            cmd = [
                sys.executable, "main.py", "ingest",
                "--api", "databento",
                "--job", job_name,
                "--verbose"
            ]
            
            self.logger.info(f"Executing pipeline command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent.parent.parent,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                self.logger.info(f"Pipeline execution successful in {execution_time:.2f}s")
                return True, execution_time, None
            else:
                error_msg = f"Pipeline failed with return code {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                self.logger.error(error_msg)
                return False, execution_time, error_msg
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            error_msg = f"Pipeline execution timed out after {execution_time:.2f}s"
            self.logger.error(error_msg)
            return False, execution_time, error_msg
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Pipeline execution failed with error: {e}"
            self.logger.error(error_msg)
            return False, execution_time, error_msg
    
    def run_idempotency_test(self, job_name: str, num_runs: int = 3) -> List[IdempotencyTestResult]:
        """
        Run idempotency test by executing the same job multiple times.
        
        Args:
            job_name: Name of the job to test
            num_runs: Number of times to run the job
            
        Returns:
            List of test results for each run
        """
        results = []
        
        for run_num in range(1, num_runs + 1):
            self.logger.info(f"Starting idempotency test run {run_num}/{num_runs}")
            
            # Get record counts before execution
            records_before = self.get_table_record_counts()
            
            # Run the pipeline
            success, exec_time, error_msg = self.run_pipeline_job(job_name)
            
            # Get record counts after execution
            records_after = self.get_table_record_counts()
            
            # Check for duplicates
            duplicates = self.check_for_duplicates()
            
            # Create test result
            result = IdempotencyTestResult(
                test_name=f"idempotency_{job_name}",
                run_number=run_num,
                execution_time=exec_time,
                records_before=records_before,
                records_after=records_after,
                duplicates_found=duplicates,
                pipeline_success=success,
                error_message=error_msg
            )
            
            results.append(result)
            
            # Log results for this run
            self.logger.info(f"Run {run_num} completed:")
            for table in self.monitored_tables:
                before = records_before.get(table, 0)
                after = records_after.get(table, 0)
                dups = duplicates.get(table, 0)
                self.logger.info(f"  {table}: {before} -> {after} records, {dups} duplicate groups")
            
            # Small delay between runs
            if run_num < num_runs:
                time.sleep(2)
        
        return results
    
    def analyze_idempotency_results(self, results: List[IdempotencyTestResult]) -> Dict[str, Any]:
        """
        Analyze idempotency test results and generate summary.
        
        Args:
            results: List of test results
            
        Returns:
            Analysis summary dictionary
        """
        if not results:
            return {"error": "No results to analyze"}
        
        analysis = {
            "total_runs": len(results),
            "successful_runs": sum(1 for r in results if r.pipeline_success),
            "failed_runs": sum(1 for r in results if not r.pipeline_success),
            "idempotency_passed": True,
            "idempotency_issues": [],
            "record_progression": {},
            "duplicate_analysis": {},
            "performance_metrics": {
                "avg_execution_time": sum(r.execution_time for r in results) / len(results),
                "min_execution_time": min(r.execution_time for r in results),
                "max_execution_time": max(r.execution_time for r in results)
            }
        }
        
        # Analyze record progression and idempotency
        for table in self.monitored_tables:
            table_analysis = {
                "record_counts": [],
                "total_duplicates": 0,
                "idempotent": True
            }
            
            for i, result in enumerate(results):
                after_count = result.records_after.get(table, 0)
                duplicate_count = result.duplicates_found.get(table, 0)
                
                table_analysis["record_counts"].append(after_count)
                table_analysis["total_duplicates"] += duplicate_count
                
                # Check idempotency: after first run, record counts shouldn't increase
                if i > 0 and after_count > results[0].records_after.get(table, 0):
                    table_analysis["idempotent"] = False
                    analysis["idempotency_passed"] = False
                    analysis["idempotency_issues"].append(
                        f"{table}: Record count increased from {results[0].records_after.get(table, 0)} "
                        f"to {after_count} on run {i + 1}"
                    )
                
                # Check for duplicates
                if duplicate_count > 0:
                    table_analysis["idempotent"] = False
                    analysis["idempotency_passed"] = False
                    analysis["idempotency_issues"].append(
                        f"{table}: {duplicate_count} duplicate groups found on run {i + 1}"
                    )
            
            analysis["record_progression"][table] = table_analysis
            analysis["duplicate_analysis"][table] = table_analysis["total_duplicates"]
        
        return analysis
    
    def generate_report(self, results: List[IdempotencyTestResult], analysis: Dict[str, Any]) -> str:
        """Generate a comprehensive idempotency test report."""
        report_lines = []
        
        # Header
        report_lines.append("=" * 80)
        report_lines.append("IDEMPOTENCY TEST REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().isoformat()}")
        report_lines.append(f"Test Job: {results[0].test_name if results else 'Unknown'}")
        report_lines.append("")
        
        # Executive Summary
        report_lines.append("EXECUTIVE SUMMARY:")
        report_lines.append("-" * 40)
        overall_status = "✅ PASSED" if analysis.get("idempotency_passed", False) else "❌ FAILED"
        report_lines.append(f"Idempotency Status: {overall_status}")
        report_lines.append(f"Total Runs: {analysis.get('total_runs', 0)}")
        report_lines.append(f"Successful Runs: {analysis.get('successful_runs', 0)}")
        report_lines.append(f"Failed Runs: {analysis.get('failed_runs', 0)}")
        report_lines.append("")
        
        # Performance Metrics
        perf = analysis.get("performance_metrics", {})
        report_lines.append("PERFORMANCE METRICS:")
        report_lines.append("-" * 40)
        report_lines.append(f"Average Execution Time: {perf.get('avg_execution_time', 0):.2f}s")
        report_lines.append(f"Min Execution Time: {perf.get('min_execution_time', 0):.2f}s")
        report_lines.append(f"Max Execution Time: {perf.get('max_execution_time', 0):.2f}s")
        report_lines.append("")
        
        # Record Progression Analysis
        report_lines.append("RECORD PROGRESSION ANALYSIS:")
        report_lines.append("-" * 40)
        for table, table_analysis in analysis.get("record_progression", {}).items():
            counts = table_analysis.get("record_counts", [])
            idempotent = table_analysis.get("idempotent", True)
            status = "✅ IDEMPOTENT" if idempotent else "❌ NOT IDEMPOTENT"
            
            report_lines.append(f"{table}: {status}")
            report_lines.append(f"  Record counts across runs: {counts}")
            
            if not idempotent:
                report_lines.append(f"  Total duplicates found: {table_analysis.get('total_duplicates', 0)}")
        
        report_lines.append("")
        
        # Issues Found
        issues = analysis.get("idempotency_issues", [])
        if issues:
            report_lines.append("ISSUES FOUND:")
            report_lines.append("-" * 40)
            for issue in issues:
                report_lines.append(f"❌ {issue}")
            report_lines.append("")
        
        # Detailed Run Results
        report_lines.append("DETAILED RUN RESULTS:")
        report_lines.append("-" * 40)
        for result in results:
            status = "✅ SUCCESS" if result.pipeline_success else "❌ FAILED"
            report_lines.append(f"Run {result.run_number}: {status} ({result.execution_time:.2f}s)")
            
            if not result.pipeline_success and result.error_message:
                report_lines.append(f"  Error: {result.error_message[:200]}...")
            
            for table in self.monitored_tables:
                before = result.records_before.get(table, 0)
                after = result.records_after.get(table, 0)
                dups = result.duplicates_found.get(table, 0)
                report_lines.append(f"  {table}: {before} -> {after} records, {dups} duplicates")
        
        return "\n".join(report_lines)


def main():
    """Main function for running idempotency tests."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("🔄 Idempotency Testing for Story 2.7")
    print("=" * 50)
    
    # Database configuration from environment
    db_config = {
        'host': os.getenv('TIMESCALEDB_TEST_HOST', 'localhost'),
        'port': int(os.getenv('TIMESCALEDB_TEST_PORT', '5432')),
        'database': os.getenv('TIMESCALEDB_TEST_DB', 'hist_data_test'),
        'user': os.getenv('TIMESCALEDB_TEST_USER', 'postgres'),
        'password': os.getenv('TIMESCALEDB_TEST_PASSWORD', 'password')
    }
    
    print(f"Database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    # Initialize tester
    tester = IdempotencyTester(db_config)
    
    if not tester.connect_database():
        print("❌ Failed to connect to database")
        return False
    
    try:
        # Test job configuration (using small dataset for faster testing)
        test_job = "idempotency_validation_test"  # Defined in databento_e2e_test_config.yaml
        
        print(f"Testing idempotency with job: {test_job}")
        print("Running pipeline 3 times to verify idempotency...")
        
        # Run the idempotency test
        results = tester.run_idempotency_test(test_job, num_runs=3)
        
        # Analyze results
        analysis = tester.analyze_idempotency_results(results)
        
        # Generate and display report
        report = tester.generate_report(results, analysis)
        print("\n" + report)
        
        # Save report to file
        report_file = Path("idempotency_test_report.txt")
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_file}")
        
        # Return success status
        return analysis.get("idempotency_passed", False)
        
    finally:
        tester.disconnect_database()


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Idempotency test PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Idempotency test FAILED!")
        sys.exit(1) 