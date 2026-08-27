"""Shared access to the generated data files the enrichment analyses depend on.

Every analysis entry point needs the same six files. Their paths used to be spelled out
as bare ``"data/..."`` literals inside each function -- an identical block repeated in
eight places, none of which could be pointed anywhere else. They are resolved here
instead, through :mod:`chebin.config`, so the package works from any working directory.
"""

from __future__ import annotations

import json

from chebin.config import data_path, require_data_path

#: Names, relative to the data folder, of the files every analysis needs.
REMOVED_LEAVES_CSV = "removed_leaf_classes_with_smiles.csv"
LEAF_TO_ANCESTORS_MAP = "removed_leaf_classes_to_ALL_parents_map.json"
CLASS_TO_LEAF_MAP = "class_to_leaf_descendants_map.json"
PARENT_MAP = "chebi_parent_map.json"
CLASS_TO_ALL_ROLES_MAP = "class_to_all_roles_map.json"
ROLES_TO_LEAVES_MAP = "roles_to_leaves_map.json"
ID_TO_NAME_MAP = "chebi_id_to_name_map.json"

#: Default narrow background: the first Homo sapiens background (HMDB + LOTUS).
#: Optional -- create_all_files only builds it when the HMDB XML is present.
HUMAN_ENTITIES_LEAVES = "human_entities_leaves.json"


def load_data_files():
    """Load the common data files needed for enrichment analysis.

    Returns:
        tuple: (class_to_leaf_map, class_to_all_roles_map, roles_to_leaves_map,
                removed_leaves_csv, leaf_to_ancestors_map_file, parent_map_file)

        The first three are loaded JSON; the last three are paths, passed on to helpers
        that read them themselves.
    """
    removed_leaves_csv = data_path(REMOVED_LEAVES_CSV)
    leaf_to_ancestors_map_file = data_path(LEAF_TO_ANCESTORS_MAP)
    parent_map_file = data_path(PARENT_MAP)

    with open(require_data_path(CLASS_TO_LEAF_MAP)) as f:
        class_to_leaf_map = json.load(f)
    with open(require_data_path(CLASS_TO_ALL_ROLES_MAP)) as f:
        class_to_all_roles_map = json.load(f)
    with open(require_data_path(ROLES_TO_LEAVES_MAP)) as f:
        roles_to_leaves_map = json.load(f)

    return (
        class_to_leaf_map,
        class_to_all_roles_map,
        roles_to_leaves_map,
        removed_leaves_csv,
        leaf_to_ancestors_map_file,
        parent_map_file,
    )
