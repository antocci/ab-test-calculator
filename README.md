# A/B Test Sample Size Calculator

A comprehensive Python tool for calculating sample sizes for A/B tests. Supports proportions (conversion rates), means (continuous metrics), and advanced experimental designs.

## Features

- **Proportions & Means**: Calculate sample sizes for conversion rates and continuous metrics
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
```

### Command Line

```bash
# Simple test
python -m ab_test_calc.cli --baseline 0.10 --mde 0.02

# Interactive mode (recommended for beginners)
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

## Documentation

See [GUIDE.md](GUIDE.md) for:
- Full API reference
- Command-line options
- Architecture details
- More examples

## Running Tests

```bash
pytest
```

All 35 tests passing.

## License

MIT
