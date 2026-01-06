# A/B Test Sample Size Calculator

A comprehensive tool for calculating sample sizes for A/B tests, supporting proportions (conversion rates), means (continuous metrics), and advanced experimental designs.

## Installation

```bash
# Install dependencies
pip install numpy scipy

# Or install as a package
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

# Interactive mode (guided wizard)
python -m ab_test_calc.cli --interactive
```

## Examples

### 1. Conversion Rate (Proportions)

Detect a change from 20% to 25% conversion (5 percentage points):

```python
from ab_test_calc import calculate_sample_size, print_report

result = calculate_sample_size(
    baseline=0.20,          # Current: 20%
    mde=0.05,               # Detect: +5 percentage points
    mde_type='absolute',    # MDE is in absolute terms
    power=0.8,              # 80% power
    alpha=0.05,             # 5% significance
)
print_report(result)
# Output: ~1,031 per group
```

### 2. Average Order Value (Means)

Detect a $2 increase in average order value:

```python
result = calculate_sample_size(
    baseline=100,           # Current: $100
    mde=2,                  # Detect: +$2
    mde_type='absolute',
    metric_type='mean',
    std_dev=20,             # Historical standard deviation
    test_type='t',          # Use T-test for means
)
print_report(result)
# Output: ~1,570 per group
```

### 3. Welch's T-Test (Unequal Variances)

When treatment might affect variance:

```python
result = calculate_sample_size(
    baseline=100,
    mde=2,
    mde_type='absolute',
    metric_type='mean',
    std_dev=20,             # Control SD
    std_dev_2=30,           # Treatment SD (higher variance)
    test_type='t',
)
print_report(result)
# Output: ~2,556 per group (more samples needed)
```

### 4. Multiple Treatments (A/B/n Test)

Testing 3 variations against 1 control with Bonferroni correction:

```python
result = calculate_sample_size(
    baseline=0.20,
    mde=0.05,
    mde_type='absolute',
    n_treatments=3,         # 3 treatment groups
    n_comparisons=3,        # 3 tests (each vs control)
    correction='bonferroni',
)
print_report(result)
```

### 5. Complex Design with Weighted Traffic

Multiple controls/treatments with uneven traffic allocation:

```python
result = calculate_sample_size(
    baseline=0.20,
    mde=0.03,
    mde_type='absolute',
    n_controls=2,
    n_treatments=3,
    weights=[35, 15, 20, 18, 12],  # Traffic %: C1, C2, T1, T2, T3
    correction='bonferroni',
)
print_report(result)
```

## Command Line Reference

```bash
# Basic usage
python -m ab_test_calc.cli --baseline 0.10 --mde 0.02

# All options
python -m ab_test_calc.cli \
    --baseline 0.20 \
    --mde 0.05 \
    --type absolute \          # or 'relative'
    --metric_type proportion \ # or 'mean'
    --power 0.8 \
    --alpha 0.05 \
    --sides 2 \                # 1 or 2
    --test_type z \            # 'z' or 't'
    --std_dev 20 \             # for means
    --n_treatments 3 \
    --correction bonferroni    # or 'sidak'
```

## API Reference

### `calculate_sample_size()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `baseline` | float | required | Current metric value (0-1 for proportions) |
| `mde` | float | required | Minimum Detectable Effect |
| `power` | float | 0.8 | Statistical power (1 - Type II error) |
| `alpha` | float | 0.05 | Significance level (Type I error) |
| `mde_type` | str | 'absolute' | 'absolute' or 'relative' |
| `metric_type` | str | 'proportion' | 'proportion' or 'mean' |
| `std_dev` | float | None | Standard deviation (required for means) |
| `std_dev_2` | float | None | Treatment SD (enables Welch's test) |
| `test_type` | str | 'z' | 'z', 't', or 'chi2' |
| `sides` | int | 2 | 1 (one-sided) or 2 (two-sided) |
| `ratio` | float | 1.0 | Treatment/Control size ratio |
| `n_controls` | int | 1 | Number of control groups |
| `n_treatments` | int | 1 | Number of treatment groups |
| `n_comparisons` | int | auto | Number of statistical tests |
| `correction` | str | None | 'bonferroni' or 'sidak' |
| `weights` | list | None | Traffic weights for all groups |

### Return Value

Dictionary with:
- `sample_size_per_variant`: Samples per group
- `total_sample_size`: Total samples needed
- `alpha_corrected`: Alpha after correction
- `bottleneck_pair`: (for weighted) limiting comparison
- And more...

## Glossary

| Term | Description |
|------|-------------|
| **Baseline** | Current value of your metric |
| **MDE** | Smallest change worth detecting |
| **Power** | Probability of detecting a real effect (typically 80%) |
| **Alpha** | Probability of false positive (typically 5%) |
| **One-sided** | Only test if treatment is better |
| **Two-sided** | Test if treatment is different (better or worse) |
| **Bonferroni** | Conservative correction: α / n_comparisons |
| **Sidak** | Less conservative: 1 - (1-α)^(1/n) |

## Project Structure

```
ab_tests/
├── ab_test_calc/           # Main package
│   ├── __init__.py
│   ├── core.py
│   ├── validation.py
│   ├── report.py
│   └── cli.py
├── tests/
│   └── test_ab_calc.py     # Test suite (35 tests)
├── _extras/                # Archived/optional files
├── example_notebook.ipynb  # Jupyter examples
├── run_example.py          # Python examples
├── pyproject.toml          # Package configuration
└── GUIDE.md                # This file
```

## Architecture: Module Descriptions

### `__init__.py` — Public API

Defines what is exported when you import the package:

```python
from ab_test_calc import calculate_sample_size, print_report
```

This file re-exports functions from other modules so users don't need to know the internal structure. It also defines `__version__` and `__all__`.

### `core.py` — Calculation Engine

The mathematical heart of the calculator (~280 lines). Contains:

| Function | Purpose |
|----------|---------|
| `calculate_sample_size()` | Main entry point. Orchestrates the calculation. |
| `_calculate_single_pair()` | Calculates N for one control-treatment pair. |
| `_calculate_weighted_design()` | Handles multi-group weighted designs (worst-case pair logic). |
| `get_critical_value()` | Returns z/t critical values for given alpha and sides. |
| `apply_correction()` | Applies Bonferroni or Sidak correction to alpha. |

Key formulas implemented:
- Z-test and T-test sample size formulas
- Welch-Satterthwaite degrees of freedom for unequal variances
- Iterative T-test convergence for small samples

### `validation.py` — Input Validation

Validates all parameters before calculation (~110 lines). Catches errors early with clear messages:

```python
from ab_test_calc.validation import ValidationError

# These will raise ValidationError:
calculate_sample_size(baseline=0.1, mde=0.02, alpha=1.5)  # alpha > 1
calculate_sample_size(baseline=1.5, mde=0.02)              # baseline > 1 for proportion
calculate_sample_size(baseline=100, mde=5, metric_type='mean')  # missing std_dev
```

Checks performed:
- `0 < alpha < 1` and `0 < power < 1`
- `0 < baseline < 1` for proportions
- `std_dev > 0` when required
- Target rate stays in valid range
- Weights length matches group count
- And more...

### `report.py` — Output Formatting

Formats calculation results for display (~95 lines):

| Function | Purpose |
|----------|---------|
| `print_report(result)` | Prints formatted table to console |
| `format_result_summary(result)` | Returns one-line summary string |

Example output:
```
========================================
             RESULTS
========================================
Metric:          Proportion
Design:          1 Control(s) vs 1 Treatment(s)
...
```

### `cli.py` — Command Line Interface

Handles user interaction (~350 lines):

| Function | Purpose |
|----------|---------|
| `main()` | Entry point. Parses `--baseline`, `--mde`, etc. |
| `run_interactive()` | Step-by-step wizard with explanations |
| `prompt()` | Helper for validated user input |

Interactive mode guides users through each parameter with explanations:
```
STEP 1: What metric are you testing?
   - proportion: Conversion rate, CTR, signup rate (values 0-1)
   - mean: Revenue, time on page, order value (any number)
Metric type (proportion/mean) [default: proportion]:
```

## Data Flow

```
User Input
    │
    ▼
┌─────────┐
│  cli.py │  ← Parses arguments or runs interactive wizard
└────┬────┘
     │
     ▼
┌──────────────┐
│ validation.py │  ← Validates all parameters
└──────┬───────┘
       │
       ▼
┌──────────┐
│  core.py │  ← Performs mathematical calculations
└────┬─────┘
     │
     ▼
┌───────────┐
│ report.py │  ← Formats and displays results
└───────────┘
```

## Why This Structure?

| Benefit | Explanation |
|---------|-------------|
| **Testability** | Each module can be tested independently |
| **Maintainability** | Changes to UI don't affect math, and vice versa |
| **Reusability** | Use `core.py` in other projects without CLI |
| **Readability** | ~200-350 lines per file instead of 685 in one |
| **Separation of concerns** | Input handling, logic, and output are separate |

## Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=ab_test_calc

# Verbose output
pytest -v
```
