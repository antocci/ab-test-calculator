"""Core sample size calculation logic for A/B tests."""

import numpy as np
from scipy import stats
from typing import Dict, Optional, List, Any

from .validation import validate_inputs

# Constants
DEFAULT_POWER = 0.8
DEFAULT_ALPHA = 0.05
DEFAULT_MDE_TYPE = 'absolute'
DEFAULT_TEST_TYPE = 'z'
DEFAULT_SIDES = 2
CONVERGENCE_THRESHOLD = 0.1
MAX_ITERATIONS = 15
INITIAL_N_ESTIMATE = 100000  # Large N for initial Z-approximation


def get_critical_value(
    alpha: float,
    sides: int,
    test_type: str,
    df: Optional[float] = None
) -> float:
    """
    Calculate critical value for the given test parameters.

    Args:
        alpha: Significance level (already corrected if applicable).
        sides: 1 for one-sided, 2 for two-sided test.
        test_type: 'z', 't', or 'chi2'.
        df: Degrees of freedom (required for t-test).

    Returns:
        Critical value from the appropriate distribution.
    """
    alpha_tail = alpha / 2 if sides == 2 else alpha

    if test_type in ('z', 'chi2'):
        return stats.norm.ppf(1 - alpha_tail)
    else:  # t-test
        if df is None or df < 1:
            df = 1
        return stats.t.ppf(1 - alpha_tail, df)


def apply_correction(alpha: float, n_comparisons: int, method: str) -> float:
    """
    Apply multiple comparison correction to alpha.

    Args:
        alpha: Original significance level.
        n_comparisons: Number of comparisons.
        method: 'bonferroni' or 'sidak'.

    Returns:
        Corrected alpha value.
    """
    method = method.lower()
    if method == 'bonferroni':
        return alpha / n_comparisons
    elif method == 'sidak':
        return 1 - (1 - alpha) ** (1 / n_comparisons)
    else:
        raise ValueError(f"Unknown correction method: {method}")


def _calculate_single_pair(
    baseline: float,
    delta: float,
    power: float,
    alpha_corrected: float,
    ratio: float,
    metric_type: str,
    std_dev: Optional[float],
    std_dev_2: Optional[float],
    test_type: str,
    sides: int,
) -> float:
    """
    Calculate sample size for a single control-treatment pair.

    Returns:
        Required sample size for control group (n1).
    """
    k = ratio
    sigma1 = std_dev or 0.0
    sigma2 = std_dev_2 if std_dev_2 is not None else sigma1

    # Prepare variance terms based on metric type
    if metric_type == 'proportion':
        p1 = baseline
        p2 = p1 + delta

        # Term A: baseline variance for H0
        term_a = np.sqrt(p1 * (1 - p1) * (1 + 1 / k))
        # Term B: unpooled variance for H1
        term_b = np.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / k)
    else:
        term_a = None
        term_b = None

    def compute_n1(current_n1: float) -> float:
        """Compute n1 given current estimate (for iterative t-test)."""
        # Get critical values
        if test_type in ('z', 'chi2'):
            cv_alpha = get_critical_value(alpha_corrected, sides, test_type)
            cv_power = stats.norm.ppf(power)
        else:  # t-test
            n1, n2 = current_n1, k * current_n1

            if metric_type == 'mean':
                # Welch-Satterthwaite degrees of freedom
                v1 = sigma1 ** 2 / n1
                v2 = sigma2 ** 2 / n2
                if (v1 + v2) < 1e-12:
                    df = n1 + n2 - 2
                else:
                    df = (v1 + v2) ** 2 / ((v1 ** 2) / (n1 - 1) + (v2 ** 2) / (n2 - 1))
            else:
                # Proportions: simple pooled df
                df = max(1, n1 + n2 - 2)

            cv_alpha = get_critical_value(alpha_corrected, sides, test_type, df)
            cv_power = stats.t.ppf(power, df)

        # Calculate n1
        if metric_type == 'proportion':
            numerator = (cv_alpha * term_a + cv_power * term_b) ** 2
        else:
            # For means: n1 = (sigma1^2 + sigma2^2/k) * (cv_a + cv_b)^2 / delta^2
            variance_factor = sigma1 ** 2 + sigma2 ** 2 / k
            numerator = variance_factor * (cv_alpha + cv_power) ** 2

        return numerator / (delta ** 2)

    # Initial estimate using Z-approximation
    n1 = compute_n1(INITIAL_N_ESTIMATE)

    # Iterate for t-test convergence
    if test_type == 't':
        for _ in range(MAX_ITERATIONS):
            prev_n = n1
            n1 = compute_n1(n1)
            if abs(n1 - prev_n) < CONVERGENCE_THRESHOLD:
                break

    return float(np.ceil(n1))


def calculate_sample_size(
    baseline: float,
    mde: float,
    power: float = DEFAULT_POWER,
    alpha: float = DEFAULT_ALPHA,
    mde_type: str = DEFAULT_MDE_TYPE,
    ratio: float = 1.0,
    metric_type: str = 'proportion',
    std_dev: Optional[float] = None,
    std_dev_2: Optional[float] = None,
    test_type: str = DEFAULT_TEST_TYPE,
    n_comparisons: Optional[int] = None,
    correction: Optional[str] = None,
    n_controls: int = 1,
    n_treatments: int = 1,
    sides: int = DEFAULT_SIDES,
    weights: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Calculate required sample size for an A/B test.

    Supports advanced experimental designs including multiple variations,
    uneven traffic weighting, and multiple comparison corrections.

    Args:
        baseline: Current metric value (0-1 for proportions, any value for means).
        mde: Minimum Detectable Effect.
        power: Statistical power (1 - Beta), typically 0.8.
        alpha: Significance level (Type I error rate), typically 0.05.
        mde_type: 'absolute' (default) or 'relative'.
            Absolute: target = baseline + mde
            Relative: target = baseline * (1 + mde)
        ratio: Treatment/Control size ratio. Ignored if weights provided.
        metric_type: 'proportion' or 'mean'.
        std_dev: Standard deviation for control (required for means).
        std_dev_2: Standard deviation for treatment (enables Welch's test).
        test_type: 'z' (default), 't', or 'chi2'.
        n_comparisons: Number of hypotheses. Defaults to n_controls * n_treatments.
        correction: 'bonferroni', 'sidak', or None.
        n_controls: Number of control groups.
        n_treatments: Number of treatment groups.
        sides: 1 (one-sided) or 2 (two-sided).
        weights: Traffic weights for all groups [C1, C2..., T1, T2...].

    Returns:
        Dictionary with sample sizes and calculation metadata.

    Examples:
        Simple A/B test:
        >>> calculate_sample_size(baseline=0.1, mde=0.02)

        Complex design with weights:
        >>> calculate_sample_size(
        ...     baseline=0.2, mde=0.03,
        ...     n_controls=2, n_treatments=3,
        ...     weights=[35, 15, 20, 18, 12],
        ...     correction='bonferroni'
        ... )
    """
    # Normalize inputs
    n_controls = max(1, n_controls)
    n_treatments = max(1, n_treatments)

    if n_comparisons is None:
        n_comparisons = n_controls * n_treatments

    n_comparisons = max(1, n_comparisons)

    # Validate all inputs
    validate_inputs(
        baseline=baseline,
        mde=mde,
        power=power,
        alpha=alpha,
        mde_type=mde_type,
        ratio=ratio,
        metric_type=metric_type,
        std_dev=std_dev,
        std_dev_2=std_dev_2,
        test_type=test_type,
        n_comparisons=n_comparisons,
        correction=correction,
        n_controls=n_controls,
        n_treatments=n_treatments,
        sides=sides,
        weights=weights,
    )

    # Calculate effect size (delta)
    if mde_type == 'relative':
        delta = baseline * mde
    else:
        delta = mde

    # Apply multiple comparison correction
    alpha_corrected = alpha
    if correction:
        alpha_corrected = apply_correction(alpha, n_comparisons, correction)

    # Handle weighted design (worst-case pair logic)
    if weights is not None:
        return _calculate_weighted_design(
            baseline=baseline,
            delta=delta,
            power=power,
            alpha=alpha,
            alpha_corrected=alpha_corrected,
            metric_type=metric_type,
            std_dev=std_dev,
            std_dev_2=std_dev_2,
            test_type=test_type,
            n_comparisons=n_comparisons,
            correction=correction,
            n_controls=n_controls,
            n_treatments=n_treatments,
            sides=sides,
            weights=weights,
        )

    # Standard calculation (uniform or simple ratio)
    n1 = _calculate_single_pair(
        baseline=baseline,
        delta=delta,
        power=power,
        alpha_corrected=alpha_corrected,
        ratio=ratio,
        metric_type=metric_type,
        std_dev=std_dev,
        std_dev_2=std_dev_2,
        test_type=test_type,
        sides=sides,
    )

    n2 = float(np.ceil(n1 * ratio))
    total = (n1 * n_controls) + (n2 * n_treatments)

    return {
        "sample_size_per_variant": n1,
        "sample_size_control": n1,
        "sample_size_treatment": n2,
        "total_sample_size": total,
        "n_controls": n_controls,
        "n_treatments": n_treatments,
        "control_sample_size": n1 * n_controls,
        "treatment_sample_size_total": n2 * n_treatments,
        "baseline_value": baseline,
        "absolute_effect": delta,
        "alpha_raw": alpha,
        "alpha_corrected": alpha_corrected,
        "metric_type": metric_type,
        "test_type": test_type,
        "std_dev_control": std_dev if metric_type == 'mean' else None,
        "std_dev_treatment": std_dev_2 if metric_type == 'mean' else None,
        "sides": sides,
        "ratio": ratio,
        "power": power,
        "weights": weights,
        "correction": correction,
    }


def _calculate_weighted_design(
    baseline: float,
    delta: float,
    power: float,
    alpha: float,
    alpha_corrected: float,
    metric_type: str,
    std_dev: Optional[float],
    std_dev_2: Optional[float],
    test_type: str,
    n_comparisons: int,
    correction: Optional[str],
    n_controls: int,
    n_treatments: int,
    sides: int,
    weights: List[float],
) -> Dict[str, Any]:
    """
    Calculate sample size for weighted multi-group design.

    Uses worst-case pair logic to ensure all comparisons meet power requirements.
    """
    # Normalize weights
    total_w = sum(weights)
    norm_weights = [w / total_w for w in weights]

    w_controls = norm_weights[:n_controls]
    w_treatments = norm_weights[n_controls:]

    # Find worst-case pair (requires most samples)
    worst_case = None
    max_total = 0

    for i, w_c in enumerate(w_controls):
        for j, w_t in enumerate(w_treatments):
            k_pair = w_t / w_c

            n_control = _calculate_single_pair(
                baseline=baseline,
                delta=delta,
                power=power,
                alpha_corrected=alpha_corrected,
                ratio=k_pair,
                metric_type=metric_type,
                std_dev=std_dev,
                std_dev_2=std_dev_2,
                test_type=test_type,
                sides=sides,
            )

            total_required = n_control / w_c

            if total_required > max_total:
                max_total = total_required
                worst_case = {
                    'pair': f"C{i + 1} vs T{j + 1}",
                    'ratio': k_pair,
                    'w_c': w_c,
                    'w_t': w_t,
                }

    return {
        'sample_size_control': max_total * (sum(w_controls) / n_controls),
        'sample_size_treatment': max_total * (sum(w_treatments) / n_treatments),
        'sample_size_per_variant': max_total / (n_controls + n_treatments),
        'total_sample_size': max_total,
        'baseline_value': baseline,
        'absolute_effect': delta,
        'alpha_raw': alpha,
        'alpha_corrected': alpha_corrected,
        'power': power,
        'ratio': worst_case['ratio'],
        'metric_type': metric_type,
        'test_type': test_type,
        'n_controls': n_controls,
        'n_treatments': n_treatments,
        'sides': sides,
        'bottleneck_pair': worst_case['pair'],
        'bottleneck_ratio': worst_case['ratio'],
        'weights': weights,
        'correction': correction,
    }
