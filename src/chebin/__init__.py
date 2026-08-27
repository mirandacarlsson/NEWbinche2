"""ChEBI-N enrichment analysis tooling.

The eight ``run_*`` entry points are re-exported here so callers can write
``from chebin import run_enrichment_analysis`` instead of reaching into the
module layout. Import from this top level: the internal paths are free to move.

Every entry point needs the generated data folder. Point chebin at one with
``set_data_dir()`` or the ``CHEBIN_DATA_DIR`` environment variable, and run
``create_all_files()`` first if it has not been generated yet.
"""

from .calculations.fishers_calculations import (
    run_enrichment_analysis,
    run_enrichment_analysis_plain_enrich_pruning_strategy,
)
from .calculations.weighted_calculations import (
    run_weighted_enrichment_analysis,
    run_weighted_enrichment_analysis_plain_enrich_pruning_strategy,
    run_weighted_narrow_background_enrichment_analysis,
    run_weighted_narrow_background_enrichment_analysis_plain_enrich_pruning_strategy,
)
from .config import get_data_dir, set_data_dir
from .preparing_data.create_files import create_all_files
from .preparing_data.wikidata.narrow_background_fishers import (
    run_narrow_background_enrichment_analysis,
    run_narrow_background_enrichment_analysis_plain_enrich_pruning_strategy,
)
from .visualization import export_graph_html

__all__ = [
    "create_all_files",
    "export_graph_html",
    "get_data_dir",
    "run_enrichment_analysis",
    "run_enrichment_analysis_plain_enrich_pruning_strategy",
    "run_narrow_background_enrichment_analysis",
    "run_narrow_background_enrichment_analysis_plain_enrich_pruning_strategy",
    "run_weighted_enrichment_analysis",
    "run_weighted_enrichment_analysis_plain_enrich_pruning_strategy",
    "run_weighted_narrow_background_enrichment_analysis",
    "run_weighted_narrow_background_enrichment_analysis_plain_enrich_pruning_strategy",
    "set_data_dir",
]
