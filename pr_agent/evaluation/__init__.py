"""
PR Agent Evaluation System

A comprehensive evaluation framework for measuring PR Agent performance
using standardized Kubernetes test cases with known errors.
"""

from .test_cases import (
    KubernetesTestCases,
    TestCase,
    KnownError,
    ErrorCategory,
    ErrorSeverity
)

from .metrics import (
    ErrorDetectionParser,
    MetricsCalculator,
    DetectedError,
    EvaluationResult,
    ModelPerformanceReport,
    EvaluationReporter
)

from .runner import (
    ModelEvaluationRunner,
    QuickTestRunner
)

__version__ = "1.0.0"
__all__ = [
    # Test Cases
    "KubernetesTestCases",
    "TestCase", 
    "KnownError",
    "ErrorCategory",
    "ErrorSeverity",
    
    # Metrics
    "ErrorDetectionParser",
    "MetricsCalculator", 
    "DetectedError",
    "EvaluationResult",
    "ModelPerformanceReport",
    "EvaluationReporter",
    
    # Runner
    "ModelEvaluationRunner",
    "QuickTestRunner"
]