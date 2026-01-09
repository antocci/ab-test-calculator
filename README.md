# A/B Test Sample Size Calculator

A comprehensive Python tool for calculating sample sizes for A/B tests. Supports proportions (conversion rates), means (continuous metrics), and advanced experimental designs.

## Features

- **Proportions & Means**: Calculate sample sizes for conversion rates and continuous metrics
- **Reverse Calculation**: Find MDE for a given sample size
- **Multiple Test Types**: Z-test, T-test, Welch's T-test for unequal variances
- **Advanced Designs**: Multi-group experiments with weighted traffic allocation
- **Multiple Comparisons**: Bonferroni and Sidak corrections
- **CLI & Python API**: Use from command line or import in your code
- **Interactive Mode**: Guided wizard with explanations for each parameter

## Installation

```bash
pip install numpy scipy

# Clone and install
git clone https://github.com/antocci/ab-test-calculator.git
cd ab-test-calculator
pip install -e .
```

## Quick Start

### Python API

```python
from ab_test_calc import calculate_sample_size, print_report

# Simple A/B test: detect 10% -> 12% conversion
result = calculate_sample_size(baseline=0.10, mde=0.02)
print_report(result)

# Reverse: what MDE can I detect with 5000 samples?
from ab_test_calc import calculate_mde_for_sample, print_mde_report
result = calculate_mde_for_sample(baseline=0.10, sample_size_per_group=5000)
print_mde_report(result)
```

### Command Line

```bash
# Calculate sample size
python -m ab_test_calc.cli --baseline 0.10 --mde 0.02

# Calculate MDE for given sample size
python -m ab_test_calc.cli --baseline 0.10 --sample-size 5000

# Interactive mode
python -m ab_test_calc.cli --interactive
```

## Examples

### Conversion Rate Test

```python
result = calculate_sample_size(
    baseline=0.20,       # Current: 20%
    mde=0.05,            # Detect: +5 percentage points
    mde_type='absolute',
    power=0.8,
    alpha=0.05,
)
# Output: ~1,031 per group
```

### Revenue/Mean Test

```python
result = calculate_sample_size(
    baseline=100,        # Current average: $100
    mde=2,               # Detect: +$2
    metric_type='mean',
    std_dev=20,
    test_type='t',
)
# Output: ~1,570 per group
```

### Complex Design with Weights

```python
result = calculate_sample_size(
    baseline=0.20,
    mde=0.03,
    n_controls=2,
    n_treatments=3,
    weights=[35, 15, 20, 18, 12],  # Traffic allocation
    correction='bonferroni',
)
```

## Interactive Mode

For guided setup with explanations, run:

```bash
python -m ab_test_calc.cli --interactive
```

The wizard walks you through each parameter step-by-step:

1. **Metric type** — conversion rate (proportion) or continuous value (mean)
2. **Baseline** — your current metric value
3. **MDE** — minimum effect size you want to detect
4. **Variability** — standard deviation (for mean metrics only)
5. **Statistical parameters** — power, alpha, one/two-sided, z/t-test
6. **Experimental design** — number of groups, traffic allocation
7. **Multiple comparisons** — Bonferroni/Sidak corrections if needed

Each step includes explanations and sensible defaults — just press Enter to accept them.

## Documentation

See [GUIDE.md](GUIDE.md) for:
- Full API reference
- Command-line options
- Architecture details
- More examples
