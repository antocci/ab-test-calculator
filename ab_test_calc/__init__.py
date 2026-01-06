"""
A/B Test Sample Size Calculator.

A comprehensive tool for calculating sample sizes for A/B tests,
supporting proportions, means, multiple comparisons, and weighted designs.

Example:
    >>> from ab_test_calc import calculate_sample_size, print_report
    >>> result = calculate_sample_size(baseline=0.10, mde=0.02)
    >>> print_report(result)
"""

from .core import calculate_sample_size
from .report import print_report, format_result_summary
from .validation import ValidationError
from .cli import run_interactive, main

__version__ = "1.0.0"

__all__ = [
    "calculate_sample_size",
    "print_report",
    "format_result_summary",
    "run_interactive",
    "ValidationError",
    "__version__",
]
