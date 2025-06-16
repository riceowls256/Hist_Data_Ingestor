"""
MVP Verification Test Suite

This module contains scripts and tests to verify that the MVP meets all success metrics
defined in the PRD. These tests validate:

1. Data Availability from Databento (AC1)
2. Query Performance targets <5s (AC2) 
3. Data Integrity rates <1% failure (AC3)
4. Operational Stability 95% (AC4)
5. Comprehensive results reporting (AC5)

All tests follow the project's operational guidelines and integrate with existing
test infrastructure.
"""

__version__ = "1.0.0"

from .data_availability_test import DataAvailabilityTest
from .performance_benchmark_test import PerformanceBenchmarkTest  
from .data_integrity_analysis import DataIntegrityAnalysis
from .operational_stability_test import OperationalStabilityTest
from .master_verification_runner import MasterVerificationRunner
from .verification_utils import VerificationUtils

__all__ = [
    "DataAvailabilityTest",
    "PerformanceBenchmarkTest", 
    "DataIntegrityAnalysis",
    "OperationalStabilityTest",
    "MasterVerificationRunner",
    "VerificationUtils"
] 