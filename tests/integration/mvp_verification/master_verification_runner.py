"""
Master Verification Runner (AC5)

This script orchestrates the execution of all MVP verification tests and generates
comprehensive results, executive summaries, and recommendations for MVP readiness.

Runs all verification tests:
1. Data Availability Test (AC1)
2. Performance Benchmark Test (AC2) 
3. Data Integrity Analysis (AC3)
4. Operational Stability Test (AC4)
"""

import time
import json
from typing import Dict, Any, List
from datetime import datetime
import structlog

from .verification_utils import VerificationUtils, MVPVerificationResult
from .data_availability_test import DataAvailabilityTest
from .performance_benchmark_test import PerformanceBenchmarkTest
from .data_integrity_analysis import DataIntegrityAnalysis
from .operational_stability_test import OperationalStabilityTest


class MasterVerificationRunner:
    """Master orchestrator for all MVP verification tests."""
    
    def __init__(self):
        self.utils = VerificationUtils()
        self.logger = structlog.get_logger(self.__class__.__name__)
        
        # Initialize test modules
        self.tests = {
            'data_availability': DataAvailabilityTest(),
            'performance_benchmark': PerformanceBenchmarkTest(),
            'data_integrity': DataIntegrityAnalysis(),
            'operational_stability': OperationalStabilityTest()
        }
    
    def run_all_tests(self, save_results: bool = True) -> Dict[str, Any]:
        """Run all MVP verification tests and generate comprehensive report."""
        self.logger.info("Starting comprehensive MVP verification test suite")
        
        start_time = time.time()
        test_results = []
        
        try:
            # Execute each test
            for test_name, test_instance in self.tests.items():
                self.logger.info(f"Executing {test_name} test")
                
                try:
                    result = test_instance.run_test()
                    test_results.append(result)
                    
                    self.logger.info(
                        f"Test {test_name} completed",
                        status=result.status,
                        execution_time=result.execution_time
                    )
                    
                except Exception as e:
                    self.logger.error(f"Test {test_name} failed", error=str(e))
                    
                    # Create error result
                    error_result = MVPVerificationResult(
                        test_name=test_name,
                        status="ERROR",
                        execution_time=0.0,
                        details={'error': str(e)},
                        recommendations=[f"Fix {test_name} test execution and retry"],
                        timestamp=""
                    )
                    test_results.append(error_result)
            
            # Generate comprehensive analysis
            comprehensive_analysis = self._generate_comprehensive_analysis(test_results)
            
            # Create executive summary
            executive_summary = self.utils.create_executive_summary(test_results)
            
            # Combine all results
            final_results = {
                'mvp_verification_summary': {
                    'execution_timestamp': datetime.now().isoformat(),
                    'total_execution_time': time.time() - start_time,
                    'mvp_ready': executive_summary['mvp_readiness'] == 'READY',
                    'overall_status': executive_summary['mvp_readiness']
                },
                'executive_summary': executive_summary,
                'comprehensive_analysis': comprehensive_analysis,
                'individual_test_results': [result.to_dict() for result in test_results],
                'test_execution_order': list(self.tests.keys())
            }
            
            # Save results if requested
            if save_results:
                self._save_comprehensive_results(final_results)
            
            self.logger.info(
                "MVP verification suite completed",
                mvp_ready=final_results['mvp_verification_summary']['mvp_ready'],
                total_time=final_results['mvp_verification_summary']['total_execution_time'],
                tests_passed=executive_summary['overall_score']
            )
            
            return final_results
            
        except Exception as e:
            self.logger.error("MVP verification suite failed", error=str(e))
            
            return {
                'mvp_verification_summary': {
                    'execution_timestamp': datetime.now().isoformat(),
                    'total_execution_time': time.time() - start_time,
                    'mvp_ready': False,
                    'overall_status': 'ERROR'
                },
                'error': str(e),
                'partial_results': [result.to_dict() for result in test_results]
            }
    
    def _generate_comprehensive_analysis(self, test_results: List[MVPVerificationResult]) -> Dict[str, Any]:
        """Generate comprehensive analysis across all test results."""
        
        # Aggregate results by status
        status_counts = {}
        for result in test_results:
            status = result.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Analyze performance metrics
        performance_metrics = self._analyze_performance_metrics(test_results)
        
        # Identify critical issues
        critical_issues = self._identify_critical_issues(test_results)
        
        # Generate cross-test insights
        cross_test_insights = self._generate_cross_test_insights(test_results)
        
        # Calculate MVP readiness score
        mvp_score = self._calculate_mvp_readiness_score(test_results)
        
        return {
            'status_summary': status_counts,
            'performance_metrics': performance_metrics,
            'critical_issues': critical_issues,
            'cross_test_insights': cross_test_insights,
            'mvp_readiness_score': mvp_score,
            'nfr_compliance': self._check_nfr_compliance(test_results),
            'recommended_actions': self._generate_recommended_actions(test_results)
        }
    
    def _analyze_performance_metrics(self, test_results: List[MVPVerificationResult]) -> Dict[str, Any]:
        """Analyze performance metrics across all tests."""
        
        total_execution_time = sum(result.execution_time for result in test_results)
        
        # Find performance-related results
        performance_test = next(
            (result for result in test_results if result.test_name == 'performance_benchmark'),
            None
        )
        
        performance_analysis = {
            'total_test_execution_time': total_execution_time,
            'individual_test_times': {
                result.test_name: result.execution_time for result in test_results
            }
        }
        
        if performance_test and performance_test.status != "ERROR":
            details = performance_test.details
            performance_analysis.update({
                'query_performance_summary': {
                    'target_met': details.get('overall_success', False),
                    'scenarios_passing': details.get('scenarios_meeting_target', 0),
                    'total_scenarios': details.get('total_scenarios', 0),
                    'overall_success_rate': details.get('overall_success_rate', 0)
                }
            })
        
        return performance_analysis
    
    def _identify_critical_issues(self, test_results: List[MVPVerificationResult]) -> List[Dict[str, Any]]:
        """Identify critical issues that prevent MVP readiness."""
        
        critical_issues = []
        
        for result in test_results:
            if result.status == "FAIL":
                critical_issues.append({
                    'test_name': result.test_name,
                    'issue_type': 'FAILED_TEST',
                    'description': f'{result.test_name} test failed critical requirements',
                    'recommendations': result.recommendations[:3]  # Top 3 recommendations
                })
            
            elif result.status == "ERROR":
                critical_issues.append({
                    'test_name': result.test_name,
                    'issue_type': 'TEST_EXECUTION_ERROR',
                    'description': f'{result.test_name} test could not be executed',
                    'error_details': result.details.get('error', 'Unknown error'),
                    'recommendations': result.recommendations
                })
        
        return critical_issues
    
    def _generate_cross_test_insights(self, test_results: List[MVPVerificationResult]) -> Dict[str, Any]:
        """Generate insights by analyzing results across multiple tests."""
        
        insights = {
            'data_pipeline_health': 'UNKNOWN',
            'system_readiness': 'UNKNOWN',
            'data_quality_status': 'UNKNOWN'
        }
        
        # Get test results by name
        results_dict = {result.test_name: result for result in test_results}
        
        # Analyze data pipeline health
        data_avail = results_dict.get('data_availability')
        data_integrity = results_dict.get('data_integrity')
        
        if data_avail and data_integrity:
            if data_avail.status == "PASS" and data_integrity.status == "PASS":
                insights['data_pipeline_health'] = 'HEALTHY'
            elif data_avail.status in ["PASS", "WARNING"] and data_integrity.status in ["PASS", "WARNING"]:
                insights['data_pipeline_health'] = 'FUNCTIONAL_WITH_ISSUES'
            else:
                insights['data_pipeline_health'] = 'UNHEALTHY'
        
        # Analyze system readiness
        performance = results_dict.get('performance_benchmark')
        # operational = results_dict.get('operational_stability')
        
        if performance:
            if performance.status == "PASS":
                insights['system_readiness'] = 'READY'
            elif performance.status == "WARNING":
                insights['system_readiness'] = 'NEEDS_OPTIMIZATION'
            else:
                insights['system_readiness'] = 'NOT_READY'
        
        # Data quality status
        if data_integrity:
            if data_integrity.status == "PASS":
                insights['data_quality_status'] = 'HIGH_QUALITY'
            elif data_integrity.status == "WARNING":
                insights['data_quality_status'] = 'ACCEPTABLE_QUALITY'
            else:
                insights['data_quality_status'] = 'POOR_QUALITY'
        
        return insights
    
    def _calculate_mvp_readiness_score(self, test_results: List[MVPVerificationResult]) -> Dict[str, Any]:
        """Calculate numerical MVP readiness score."""
        
        total_tests = len(test_results)
        if total_tests == 0:
            return {'score': 0, 'percentage': 0, 'grade': 'F'}
        
        # Weight tests by importance
        test_weights = {
            'data_availability': 0.3,
            'performance_benchmark': 0.3,
            'data_integrity': 0.3,
            'operational_stability': 0.1
        }
        
        total_weight = 0
        weighted_score = 0
        
        for result in test_results:
            weight = test_weights.get(result.test_name, 0.1)
            total_weight += weight
            
            if result.status == "PASS":
                weighted_score += weight * 100
            elif result.status == "WARNING":
                weighted_score += weight * 75
            elif result.status == "FAIL":
                weighted_score += weight * 25
            # ERROR = 0 points
        
        final_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # Assign grade
        if final_score >= 90:
            grade = 'A'
        elif final_score >= 80:
            grade = 'B'
        elif final_score >= 70:
            grade = 'C'
        elif final_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'score': final_score,
            'percentage': f"{final_score:.1f}%",
            'grade': grade,
            'mvp_ready': final_score >= 80,  # B grade or better required
            'weighting_used': test_weights
        }
    
    def _check_nfr_compliance(self, test_results: List[MVPVerificationResult]) -> Dict[str, Any]:
        """Check compliance with Non-Functional Requirements."""
        
        nfr_status = {
            'NFR_2_operational_stability': 'NOT_TESTED',  # 95% operational stability
            'NFR_3_data_integrity': 'NOT_TESTED',        # <1% validation failure
            'NFR_4_1_bulk_ingestion': 'NOT_TESTED',      # 1 year data in 2-4 hours
            'NFR_4_2_query_performance': 'NOT_TESTED'    # <5 seconds for standard query
        }
        
        results_dict = {result.test_name: result for result in test_results}
        
        # Check NFR 3 - Data Integrity
        integrity_test = results_dict.get('data_integrity')
        if integrity_test:
            if integrity_test.status == "PASS":
                nfr_status['NFR_3_data_integrity'] = 'COMPLIANT'
            elif integrity_test.status == "WARNING":
                nfr_status['NFR_3_data_integrity'] = 'PARTIALLY_COMPLIANT'
            else:
                nfr_status['NFR_3_data_integrity'] = 'NON_COMPLIANT'
        
        # Check NFR 4.2 - Query Performance
        performance_test = results_dict.get('performance_benchmark')
        if performance_test:
            if performance_test.status == "PASS":
                nfr_status['NFR_4_2_query_performance'] = 'COMPLIANT'
            elif performance_test.status == "WARNING":
                nfr_status['NFR_4_2_query_performance'] = 'PARTIALLY_COMPLIANT'
            else:
                nfr_status['NFR_4_2_query_performance'] = 'NON_COMPLIANT'
        
        return nfr_status
    
    def _generate_recommended_actions(self, test_results: List[MVPVerificationResult]) -> List[Dict[str, Any]]:
        """Generate prioritized recommended actions."""
        
        actions = []
        
        # High priority - Failed tests
        for result in test_results:
            if result.status == "FAIL":
                actions.append({
                    'priority': 'HIGH',
                    'category': 'CRITICAL_FAILURE',
                    'action': f'Fix {result.test_name} test failures',
                    'recommendations': result.recommendations[:2]
                })
        
        # Medium priority - Warnings
        for result in test_results:
            if result.status == "WARNING":
                actions.append({
                    'priority': 'MEDIUM',
                    'category': 'OPTIMIZATION',
                    'action': f'Optimize {result.test_name} performance',
                    'recommendations': result.recommendations[:1]
                })
        
        # Low priority - Errors (infrastructure issues)
        for result in test_results:
            if result.status == "ERROR":
                actions.append({
                    'priority': 'LOW',
                    'category': 'INFRASTRUCTURE',
                    'action': f'Fix {result.test_name} test execution',
                    'recommendations': result.recommendations
                })
        
        return actions
    
    def _save_comprehensive_results(self, results: Dict[str, Any]) -> str:
        """Save comprehensive results to file."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mvp_comprehensive_verification_{timestamp}.json"
        
        filepath = self.utils.save_results_to_file(
            [MVPVerificationResult(**result) for result in results['individual_test_results']],
            filename
        )
        
        # Also save the comprehensive analysis separately
        analysis_filename = f"mvp_analysis_{timestamp}.json"
        analysis_filepath = f"logs/{analysis_filename}"
        
        with open(analysis_filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info("Comprehensive results saved", 
                        filepath=filepath, 
                        analysis_filepath=analysis_filepath)
        
        return filepath
    
    def generate_executive_report(self, results: Dict[str, Any]) -> str:
        """Generate an executive summary report."""
        
        summary = results['executive_summary']
        analysis = results['comprehensive_analysis']
        
        report = []
        report.append("=" * 60)
        report.append("MVP VERIFICATION EXECUTIVE SUMMARY")
        report.append("=" * 60)
        report.append("")
        
        # Overall status
        report.append(f"MVP READINESS: {summary['mvp_readiness']}")
        report.append(f"Overall Score: {summary['overall_score']} ({summary['pass_rate']})")
        report.append(f"Execution Time: {summary['execution_summary']['total_execution_time']:.1f}s")
        report.append("")
        
        # Critical issues
        if analysis['critical_issues']:
            report.append("CRITICAL ISSUES:")
            for issue in analysis['critical_issues']:
                report.append(f"  ⚠️  {issue['description']}")
            report.append("")
        
        # NFR Compliance
        report.append("NFR COMPLIANCE:")
        for nfr, status in analysis['nfr_compliance'].items():
            status_icon = "✅" if status == "COMPLIANT" else "❌" if status == "NON_COMPLIANT" else "⚠️"
            report.append(f"  {status_icon} {nfr}: {status}")
        report.append("")
        
        # Recommendations
        report.append("TOP RECOMMENDATIONS:")
        for rec in summary['recommendations'][:5]:
            report.append(f"  • {rec}")
        
        return "\n".join(report) 