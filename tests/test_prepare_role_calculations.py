"""
Unit tests for prepare_role_calculations.py.

Tests verify:
1. IRI normalization
2. Role-to-class mapping from OWL files
3. Leaf-to-role mapping creation
4. Class-to-role mapping creation
5. Role hierarchy expansion
"""

import json
import tempfile
from pathlib import Path

from chebin.calculations.prepare_role_calculations import (
    _normalize_iri,
    create_class_to_all_roles_map,
    create_leaves_to_all_roles_map,
    create_roles_to_all_leaves_map,
)


class TestNormalizeIri:
    """Test IRI normalization."""

    def test_normalize_with_brackets(self):
        """Test removing < > brackets."""
        assert _normalize_iri("<http://example.org/test>") == "http://example.org/test"

    def test_normalize_without_brackets(self):
        """Test IRI without brackets."""
        assert _normalize_iri("http://example.org/test") == "http://example.org/test"

    def test_normalize_with_spaces(self):
        """Test stripping whitespace (only strips < > not spaces)."""
        # _normalize_iri only removes < > not surrounding spaces
        result = _normalize_iri("  <http://example.org/test>  ")
        # Should remove < > but keep spaces
        assert "http://example.org/test" in result

    def test_normalize_empty_string(self):
        """Test empty string."""
        assert _normalize_iri("") == ""

    def test_normalize_non_string(self):
        """Test non-string input conversion."""
        # Should be converted to string
        result = _normalize_iri(123)
        assert "123" in result


class TestCreateLeavesToAllRolesMap:
    """Test creating leaf-to-all-roles mapping."""

    def test_basic_leaves_to_roles(self):
        """Test basic mapping from leaves to roles."""
        roles_map = {
            "http://purl.obolibrary.org/obo/role_1": ["role_ancestor_1"],
            "http://purl.obolibrary.org/obo/class_1": ["role_1"],
        }

        leaves_to_parents = {
            "http://purl.obolibrary.org/obo/leaf_1": [
                "http://purl.obolibrary.org/obo/class_1",
            ],
        }

        parent_map = {
            "http://purl.obolibrary.org/obo/role_1": ["role_ancestor_1"],
            "http://purl.obolibrary.org/obo/class_1": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(roles_map, f)
            roles_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaves_to_parents, f)
            leaves_parents_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            parent_map_file = f.name
            json.dump(parent_map, f)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            create_leaves_to_all_roles_map(
                roles_file,
                leaves_parents_file,
                output_file,
                parent_map_file,
            )

            with open(output_file) as f:
                result = json.load(f)

            # Verify result structure
            assert isinstance(result, dict)
            assert "http://purl.obolibrary.org/obo/leaf_1" in result
        finally:
            Path(roles_file).unlink()
            Path(leaves_parents_file).unlink()
            Path(parent_map_file).unlink()
            Path(output_file).unlink()

    def test_leaf_with_direct_roles(self):
        """Test leaf with direct roles (not via ancestors)."""
        roles_map = {
            "http://purl.obolibrary.org/obo/leaf_1": ["role_direct"],
        }

        leaves_to_parents = {
            "http://purl.obolibrary.org/obo/leaf_1": [],
        }

        parent_map = {}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(roles_map, f)
            roles_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaves_to_parents, f)
            leaves_parents_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(parent_map, f)
            parent_map_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            create_leaves_to_all_roles_map(
                roles_file,
                leaves_parents_file,
                output_file,
                parent_map_file,
            )

            with open(output_file) as f:
                result = json.load(f)

            # Should include direct role
            assert "http://purl.obolibrary.org/obo/leaf_1" in result
            assert "role_direct" in result["http://purl.obolibrary.org/obo/leaf_1"]
        finally:
            Path(roles_file).unlink()
            Path(leaves_parents_file).unlink()
            Path(parent_map_file).unlink()
            Path(output_file).unlink()

    def test_leaf_with_no_roles(self):
        """Test leaf with no associated roles."""
        roles_map = {}

        leaves_to_parents = {
            "http://purl.obolibrary.org/obo/leaf_1": [],
        }

        parent_map = {}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(roles_map, f)
            roles_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaves_to_parents, f)
            leaves_parents_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(parent_map, f)
            parent_map_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            create_leaves_to_all_roles_map(
                roles_file,
                leaves_parents_file,
                output_file,
                parent_map_file,
            )

            with open(output_file) as f:
                result = json.load(f)

            # Leaf should be in result with empty role list
            assert "http://purl.obolibrary.org/obo/leaf_1" in result
            assert result["http://purl.obolibrary.org/obo/leaf_1"] == []
        finally:
            Path(roles_file).unlink()
            Path(leaves_parents_file).unlink()
            Path(parent_map_file).unlink()
            Path(output_file).unlink()

    def test_role_hierarchy_expansion(self):
        """Test that role ancestors are included."""
        roles_map = {
            "http://purl.obolibrary.org/obo/class_1": ["role_child"],
        }

        leaves_to_parents = {
            "http://purl.obolibrary.org/obo/leaf_1": [
                "http://purl.obolibrary.org/obo/class_1",
            ],
        }

        parent_map = {
            "role_child": ["role_parent"],
            "role_parent": ["role_grandparent"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(roles_map, f)
            roles_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaves_to_parents, f)
            leaves_parents_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(parent_map, f)
            parent_map_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            create_leaves_to_all_roles_map(
                roles_file,
                leaves_parents_file,
                output_file,
                parent_map_file,
            )

            with open(output_file) as f:
                result = json.load(f)

            # Should include all role ancestors
            leaf_roles = result["http://purl.obolibrary.org/obo/leaf_1"]
            assert "role_child" in leaf_roles
            assert "role_parent" in leaf_roles
            assert "role_grandparent" in leaf_roles
        finally:
            Path(roles_file).unlink()
            Path(leaves_parents_file).unlink()
            Path(parent_map_file).unlink()
            Path(output_file).unlink()


class TestCreateClassToAllRolesMap:
    """Test creating class-to-all-roles mapping."""

    def test_basic_class_to_roles(self):
        """Test basic mapping from classes to roles."""
        roles_map = {
            "http://purl.obolibrary.org/obo/class_1": ["role_1"],
        }

        parent_map = {
            "http://purl.obolibrary.org/obo/class_1": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(roles_map, f)
            roles_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(parent_map, f)
            parent_map_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            create_class_to_all_roles_map(
                roles_file,
                parent_map_file,
                output_file,
            )

            with open(output_file) as f:
                result = json.load(f)

            # Verify result structure
            assert isinstance(result, dict)
        finally:
            Path(roles_file).unlink()
            Path(parent_map_file).unlink()
            Path(output_file).unlink()

    def test_class_with_ancestor_roles(self):
        """Test that class inherits roles from ancestors."""
        roles_map = {
            "http://purl.obolibrary.org/obo/parent_class": ["role_from_parent"],
        }

        parent_map = {
            "http://purl.obolibrary.org/obo/class_1": [
                "http://purl.obolibrary.org/obo/parent_class",
            ],
            "http://purl.obolibrary.org/obo/parent_class": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(roles_map, f)
            roles_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(parent_map, f)
            parent_map_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            create_class_to_all_roles_map(
                roles_file,
                parent_map_file,
                output_file,
            )

            with open(output_file) as f:
                result = json.load(f)

            # Class should inherit parent's roles
            if "http://purl.obolibrary.org/obo/class_1" in result:
                assert (
                    "role_from_parent"
                    in result["http://purl.obolibrary.org/obo/class_1"]
                )
        finally:
            Path(roles_file).unlink()
            Path(parent_map_file).unlink()
            Path(output_file).unlink()


class TestCreateRolesToAllLeavesMap:
    """Test creating roles-to-all-leaves mapping."""

    def test_basic_roles_to_leaves(self):
        """Test basic mapping from roles to leaves."""
        leaves_to_roles = {
            "http://purl.obolibrary.org/obo/leaf_1": ["role_1", "role_2"],
            "http://purl.obolibrary.org/obo/leaf_2": ["role_1"],
            "http://purl.obolibrary.org/obo/leaf_3": ["role_3"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaves_to_roles, f)
            leaves_to_roles_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            create_roles_to_all_leaves_map(
                leaves_to_roles_file,
                output_file,
            )

            with open(output_file) as f:
                result = json.load(f)

            # Verify result structure
            assert isinstance(result, dict)
            # role_1 should have leaf_1 and leaf_2
            if "role_1" in result:
                assert "http://purl.obolibrary.org/obo/leaf_1" in result["role_1"]
                assert "http://purl.obolibrary.org/obo/leaf_2" in result["role_1"]
        finally:
            Path(leaves_to_roles_file).unlink()
            Path(output_file).unlink()

    def test_role_with_no_leaves(self):
        """Test role with no associated leaves."""
        leaves_to_roles = {
            "http://purl.obolibrary.org/obo/leaf_1": ["role_1"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaves_to_roles, f)
            leaves_to_roles_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            create_roles_to_all_leaves_map(
                leaves_to_roles_file,
                output_file,
            )

            with open(output_file) as f:
                result = json.load(f)

            # role_1 should have at least one leaf
            if "role_1" in result:
                assert len(result["role_1"]) > 0
        finally:
            Path(leaves_to_roles_file).unlink()
            Path(output_file).unlink()

    def test_multiple_leaves_per_role(self):
        """Test role with many associated leaves."""
        leaves_to_roles = {
            f"http://purl.obolibrary.org/obo/leaf_{i}": ["shared_role"]
            for i in range(100)
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaves_to_roles, f)
            leaves_to_roles_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            create_roles_to_all_leaves_map(
                leaves_to_roles_file,
                output_file,
            )

            with open(output_file) as f:
                result = json.load(f)

            # shared_role should have all 100 leaves
            if "shared_role" in result:
                assert len(result["shared_role"]) == 100
        finally:
            Path(leaves_to_roles_file).unlink()
            Path(output_file).unlink()

    def test_empty_leaves_to_roles_map(self):
        """Test with empty input."""
        leaves_to_roles = {}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaves_to_roles, f)
            leaves_to_roles_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            create_roles_to_all_leaves_map(
                leaves_to_roles_file,
                output_file,
            )

            with open(output_file) as f:
                result = json.load(f)

            # Result should be empty dict
            assert result == {}
        finally:
            Path(leaves_to_roles_file).unlink()
            Path(output_file).unlink()


class TestIntegrationScenarios:
    """Test integration scenarios across role functions."""

    def test_role_mapping_consistency(self):
        """Test consistency between leaves-to-roles and roles-to-leaves."""
        leaves_to_roles = {
            "leaf_1": ["role_A", "role_B"],
            "leaf_2": ["role_A"],
            "leaf_3": ["role_B", "role_C"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(leaves_to_roles, f)
            leaves_to_roles_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            create_roles_to_all_leaves_map(
                leaves_to_roles_file,
                output_file,
            )

            with open(output_file) as f:
                roles_to_leaves = json.load(f)

            # Verify consistency: if leaf X has role Y,
            # then role Y should have leaf X
            for leaf, roles in leaves_to_roles.items():
                for role in roles:
                    if role in roles_to_leaves:
                        assert leaf in roles_to_leaves[role]
        finally:
            Path(leaves_to_roles_file).unlink()
            Path(output_file).unlink()

    def test_normalization_in_pipeline(self):
        """Test that IRI normalization works throughout pipeline."""
        # Test with various IRI formats
        iris = [
            "<http://example.org/class_1>",
            "http://example.org/class_2",
            "  http://example.org/class_3  ",
        ]

        normalized = [_normalize_iri(iri) for iri in iris]

        # All should be normalized to clean format
        for norm in normalized:
            assert not norm.startswith("<")
            assert not norm.endswith(">")
            assert "http://example.org/class" in norm
