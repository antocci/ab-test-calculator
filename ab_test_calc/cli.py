"""Command-line interface for A/B test sample size calculator."""

import argparse
import sys
from typing import Optional, Any, List

from .core import calculate_sample_size, DEFAULT_POWER, DEFAULT_ALPHA, DEFAULT_MDE_TYPE
from .report import print_report

__version__ = "1.0.0"


def prompt(
    text: str,
    default: Any = None,
    options: Optional[List[str]] = None,
    aliases: Optional[dict] = None,
    type_func: type = str,
    required: bool = True,
    example: Optional[str] = None,
) -> Any:
    """
    Prompt user for input with validation.

    Args:
        text: Prompt text to display.
        default: Default value if user presses Enter.
        options: Valid options to accept.
        aliases: Mapping of shortcuts to full values.
        type_func: Type conversion function.
        required: Whether input is required.
        example: Example value to show.

    Returns:
        Validated and converted user input.
    """
    # Build prompt suffix
    suffix_parts = []
    if default is not None:
        suffix_parts.append(f"default: {default}")
    if example and default is None:
        suffix_parts.append(f"e.g. {example}")

    suffix = f" [{', '.join(suffix_parts)}]" if suffix_parts else ""

    while True:
        try:
            raw = input(f"{text}{suffix}: ").strip()

            # Handle empty input
            if not raw:
                if default is not None:
                    return default
                if not required:
                    return None
                print("   This field is required.")
                continue

            # Normalize for matching
            val = raw.lower()

            # Apply aliases
            if aliases and val in aliases:
                val = aliases[val]

            # Type conversion (handle comma as decimal separator)
            if type_func in (float, int):
                val = type_func(raw.replace(',', '.'))
            else:
                val = type_func(val)

            # Validate against options
            if options and val not in options:
                print(f"   Invalid choice. Options: {', '.join(map(str, options))}")
                continue

            return val

        except ValueError:
            print(f"   Invalid format. Expected {type_func.__name__}.")
        except (EOFError, KeyboardInterrupt):
            print("\n   Cancelled.")
            sys.exit(0)


def run_interactive() -> None:
    """
    Launch interactive wizard for sample size calculation.

    Guides user through all parameters with helpful prompts and examples.
    """
    print("\n" + "=" * 50)
    print("       A/B Test Sample Size Calculator")
    print("=" * 50)
    print("Press Enter to accept [default] values.\n")

    try:
        # Step 1: What are you measuring?
        print("STEP 1: What metric are you testing?")
        print("   - proportion: Conversion rate, CTR, signup rate (values 0-1)")
        print("   - mean: Revenue, time on page, order value (any number)")
        metric_type = prompt(
            "Metric type (proportion/mean)",
            default='proportion',
            options=['proportion', 'mean'],
            aliases={'p': 'proportion', 'm': 'mean'},
        )

        # Step 2: Current value
        print("\nSTEP 2: What is your current metric value?")
        if metric_type == 'proportion':
            print("   Enter as decimal (0.10 = 10%, 0.05 = 5%)")
            baseline = prompt(
                "Current conversion rate",
                type_func=float,
                example="0.10",
            )
        else:
            baseline = prompt(
                "Current average value",
                type_func=float,
                example="100",
            )

        # Step 3: What change do you want to detect?
        print("\nSTEP 3: What is the minimum change you want to detect (MDE)?")
        if metric_type == 'proportion':
            print("   Absolute: Enter the percentage point difference")
            print("   Example: To detect 10% -> 12%, enter 0.02")
            mde = prompt(
                "Minimum detectable effect",
                type_func=float,
                example="0.02",
            )
        else:
            print("   Enter the absolute difference you want to detect")
            mde = prompt(
                "Minimum detectable effect",
                type_func=float,
                example="5",
            )

        print("\nMDE type:")
        print("   - absolute: Change in units (e.g., +2 percentage points)")
        print("   - relative: Change in percent (e.g., +10% of baseline)")
        mde_type = prompt(
            "MDE type (absolute/relative)",
            default='absolute',
            options=['absolute', 'relative'],
            aliases={'a': 'absolute', 'r': 'relative'},
        )

        # Step 4: Variability (only for means)
        std_dev = None
        std_dev_2 = None
        if metric_type == 'mean':
            print("\nSTEP 4: What is the variability in your data?")
            print("   Standard deviation measures how spread out your data is.")
            print("   You can find this in your historical data.")
            std_dev = prompt(
                "Standard deviation (control group)",
                type_func=float,
                example="20",
            )

            print("   If treatment might have different variability, enter it.")
            print("   Otherwise, press Enter to use the same value.")
            std_dev_2_input = prompt(
                "Standard deviation (treatment)",
                default=None,
                required=False,
                type_func=float,
            )
            std_dev_2 = std_dev_2_input if std_dev_2_input else None

        # Step 5: Statistical parameters
        step_num = 5 if metric_type == 'mean' else 4
        print(f"\nSTEP {step_num}: Statistical parameters")

        print("   Power = probability of detecting a real effect")
        print("   Higher power = more samples needed, but fewer missed effects")
        power = prompt(
            "Statistical power (0.8 = 80%)",
            default=0.8,
            type_func=float,
            example="0.8",
        )

        print("\n   Alpha = probability of false positive")
        print("   Lower alpha = more samples needed, but fewer false alarms")
        alpha = prompt(
            "Significance level (0.05 = 5%)",
            default=0.05,
            type_func=float,
            example="0.05",
        )

        print("\n   One-sided: Only testing if treatment is BETTER")
        print("   Two-sided: Testing if treatment is DIFFERENT (better or worse)")
        sides = prompt(
            "Test type (1=one-sided, 2=two-sided)",
            default=2,
            options=[1, 2],
            type_func=int,
        )

        print("\n   Z-test: Standard, good for large samples")
        print("   T-test: More conservative, better for smaller samples")
        test_type = prompt(
            "Test statistic (z/t)",
            default='z',
            options=['z', 't'],
        )

        # Step 6: Experimental design
        step_num += 1
        print(f"\nSTEP {step_num}: Experimental design")
        print("   Most A/B tests have 1 control and 1 treatment.")
        print("   For A/B/n tests, you can have multiple treatments.")

        use_weights = prompt(
            "Use custom traffic allocation? (y/n)",
            default='n',
            options=['y', 'n'],
        )

        weights = None
        n_controls = 1
        n_treatments = 1
        ratio = 1.0

        if use_weights == 'y':
            print("\n   Enter traffic weights as space or comma-separated numbers.")
            print("   First number(s) = control group(s), rest = treatment group(s)")
            print("   Example: '50 50' for equal split, '20 40 40' for 1 control + 2 treatments")

            weights_input = prompt(
                "Traffic weights",
                example="50 50",
            )

            try:
                parts = weights_input.replace(',', ' ').split()
                weights = [float(x) for x in parts]

                if len(weights) < 2:
                    print("   Need at least 2 groups. Using default 50/50 split.")
                    weights = None
                else:
                    n_controls = prompt(
                        f"How many of these {len(weights)} groups are controls?",
                        default=1,
                        type_func=int,
                    )

                    if n_controls < 1 or n_controls >= len(weights):
                        print(f"   Invalid. Using 1 control.")
                        n_controls = 1

                    n_treatments = len(weights) - n_controls

                    total_w = sum(weights)
                    shares = [f"{w/total_w:.0%}" for w in weights]
                    print(f"   -> {n_controls} control(s): {', '.join(shares[:n_controls])}")
                    print(f"   -> {n_treatments} treatment(s): {', '.join(shares[n_controls:])}")

            except ValueError:
                print("   Could not parse. Using default 50/50 split.")
                weights = None
        else:
            n_controls = prompt(
                "Number of control groups",
                default=1,
                type_func=int,
            )
            n_treatments = prompt(
                "Number of treatment groups",
                default=1,
                type_func=int,
            )

            if n_controls > 1 or n_treatments > 1:
                print("\n   Ratio = treatment group size / control group size")
                print("   Example: ratio=2 means treatment has twice as many users")
                ratio = prompt(
                    "Size ratio (treatment/control)",
                    default=1.0,
                    type_func=float,
                )

        # Step 7: Multiple comparisons
        n_comparisons_default = n_controls * n_treatments
        correction = None

        if n_comparisons_default > 1 or (n_controls > 1 or n_treatments > 1):
            step_num += 1
            print(f"\nSTEP {step_num}: Multiple comparisons correction")
            print(f"   You have {n_comparisons_default} comparison(s) by default.")
            print("   Multiple comparisons increase false positive risk.")
            print("   Correction adjusts alpha to control overall error rate.")

            n_comparisons = prompt(
                "Number of comparisons",
                default=n_comparisons_default,
                type_func=int,
            )

            if n_comparisons > 1:
                print("\n   - none: No correction (higher false positive risk)")
                print("   - bonferroni: Conservative (alpha / n_comparisons)")
                print("   - sidak: Slightly less conservative")
                correction = prompt(
                    "Correction method (none/bonferroni/sidak)",
                    default='none',
                    options=['none', 'bonferroni', 'sidak'],
                    aliases={'n': 'none', 'b': 'bonferroni', 's': 'sidak'},
                )
                if correction == 'none':
                    correction = None
        else:
            n_comparisons = 1

        # Calculate!
        result = calculate_sample_size(
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

        print_report(result)

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="A/B Test Sample Size Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple conversion rate test (10% -> 12%)
  %(prog)s --baseline 0.10 --mde 0.02

  # Mean test with standard deviation
  %(prog)s --metric_type mean --baseline 100 --mde 5 --std_dev 20

  # Multiple treatments with Bonferroni correction
  %(prog)s --baseline 0.10 --mde 0.02 --n_treatments 3 --correction bonferroni

  # Interactive mode
  %(prog)s --interactive
        """,
    )

    # Version
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    # Mode
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Run interactive wizard')

    # Required parameters
    parser.add_argument('--baseline', type=float,
                        help='Current metric value (e.g., 0.10 for 10%% conversion)')
    parser.add_argument('--mde', type=float,
                        help='Minimum Detectable Effect')

    # Metric configuration
    parser.add_argument('--metric_type', choices=['proportion', 'mean'],
                        default='proportion',
                        help='Type of metric (default: proportion)')
    parser.add_argument('--type', dest='mde_type',
                        choices=['relative', 'absolute'],
                        default=DEFAULT_MDE_TYPE,
                        help=f'MDE interpretation (default: {DEFAULT_MDE_TYPE})')

    # Statistical parameters
    parser.add_argument('--power', type=float, default=DEFAULT_POWER,
                        help=f'Statistical power (default: {DEFAULT_POWER})')
    parser.add_argument('--alpha', type=float, default=DEFAULT_ALPHA,
                        help=f'Significance level (default: {DEFAULT_ALPHA})')
    parser.add_argument('--sides', type=int, choices=[1, 2], default=2,
                        help='1 for one-sided, 2 for two-sided (default: 2)')
    parser.add_argument('--test_type', choices=['z', 't'], default='z',
                        help='Test statistic (default: z)')

    # Variance (for means)
    parser.add_argument('--std_dev', type=float,
                        help='Standard deviation (required for means)')
    parser.add_argument('--std_dev_2', type=float,
                        help='Treatment standard deviation (for Welch test)')

    # Design
    parser.add_argument('--ratio', type=float, default=1.0,
                        help='Treatment/Control size ratio (default: 1.0)')
    parser.add_argument('--n_controls', type=int, default=1,
                        help='Number of control groups (default: 1)')
    parser.add_argument('--n_treatments', type=int, default=1,
                        help='Number of treatment groups (default: 1)')
    parser.add_argument('--weights', type=str,
                        help='Traffic weights (e.g., "50,50" or "20 40 40")')

    # Corrections
    parser.add_argument('--n_comparisons', type=int,
                        help='Number of comparisons (default: n_controls * n_treatments)')
    parser.add_argument('--correction', choices=['bonferroni', 'sidak'],
                        help='Multiple comparison correction method')

    args = parser.parse_args()

    # Interactive mode
    if args.interactive or (args.baseline is None and args.mde is None):
        run_interactive()
        return

    # Validate required args for CLI mode
    if args.baseline is None or args.mde is None:
        parser.error("--baseline and --mde are required (or use --interactive)")

    # Parse weights if provided
    weights = None
    if args.weights:
        try:
            parts = args.weights.replace(',', ' ').split()
            weights = [float(x) for x in parts]
        except ValueError:
            parser.error(f"Invalid weights format: {args.weights}")

    # Calculate
    try:
        result = calculate_sample_size(
            baseline=args.baseline,
            mde=args.mde,
            power=args.power,
            alpha=args.alpha,
            mde_type=args.mde_type,
            ratio=args.ratio,
            metric_type=args.metric_type,
            std_dev=args.std_dev,
            std_dev_2=args.std_dev_2,
            test_type=args.test_type,
            n_comparisons=args.n_comparisons,
            correction=args.correction,
            n_controls=args.n_controls,
            n_treatments=args.n_treatments,
            sides=args.sides,
            weights=weights,
        )
        print_report(result)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
