"""Download and load the ChEBI ontology."""
# deptry: ignore=DEP001,DEP002

import os
import urllib.request

import pyhornedowl

# URL and local save path
CHEBI_URL = "https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.owl"
DATA_DIR = "data"
OWL_PATH = os.path.join(DATA_DIR, "chebi.owl")


def download_chebi(download_dir=None, force=True):
    """Download ChEBI ontology to specified directory (default: data/).

    ChEBI is updated continuously, so the ontology is re-downloaded by default rather
    than reused: building against whatever copy happens to be on disk would silently
    produce data files from an outdated release. This matches the other downloads in the
    pipeline (LOTUS, Recon3D), which always fetch fresh.

    Args:
        download_dir (str): Directory to download the OWL file to. If None, uses DATA_DIR ("data/").
        force (bool): Re-download even when a local copy exists (default). Pass False to
            deliberately reuse a local copy -- useful when iterating on a later stage,
            but the result is only as current as that file.

    Returns:
        str: Path to the downloaded OWL file
    """
    if download_dir is None:
        download_dir = DATA_DIR

    os.makedirs(download_dir, exist_ok=True)
    owl_path = os.path.join(download_dir, "chebi.owl")

    if not force and os.path.exists(owl_path):
        print(f"Reusing existing ChEBI ontology at {owl_path} (force=False).")
        return owl_path

    print("⬇ Downloading ChEBI ontology...")
    urllib.request.urlretrieve(CHEBI_URL, owl_path)
    print("Download complete.")

    return owl_path


def load_chebi(download_dir=None, force=True):
    """Load ChEBI ontology from specified directory (default: data/).

    Args:
        download_dir (str): Directory to download/load the OWL file from. If None, uses DATA_DIR ("data/").
                           Useful option: "data_new/" to keep the download separate from older versions.
        force (bool): Re-download even when a local copy exists. See :func:`download_chebi`.

    Returns:
        pyhornedowl ontology object
    """
    owl_file = download_chebi(download_dir=download_dir, force=force)
    print("Loading ChEBI ontology...")
    ontology = pyhornedowl.open_ontology(owl_file)
    print(
        f"Loaded ontology with {len(ontology.get_classes())} classes "
        f"and {len(ontology.get_axioms())} axioms.",
    )
    return ontology


def load_ontology(owl_file):
    print("Loading ontology...")
    ontology = pyhornedowl.open_ontology(owl_file)
    print(
        f"Loaded ontology from {owl_file} with {len(ontology.get_classes())} classes "
        f"and {len(ontology.get_axioms())} axioms.",
    )
    return ontology


if __name__ == "__main__":
    chebi_ontology = load_chebi()

    # load_ontology("data/filtered_chebi_no_leaves_with_smiles_no_deprecated.owl")

    # csv = ("data/removed_leaf_classes_with_smiles.csv")
    # # open and read the CSV file
    # df = pd.read_csv(csv)
    # len_df = len(df)
    # print(f"Number of entries in CSV: {len_df}")
