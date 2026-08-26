"""
Unit tests for pre_fishers_calculations.py.

Tests verify:
1. Structural leaf identification and filtering
2. Class-to-leaf mapping building
3. Leaf counting for classes and roles
4. Error handling and validation
5. Cache functionality
"""

import json
import tempfile
from pathlib import Path

import pytest

from chebin.calculations.pre_fishers_calculations import (
    build_class_to_leaf_map,
    count_removed_classes_for_class,
    count_removed_classes_for_roles,
    count_removed_leaves,
    get_structural_leaf_ids,
)


class TestGetStructuralLeafIds:
    """Test structural leaf identification."""

    def test_filter_structural_only(self):
        """Test that only 'structural' classification is included."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,Classification\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_1,structural\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_2,functional\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_3,structural\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_4,neither\n")
            csv_file = f.name

        try:
            result = get_structural_leaf_ids(csv_file)
            assert isinstance(result, set)
            # Should only have structural leaves
            assert len(result) == 2
            assert "http://purl.obolibrary.org/obo/CHEBI_1" in result
            assert "http://purl.obolibrary.org/obo/CHEBI_3" in result
            # Should exclude functional and neither
            assert "http://purl.obolibrary.org/obo/CHEBI_2" not in result
            assert "http://purl.obolibrary.org/obo/CHEBI_4" not in result
        finally:
            Path(csv_file).unlink()

    def test_empty_file(self):
        """Test with empty CSV."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,Classification\n")
            csv_file = f.name

        try:
            result = get_structural_leaf_ids(csv_file)
            assert isinstance(result, set)
            assert len(result) == 0
        finally:
            Path(csv_file).unlink()

    def test_all_structural(self):
        """Test with all structural leaves."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,Classification\n")
            for i in range(1, 6):
                f.write(f"http://purl.obolibrary.org/obo/CHEBI_{i},structural\n")
            csv_file = f.name

        try:
            result = get_structural_leaf_ids(csv_file)
            assert len(result) == 5
        finally:
            Path(csv_file).unlink()

    def test_caching(self):
        """Test that results are cached."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,Classification\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_1,structural\n")
            csv_file = f.name

        try:
            result1 = get_structural_leaf_ids(csv_file)
            result2 = get_structural_leaf_ids(csv_file)
            # Should be identical (cached)
            assert result1 is result2
        finally:
            Path(csv_file).unlink()

    def test_case_sensitivity(self):
        """Test that classification is case-sensitive."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,Classification\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_1,structural\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_2,Structural\n")  # Wrong case
            f.write("http://purl.obolibrary.org/obo/CHEBI_3,STRUCTURAL\n")  # Wrong case
            csv_file = f.name

        try:
            result = get_structural_leaf_ids(csv_file)
            # Only lowercase 'structural' should be included
            assert len(result) == 1
            assert "http://purl.obolibrary.org/obo/CHEBI_1" in result
        finally:
            Path(csv_file).unlink()


class TestCountRemovedLeaves:
    """Test counting removed leaves."""

    def test_count_leaves(self):
        """Test basic leaf counting."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,Classification\n")
            for i in range(1, 4):
                f.write(f"http://purl.obolibrary.org/obo/CHEBI_{i},structural\n")
            csv_file = f.name

        try:
            count = count_removed_leaves(csv_file)
            assert count == 3
        finally:
            Path(csv_file).unlink()

    def test_empty_count(self):
        """Test with no leaves."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,Classification\n")
            csv_file = f.name

        try:
            count = count_removed_leaves(csv_file)
            assert count == 0
        finally:
            Path(csv_file).unlink()


class TestBuildClassToLeafMap:
    """Test building class-to-leaf mapping."""

    def test_basic_map_building(self):
        """Test basic map construction from leaf-to-ancestors."""
        leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_10": [
                "http://purl.obolibrary.org/obo/CHEBI_1",
                "http://purl.obolibrary.org/obo/CHEBI_0",
            ],
            "http://purl.obolibrary.org/obo/CHEBI_11": [
                "http://purl.obolibrary.org/obo/CHEBI_1",
            ],
            "http://purl.obolibrary.org/obo/CHEBI_12": [
                "http://purl.obolibrary.org/obo/CHEBI_2",
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaf_map, f)
            leaf_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            build_class_to_leaf_map(leaf_file, output_file)

            # Verify output
            with open(output_file) as f:
                result = json.load(f)

            # CHEBI_1 should have both CHEBI_10 and CHEBI_11
            assert "http://purl.obolibrary.org/obo/CHEBI_1" in result
            leaves_1 = result["http://purl.obolibrary.org/obo/CHEBI_1"]
            assert "http://purl.obolibrary.org/obo/CHEBI_10" in leaves_1
            assert "http://purl.obolibrary.org/obo/CHEBI_11" in leaves_1
            assert len(leaves_1) == 2

            # CHEBI_2 should have only CHEBI_12
            assert "http://purl.obolibrary.org/obo/CHEBI_2" in result
            assert result["http://purl.obolibrary.org/obo/CHEBI_2"] == [
                "http://purl.obolibrary.org/obo/CHEBI_12",
            ]
        finally:
            Path(leaf_file).unlink()
            Path(output_file).unlink()

    def test_empty_map(self):
        """Test with empty leaf-to-ancestors."""
        leaf_map = {}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaf_map, f)
            leaf_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            build_class_to_leaf_map(leaf_file, output_file)

            with open(output_file) as f:
                result = json.load(f)

            assert result == {}
        finally:
            Path(leaf_file).unlink()
            Path(output_file).unlink()

    def test_multiple_leaves_same_ancestor(self):
        """Test multiple leaves with same ancestor."""
        leaf_map = {
            "leaf_A": ["ancestor_1"],
            "leaf_B": ["ancestor_1"],
            "leaf_C": ["ancestor_1"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaf_map, f)
            leaf_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            build_class_to_leaf_map(leaf_file, output_file)

            with open(output_file) as f:
                result = json.load(f)

            # ancestor_1 should have all three leaves
            assert len(result["ancestor_1"]) == 3
            assert set(result["ancestor_1"]) == {"leaf_A", "leaf_B", "leaf_C"}
        finally:
            Path(leaf_file).unlink()
            Path(output_file).unlink()


class TestCountRemovedClassesForClass:
    """Test counting leaf descendants for classes."""

    def test_valid_structural_class(self):
        """Test counting leaves for valid structural class."""
        class_to_leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_1": [
                "http://purl.obolibrary.org/obo/CHEBI_10",
                "http://purl.obolibrary.org/obo/CHEBI_11",
            ],
        }

        leaves, n_leaves = count_removed_classes_for_class(
            "http://purl.obolibrary.org/obo/CHEBI_1",
            class_to_leaf_map,
            "structural",
            {},
            {},
        )

        assert n_leaves == 2
        assert len(leaves) == 2
        assert "http://purl.obolibrary.org/obo/CHEBI_10" in leaves

    def test_missing_class_raises_error(self):
        """Test that missing class raises ValueError."""
        class_to_leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_1": [
                "http://purl.obolibrary.org/obo/CHEBI_10",
            ],
        }

        with pytest.raises(ValueError, match="not found in class_to_leaf_map"):
            count_removed_classes_for_class(
                "http://purl.obolibrary.org/obo/CHEBI_999",
                class_to_leaf_map,
                "structural",
                {},
                {},
            )

    def test_empty_leaves_raises_error(self):
        """Test that empty leaf list raises ValueError."""
        class_to_leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_1": [],
        }

        with pytest.raises(ValueError, match="has no leaf descendants"):
            count_removed_classes_for_class(
                "http://purl.obolibrary.org/obo/CHEBI_1",
                class_to_leaf_map,
                "structural",
                {},
                {},
            )

    def test_invalid_classification_raises_error(self):
        """Test that invalid classification raises ValueError."""
        class_to_leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_1": [
                "http://purl.obolibrary.org/obo/CHEBI_10",
            ],
        }

        with pytest.raises(ValueError, match="Classification must be"):
            count_removed_classes_for_class(
                "http://purl.obolibrary.org/obo/CHEBI_1",
                class_to_leaf_map,
                "invalid",
                {},
                {},
            )

    def test_functional_not_implemented(self):
        """Test that functional classification raises error."""
        class_to_leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_1": [
                "http://purl.obolibrary.org/obo/CHEBI_10",
            ],
        }

        with pytest.raises(ValueError, match="not yet implemented"):
            count_removed_classes_for_class(
                "http://purl.obolibrary.org/obo/CHEBI_1",
                class_to_leaf_map,
                "functional",
                {},
                {},
            )

    def test_structural_leaf_filtering(self):
        """Test filtering by structural_leaf_ids."""
        class_to_leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_1": [
                "http://purl.obolibrary.org/obo/CHEBI_10",
                "http://purl.obolibrary.org/obo/CHEBI_11",
                "http://purl.obolibrary.org/obo/CHEBI_12",
            ],
        }
        structural_ids = {
            "http://purl.obolibrary.org/obo/CHEBI_10",
            "http://purl.obolibrary.org/obo/CHEBI_11",
        }

        leaves, n_leaves = count_removed_classes_for_class(
            "http://purl.obolibrary.org/obo/CHEBI_1",
            class_to_leaf_map,
            "structural",
            {},
            {},
            structural_leaf_ids=structural_ids,
        )

        # Should only have the structural leaves
        assert n_leaves == 2
        assert len(leaves) == 2
        assert "http://purl.obolibrary.org/obo/CHEBI_12" not in leaves

    def test_no_structural_leaves_after_filtering(self):
        """Test when filtering removes all leaves."""
        class_to_leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_1": [
                "http://purl.obolibrary.org/obo/CHEBI_10",
            ],
        }
        structural_ids = {
            "http://purl.obolibrary.org/obo/CHEBI_999",  # Different leaf
        }

        leaves, n_leaves = count_removed_classes_for_class(
            "http://purl.obolibrary.org/obo/CHEBI_1",
            class_to_leaf_map,
            "structural",
            {},
            {},
            structural_leaf_ids=structural_ids,
        )

        # No leaves should pass filtering
        assert n_leaves == 0
        assert len(leaves) == 0

    def test_full_classification_with_structural_only(self):
        """Test 'full' classification (should include structural)."""
        class_to_leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_1": [
                "http://purl.obolibrary.org/obo/CHEBI_10",
                "http://purl.obolibrary.org/obo/CHEBI_11",
            ],
        }

        leaves, n_leaves = count_removed_classes_for_class(
            "http://purl.obolibrary.org/obo/CHEBI_1",
            class_to_leaf_map,
            "full",
            {},
            {},
        )

        assert n_leaves == 2
        assert len(leaves) == 2


class TestCountRemovedClassesForRoles:
    """Test counting leaf descendants for roles."""

    def test_valid_functional_role(self):
        """Test counting leaves for valid functional role."""
        roles_to_leaves_map = {
            "http://purl.obolibrary.org/obo/role_1": [
                "http://purl.obolibrary.org/obo/CHEBI_10",
                "http://purl.obolibrary.org/obo/CHEBI_11",
            ],
        }

        _, n_leaves = count_removed_classes_for_roles(
            "http://purl.obolibrary.org/obo/role_1",
            {},
            "functional",
            roles_to_leaves_map,
        )

        assert n_leaves == 2

    def test_empty_role(self):
        """Test role with no associated leaves."""
        roles_to_leaves_map = {}

        _, n_leaves = count_removed_classes_for_roles(
            "http://purl.obolibrary.org/obo/role_1",
            {},
            "functional",
            roles_to_leaves_map,
        )

        assert n_leaves == 0

    def test_structural_not_supported(self):
        """Test that structural classification returns 0."""
        result = count_removed_classes_for_roles(
            "http://purl.obolibrary.org/obo/role_1",
            {},
            "structural",
            {},
        )

        # Should return (0, 0) or similar for unsupported classification
        assert result[1] == 0

    def test_full_classification(self):
        """Test 'full' classification for roles."""
        roles_to_leaves_map = {
            "http://purl.obolibrary.org/obo/role_1": [
                "http://purl.obolibrary.org/obo/CHEBI_10",
            ],
        }

        _, n_leaves = count_removed_classes_for_roles(
            "http://purl.obolibrary.org/obo/role_1",
            {},
            "full",
            roles_to_leaves_map,
        )

        assert n_leaves == 1


class TestEdgeCasesAndIntegration:
    """Test edge cases and integration scenarios."""

    def test_pipeline_structural_to_functional_split(self):
        """Test splitting structural and functional leaves."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,Classification\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_10,structural\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_11,functional\n")
            removed_csv_path = f.name

        try:
            structural = get_structural_leaf_ids(removed_csv_path)
            assert len(structural) == 1
            assert "http://purl.obolibrary.org/obo/CHEBI_10" in structural
        finally:
            Path(removed_csv_path).unlink()

    def test_large_class_with_many_leaves(self):
        """Test handling large classes."""
        class_to_leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_1": [
                f"http://purl.obolibrary.org/obo/CHEBI_{i}" for i in range(1000, 2000)
            ],
        }

        leaves, n_leaves = count_removed_classes_for_class(
            "http://purl.obolibrary.org/obo/CHEBI_1",
            class_to_leaf_map,
            "structural",
            {},
            {},
        )

        assert n_leaves == 1000
        assert len(leaves) == 1000

    def test_duplicate_leaves_in_map(self):
        """Test handling when same leaf appears under multiple ancestors."""
        leaf_map = {
            "shared_leaf": ["ancestor_1", "ancestor_2"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaf_map, f)
            leaf_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            build_class_to_leaf_map(leaf_file, output_file)

            with open(output_file) as f:
                result = json.load(f)

            # Both ancestors should have the shared leaf
            assert "shared_leaf" in result["ancestor_1"]
            assert "shared_leaf" in result["ancestor_2"]
        finally:
            Path(leaf_file).unlink()
            Path(output_file).unlink()
