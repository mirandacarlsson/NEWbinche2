"""
Unit tests for weighted_calculations.py (SaddleSum algorithm).

Tests verify:
1. Exact empirical p-values for num_hits=1
2. Saddlepoint approximation for num_hits>1
3. Zero-weight handling
4. Numerical edge cases
5. Parameter consistency
"""
# deptry: ignore=DEP004

import math

import numpy as np
import pytest  # type: ignore[import-untyped]

from calculations.weighted_calculations import (
    _SaddleSum,
    auto_scale_weights,
)


class TestSaddleSumBasic:
    """Test basic SaddleSum functionality."""

    def test_init_stores_background_info(self):
        """Verify __init__ correctly computes background statistics."""
        weights = np.array([0.5, 1.0, 1.5, 0.0, 2.0])
        saddler = _SaddleSum(weights)

        # Verify total count includes zeros
        assert saddler._N == 5
        # Verify mean is computed over ALL weights
        assert saddler._mean == pytest.approx(1.0)  # (0.5+1+1.5+0+2)/5
        # Verify max is from all weights
        assert saddler._wmax == 2.0
        # Verify non-zero weights are separated
        assert saddler._weights.size == 4  # Excludes one zero
        assert saddler._n_zeros == 1

    def test_init_all_zeros(self):
        """Edge case: all zero weights."""
        weights = np.array([0.0, 0.0, 0.0])
        saddler = _SaddleSum(weights)

        assert saddler._N == 3
        assert saddler._mean == 0.0
        assert saddler._wmax == 0.0
        assert saddler._weights.size == 0
        assert saddler._n_zeros == 3

    def test_init_no_zeros(self):
        """Edge case: no zero weights."""
        weights = np.array([0.5, 1.0, 1.5, 2.0])
        saddler = _SaddleSum(weights)

        assert saddler._N == 4
        assert saddler._n_zeros == 0
        assert saddler._weights.size == 4


class TestExactSingletonPValue:
    """Test _exact_singleton_right_tail for num_hits=1 case."""

    def test_singleton_simple_case(self):
        """
        Simple example: background = [0, 0, 1, 2, 3]
        Query: score=2, num_hits=1
        Expected: P(W >= 2) = 2/5 = 0.4
          Weights >= 2: {2, 3} = 2 leaves
        """
        weights = np.array([0.0, 0.0, 1.0, 2.0, 3.0])
        saddler = _SaddleSum(weights)

        p_value = saddler.pvalue(2.0, 1)
        # Should be empirical: count(w >= 2) / N = 2/5 = 0.4
        assert p_value == pytest.approx(0.4, abs=1e-10)

    def test_singleton_all_hits(self):
        """
        Background = [1, 2, 3]
        Query: score=1, num_hits=1
        Expected: P(W >= 1) = 3/3 = 1.0
        """
        weights = np.array([1.0, 2.0, 3.0])
        saddler = _SaddleSum(weights)

        p_value = saddler.pvalue(1.0, 1)
        assert p_value == pytest.approx(1.0, abs=1e-10)

    def test_singleton_no_hits(self):
        """
        Background = [1, 2, 3]
        Query: score=3.5, num_hits=1
        Expected: P(W >= 3.5) = 0/3, but bounded by min_pval = 1/3
        """
        weights = np.array([1.0, 2.0, 3.0])
        saddler = _SaddleSum(weights)

        p_value = saddler.pvalue(3.5, 1)
        # Should be min(0, 1/3) = 1/3 (minimum p-value)
        assert p_value == pytest.approx(1.0 / 3.0, abs=1e-10)

    def test_singleton_with_zeros_score_positive(self):
        """
        Background = [0, 0, 1, 2]
        Query: score=1, num_hits=1
        Expected: P(W >= 1) = count(w >= 1) / 4 = 2/4 = 0.5
          (zeros don't count since 0 < 1)
        """
        weights = np.array([0.0, 0.0, 1.0, 2.0])
        saddler = _SaddleSum(weights)

        p_value = saddler.pvalue(1.0, 1)
        assert p_value == pytest.approx(0.5, abs=1e-10)

    def test_singleton_with_zeros_score_nonpositive(self):
        """
        Background = [0, 0, 1, 2]
        Query: score=0, num_hits=1
        Expected: P(W >= 0) = count(w >= 0) / 4 = 4/4 = 1.0
          (all weights, including zeros, satisfy >= 0)
        """
        weights = np.array([0.0, 0.0, 1.0, 2.0])
        saddler = _SaddleSum(weights)

        p_value = saddler.pvalue(0.0, 1)
        assert p_value == pytest.approx(1.0, abs=1e-10)


class TestZeroWeightHandling:
    """Verify correct treatment of zero-weight leaves."""

    def test_mathematical_equivalence_with_zeros(self):
        """
        Verify that [0, 1, 2] and [1, 2] produce consistent relative p-values.

        The absolute p-value will differ (N=3 vs N=2), but the relative ranking
        should be preserved.
        """
        weights_with_zeros = np.array([0.0, 1.0, 2.0])
        weights_no_zeros = np.array([1.0, 2.0])

        saddler_with = _SaddleSum(weights_with_zeros)
        saddler_without = _SaddleSum(weights_no_zeros)

        # For num_hits=1, test several scores
        test_scores = [0.5, 1.0, 1.5, 2.0, 2.5]

        for score in test_scores:
            p_with = saddler_with.pvalue(score, 1)
            p_without = saddler_without.pvalue(score, 1)

            # Both should be valid probabilities
            assert 0 <= p_with <= 1
            assert 0 <= p_without <= 1

            # For score > 0, the relative order should be preserved
            # (since zero-weights contribute equally to numerator and denominator)
            if score > 0:
                # p_with should be <= p_without (more conservative)
                assert p_with <= p_without + 1e-10


class TestAutoScaleWeights:
    """Test weight scaling helper."""

    def test_scale_up_small_weights(self):
        """Weights below target max should be scaled up."""
        weights = {"a": 0.1, "b": 0.2, "c": 0.3}
        scaled = auto_scale_weights(weights, target_max=1000.0)

        # max(|weights|) = 0.3, so scale = 1000/0.3 ≈ 3333.33
        assert scaled["a"] == pytest.approx(0.1 * 1000 / 0.3)
        assert scaled["b"] == pytest.approx(0.2 * 1000 / 0.3)
        assert scaled["c"] == pytest.approx(0.3 * 1000 / 0.3)
        assert max(scaled.values()) == pytest.approx(1000.0)

    def test_no_scale_large_weights(self):
        """Weights already >= target max should not be scaled."""
        weights = {"a": 1000.0, "b": 2000.0}
        scaled = auto_scale_weights(weights, target_max=1000.0)

        assert scaled == weights

    def test_scale_zero_weights_dict(self):
        """Empty dict should return empty dict."""
        weights = {}
        scaled = auto_scale_weights(weights, target_max=1000.0)

        assert scaled == {}


class TestNumericalStability:
    """Test edge cases and numerical stability."""

    def test_large_background(self):
        """Large background should not cause overflow."""
        np.random.seed(42)
        weights = np.random.exponential(1.0, 10000)

        saddler = _SaddleSum(weights)

        # Should handle without exception
        assert saddler._N == 10000
        assert saddler._wmax > 0

        # Test a query
        p_value = saddler.pvalue(weights.mean(), 100)
        assert 0 <= p_value <= 1
        assert math.isfinite(p_value)

    def test_score_way_above_max(self):
        """Score much larger than any weight should have valid p-value."""
        weights = np.array([1.0, 2.0, 3.0])
        saddler = _SaddleSum(weights)

        # For m=1, should be empirical (0/3 = min_pval=1/3, no weight >=1000)
        p_value_m1 = saddler.pvalue(1000.0, 1)
        assert p_value_m1 == pytest.approx(1.0 / 3.0)

        # For m>1 with extreme score, should return valid p-value
        # (saddlepoint behavior at extremes differs from m=1 empirical)
        p_value_m10 = saddler.pvalue(1000.0, 10)
        assert 0 <= p_value_m10 <= 1

    def test_mean_boundary(self):
        """Score at or below mean should give p=1.0."""
        weights = np.array([1.0, 2.0, 3.0, 4.0])  # mean = 2.5
        saddler = _SaddleSum(weights)

        # Below mean
        p_below = saddler.pvalue(2.4, 10)
        assert p_below == 1.0

        # At mean (approximately)
        p_at = saddler.pvalue(2.5, 10)
        assert p_at == 1.0


class TestParameterConsistency:
    """Test that parameter handling is consistent with Fisher pipeline."""

    def test_saddler_reproducibility(self):
        """Same background should give identical results on repeat queries."""
        weights = np.array([0.5, 1.0, 1.5, 2.0, 0.0])
        saddler = _SaddleSum(weights)

        # Query twice
        p_first = saddler.pvalue(1.0, 5)
        p_second = saddler.pvalue(1.0, 5)

        assert p_first == p_second

    def test_fallback_logging(self):
        """Fallback logger should initialize without error."""
        weights = np.array([1.0, 2.0, 3.0])
        saddler = _SaddleSum(weights)

        # Query that might trigger fallback
        saddler.pvalue(10.0, 1)

        # Should not raise
        saddler.log_fallback_summary()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
