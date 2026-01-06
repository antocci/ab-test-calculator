"""Report formatting for A/B test calculation results."""

from typing import Dict, Any


def print_report(result: Dict[str, Any]) -> None:
    """
    Display a formatted, human-readable report of calculation results.

    Args:
        result: Dictionary returned by calculate_sample_size().

    Example:
        >>> result = calculate_sample_size(baseline=0.2, mde=0.05)
        >>> print_report(result)
    """
    print("\n" + "=" * 40)
    print("             RESULTS")
    print("=" * 40)

    # Context summary
    print(f"Metric:          {result['metric_type'].title()}")
    print(f"Design:          {result['n_controls']} Control(s) vs {result['n_treatments']} Treatment(s)")

    # Test type with Welch's indicator
    is_welch = (
        result.get('std_dev_treatment')
        and result.get('std_dev_control')
        and result['std_dev_control'] != result['std_dev_treatment']
    )
    test_prefix = "Welch's " if is_welch else ""
    test_suffix = "T-Test" if result['test_type'] == 't' else "Z-Test"
    print(f"Test Type:       {test_prefix}{test_suffix}, {result['sides']}-Sided")

    # Bottleneck pair for weighted designs
    if result.get('bottleneck_pair'):
        print(f"Bottleneck:      {result['bottleneck_pair']} (Requires most samples)")

    # Baseline and target values
    if result['metric_type'] == 'proportion':
        baseline = result['baseline_value']
        delta = result['absolute_effect']
        target = baseline + delta
        print(f"Baseline:        {baseline:.2%}")
        print(f"Target:          {target:.2%}")
        sign = '+' if delta > 0 else ''
        print(f"Lift (Abs):      {sign}{delta:.2%}")
    else:
        print(f"Baseline:        {result['baseline_value']}")
        print(f"MDE (Abs):       {result['absolute_effect']}")
        if result.get('std_dev_control'):
            print(f"Std Dev (Ctrl):  {result['std_dev_control']}")
        if result.get('std_dev_treatment') and result.get('std_dev_treatment') != result.get('std_dev_control'):
            print(f"Std Dev (Trt):   {result['std_dev_treatment']}")

    # Alpha (with correction info if applicable)
    if result['alpha_corrected'] != result['alpha_raw']:
        correction_label = result.get('correction', 'adjusted')
        print(f"Alpha (Adj):     {result['alpha_corrected']:.5f} ({correction_label})")
    else:
        print(f"Alpha:           {result['alpha_raw']}")

    print(f"Power:           {result['power']:.0%}")

    print("-" * 40)

    # Sample sizes
    weights = result.get('weights')
    if weights:
        _print_weighted_breakdown(result, weights)
    else:
        _print_standard_breakdown(result)

    print("=" * 40 + "\n")


def _print_weighted_breakdown(result: Dict[str, Any], weights: list) -> None:
    """Print sample size breakdown for weighted designs."""
    total_n = result['total_sample_size']
    total_w = sum(weights)
    shares = [w / total_w for w in weights]

    print(f"Total Sample Size:        {int(total_n):,}")
    print("-" * 40)
    print("Group Breakdown:")

    n_ctrl = result['n_controls']
    n_trt = result['n_treatments']

    idx = 0
    for i in range(n_ctrl):
        share = shares[idx]
        n_group = total_n * share
        print(f"   Control {i + 1} ({share:.1%}):    {int(n_group):,}")
        idx += 1

    for i in range(n_trt):
        share = shares[idx]
        n_group = total_n * share
        print(f"   Treatment {i + 1} ({share:.1%}):  {int(n_group):,}")
        idx += 1


def _print_standard_breakdown(result: Dict[str, Any]) -> None:
    """Print sample size breakdown for standard designs."""
    ratio = result['ratio']

    if abs(ratio - 1.0) > 1e-5:
        print(f"Ratio (Trt/Ctrl): {ratio:.2f}")
        print(f"N (Control):           {int(result['sample_size_control']):,}")
        print(f"N (Treatment):         {int(result['sample_size_treatment']):,}")
    else:
        print(f"Sample Size Per Group: {int(result['sample_size_per_variant']):,}")

    print(f"TOTAL Sample Size:     {int(result['total_sample_size']):,}")


def format_result_summary(result: Dict[str, Any]) -> str:
    """
    Format a one-line summary of the result.

    Args:
        result: Dictionary returned by calculate_sample_size().

    Returns:
        Formatted string summary.
    """
    total = int(result['total_sample_size'])
    per_variant = int(result['sample_size_per_variant'])

    if result.get('weights'):
        return f"Total: {total:,} (weighted across {result['n_controls']}C + {result['n_treatments']}T groups)"
    elif result['n_controls'] == 1 and result['n_treatments'] == 1:
        return f"{per_variant:,} per group, {total:,} total"
    else:
        return f"{per_variant:,} per variant, {total:,} total ({result['n_controls']}C + {result['n_treatments']}T)"
