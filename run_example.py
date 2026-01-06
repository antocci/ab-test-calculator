#!/usr/bin/env python3
"""Example usage of A/B test sample size calculator."""

from ab_test_calc import calculate_sample_size, print_report


def main():
    print("=" * 50)
    print("Example 1: Simple A/B Test (Conversion Rate)")
    print("=" * 50)

    result = calculate_sample_size(
        baseline=0.10,      # Current conversion: 10%
        mde=0.02,           # Want to detect +2 percentage points
        mde_type='absolute',
        power=0.80,
        alpha=0.05,
    )
    print_report(result)

    print("=" * 50)
    print("Example 2: Complex A/B/n with Weights")
    print("=" * 50)

    result = calculate_sample_size(
        baseline=0.20,
        mde=0.03,
        mde_type='absolute',
        power=0.80,
        alpha=0.05,
        n_controls=2,
        n_treatments=3,
        weights=[0.35, 0.15, 0.20, 0.18, 0.12],
        n_comparisons=6,
        correction='bonferroni',
        sides=2,
    )
    print_report(result)

    print("=" * 50)
    print("Example 3: Mean Metric (Revenue)")
    print("=" * 50)

    result = calculate_sample_size(
        baseline=100,       # Current avg revenue: $100
        mde=5,              # Want to detect +$5
        mde_type='absolute',
        metric_type='mean',
        std_dev=30,         # Historical std dev
        test_type='t',
    )
    print_report(result)


if __name__ == "__main__":
    main()
