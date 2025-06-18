"""
Performance Benchmark Test (AC2)

This test uses the CLI query command for benchmark queries and measures response time
to validate the <5 second performance target (NFR 4.2) for querying 1 month daily data.

Performance Target: 80% of queries must meet <5 second target
"""

import time
import subprocess
import statistics
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import structlog
import json
import os

from .verification_utils import VerificationUtils, MVPVerificationResult


class PerformanceBenchmarkTest:
    """Test query performance against NFR targets using CLI commands."""
    
    def __init__(self):
        self.utils = VerificationUtils()
        self.logger = structlog.get_logger(self.__class__.__name__)
        
        # Performance testing configuration
        self.performance_target = 5.0  # seconds
        self.success_threshold = 0.8   # 80% of queries must meet target
        self.test_iterations = 10      # number of test runs per scenario
        
        # Test scenarios
        self.test_scenarios = [
            {
                'name': 'single_symbol_month',
                'description': '1 month daily data for single symbol',
                'symbols': ['ES.c.0'],
                'days_back': 30,
                'schema': 'ohlcv-1d'
            },
            {
                'name': 'multiple_symbols_month', 
                'description': '1 month daily data for 3 symbols',
                'symbols': ['ES.c.0', 'CL.c.0', 'NG.c.0'],
                'days_back': 30,
                'schema': 'ohlcv-1d'
            },
            {
                'name': 'single_symbol_quarter',
                'description': '3 months daily data for single symbol',
                'symbols': ['ES.c.0'],
                'days_back': 90,
                'schema': 'ohlcv-1d'
            },
            {
                'name': 'all_mvp_symbols_month',
                'description': '1 month daily data for all MVP symbols',
                'symbols': self.utils.MVP_SYMBOLS,
                'days_back': 30,
                'schema': 'ohlcv-1d'
            }
        ]
    
    def run_test(self) -> MVPVerificationResult:
        """Execute the complete performance benchmark test."""
        self.logger.info("Starting performance benchmark test")
        
        start_time = time.time()
        
        try:
            # Run all performance scenarios
            scenario_results = []
            
            for scenario in self.test_scenarios:
                self.logger.info(f"Running scenario: {scenario['name']}")
                scenario_result = self._run_scenario(scenario)
                scenario_results.append(scenario_result)
            
            # Aggregate and analyze results
            performance_analysis = self._analyze_performance_results(scenario_results)
            
            # Determine overall test status
            status = self._determine_test_status(performance_analysis)
            recommendations = self.utils.generate_recommendations(
                'performance_benchmark', status, performance_analysis
            )
            
            execution_time = time.time() - start_time
            
            result = MVPVerificationResult(
                test_name="performance_benchmark",
                status=status,
                execution_time=execution_time,
                details=performance_analysis,
                recommendations=recommendations,
                timestamp=""
            )
            
            self.logger.info(
                "Performance benchmark test completed",
                status=status,
                execution_time=execution_time
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error("Performance benchmark test failed", error=str(e))
            
            return MVPVerificationResult(
                test_name="performance_benchmark",
                status="ERROR",
                execution_time=execution_time,
                details={'error': str(e)},
                recommendations=['Fix CLI connectivity and retry test'],
                timestamp=""
            )
    
    def _run_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single performance test scenario multiple times."""
        scenario_name = scenario['name']
        symbols = scenario['symbols']
        days_back = scenario['days_back']
        schema = scenario['schema']
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        execution_times = []
        results = []
        errors = []
        
        for iteration in range(self.test_iterations):
            self.logger.debug(
                f"Running iteration {iteration + 1}/{self.test_iterations}",
                scenario=scenario_name
            )
            
            try:
                execution_time, query_result = self._execute_cli_query(
                    symbols=symbols,
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    schema=schema
                )
                
                execution_times.append(execution_time)
                results.append({
                    'iteration': iteration + 1,
                    'execution_time': execution_time,
                    'success': True,
                    'record_count': self._extract_record_count(query_result),
                    'error': None
                })
                
            except Exception as e:
                error_msg = str(e)
                errors.append(error_msg)
                results.append({
                    'iteration': iteration + 1,
                    'execution_time': None,
                    'success': False,
                    'record_count': 0,
                    'error': error_msg
                })
                
                self.logger.warning(
                    f"Query failed in iteration {iteration + 1}",
                    scenario=scenario_name,
                    error=error_msg
                )
        
        # Calculate statistics
        successful_times = [t for t in execution_times if t is not None]
        
        scenario_result = {
            'scenario': scenario,
            'total_iterations': self.test_iterations,
            'successful_iterations': len(successful_times),
            'failed_iterations': len(errors),
            'execution_times': execution_times,
            'results': results,
            'errors': errors,
            'statistics': self._calculate_timing_statistics(successful_times) if successful_times else None
        }
        
        return scenario_result
    
    def _execute_cli_query(self, symbols: List[str], start_date: str, end_date: str, schema: str) -> Tuple[float, Dict]:
        """Execute a CLI query command and measure execution time."""
        # Construct CLI command
        symbols_str = ','.join(symbols)
        
        cmd = [
            'python', 'main.py', 'query',
            '--symbols', symbols_str,
            '--start-date', start_date,
            '--end-date', end_date,
            '--schema', schema,
            '--output-format', 'json'
        ]
        
        # Execute command and measure time
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode != 0:
                raise RuntimeError(f"CLI command failed: {result.stderr}")
            
            # Parse JSON output if possible
            try:
                output_data = json.loads(result.stdout) if result.stdout.strip() else {}
            except json.JSONDecodeError:
                # If not JSON, create simple result
                output_data = {
                    'stdout': result.stdout,
                    'record_count': result.stdout.count('\n') if result.stdout else 0
                }
            
            return execution_time, output_data
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            raise RuntimeError(f"Query timed out after 30 seconds (execution_time: {execution_time:.2f}s)")
        except Exception as e:
            execution_time = time.time() - start_time
            raise RuntimeError(f"Query execution failed: {str(e)} (execution_time: {execution_time:.2f}s)")
    
    def _extract_record_count(self, query_result: Dict[str, Any]) -> int:
        """Extract record count from query result."""
        if isinstance(query_result, dict):
            # Try various ways to get record count
            if 'record_count' in query_result:
                return query_result['record_count']
            elif 'data' in query_result and isinstance(query_result['data'], list):
                return len(query_result['data'])
            elif 'results' in query_result and isinstance(query_result['results'], list):
                return len(query_result['results'])
            else:
                return query_result.get('record_count', 0)
        return 0
    
    def _calculate_timing_statistics(self, execution_times: List[float]) -> Dict[str, float]:
        """Calculate timing statistics for execution times."""
        if not execution_times:
            return {}
        
        return {
            'count': len(execution_times),
            'mean': statistics.mean(execution_times),
            'median': statistics.median(execution_times),
            'min': min(execution_times),
            'max': max(execution_times),
            'std_dev': statistics.stdev(execution_times) if len(execution_times) > 1 else 0.0,
            'percentile_95': statistics.quantiles(execution_times, n=20)[18] if len(execution_times) >= 20 else max(execution_times),
            'under_target_count': sum(1 for t in execution_times if t <= self.performance_target),
            'under_target_percentage': (sum(1 for t in execution_times if t <= self.performance_target) / len(execution_times)) * 100
        }
    
    def _analyze_performance_results(self, scenario_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance results across all scenarios."""
        all_execution_times = []
        scenario_summaries = []
        
        for scenario_result in scenario_results:
            stats = scenario_result.get('statistics')
            if stats:
                all_execution_times.extend([
                    t for t in scenario_result['execution_times'] 
                    if t is not None
                ])
                
                scenario_summaries.append({
                    'scenario_name': scenario_result['scenario']['name'],
                    'description': scenario_result['scenario']['description'],
                    'successful_iterations': scenario_result['successful_iterations'],
                    'total_iterations': scenario_result['total_iterations'],
                    'success_rate': (scenario_result['successful_iterations'] / scenario_result['total_iterations']) * 100,
                    'mean_execution_time': stats['mean'],
                    'under_target_percentage': stats['under_target_percentage'],
                    'meets_target': stats['under_target_percentage'] >= (self.success_threshold * 100)
                })
        
        # Overall statistics
        overall_stats = self._calculate_timing_statistics(all_execution_times) if all_execution_times else {}
        
        # Determine overall success
        scenarios_meeting_target = sum(1 for s in scenario_summaries if s['meets_target'])
        overall_success = scenarios_meeting_target == len(scenario_summaries)
        
        analysis = {
            'performance_target': self.performance_target,
            'success_threshold': self.success_threshold,
            'total_scenarios': len(scenario_summaries),
            'scenarios_meeting_target': scenarios_meeting_target,
            'overall_success': overall_success,
            'scenario_summaries': scenario_summaries,
            'scenario_details': scenario_results,
            'overall_statistics': overall_stats,
            'total_queries_executed': len(all_execution_times),
            'overall_success_rate': (sum(s['successful_iterations'] for s in scenario_results) / 
                                   sum(s['total_iterations'] for s in scenario_results)) * 100 if scenario_results else 0
        }
        
        return analysis
    
    def _determine_test_status(self, analysis: Dict[str, Any]) -> str:
        """Determine overall test status based on performance analysis."""
        # Critical failure - no successful queries
        if analysis['total_queries_executed'] == 0:
            return "FAIL"
        
        # Critical failure - overall success rate too low
        if analysis['overall_success_rate'] < 70:
            return "FAIL"
        
        # Primary success criteria - all scenarios meet target
        if analysis['overall_success']:
            return "PASS"
        
        # Warning - some scenarios meet target
        if analysis['scenarios_meeting_target'] > 0:
            return "WARNING"
        
        # Failure - no scenarios meet target  
        return "FAIL"
    
    def generate_detailed_report(self, result: MVPVerificationResult) -> str:
        """Generate a detailed text report of the performance benchmark test."""
        analysis = result.details
        
        report = []
        report.append("=== MVP PERFORMANCE BENCHMARK VERIFICATION REPORT ===")
        report.append(f"Test Status: {result.status}")
        report.append(f"Execution Time: {result.execution_time:.2f} seconds")
        report.append(f"Timestamp: {result.timestamp}")
        report.append("")
        
        # Overall summary
        report.append("PERFORMANCE SUMMARY:")
        report.append(f"  Target: {analysis['performance_target']} seconds")
        report.append(f"  Success Threshold: {analysis['success_threshold'] * 100:.0f}% of queries")
        report.append(f"  Total Queries: {analysis['total_queries_executed']}")
        report.append(f"  Overall Success Rate: {analysis['overall_success_rate']:.1f}%")
        report.append(f"  Scenarios Meeting Target: {analysis['scenarios_meeting_target']}/{analysis['total_scenarios']}")
        report.append("")
        
        # Scenario details
        report.append("SCENARIO RESULTS:")
        for scenario in analysis['scenario_summaries']:
            status_icon = "✓" if scenario['meets_target'] else "✗"
            report.append(f"  {status_icon} {scenario['scenario_name']}: {scenario['description']}")
            report.append(f"    Success Rate: {scenario['success_rate']:.1f}%")
            report.append(f"    Mean Time: {scenario['mean_execution_time']:.2f}s")
            report.append(f"    Under Target: {scenario['under_target_percentage']:.1f}%")
            report.append("")
        
        # Overall statistics
        if analysis['overall_statistics']:
            stats = analysis['overall_statistics']
            report.append("OVERALL TIMING STATISTICS:")
            report.append(f"  Mean: {stats['mean']:.2f}s")
            report.append(f"  Median: {stats['median']:.2f}s")
            report.append(f"  Min: {stats['min']:.2f}s")
            report.append(f"  Max: {stats['max']:.2f}s")
            report.append(f"  95th Percentile: {stats['percentile_95']:.2f}s")
            report.append(f"  Under Target: {stats['under_target_percentage']:.1f}%")
            report.append("")
        
        # Recommendations
        if result.recommendations:
            report.append("RECOMMENDATIONS:")
            for rec in result.recommendations:
                report.append(f"  - {rec}")
        
        return "\n".join(report) 