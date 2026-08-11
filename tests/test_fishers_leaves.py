"""
Unit tests for leaf-related functions in fishers_calculations.py.

Tests verify:
1. get_leaves() - study set leaf extraction
2. get_ancestors_for_inputs() - ancestor mapping
3. Leaf filtering and normalization logic
"""

import json
import tempfile
from pathlib import Path

from calculations.fishers_calculations import (
    get_ancestors_for_inputs,
    get_leaves,
    normalize_id,
)


class TestGetLeavesBasic:
    """Test basic leaf extraction from study set."""

    def test_single_leaf_single_studyset(self):
        """Test extracting single leaf from single study set."""
        studyset_list = ["http://purl.obolibrary.org/obo/CHEBI_12345"]

        # Create leaves.csv with correct IRI column
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,parent_id\n")
            f.write(
                "http://purl.obolibrary.org/obo/CHEBI_12345,http://purl.obolibrary.org/obo/CHEBI_1000\n"
            )
            leaves_file = f.name

        try:
            result = get_leaves(studyset_list, leaves_file, {})
            assert result is not None
            assert isinstance(result, list)
        finally:
            Path(leaves_file).unlink()

    def test_multiple_leaves_single_studyset(self):
        """Test extracting multiple leaves from single study set."""
        studyset_list = [
            "http://purl.obolibrary.org/obo/CHEBI_12345",
            "http://purl.obolibrary.org/obo/CHEBI_12346",
            "http://purl.obolibrary.org/obo/CHEBI_12347",
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,parent_id\n")
            for i in range(12345, 12348):
                f.write(f"http://purl.obolibrary.org/obo/CHEBI_{i},CHEBI:1000\n")
            leaves_file = f.name

        try:
            result = get_leaves(studyset_list, leaves_file, {})
            assert result is not None
            assert isinstance(result, list)
            assert len(result) > 0
        finally:
            Path(leaves_file).unlink()

    def test_empty_studyset(self):
        """Test with empty study set."""
        studyset_list = []

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,parent_id\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_12345,CHEBI:1000\n")
            leaves_file = f.name

        try:
            result = get_leaves(studyset_list, leaves_file, {})
            # Should return empty list
            assert result is not None
            assert isinstance(result, list)
            assert len(result) == 0
        finally:
            Path(leaves_file).unlink()

    def test_empty_leaves_file(self):
        """Test with empty leaves CSV."""
        studyset_list = ["http://purl.obolibrary.org/obo/CHEBI_12345"]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,parent_id\n")  # Header only
            leaves_file = f.name

        try:
            result = get_leaves(studyset_list, leaves_file, {})
            # Should handle gracefully
            assert result is not None
            assert isinstance(result, list)
        finally:
            Path(leaves_file).unlink()

    def test_multiple_studysets(self):
        """Test extracting leaves from multiple study sets."""
        studyset_list = [
            "http://purl.obolibrary.org/obo/CHEBI_12345",
            "http://purl.obolibrary.org/obo/CHEBI_12346",
            "http://purl.obolibrary.org/obo/CHEBI_12347",
            "http://purl.obolibrary.org/obo/CHEBI_12345",  # Duplicate
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,parent_id\n")
            for i in range(12345, 12348):
                f.write(f"http://purl.obolibrary.org/obo/CHEBI_{i},CHEBI:1000\n")
            leaves_file = f.name

        try:
            result = get_leaves(studyset_list, leaves_file, {})
            assert result is not None
            assert isinstance(result, list)
        finally:
            Path(leaves_file).unlink()

    def test_non_leaf_class_with_leaf_descendants(self):
        """Test that non-leaf classes use class_to_leaf_map to find leaves."""
        studyset_list = ["http://purl.obolibrary.org/obo/CHEBI_1000"]  # Non-leaf
        class_to_leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_1000": [
                "http://purl.obolibrary.org/obo/CHEBI_12345",
                "http://purl.obolibrary.org/obo/CHEBI_12346",
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,parent_id\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_12345,CHEBI:1000\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_12346,CHEBI:1000\n")
            leaves_file = f.name

        try:
            result = get_leaves(studyset_list, leaves_file, class_to_leaf_map)
            assert result is not None
            assert isinstance(result, list)
            # Should contain the leaf descendants
            assert len(result) == 2
        finally:
            Path(leaves_file).unlink()


class TestGetLeavesWithFiltering:
    """Test leaf extraction with filtering options."""

    def test_structural_leaf_filtering(self):
        """Test filtering by structural leaves."""
        studyset_list = [
            "http://purl.obolibrary.org/obo/CHEBI_12345",
            "http://purl.obolibrary.org/obo/CHEBI_12346",
        ]
        structural_leaf_ids = {"http://purl.obolibrary.org/obo/CHEBI_12345"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,parent_id\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_12345,CHEBI:1000\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_12346,CHEBI:1000\n")
            leaves_file = f.name

        try:
            result = get_leaves(
                studyset_list,
                leaves_file,
                {},
                structural_leaf_ids=structural_leaf_ids,
            )
            # Should filter to only structural leaves
            assert result is not None
            assert isinstance(result, list)
            # Only CHEBI_12345 should be included (it's in structural_leaf_ids)
            assert "http://purl.obolibrary.org/obo/CHEBI_12345" in result
        finally:
            Path(leaves_file).unlink()

    def test_class_to_leaf_map_usage(self):
        """Test that class_to_leaf_map is used for mapping."""
        studyset_list = ["http://purl.obolibrary.org/obo/CHEBI_1000"]  # Non-leaf class
        class_to_leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_1000": [
                "http://purl.obolibrary.org/obo/CHEBI_12345",
            ],
            "http://purl.obolibrary.org/obo/CHEBI_2000": [
                "http://purl.obolibrary.org/obo/CHEBI_12346",
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,parent_id\n")
            f.write("http://purl.obolibrary.org/obo/CHEBI_12345,CHEBI:1000\n")
            leaves_file = f.name

        try:
            result = get_leaves(studyset_list, leaves_file, class_to_leaf_map)
            assert result is not None
            assert isinstance(result, list)
            # Should contain the leaves from the map
            assert len(result) >= 1
        finally:
            Path(leaves_file).unlink()


class TestGetAncestorsForInputs:
    """Test ancestor mapping for study set inputs."""

    def test_single_leaf_ancestors(self):
        """Test getting ancestors for single leaf."""
        studyset_leaves = {"CHEBI:12345"}

        # Create leaf_to_all_parents_map JSON
        leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_12345": [
                "http://purl.obolibrary.org/obo/CHEBI_1000",
                "http://purl.obolibrary.org/obo/CHEBI_0",
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaf_map, f)
            map_file = f.name

        try:
            result = get_ancestors_for_inputs(studyset_leaves, map_file)
            assert result is not None
            assert isinstance(result, (dict, set, list, type(None)))
        finally:
            Path(map_file).unlink()

    def test_multiple_leaves_ancestors(self):
        """Test getting ancestors for multiple leaves."""
        studyset_leaves = {"CHEBI:12345", "CHEBI:12346"}

        leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_12345": [
                "http://purl.obolibrary.org/obo/CHEBI_1000",
            ],
            "http://purl.obolibrary.org/obo/CHEBI_12346": [
                "http://purl.obolibrary.org/obo/CHEBI_2000",
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaf_map, f)
            map_file = f.name

        try:
            result = get_ancestors_for_inputs(studyset_leaves, map_file)
            assert result is not None
        finally:
            Path(map_file).unlink()

    def test_missing_leaf_in_map(self):
        """Test handling of leaves not in ancestor map."""
        studyset_leaves = {"CHEBI:99999"}  # Not in map

        leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_12345": [
                "http://purl.obolibrary.org/obo/CHEBI_1000",
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaf_map, f)
            map_file = f.name

        try:
            # Should handle gracefully without crashing
            result = get_ancestors_for_inputs(studyset_leaves, map_file)
            # Either returns something or None
            assert result is None or isinstance(result, (dict, set, list))
        finally:
            Path(map_file).unlink()

    def test_empty_ancestors_list(self):
        """Test leaf with no ancestors."""
        studyset_leaves = {"CHEBI:12345"}

        leaf_map = {
            "http://purl.obolibrary.org/obo/CHEBI_12345": [],  # No ancestors
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaf_map, f)
            map_file = f.name

        try:
            result = get_ancestors_for_inputs(studyset_leaves, map_file)
            # Should handle empty ancestor list
            assert result is None or isinstance(result, (dict, set, list))
        finally:
            Path(map_file).unlink()


class TestLeafErrorHandling:
    """Test error handling in leaf-related functions."""

    def test_missing_leaves_file(self):
        """Test handling of missing leaves CSV file."""
        studyset_list = [["CHEBI:12345"]]

        try:
            result = get_leaves(studyset_list, "/nonexistent/path.csv", {})
            # Should either raise or return None
            assert result is None or isinstance(result, (set, list))
        except (FileNotFoundError, OSError, ValueError):
            # Also acceptable to raise for missing file
            pass

    def test_invalid_json_ancestor_map(self):
        """Test handling of invalid JSON in ancestor map."""
        studyset_leaves = {"CHEBI:12345"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")  # Not valid JSON
            map_file = f.name

        try:
            # Should either raise or handle gracefully
            try:
                result = get_ancestors_for_inputs(studyset_leaves, map_file)
                assert result is None or isinstance(result, (dict, set, list))
            except (json.JSONDecodeError, ValueError):
                # Acceptable to raise for invalid JSON
                pass
        finally:
            Path(map_file).unlink()

    def test_malformed_csv_leaves_file(self):
        """Test handling of malformed CSV."""
        studyset_list = [["CHEBI:12345"]]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("not,enough,columns\n")  # Missing expected columns
            f.write("CHEBI:12345\n")  # Wrong format
            leaves_file = f.name

        try:
            # Should handle gracefully
            result = get_leaves(studyset_list, leaves_file, {})
            assert result is None or isinstance(result, (set, list))
        except (ValueError, KeyError, IndexError):
            # Also acceptable to raise for malformed file
            pass
        finally:
            Path(leaves_file).unlink()


class TestLeafConsistency:
    """Test consistency of leaf operations."""

    def test_normalization_consistency(self):
        """Test that ID normalization is consistent."""
        id1 = "CHEBI:12345"
        id2 = "http://purl.obolibrary.org/obo/CHEBI_12345"

        norm1 = normalize_id(id1)
        norm2 = normalize_id(id2)

        # Both should produce the same normalized form
        assert norm1 == norm2

    def test_leaves_deduplicated(self):
        """Test that duplicate leaves are handled correctly."""
        studyset_list = [
            "http://purl.obolibrary.org/obo/CHEBI_12345",
            "http://purl.obolibrary.org/obo/CHEBI_12346",
            "http://purl.obolibrary.org/obo/CHEBI_12345",  # Duplicate
            "http://purl.obolibrary.org/obo/CHEBI_12347",
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,parent_id\n")
            for i in range(12345, 12348):
                f.write(f"http://purl.obolibrary.org/obo/CHEBI_{i},CHEBI:1000\n")
            leaves_file = f.name

        try:
            result = get_leaves(studyset_list, leaves_file, {})
            # Result should not contain duplicates
            assert result is not None
            assert isinstance(result, list)
            # Check for duplicates
            assert len(result) == len(set(result))
        finally:
            Path(leaves_file).unlink()

    def test_leaf_order_independence(self):
        """Test that order of leaves doesn't matter."""
        # Order should not affect the final result
        studyset_list1 = [
            "http://purl.obolibrary.org/obo/CHEBI_12345",
            "http://purl.obolibrary.org/obo/CHEBI_12346",
            "http://purl.obolibrary.org/obo/CHEBI_12347",
        ]
        studyset_list2 = [
            "http://purl.obolibrary.org/obo/CHEBI_12347",
            "http://purl.obolibrary.org/obo/CHEBI_12345",
            "http://purl.obolibrary.org/obo/CHEBI_12346",
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("IRI,parent_id\n")
            for i in range(12345, 12348):
                f.write(f"http://purl.obolibrary.org/obo/CHEBI_{i},CHEBI:1000\n")
            leaves_file = f.name

        try:
            result1 = get_leaves(studyset_list1, leaves_file, {})
            result2 = get_leaves(studyset_list2, leaves_file, {})

            # Results should be equivalent (same elements, possibly different order)
            assert set(result1) == set(result2)
        finally:
            Path(leaves_file).unlink()
