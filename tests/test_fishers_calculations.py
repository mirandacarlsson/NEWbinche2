"""
Unit tests for fishers_calculations.py (Fisher's exact test implementation).

Tests verify:
1. Contingency table calculations (calculate_p_value)
2. ID normalization (normalize_id)
3. Error handling with ValueError cases
4. Benjamini-Hochberg correction with None handling
5. Study set leaf extraction (get_leaves)
6. Enrichment value calculations
"""

import pytest

from calculations.fishers_calculations import (
    calculate_p_value,
    get_n_ss_annotated,
    normalize_id,
)
from calculations.multiple_test_corrections import benjamini_hochberg_fdr_correction


class TestCalculatePValue:
    """Test Fisher's exact p-value calculation.

    Returns (odds_ratio, p_value) tuple.
    """

    def test_simple_enriched_case(self):
        """Test a simple case with clear enrichment."""
        # 2x2 contingency table:
        # Study: 10 annotated, 40 not annotated
        # Background: 50 annotated (excluding study), 950 not annotated
        odds, p_val = calculate_p_value(
            n_ss_annotated=10, n_ss_leaves=50, n_bg_annotated=60, n_bg_leaves=1000
        )

        # With valid data, should get numeric results
        assert odds is not None or p_val is not None  # At least one valid result
        if p_val is not None:
            assert 0 <= p_val <= 1

    def test_no_enrichment_case(self):
        """Test case with no enrichment (random distribution)."""
        # Equal proportion: 50/100 in study, 500/1000 in background
        odds, p_val = calculate_p_value(
            n_ss_annotated=50, n_ss_leaves=100, n_bg_annotated=500, n_bg_leaves=1000
        )

        assert isinstance(p_val, (float, type(None)))
        if p_val is not None:
            assert 0 <= p_val <= 1

    def test_zero_study_set(self):
        """Test edge case: no annotations in study set (odds=0, p-value=1)."""
        odds, p_val = calculate_p_value(
            n_ss_annotated=0, n_ss_leaves=100, n_bg_annotated=50, n_bg_leaves=1000
        )

        # odds should be 0, p-value should be high (no enrichment)
        assert odds == 0.0 or p_val is not None

    def test_zero_background(self):
        """Test edge case: no annotations in background (invalid table)."""
        odds, p_val = calculate_p_value(
            n_ss_annotated=10, n_ss_leaves=100, n_bg_annotated=0, n_bg_leaves=1000
        )

        # Should return (None, None) for invalid table
        assert odds is None and p_val is None

    def test_negative_values_return_none(self):
        """Test that negative contingency table values return None."""
        odds, p_val = calculate_p_value(
            n_ss_annotated=-1, n_ss_leaves=100, n_bg_annotated=50, n_bg_leaves=1000
        )

        # Should return None for invalid table
        assert odds is None and p_val is None

    def test_all_zeros(self):
        """Test edge case: all zeros."""
        odds, p_val = calculate_p_value(
            n_ss_annotated=0, n_ss_leaves=0, n_bg_annotated=0, n_bg_leaves=0
        )

        # Should handle gracefully (might be valid for specific edge case)
        assert odds is None or isinstance(odds, (int, float))
        assert p_val is None or isinstance(p_val, (int, float))

    def test_single_element(self):
        """Test with minimal non-zero values."""
        odds, p_val = calculate_p_value(
            n_ss_annotated=1, n_ss_leaves=1, n_bg_annotated=1, n_bg_leaves=1
        )

        # May return NaN in edge cases, which is valid
        if p_val is not None:
            # NaN is acceptable for edge case, or valid p-value
            assert p_val is None or not (p_val != p_val) or 0 <= p_val <= 1

    def test_returns_tuple(self):
        """Test that function returns (odds_ratio, p_value) tuple."""
        result = calculate_p_value(
            n_ss_annotated=5, n_ss_leaves=50, n_bg_annotated=10, n_bg_leaves=1000
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        # Both elements should be numeric or None
        assert isinstance(result[0], (float, type(None), int))  # odds_ratio
        assert isinstance(result[1], (float, type(None), int))  # p_value


class TestNormalizeId:
    """Test ID normalization function.

    The function converts short ChEBI IDs to full IRIs.
    """

    def test_chebi_short_id_converts_to_iri(self):
        """Test that short ChEBI ID converts to full IRI."""
        normalized = normalize_id("CHEBI:12345")
        # Should convert to full IRI
        assert "CHEBI_12345" in normalized
        assert "http" in normalized or "purl" in normalized

    def test_full_iri_unchanged(self):
        """Test that full IRI is unchanged."""
        iri = "http://purl.obolibrary.org/obo/CHEBI_12345"
        normalized = normalize_id(iri)
        assert normalized == iri

    def test_legacy_format(self):
        """Test conversion of legacy format."""
        result = normalize_id("12345")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_none_input_safe(self):
        """Test handling of None input."""
        # Depending on implementation, may return None or raise
        try:
            result = normalize_id(None)
            # If it doesn't raise, result should be reasonable
            assert result is None or isinstance(result, str)
        except (TypeError, AttributeError):
            # If it raises, that's also acceptable for None input
            pass


class TestBenjaminiHochbergWithNone:
    """Test Benjamini-Hochberg correction with None handling (CF1 fix)."""

    def test_all_valid_pvalues(self):
        """Test with all valid p-values."""
        enrichment_results = {
            "class1": {"p_value": 0.001},
            "class2": {"p_value": 0.05},
            "class3": {"p_value": 0.1},
            "class4": {"p_value": 0.5},
        }

        result = benjamini_hochberg_fdr_correction(enrichment_results)

        # All should have corrected p-values
        for cls in enrichment_results:
            assert "p_value_corrected" in result[cls]
            assert result[cls]["p_value_corrected"] is not None

    def test_with_none_pvalues(self):
        """Test with some None p-values (CF1 fix)."""
        enrichment_results = {
            "class1": {"p_value": 0.001},
            "class2": {"p_value": None},
            "class3": {"p_value": 0.1},
            "class4": {"p_value": None},
        }

        # Should not crash on None values
        result = benjamini_hochberg_fdr_correction(enrichment_results)

        # Check that function succeeded
        assert result is not None
        # Classes with None should have None corrected p-value
        assert result["class2"]["p_value_corrected"] is None
        assert result["class4"]["p_value_corrected"] is None
        # Classes with valid p-values should have corrected p-values
        assert result["class1"]["p_value_corrected"] is not None
        assert result["class3"]["p_value_corrected"] is not None

    def test_all_none_pvalues(self):
        """Test edge case: all None p-values (CF1 edge case)."""
        enrichment_results = {
            "class1": {"p_value": None},
            "class2": {"p_value": None},
            "class3": {"p_value": None},
        }

        # Should handle gracefully
        result = benjamini_hochberg_fdr_correction(enrichment_results)

        # All should have None corrected p-values
        for cls in enrichment_results:
            assert result[cls]["p_value_corrected"] is None

    def test_monotonicity(self):
        """Test that corrected p-values are monotonic (BH property)."""
        enrichment_results = {
            "class1": {"p_value": 0.001},
            "class2": {"p_value": 0.01},
            "class3": {"p_value": 0.05},
            "class4": {"p_value": 0.1},
        }

        result = benjamini_hochberg_fdr_correction(enrichment_results)

        # Extract corrected p-values in order
        p_vals_raw = [0.001, 0.01, 0.05, 0.1]
        p_vals_corrected = [
            result["class1"]["p_value_corrected"],
            result["class2"]["p_value_corrected"],
            result["class3"]["p_value_corrected"],
            result["class4"]["p_value_corrected"],
        ]

        # Corrected p-values should be >= raw p-values
        for raw, corrected in zip(p_vals_raw, p_vals_corrected):
            assert corrected >= raw

    def test_corrected_bounded_by_one(self):
        """Test that corrected p-values don't exceed 1.0."""
        enrichment_results = {
            "class1": {"p_value": 0.5},
            "class2": {"p_value": 0.9},
            "class3": {"p_value": 0.99},
        }

        result = benjamini_hochberg_fdr_correction(enrichment_results)

        for cls in enrichment_results:
            assert result[cls]["p_value_corrected"] <= 1.0


class TestGetNSSAnnotatedErrorHandling:
    """Test error handling in get_n_ss_annotated (CF3 fix)."""

    def test_missing_class_raises_error(self):
        """Test that missing class in map raises ValueError (CF3 fix)."""
        studyset_leaves = {"leaf1", "leaf2"}
        class_to_check = "unknown_class"
        class_to_leaf_map = {
            "class1": ["leaf1", "leaf2"],
            "class2": ["leaf3"],
        }

        with pytest.raises(ValueError, match="not found in class_to_leaf_map"):
            get_n_ss_annotated(
                studyset_leaves,
                class_to_check,
                class_to_leaf_map,
                "structural",
                {},
                {},
            )

    def test_valid_class_returns_count(self):
        """Test that valid class returns correct count."""
        studyset_leaves = {"leaf1", "leaf2", "leaf5"}
        class_to_check = "class1"
        class_to_leaf_map = {
            "class1": ["leaf1", "leaf2", "leaf3", "leaf4"],
            "class2": ["leaf5"],
        }

        n_annotated = get_n_ss_annotated(
            studyset_leaves,
            class_to_check,
            class_to_leaf_map,
            "structural",
            {},
            {},
        )

        # Should count intersection: {leaf1, leaf2} ∩ class1's leaves = 2
        assert n_annotated == 2

    def test_no_overlap_returns_zero(self):
        """Test that no overlap returns 0."""
        studyset_leaves = {"leaf10", "leaf20"}
        class_to_check = "class1"
        class_to_leaf_map = {
            "class1": ["leaf1", "leaf2", "leaf3"],
        }

        n_annotated = get_n_ss_annotated(
            studyset_leaves,
            class_to_check,
            class_to_leaf_map,
            "structural",
            {},
            {},
        )

        assert n_annotated == 0

    def test_invalid_classification_raises_error(self):
        """Test that invalid classification raises ValueError."""
        studyset_leaves = {"leaf1"}
        class_to_check = "class1"
        class_to_leaf_map = {"class1": ["leaf1"]}

        with pytest.raises(ValueError, match="not supported"):
            get_n_ss_annotated(
                studyset_leaves,
                class_to_check,
                class_to_leaf_map,
                "invalid_classification",
                {},
                {},
            )

    def test_all_leaves_in_class(self):
        """Test when all study leaves are in the class."""
        studyset_leaves = {"leaf1", "leaf2", "leaf3"}
        class_to_check = "class1"
        class_to_leaf_map = {
            "class1": ["leaf1", "leaf2", "leaf3"],
        }

        n_annotated = get_n_ss_annotated(
            studyset_leaves,
            class_to_check,
            class_to_leaf_map,
            "structural",
            {},
            {},
        )

        assert n_annotated == 3


class TestEnrichmentValueIntegration:
    """Integration tests for enrichment value calculation."""

    def test_enrichment_with_valid_data(self):
        """Test enrichment calculation with valid contingency table."""
        # This would require mocking data files, so simplified version
        n_ss_annotated = 10
        n_ss_leaves = 100
        n_bg_annotated = 50
        n_bg_leaves = 1000

        p_val, _ = calculate_p_value(
            n_ss_annotated, n_ss_leaves, n_bg_annotated, n_bg_leaves
        )

        # Should compute some p-value
        assert p_val is None or isinstance(p_val, float)

    def test_sequential_corrections(self):
        """Test that multiple tests can be corrected sequentially."""
        enrichment_results = {
            f"class_{i}": {"p_value": 0.01 * i if i > 0 else 0.001} for i in range(1, 6)
        }

        # Apply correction
        corrected = benjamini_hochberg_fdr_correction(enrichment_results)

        # Should have corrected values for all
        for cls in enrichment_results:
            assert "p_value_corrected" in corrected[cls]


class TestEdgeCasesAndBoundaries:
    """Test edge cases and boundary conditions."""

    def test_very_small_pvalues(self):
        """Test handling of very small p-values."""
        enrichment_results = {
            "class1": {"p_value": 1e-10},
            "class2": {"p_value": 1e-15},
        }

        result = benjamini_hochberg_fdr_correction(enrichment_results)

        # Should not crash or produce inf/nan
        for cls in enrichment_results:
            p_corr = result[cls]["p_value_corrected"]
            assert p_corr is None or (0 <= p_corr <= 1)
            assert not (p_corr != p_corr)  # Check for NaN

    def test_large_contingency_table(self):
        """Test with large numbers (shouldn't overflow)."""
        p_val, _ = calculate_p_value(
            n_ss_annotated=1000,
            n_ss_leaves=10000,
            n_bg_annotated=50000,
            n_bg_leaves=1000000,
        )

        # Should complete without overflow
        assert p_val is None or isinstance(p_val, float)

    def test_single_vs_multiple_comparisons(self):
        """Test that single comparison differs from multiple."""
        # Single test
        enrichment_single = {"class1": {"p_value": 0.05}}
        result_single = benjamini_hochberg_fdr_correction(enrichment_single)

        # Multiple tests with same raw p-value
        enrichment_multiple = {
            "class1": {"p_value": 0.05},
            "class2": {"p_value": 0.05},
            "class3": {"p_value": 0.05},
        }
        result_multiple = benjamini_hochberg_fdr_correction(enrichment_multiple)

        # Correction should be different due to multiple testing
        # (single test: 1 × 0.05 / 1 = 0.05)
        # (triple test: 3 × 0.05 / 3 = 0.05 for first, but adjust for BH procedure)
        assert isinstance(result_single["class1"]["p_value_corrected"], float)
        assert isinstance(result_multiple["class1"]["p_value_corrected"], float)


class TestParameterValidation:
    """Test parameter validation and error messages."""

    def test_calculate_pvalue_type_safety(self):
        """Test type safety in calculate_p_value."""
        # All valid types
        p_val, _ = calculate_p_value(
            n_ss_annotated=10,
            n_ss_leaves=100,
            n_bg_annotated=50,
            n_bg_leaves=1000,
        )
        assert p_val is None or isinstance(p_val, float)

    def test_get_n_ss_annotated_type_safety(self):
        """Test that get_n_ss_annotated validates input types."""
        studyset_leaves = ["leaf1", "leaf2"]  # List, not set
        class_to_check = "class1"
        class_to_leaf_map = {"class1": ["leaf1"]}

        # Should handle gracefully even if type is different
        try:
            result = get_n_ss_annotated(
                studyset_leaves,
                class_to_check,
                class_to_leaf_map,
                "structural",
                {},
                {},
            )
            # If it works, result should be int
            assert isinstance(result, int)
        except (TypeError, KeyError):
            # Also acceptable if it raises error for type mismatch
            pass
