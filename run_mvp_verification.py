#!/usr/bin/env python3
"""
MVP Verification Test Runner

Simple CLI script to execute MVP verification tests and generate reports.

Usage:
    python run_mvp_verification.py [--test TEST_NAME] [--report-only] [--verbose]

Examples:
    python run_mvp_verification.py                    # Run all tests
    python run_mvp_verification.py --test data_availability  # Run specific test
    python run_mvp_verification.py --report-only      # Generate report from last results
    python run_mvp_verification.py --verbose          # Detailed output
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from tests.integration.mvp_verification.master_verification_runner import MasterVerificationRunner
    from tests.integration.mvp_verification.data_availability_test import DataAvailabilityTest
    from tests.integration.mvp_verification.performance_benchmark_test import PerformanceBenchmarkTest
    from tests.integration.mvp_verification.data_integrity_analysis import DataIntegrityAnalysis
    from tests.integration.mvp_verification.operational_stability_test import OperationalStabilityTest
except ImportError as e:
    print(f"Error importing MVP verification modules: {e}")
    print("Make sure you're running this from the project root directory.")
    sys.exit(1)


def run_single_test(test_name: str, verbose: bool = False):
    """Run a single verification test."""
    test_classes = {
        'data_availability': DataAvailabilityTest,
        'performance_benchmark': PerformanceBenchmarkTest,
        'data_integrity': DataIntegrityAnalysis,
        'operational_stability': OperationalStabilityTest
    }
    
    if test_name not in test_classes:
        print(f"Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_classes.keys())}")
        return False
    
    print(f"Running {test_name} test...")
    
    try:
        test_instance = test_classes[test_name]()
        result = test_instance.run_test()
        
        print(f"\nTest Results:")
        print(f"  Status: {result.status}")
        print(f"  Execution Time: {result.execution_time:.2f} seconds")
        
        if verbose and hasattr(test_instance, 'generate_detailed_report'):
            print(f"\nDetailed Report:")
            print(test_instance.generate_detailed_report(result))
        
        if result.recommendations:
            print(f"\nRecommendations:")
            for rec in result.recommendations:
                print(f"  • {rec}")
        
        return result.status in ["PASS", "WARNING"]
        
    except Exception as e:
        print(f"Error running {test_name} test: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def run_all_tests(verbose: bool = False):
    """Run all MVP verification tests."""
    print("Starting comprehensive MVP verification test suite...")
    print("=" * 60)
    
    try:
        runner = MasterVerificationRunner()
        results = runner.run_all_tests(save_results=True)
        
        # Display executive summary
        executive_report = runner.generate_executive_report(results)
        print(executive_report)
        
        # Show individual test results if verbose
        if verbose:
            print("\n" + "=" * 60)
            print("DETAILED TEST RESULTS")
            print("=" * 60)
            
            for test_result in results['individual_test_results']:
                print(f"\n{test_result['test_name'].upper()} TEST:")
                print(f"  Status: {test_result['status']}")
                print(f"  Execution Time: {test_result['execution_time']:.2f}s")
                
                if test_result['recommendations']:
                    print("  Recommendations:")
                    for rec in test_result['recommendations'][:3]:
                        print(f"    • {rec}")
        
        # Return overall success
        mvp_ready = results['mvp_verification_summary']['mvp_ready']
        print(f"\n{'✅' if mvp_ready else '❌'} MVP Ready: {mvp_ready}")
        
        return mvp_ready
        
    except Exception as e:
        print(f"Error running test suite: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def generate_report_from_last_results(verbose: bool = False):
    """Generate report from the most recent test results."""
    logs_dir = Path("logs")
    
    if not logs_dir.exists():
        print("No logs directory found. Run tests first.")
        return False
    
    # Find most recent results file
    result_files = list(logs_dir.glob("mvp_*verification_*.json"))
    
    if not result_files:
        print("No previous test results found. Run tests first.")
        return False
    
    latest_file = max(result_files, key=lambda f: f.stat().st_mtime)
    
    try:
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        print(f"Loading results from: {latest_file.name}")
        print("=" * 60)
        
        # Display summary
        if 'results' in data:
            # Individual results file format
            total_tests = data['total_tests']
            passed_tests = data['passed_tests']
            failed_tests = data['failed_tests']
            
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {failed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            if verbose:
                print("\nTest Details:")
                for result in data['results']:
                    print(f"  {result['test_name']}: {result['status']}")
        
        else:
            # Comprehensive results file format
            summary = data.get('executive_summary', {})
            print(f"MVP Readiness: {summary.get('mvp_readiness', 'UNKNOWN')}")
            print(f"Overall Score: {summary.get('overall_score', 'N/A')}")
            
            if verbose and 'comprehensive_analysis' in data:
                analysis = data['comprehensive_analysis']
                if 'critical_issues' in analysis:
                    print("\nCritical Issues:")
                    for issue in analysis['critical_issues']:
                        print(f"  • {issue['description']}")
        
        return True
        
    except Exception as e:
        print(f"Error reading results file: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run MVP verification tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--test',
        choices=['data_availability', 'performance_benchmark', 'data_integrity', 'operational_stability'],
        help='Run specific test only'
    )
    
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Generate report from last test results without running tests'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output and reports'
    )
    
    args = parser.parse_args()
    
    # Ensure we're in the right directory
    if not Path('main.py').exists():
        print("Error: This script must be run from the project root directory.")
        print("Current directory should contain main.py file.")
        sys.exit(1)
    
    # Handle different modes
    success = False
    
    if args.report_only:
        success = generate_report_from_last_results(args.verbose)
    
    elif args.test:
        success = run_single_test(args.test, args.verbose)
    
    else:
        success = run_all_tests(args.verbose)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 