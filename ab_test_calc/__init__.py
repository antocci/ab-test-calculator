"""
A/B Test Sample Size Calculator.

A comprehensive tool for calculating sample sizes for A/B tests,
supporting proportions, means, multiple comparisons, and weighted designs.

Example:
    >>> from ab_test_calc import calculate_sample_size, print_report
    >>> result = calculate_sample_size(baseline=0.10, mde=0.02)
    >>> print_report(result)

    # Reverse calculation: find MDE for given sample size
    >>> from ab_test_calc import calculate_mde_for_sample, print_mde_report
    >>> result = calculate_mde_for_sample(baseline=0.10, sample_size_per_group=5000)
    >>> print_mde_report(result)
"""

from .core import calculate_sample_size, calculate_mde_for_sample
from .report import print_report, format_result_summary, print_mde_report
from .validation import ValidationError
from .cli import run_interactive, main

__version__ = "1.1.0"

__all__ = [
    "calculate_sample_size",
    "calculate_mde_for_sample",
    "print_report",
    "print_mde_report",
    "format_result_summary",
    "run_interactive",
    "ValidationError",
    "__version__",
]
