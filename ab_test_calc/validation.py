"""Input validation for A/B test sample size calculations."""

from typing import Optional, List


class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass


def validate_inputs(
    baseline: float,
    mde: float,
    power: float,
    alpha: float,
    mde_type: str,
    ratio: float,
    metric_type: str,
    std_dev: Optional[float],
    std_dev_2: Optional[float],
    test_type: str,
    n_comparisons: Optional[int],
    correction: Optional[str],
    n_controls: int,
    n_treatments: int,
    sides: int,
    weights: Optional[List[float]],
) -> None:
    """
    Validate all input parameters before calculation.

    Raises:
        ValidationError: If any parameter is invalid.
    """
    errors = []

    # Alpha validation
    if not (0 < alpha < 1):
        errors.append(f"alpha must be between 0 and 1, got {alpha}")

    # Power validation
    if not (0 < power < 1):
        errors.append(f"power must be between 0 and 1, got {power}")

    # Sides validation
    if sides not in (1, 2):
        errors.append(f"sides must be 1 or 2, got {sides}")

    # Metric type validation
    if metric_type not in ('proportion', 'mean'):
        errors.append(f"metric_type must be 'proportion' or 'mean', got '{metric_type}'")

    # MDE type validation
    if mde_type not in ('relative', 'absolute'):
        errors.append(f"mde_type must be 'relative' or 'absolute', got '{mde_type}'")

    # Test type validation
    if test_type not in ('z', 't', 'chi2'):
        errors.append(f"test_type must be 'z', 't', or 'chi2', got '{test_type}'")

    # Chi-square only for proportions
    if test_type == 'chi2' and metric_type == 'mean':
        errors.append("Chi-square test is only valid for proportions, not means. Use 'z' or 't' instead.")

    # Baseline validation for proportions
    if metric_type == 'proportion':
        if not (0 < baseline < 1):
            errors.append(f"For proportions, baseline must be between 0 and 1, got {baseline}")

    # MDE validation
    if mde == 0:
        errors.append("mde cannot be zero")

    # Calculate target rate for proportions to validate bounds
    if metric_type == 'proportion' and not errors:
        if mde_type == 'relative':
            target = baseline * (1 + mde)
        else:
            target = baseline + mde

        if not (0 < target < 1):
            errors.append(f"Target rate {target:.4f} is out of bounds (0, 1). Check your MDE value.")

    # Ratio validation
    if ratio <= 0:
        errors.append(f"ratio must be positive, got {ratio}")

    # Standard deviation validation for means
    if metric_type == 'mean':
        if std_dev is None:
            errors.append("std_dev is required for metric_type='mean'")
        elif std_dev <= 0:
            errors.append(f"std_dev must be positive, got {std_dev}")

        if std_dev_2 is not None and std_dev_2 <= 0:
            errors.append(f"std_dev_2 must be positive, got {std_dev_2}")

    # Group counts validation
    if n_controls < 1:
        errors.append(f"n_controls must be at least 1, got {n_controls}")

    if n_treatments < 1:
        errors.append(f"n_treatments must be at least 1, got {n_treatments}")

    # Comparisons validation
    if n_comparisons is not None and n_comparisons < 1:
        errors.append(f"n_comparisons must be at least 1, got {n_comparisons}")

    # Correction validation
    if correction is not None and correction.lower() not in ('bonferroni', 'sidak'):
        errors.append(f"correction must be 'bonferroni', 'sidak', or None, got '{correction}'")

    # Weights validation
    if weights is not None:
        expected_len = n_controls + n_treatments
        if len(weights) != expected_len:
            errors.append(
                f"weights length ({len(weights)}) must match "
                f"n_controls + n_treatments ({expected_len})"
            )

        if any(w <= 0 for w in weights):
            errors.append("All weights must be positive")

    # Raise all errors at once
    if errors:
        raise ValidationError("\n".join(errors))
