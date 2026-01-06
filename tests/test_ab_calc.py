"""Tests for A/B test sample size calculator."""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ab_test_calc import calculate_sample_size, ValidationError


class TestBasicProportions:
    """Tests for basic proportion (conversion rate) calculations."""

    def test_standard_ab_test(self):
        """
        Baseline 10%, MDE 2pp absolute, Power 0.8, Alpha 0.05.
        Expected: 3,623 per variant (matches Evan Miller's calculator).
        """
        result = calculate_sample_size(
            baseline=0.10,
            mde=0.02,
            mde_type='absolute',
            power=0.8,
            alpha=0.05,
            metric_type='proportion',
            test_type='z',
        )
        assert result['sample_size_per_variant'] == 3623

    def test_relative_mde(self):
        """Test relative MDE calculation (20% lift on 10% baseline = 12%)."""
        result = calculate_sample_size(
            baseline=0.10,
            mde=0.20,  # 20% relative lift
            mde_type='relative',
        )
        # 20% of 0.10 = 0.02 absolute, same as test above
        assert result['sample_size_per_variant'] == 3623

    def test_one_sided_vs_two_sided(self):
        """One-sided test should require fewer samples."""
        two_sided = calculate_sample_size(
            baseline=0.5,
            mde=0.05,
            mde_type='absolute',
            sides=2,
        )
        one_sided = calculate_sample_size(
            baseline=0.5,
            mde=0.05,
            mde_type='absolute',
            sides=1,
        )
        assert one_sided['sample_size_per_variant'] < two_sided['sample_size_per_variant']

    def test_higher_power_needs_more_samples(self):
        """Higher power requires more samples."""
        power_80 = calculate_sample_size(baseline=0.10, mde=0.02)
        power_90 = calculate_sample_size(baseline=0.10, mde=0.02, power=0.9)
        assert power_90['sample_size_per_variant'] > power_80['sample_size_per_variant']

    def test_lower_alpha_needs_more_samples(self):
        """Lower alpha (stricter) requires more samples."""
        alpha_05 = calculate_sample_size(baseline=0.10, mde=0.02, alpha=0.05)
        alpha_01 = calculate_sample_size(baseline=0.10, mde=0.02, alpha=0.01)
        assert alpha_01['sample_size_per_variant'] > alpha_05['sample_size_per_variant']


class TestMeans:
    """Tests for mean (continuous metric) calculations."""

    def test_basic_mean_z_test(self):
        """
        Baseline 100, MDE 5, SD 20.
        Formula: 2 * 20^2 * (1.96+0.84)^2 / 5^2 = 251.16 -> 252
        """
        result = calculate_sample_size(
            baseline=100,
            mde=5,
            mde_type='absolute',
            std_dev=20,
            metric_type='mean',
            test_type='z',
        )
        assert result['sample_size_per_variant'] == 252

    def test_t_test_more_conservative(self):
        """T-test should require slightly more samples than Z-test."""
        z_result = calculate_sample_size(
            baseline=100, mde=5, std_dev=20,
            metric_type='mean', test_type='z', mde_type='absolute',
        )
        t_result = calculate_sample_size(
            baseline=100, mde=5, std_dev=20,
            metric_type='mean', test_type='t', mde_type='absolute',
        )
        assert t_result['sample_size_per_variant'] > z_result['sample_size_per_variant']
        # Difference should be small for large N
        assert t_result['sample_size_per_variant'] - z_result['sample_size_per_variant'] < 10

    def test_welch_t_test_unequal_variance(self):
        """Higher treatment variance should increase sample size."""
        equal_var = calculate_sample_size(
            baseline=100, mde=5, mde_type='absolute',
            metric_type='mean', std_dev=20, test_type='t',
        )
        unequal_var = calculate_sample_size(
            baseline=100, mde=5, mde_type='absolute',
            metric_type='mean', std_dev=20, std_dev_2=30, test_type='t',
        )
        assert unequal_var['sample_size_per_variant'] > equal_var['sample_size_per_variant']


class TestCorrections:
    """Tests for multiple comparison corrections."""

    def test_bonferroni_halves_alpha(self):
        """Bonferroni with 2 comparisons should halve alpha."""
        result = calculate_sample_size(
            baseline=0.5, mde=0.05, mde_type='absolute',
            n_comparisons=2, correction='bonferroni',
        )
        assert result['alpha_corrected'] == pytest.approx(0.05 / 2)

    def test_bonferroni_increases_sample_size(self):
        """Correction should increase required sample size."""
        base = calculate_sample_size(baseline=0.5, mde=0.05, mde_type='absolute')
        corrected = calculate_sample_size(
            baseline=0.5, mde=0.05, mde_type='absolute',
            n_comparisons=2, correction='bonferroni',
        )
        assert corrected['sample_size_per_variant'] > base['sample_size_per_variant']

    def test_sidak_less_conservative_than_bonferroni(self):
        """Sidak correction is slightly less conservative."""
        sidak = calculate_sample_size(
            baseline=0.5, mde=0.05, mde_type='absolute',
            n_comparisons=3, correction='sidak',
        )
        bonf = calculate_sample_size(
            baseline=0.5, mde=0.05, mde_type='absolute',
            n_comparisons=3, correction='bonferroni',
        )
        assert sidak['sample_size_per_variant'] <= bonf['sample_size_per_variant']


class TestAdvancedDesigns:
    """Tests for multi-group and weighted designs."""

    def test_multiple_groups_total(self):
        """Total = N_per_variant * (n_controls + n_treatments)."""
        result = calculate_sample_size(
            baseline=0.5, mde=0.05, mde_type='absolute',
            n_controls=2, n_treatments=3,
        )
        expected_total = result['sample_size_per_variant'] * 5
        assert result['total_sample_size'] == expected_total

    def test_auto_comparisons_default(self):
        """Default n_comparisons = n_controls * n_treatments."""
        result = calculate_sample_size(
            baseline=0.5, mde=0.05, mde_type='absolute',
            n_controls=2, n_treatments=3, correction='bonferroni',
        )
        # 2 * 3 = 6 comparisons
        assert result['alpha_corrected'] == pytest.approx(0.05 / 6)

    def test_unequal_ratio(self):
        """Treatment size should scale with ratio."""
        result = calculate_sample_size(
            baseline=0.5, mde=0.05, mde_type='absolute',
            ratio=2.0,
        )
        assert result['sample_size_treatment'] == result['sample_size_control'] * 2

    def test_weighted_design_finds_bottleneck(self):
        """Weighted design should identify bottleneck pair."""
        result = calculate_sample_size(
            baseline=0.2,
            mde=0.03,
            mde_type='absolute',
            n_controls=2,
            n_treatments=3,
            weights=[35, 15, 20, 18, 12],
            correction='bonferroni',
        )
        assert 'bottleneck_pair' in result
        assert result['total_sample_size'] > 30000

    def test_weighted_total_respects_shares(self):
        """Group sizes should match weight proportions."""
        result = calculate_sample_size(
            baseline=0.2,
            mde=0.03,
            mde_type='absolute',
            n_controls=2,
            n_treatments=3,
            weights=[35, 15, 20, 18, 12],
            correction='bonferroni',
        )
        total = result['total_sample_size']
        # C1 should be 35% of total
        expected_c1 = total * 0.35
        expected_c2 = total * 0.15
        avg_control = (expected_c1 + expected_c2) / 2
        assert result['sample_size_control'] == pytest.approx(avg_control, rel=0.01)


class TestChiSquare:
    """Tests for chi-square test type."""

    def test_chi2_matches_z_test(self):
        """Chi-square should give same result as Z-test for proportions."""
        z_result = calculate_sample_size(
            baseline=0.10, mde=0.02, mde_type='absolute',
            metric_type='proportion', test_type='z',
        )
        chi2_result = calculate_sample_size(
            baseline=0.10, mde=0.02, mde_type='absolute',
            metric_type='proportion', test_type='chi2',
        )
        assert z_result['sample_size_per_variant'] == chi2_result['sample_size_per_variant']

    def test_chi2_rejects_means(self):
        """Chi-square should raise error for means."""
        with pytest.raises(ValidationError, match="Chi-square"):
            calculate_sample_size(
                baseline=100, mde=5, mde_type='absolute',
                std_dev=20, metric_type='mean', test_type='chi2',
            )


class TestValidation:
    """Tests for input validation."""

    def test_invalid_alpha(self):
        """Alpha must be between 0 and 1."""
        with pytest.raises(ValidationError, match="alpha"):
            calculate_sample_size(baseline=0.1, mde=0.02, alpha=1.5)

        with pytest.raises(ValidationError, match="alpha"):
            calculate_sample_size(baseline=0.1, mde=0.02, alpha=0)

    def test_invalid_power(self):
        """Power must be between 0 and 1."""
        with pytest.raises(ValidationError, match="power"):
            calculate_sample_size(baseline=0.1, mde=0.02, power=1.0)

        with pytest.raises(ValidationError, match="power"):
            calculate_sample_size(baseline=0.1, mde=0.02, power=0)

    def test_invalid_baseline_for_proportion(self):
        """Proportion baseline must be between 0 and 1."""
        with pytest.raises(ValidationError, match="baseline"):
            calculate_sample_size(baseline=1.5, mde=0.02, metric_type='proportion')

    def test_invalid_sides(self):
        """Sides must be 1 or 2."""
        with pytest.raises(ValidationError, match="sides"):
            calculate_sample_size(baseline=0.1, mde=0.02, sides=3)

    def test_target_out_of_bounds(self):
        """Target rate must stay in (0, 1) for proportions."""
        with pytest.raises(ValidationError, match="Target rate"):
            calculate_sample_size(baseline=0.95, mde=0.10, mde_type='absolute')

    def test_missing_std_dev_for_means(self):
        """std_dev required for means."""
        with pytest.raises(ValidationError, match="std_dev"):
            calculate_sample_size(baseline=100, mde=5, metric_type='mean')

    def test_negative_std_dev(self):
        """std_dev must be positive."""
        with pytest.raises(ValidationError, match="std_dev"):
            calculate_sample_size(
                baseline=100, mde=5, metric_type='mean', std_dev=-10,
            )

    def test_invalid_ratio(self):
        """Ratio must be positive."""
        with pytest.raises(ValidationError, match="ratio"):
            calculate_sample_size(baseline=0.1, mde=0.02, ratio=0)

    def test_weights_length_mismatch(self):
        """Weights length must match group count."""
        with pytest.raises(ValidationError, match="weights length"):
            calculate_sample_size(
                baseline=0.1, mde=0.02,
                n_controls=2, n_treatments=2,
                weights=[50, 50],  # Should be 4 weights
            )

    def test_zero_mde(self):
        """MDE cannot be zero."""
        with pytest.raises(ValidationError, match="mde"):
            calculate_sample_size(baseline=0.1, mde=0)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_high_power(self):
        """High power (99%) should work."""
        result = calculate_sample_size(baseline=0.1, mde=0.02, power=0.99)
        assert result['sample_size_per_variant'] > 0

    def test_very_small_mde(self):
        """Small MDE requires many samples."""
        result = calculate_sample_size(baseline=0.1, mde=0.001, mde_type='absolute')
        assert result['sample_size_per_variant'] > 100000

    def test_extreme_ratio(self):
        """Extreme ratio should work."""
        result = calculate_sample_size(baseline=0.1, mde=0.02, ratio=10.0)
        assert result['sample_size_treatment'] == result['sample_size_control'] * 10

    def test_small_baseline(self):
        """Small baseline (rare events) should work."""
        result = calculate_sample_size(baseline=0.01, mde=0.005, mde_type='absolute')
        assert result['sample_size_per_variant'] > 0

    def test_large_baseline(self):
        """High baseline should work."""
        result = calculate_sample_size(baseline=0.95, mde=-0.05, mde_type='absolute')
        assert result['sample_size_per_variant'] > 0


class TestResultStructure:
    """Tests for result dictionary structure."""

    def test_required_keys_present(self):
        """All required keys should be in result."""
        result = calculate_sample_size(baseline=0.1, mde=0.02)

        required_keys = [
            'sample_size_per_variant',
            'sample_size_control',
            'sample_size_treatment',
            'total_sample_size',
            'baseline_value',
            'absolute_effect',
            'alpha_raw',
            'alpha_corrected',
            'power',
            'metric_type',
            'test_type',
            'sides',
            'ratio',
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_weighted_has_bottleneck_info(self):
        """Weighted results should include bottleneck info."""
        result = calculate_sample_size(
            baseline=0.2, mde=0.03,
            n_controls=1, n_treatments=2,
            weights=[50, 25, 25],
        )
        assert 'bottleneck_pair' in result
        assert 'bottleneck_ratio' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
