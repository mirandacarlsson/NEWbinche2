# ChEBI-N

ChEBI-N is an updated version of
[BiNChE](https://github.com/pcm32/BiNCheWeb/wiki/BiNChE#graph-pruning-strategies).
It is a tool for ontology-based chemical enrichment analysis and uses the
[ChEBI](https://www.ebi.ac.uk/chebi/) ontology of chemical entities as its
background population.

It is available both as the `chebin` Python package and as a web
application at https://chebin.hastingslab.org/ that needs no local setup.

## Package usage

### Installation

ChEBI-N is published on PyPI as [`chebin`](https://pypi.org/project/chebin/) and
requires Python 3.12 or newer:

```bash
pip install chebin
```

or, with `uv`:

```bash
uv add chebin
```

<details>
<summary>Installing from a local build instead (for development)</summary>

To work against your own checkout rather than the released package, build a wheel
and point another project at it:

```bash
cd chebin
uv build
```

This produces `dist/chebin-<version>-py3-none-any.whl`. Point another project at
it:

- With `uv`, add to your `pyproject.toml`:
  ```toml
  [project]
  dependencies = ["chebin"]

  [tool.uv.sources]
  chebin = { path = "/path/to/chebin/dist/chebin-1.0.1-py3-none-any.whl" }
  ```
  then run `uv sync`.
- With plain `pip`:
  `pip install /path/to/chebin/dist/chebin-1.0.1-py3-none-any.whl`.

Whenever the source changes, rebuild the wheel (`uv build`) and re-sync to pick it
up. With `uv`, that's `uv lock --upgrade-package chebin && uv sync` --- the wheel
is pinned in `uv.lock` by exact file hash, so a same-version rebuild isn't picked
up automatically otherwise.

</details>

### 1. Generate the data files (required first)

Every function below needs a generated data folder. Build one with:

```python
from chebin import create_all_files

create_all_files(data_folder="data")
```

**This can take up to a few hours** --- it downloads and processes the full ChEBI
ontology, LOTUS/Wikidata compound data, and the Recon3D model. It only needs to be
run once (re-run it later to refresh with newer ChEBI/LOTUS data).

Before running the function, one input has to be supplied by hand: `hmdb_metabolites.xml` (the 'All
Metabolites' export from [HMDB](https://hmdb.ca/downloads)), placed in `data/` or
`data/source_files/`. Without it, `create_all_files` still runs and prints a
warning, but skips the first Homo sapiens background (HMDB + LOTUS) and everything
that depends on it.

Once it finishes, `data_folder` (`data/` by default) holds everything the
enrichment functions read directly; the `source_files/` and `intermediate_files/`
subfolders it also creates are working files nothing reads afterwards --- safe to
delete (each has its own README explaining what it is).

If you're regenerating an existing data folder rather than building one from
scratch, use `create_all_files_with_backup` instead --- it isn't re-exported at
the top level, so import it directly:

```python
from chebin.preparing_data.create_files import create_all_files_with_backup

create_all_files_with_backup(data_folder="data")
```

This renames the current `data/` to `data_last_used_YYYY.MM.DD` before building
the replacement, and keeps only the 3 most recent backups.

Note that chebin looks for the data folder at `<current working directory>/data`,
so run your analyses from the folder you generated it in. If that isn't possible,
point chebin at it with `set_data_dir("/path/to/data")` or the `CHEBIN_DATA_DIR`
environment variable.

See the [Datafiles Workflow](#workflow) section below for a step-by-step breakdown of what
each stage does and what each file consists of.

### Enrichment analysis functions

For enrichment analysis calculations, there are different functions for different options. For the simplest usage, scroll down to the [example](#2-quick-example-run-an-analysis-then-export-the-graph) below: 

All functions follow one naming pattern:

```
run_[weighted_][narrow_background_]enrichment_analysis[_plain_enrich_pruning_strategy][_from_smiles]
```

Four independent choices combine to give the full name:

- **`weighted_`** --- plain Fisher's exact test (unweighted) vs. the
  SaddleSum-derived weighted method (see [Calculations](#calculations)).
  Unweighted functions take `studyset_list` (a list of ChEBI IDs); weighted
  functions take `weights_dict` (ChEBI ID -> weight, all weights must be real and
  positive), written as a plain dict:
  ```python
  weights_dict = {"CHEBI:15377": 1.5, "CHEBI:16236": 0.8, "CHEBI:17234": 3.0}
  results, graph = run_weighted_enrichment_analysis(weights_dict)
  ```
  The `_from_smiles` weighted variants take the same shape with SMILES keys
  instead (a `{SMILES: weight}` dict), e.g.
  `{"CC(=O)Oc1ccccc1C(=O)O": 1.5, "CHEBI:16236": 0.8}` --- SMILES and ChEBI ID
  keys can be mixed freely.
- **`narrow_background_`** --- the whole ChEBI ontology as background vs. a
  restricted background (see [Background](#background)). Choose which by passing
  `narrow_background_leaves_json`:

  | Background | `narrow_background_leaves_json` |
  |---|---|
  | Homo sapiens 1 (LOTUS + HMDB) --- default | `"human"` |
  | Homo sapiens 2 (Recon3D) | `"endogenous_human"` |
  | Arabidopsis thaliana | `"arabidopsis_thaliana"` |

  An explicit path to a leaves JSON also still works (e.g. a custom background
  for another taxon) --- the three short names above are just a convenience for
  the built-in ones. #TODO add example of how it would be written with a json file

  `expand_background` (default `True`) controls what happens to study-set
  compounds outside the chosen background: kept and added to the background too
  (so every input still gets tested) if `True`, excluded from the study set
  entirely if `False`. The two extra return values,
  `leaves_to_expand_background`/`parents_to_expand_background`, report which
  leaves/input classes triggered that expansion either way.
- **`_plain_enrich_pruning_strategy`** --- the fixed
  [Plain Enrichment Pruning Strategy](#pruning-strategies) vs. manually choosing
  which pruners to apply and when.
- **`_from_smiles`** --- takes SMILES instead of ChEBI IDs (a `list[str]`, or
  `{SMILES: weight}` for weighted variants), resolved to ChEBI ID(s) the same way
  described in [Study Set](#study-set), plus a `use_parents: bool = False`
  parameter (fall back to predicted parent classes when a SMILES has no direct
  ChEBI match if set to `True`). Returns everything the ChEBI-ID version does, plus one extra
  dict: `{"unresolved_smiles": [...], "ambiguous_matches": [...]}`. #TODO: add shortexplanation of what ambiguous matches are. A mixture of SMILES and ChEBI IDs can be used.

The table below shows all the different types of enrichment analysis functions. # TODO: pruning strategies are also an input for the normal erichment analysis functions. add this under input: eg : ChEBI IDs + pruning options. and show an example above or below the graph

| Function | Input | Background | Pruning | Returns |
|---|---|---|---|---|
| `run_enrichment_analysis` | ChEBI IDs | whole ontology | manual | `(results, graph)` |
| `run_enrichment_analysis_plain_enrich_pruning_strategy` | ChEBI IDs | whole ontology | plain strategy | `(results, graph)` |
| `run_enrichment_analysis_from_smiles` | SMILES | whole ontology | manual | `(results, graph, smiles_diagnostics)` |
| `run_enrichment_analysis_plain_enrich_pruning_strategy_from_smiles` | SMILES | whole ontology | plain strategy | `(results, graph, smiles_diagnostics)` |
| `run_weighted_enrichment_analysis` | ChEBI IDs + weights | whole ontology | manual | `(results, graph)` |
| `run_weighted_enrichment_analysis_plain_enrich_pruning_strategy` | ChEBI IDs + weights | whole ontology | plain strategy | `(results, graph)` |
| `run_weighted_enrichment_analysis_from_smiles` | SMILES + weights | whole ontology | manual | `(results, graph, smiles_diagnostics)` |
| `run_weighted_enrichment_analysis_plain_enrich_pruning_strategy_from_smiles` | SMILES + weights | whole ontology | plain strategy | `(results, graph, smiles_diagnostics)` |
| `run_narrow_background_enrichment_analysis` | ChEBI IDs | narrow | manual | `(results, graph, leaves_to_expand_background, parents_to_expand_background)` |
| `run_narrow_background_enrichment_analysis_plain_enrich_pruning_strategy` | ChEBI IDs | narrow | plain strategy | `(results, graph, leaves_to_expand_background, parents_to_expand_background)` |
| `run_narrow_background_enrichment_analysis_from_smiles` | SMILES | narrow | manual | `(results, graph, leaves_to_expand_background, parents_to_expand_background, smiles_diagnostics)` |
| `run_narrow_background_enrichment_analysis_plain_enrich_pruning_strategy_from_smiles` | SMILES | narrow | plain strategy | `(results, graph, leaves_to_expand_background, parents_to_expand_background, smiles_diagnostics)` |
| `run_weighted_narrow_background_enrichment_analysis` | ChEBI IDs + weights | narrow | manual | `(results, graph, leaves_to_expand_background, parents_to_expand_background)` |
| `run_weighted_narrow_background_enrichment_analysis_plain_enrich_pruning_strategy` | ChEBI IDs + weights | narrow | plain strategy | `(results, graph, leaves_to_expand_background, parents_to_expand_background)` |
| `run_weighted_narrow_background_enrichment_analysis_from_smiles` | SMILES + weights | narrow | manual | `(results, graph, leaves_to_expand_background, parents_to_expand_background, smiles_diagnostics)` |
| `run_weighted_narrow_background_enrichment_analysis_plain_enrich_pruning_strategy_from_smiles` | SMILES + weights | narrow | plain strategy | `(results, graph, leaves_to_expand_background, parents_to_expand_background, smiles_diagnostics)` |

All are importable directly from `chebin`, e.g.
`from chebin import run_weighted_narrow_background_enrichment_analysis_from_smiles`.

#### Shared parameters

These appear on most or all of the functions above (see the linked sections for
what each option means):

| Parameter | Default | Meaning |
|---|---|---|
| `bonferroni_correct` | `False` | Apply Bonferroni correction ([Correction Method](#correction-method)) |
| `benjamini_hochberg_correct` | `True` | Apply Benjamini-Hochberg FDR correction (overrides Bonferroni if both are `True`) |
| `root_children_prune` | `False` | Apply the [Root Children Pruner](#pruning-strategies) |
| `levels` | `2` | Levels pruned by the Root Children Pruner|
| `linear_branch_prune` | `False` | Apply the [Linear Branch Collapser Pruner](#pruning-strategies) |
| `n` | `2` (manual) / `0` (plain strategy) | Nodes kept per branch by the Linear Branch Collapser Pruner |
| `high_p_value_prune` | `False` | Apply the [High P-Value Branch Pruner](#pruning-strategies) |
| `p_value_threshold` | `0.05` | Threshold used by the High P-Value Branch Pruner |
| `zero_degree_prune` | `False` | Apply the [Zero-degree Pruner](#pruning-strategies) |
| `classification` | `"structural"` | Which part of the ontology to run on: `"structural"`, `"functional"`, or `"full"` (see [Background](#background)) |
| `print_results` | `False` | Print a p-value table to stdout |
| `csv_output_path` | `None` | If given, write the results table to this CSV path |

The `_plain_enrich_pruning_strategy` functions don't take the individual
`*_prune` toggles --- the plain strategy always applies its fixed pruner sequence
--- but still take `levels`, `n`, and `p_value_threshold` to tune it.

### Visualization

```python
export_graph_html(G, enrichment_results, output_file, include_untested_leaves=False)
```

Writes `G` (the graph returned by any `run_*` function above) as a self-contained
interactive HTML page --- no server or network access needed to view it.
`enrichment_results` is the results dict returned alongside `G`; pass `None` if
you don't have one (the graph still renders, just without p-values or coloring).
`include_untested_leaves` is off by default: study-set leaves are never tested
(so never coloured) and are typically the large majority of nodes, so including
them mostly just slows down rendering --- set it to `True` to keep them anyway,
e.g. for debugging.

### 2. Quick example: run an analysis, then export the graph

```python
from chebin import run_enrichment_analysis_plain_enrich_pruning_strategy, export_graph_html

results, graph = run_enrichment_analysis_plain_enrich_pruning_strategy(
    ["CHEBI:15377", "CHEBI:16236", "CHEBI:17234"],
    print_results=True,             # print a p-value table to stdout
    csv_output_path="results.csv",  # and write it to CSV
)

export_graph_html(graph, results, "enrichment_graph.html")
```
TODO: also add example where the user chooses pruning strategies

`results` is a dict with `"study_set"` (input names), `"removed_nodes"` (names of
nodes pruned away), and `"enrichment_results"` (class name -> p-value details).
`graph` is the pruned `networkx` graph, ready to hand to `export_graph_html`,
which writes a self-contained interactive HTML page --- no server or network
access needed to view it.

## The Web Application

The web application is available at https://chebin.hastingslab.org/. It offers the
same analyses as the [package](#package-usage), without any local setup.

### Running The Analysis

To run calculations locally instead, execute `website/app.py`
in the repo.
Note that all
necessary data files must be generated beforehand for local execution (as
described in the [Workflow](#workflow) section below or using the package as described above).

### Study Set

On the home page, you can enter your study set as ChEBI IDs (one per line) or
SMILES.
You can optionally provide weights for each compound (tab or space-separated).
If SMILES are used, each SMILES is resolved to a ChEBI ID in this order: (1) an
exact string match against the local table of ChEBI leaf classes, (2) a match
via the InChIKey computed from the SMILES, (3) a direct lookup through the
[Chebifier](https://chebifier.hastingslab.org/) API. If none of these resolve,
its predicted direct parent classes (also from Chebifier) can optionally be used
for enrichment calculations instead. Where a SMILES matches several ChEBI
entries, only one of them is included in the analysis (the lowest ChEBI ID); the
alternatives are listed on the results page as ambiguous matches. Note that this
applies to a structure matching several ChEBI terms --- where a SMILES is
instead resolved to its predicted parent classes, *all* of those parents are
included (and their children added to the study set).

### Background

Using the whole ChEBI ontology as a background population is the standard
option, alternatively using only the 'Structure' or 'Role' hierarchy as target
of enrichment:

- **Structure:** Enrichment based on ChEBI structural classification. This
  target is based on classes descending from the root node 'chemical entity',
  filtered to include everything under its children 'chemical substance', and
  'molecular entity' (and not under 'atom' and 'group')
- **Role:** Enrichment based on ChEBI role classification. This is based on
  classes descending from the root node 'role'.
- **Both:** Union of structure and role classifications (note: the structure
  classification is significantly larger)

In the package these are the `classification` argument: **Structure** is
`"structural"` (the default), **Role** is `"functional"`, and **Both** is
`"full"`.

The option of using a narrower, more specified, background is also provided. For
each narrow background a set of leaf classes is specified using external
sources, as explained below. Then all the ascending classes of these leaves in
the ChEBI ontology were used as the background populations: thus only using
subsets of the ontology.

### Human background 1 (LOTUS and HMDB)

Compounds from HMDB and LOTUS (taxonomy = Homo sapiens) were mapped to ChEBI
leaf classes to serve as a background for enrichment. These are entities that
have been measured from human samples.

Matching to a ChEBI ID was attempted in this order: (1) a ChEBI ID already
present in the source data, (2) an exact SMILES match against the local table of
ChEBI leaf classes (Wikidata only), (3) an InChIKey lookup against the same
local table, (4) the Chebifier API, which performs both a direct lookup and
parent-class classification --- for parent-class matches, the deepest class in
the ChEBI hierarchy was kept to avoid overly broad annotations. Where a matched
ChEBI ID corresponded to a non-leaf class in the ontology, it was expanded to
its leaf descendants; classes with more than 150 leaf descendants were excluded
to prevent high-level classes from disproportionately inflating the background.
The resulting set of leaf classes were used to form the narrow background used
in the enrichment analysis.

### Human background 2 (Recon3D)

A second, narrower human background was built from
[Recon3D](http://bigg.ucsd.edu/models/Recon3D), a genome-scale reconstruction of
human metabolism, downloaded as JSON from [BiGG Models](http://bigg.ucsd.edu/).
Unlike the Human background above, this one is restricted to metabolites that
participate in modeled human metabolic reactions, so it excludes
externally-sourced human-associated compounds (e.g. drugs, diet).

Recon3D represents each metabolite once per cellular compartment it appears in
(e.g. `10fthf_c`, `10fthf_m` for the cytosolic and mitochondrial pools of the
same compound), so compartment-specific entries sharing a base BiGG ID were
first collapsed into a single compound record --- these always carry identical
formula, charge, and database cross-references, confirming they are the same
chemical species. This reduced Recon3D's 5,835 metabolite entries to 2,797
unique compounds.

Each compound's listed ChEBI ID(s) were then resolved to leaf classes as
follows:

1. If any listed ChEBI ID is already a leaf, **all** such leaf candidates were
   kept. BiGG often lists several ChEBI IDs for one compound (e.g. different
   protonation or tautomer states), and these are typically genuinely distinct
   structures rather than duplicates, so none were discarded in favor of a
   single "primary" one.
2. If none of the listed IDs is a leaf, each was expanded to its leaf
   descendants, excluding any class with more than 150 leaf descendants (the
   same cutoff used for the Human background, to avoid over-generic classes).
3. For compounds with no ChEBI annotation at all, a ChEBI cross-reference was
   attempted via [UniChem](https://www.ebi.ac.uk/unichem/), first by InChIKey,
   then by HMDB ID (Recon3D stores HMDB IDs in an older 5-digit format, which
   was zero-padded to UniChem's expected 7-digit format before lookup). Any
   ChEBI IDs found this way were resolved to leaves using rules 1--2 above.

Compounds for which none of the above resolved to a leaf were left out of the
background. In practice these are largely abstract macromolecule/generic
placeholders (e.g. `Rtotal` fatty-acyl chains, cytochromes, thioredoxin,
procollagen) rather than discrete chemical structures, so they would not have
been usable in a ChEBI structure-based background regardless of the matching
method.

### Arabidopsis thaliana Background

This background also uses data from LOTUS but with taxonomy = Arabidopsis
thaliana. Mapping was done in the same way as for the first human background.

### Correction Method

For multiple hypothesis testing correction, p-value correction methods are
available. The options are Benjamini-Hochberg, Bonferroni, and None.
Benjamini-Hochberg is generally recommended.

### Pruning Strategies

Pruning options are available to make the graph less cluttered. The following
pruners are available (and found in
`src/chebin/calculations/visualitations_and_pruning.py`):

- **Root Children Pruner:** Removes the roots and their children up to a defined
  level (number of levels being an adaptable parameter). This allows removal of
  more general, and less meaningful, entities in the ontology. For example,
  levels set to 2 will remove the roots and one level of their descendants.

- **Linear Branch Collapser Pruner:** Removes linear branches within the graph;
  only nodes with one parent and one child can be removed. Either a chosen
  number of nodes (n) in the linear branch will be kept, or all intermediate
  nodes in the branch can be removed (set n = 0). E.g., n = 3 will keep every
  third node in the branch.

  Note that this pruner selects nodes by graph topology alone and does not
  consider p-values: an intermediate node is removed because of its position in
  a chain, regardless of how significant it is. Since ChEBI contains many long
  single-inheritance chains, a statistically significant class can be collapsed
  away if it happens to sit mid-chain. Use a non-zero n to retain more of each
  branch.

- **High P-Value Branch Pruner:** Removes branches from the graph that only
  contain nodes with a p-value greater than 0.05 (this value can be changed). A
  node with a higher p-value will still be kept if it has at least one
  descendant with a p-value lower than the threshold. Study-set leaf classes are
  never tested and therefore have no p-value, so they do not count as
  significant descendants and do not protect their ancestors from being pruned.

- **Zero-degree Pruner:** Removes nodes that have no connections with other
  nodes; that is, nodes with a total degree of zero.

If you manually choose which pruning strategies to apply, they will be
implemented once each. Alternatively, pruning strategies can be implemented in a
looping manner. In this scenario, there is first a pre-loop phase where pruners
are applied once, and then a loop phase where pruners are applied in a loop
until no more changes are made. The looping option is:

- **Plain Enrichment Pruning Strategy:** The pre-loop phase applies the high
  p-value branch pruner (with a threshold of 0.05), the linear branch collapser
  pruner (with n = 0), and the root children pruner (levels = 2). The loop phase
  applies the high p-value branch pruner (with a threshold of 0.05), the branch
  collapser pruner and the zero-degree vertex pruner. Benjamini-Hochberg is used
  as the p-value correction method, and is recomputed over the surviving classes
  on each loop iteration.

### Calculations

For multiple hypothesis testing correction, p-value correction methods are
available. To perform enrichment analysis calculations, Fisher's exact test is
used for p-value calculations. For weighted enrichment analysis however, a
SaddleSum method is used. All weights must be real and positive numbers.

For the SaddleSum method, the code has been largely inspired by
https://ftp.ncbi.nlm.nih.gov/pub/qmbpmn/SaddleSum/src/, version
[SaddleSum-standalone-1.2.2.tar.gz](https://ftp.ncbi.nlm.nih.gov/pub/qmbpmn/SaddleSum/src/SaddleSum-standalone-1.2.2.tar.gz)
2010-08-11 17:55 1.3M

The code was translated from c to python.

After calculations have been conducted, a table with the raw and corrected
p-values is provided. Under the table, information on for example which nodes
have been removed through pruning is available.

### The Graph

On the next webpage, a graph based on the enrichment analysis is displayed. The
colouring of the nodes is based on the significance of the p-values. It is
dependent on the values in that session; it is relative by default. Making the
colour scale absolute can currently only be done by changing the code (not
available on the online webpage). To make this change in your local version, go
to `website/templates/graph.html` and change the following line:

`const colourScaleMode = 'relative'; // 'absolute' or 'relative'`

The corrected p-value is used for the coloring if it is available.

The graph will initially show only the most relevant branches. This means that
all nodes with p-values under or equal to 0.05 will be shown, including all
nodes in the paths from these nodes up to the root. If all nodes have a higher
p-value, the same will be done but for nodes with p-values lower than 1. If
there only exists nodes where all p-values are 1 or N/A, then all nodes will be
shown.

There is a slider with a p-value pruner making it possible to more precisely
adapt what significance to show on the graph. Either paths to the root of nodes
of the chosen p-value will be kept (even if their p-value is higher) or nodes
will just be looked at individually. The second option will keep *only* the
nodes with the chosen significance but may give 'island' nodes that are not
connected to anything else. This slider is particularly useful for large
datasets. The range of the slider is relatove to the values obtained in that
analysis. It can look like this:

![The p-value pruning slider in the ChEBI-N web interface](https://raw.githubusercontent.com/ontology-tools/chebin/main/figs_for_README/screenshot_pfilter.png)

There are options to choose the layout of the graph, which nodes are shown, and
how to export the graph.

Re-running all calculations with new settings, such as with different pruning
options, can be done by clicking on 'Settings'. The previously used options will
be pre-selected.

Hovering over a node displays more detailed information about it. Both raw and
corrected p-values are shown, as well as its ChEBI ID.

Nodes can be selected by clicking on them. Right-clicking on a node provides the
options as seen in the figure below.

![Right-click menu options available on a graph node](https://raw.githubusercontent.com/ontology-tools/chebin/main/figs_for_README/screenshot_graphnodes.png)

Nodes can be repositioned by clicking and dragging them.

Leaf classes are not shown in the graph, since they do not receive p-values.
Beyond the initial display described above, nodes can also be shown or hidden
manually: options are available to hide all insignificant nodes (p-value >
0.05), to show all nodes, or to show/hide only the currently selected ones.

## Datafiles Workflow

This explains in further detail how the data files have been created and
filtered. Most necessary files can simply be obtained by running
`src/chebin/preparing_data/create_files.py` or `jobs/run_create_files.sh`, whereas one has
to be downloaded manually:

- `data/hmdb_metabolites.xml` --- the 'All Metabolites' XML from
  [HMDB](https://hmdb.ca/downloads) (see step 6.3 below).

This is already done for the web application where the files are updated
automatically once every month.

### 0. Python environment

Dependencies and the Python version requirement (`>=3.12`) are declared in
`pyproject.toml`, and `uv.lock` pins every dependency (and transitive
dependency) to an exact version, so the environment is fully reproducible across
machines.

To create it, install [uv](https://docs.astral.sh/uv/) and run, from the
repository root:

```bash
uv sync
```

This creates (or updates) `.venv/` with every package pinned to the exact
version in `uv.lock`. `.python-version` pins the interpreter itself (3.14);
`uv sync` downloads a matching Python automatically if one isn't already
available, so no separate Python install step is needed.

Development-only tools (`pytest`, `prek` linting, `coverage`, `great-docs`) are
declared as a separate dependency group and are included by the plain `uv sync`
above. To skip them, e.g. for a production-only install, use `uv sync --no-dev`.

If you'd rather not use uv, the runtime dependencies (see `pyproject.toml` for
the authoritative, version-constrained list) can be installed manually with:

`pip install flask networkx numpy pandas py-horned-owl rdkit requests scipy`

### 1. Load ChEBI

Download and load the ChEBI ontology by running `src/chebin/preparing_data/load_chebi.py`.
In the script, the OWL file is downloaded from
https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.owl and cached as
`data/chebi.owl`. Re-running the script will not re-download the file if it
already exists; delete `data/chebi.owl` if you want to attain a newer version.
The version used in the webapplication is automatically updated on the 1st of
every month.

### 2. Remove leaf classes and save maps

To identify leaf classes and flatten the hierarchy, use
`src/chebin/preparing_data/pruning_smiles.py`.

**What counts as a leaf.** A class is a leaf if it has its own valid SMILES
string that is *not* a wildcard/R-group placeholder (SMILES containing the dummy
atom `*`, e.g. `*C(N)C(=O)O`, are rejected via RDKit). This holds **regardless
of whether the class has subclasses** --- a parent class with a proper SMILES
(e.g. `proline`) is a leaf in its own right, alongside its more specific
children (e.g. `L-proline`, `D-proline`).

**Flattening the hierarchy (the "splice").** Because a leaf must be terminal,
whenever a class sits under a leaf it is reconnected to that leaf's nearest
*non-leaf* ancestors, climbing past chains of stacked leaves. So `L-proline`
stops pointing at the leaf `proline` and instead points directly at the real
category above it (e.g. `alpha-amino acid`), while keeping every other ancestor
it already had (e.g. `D-proline` keeps `D-alpha-amino acid`). After the splice,
no leaf is any class's parent, so all SMILES-bearing classes become siblings
under the genuine (non-leaf) category terms. A verification step asserts the
splice preserved every class's set of reachable non-leaf ancestors before any
file is written.

Run task *"remove_leaves_with_smiles"* to find leaf classes, splice the
hierarchy, and filter out deprecated classes. The following files are created:

- A filtered OWL file with the remaining classes (from `save_filtered_owl`). The
  current file in this workspace is
  `data/filtered_chebi_no_leaves_with_smiles_no_deprecated.owl`.
- A **flattened** subclass map JSON file (`data/chebi_subclass_map.json`)
  mapping all classes to their direct subclasses after the splice (from
  `find_leaf_classes_with_smiles_and_deprecated`). Leaves have no subclasses
  here; the file also includes deprecated classes.
- A leaf-to-parents map JSON file mapping each leaf class to all of its
  **non-leaf** ancestors (from `find_leaf_classes_with_smiles_and_deprecated`).
  This file is used in later calculations.

Run task *"build_parent_map"* to create:

- `data/chebi_parent_map.json`, a map of all classes to their direct parents
  after the splice (deprecated classes are excluded). It is derived from the
  flattened subclass map, so the graph built from it shows the same sibling
  structure.

Run task *"map_names_to_classes"* to build:

- `data/chebi_id_to_name_map.json`, which maps short CHEBI IDs (e.g.,
  `CHEBI_111`) to their names.

### 2.5 Save maps connected to the roles of the classes

Maps that include the roles of the classes are needed for some enrichment
calculations. These are made in `src/chebin/calculations/prepare_role_calculations.py`.

First, run the task *"find has_role connections"*. This parses the OWL file
directly and produces a map from all classes to their **direct** roles (not
including any roles that ancestors have):

- `data/class_to_direct_roles_map.json`

This task also calls `create_leaves_to_all_roles_map`, which writes

- `data/removed_leaf_classes_to_ALL_roles_map.json` (using
  `data/removed_leaf_classes_to_ALL_parents_map.json` and
  `data/chebi_parent_map.json`)

Second, run the task *"build leaf to all roles map"*. This builds:

- `data/removed_leaf_classes_to_ALL_roles_map.json`
- `data/roles_to_leaves_map.json`

The first file maps each removed leaf class to (a) its direct roles, (b) roles
inherited from ancestor classes, and (c) **ancestors of those roles** in the
role hierarchy. The second file is the inverse: it maps each role class to all
leaf classes connected to that role.

Note: because the hierarchy was flattened in step 2, a leaf inherits roles only
from its **non-leaf** ancestors. It no longer inherits roles asserted directly
on a leaf-ancestor --- e.g. `D-proline` no longer inherits roles (such as *human
metabolite*) that are asserted on the generic `proline`, which is now itself a
leaf. A leaf's own direct roles are always kept.

Third, run the task *"build class to all roles map"* to create:

- `data/class_to_all_roles_map.json`

Here, each class is mapped to its direct roles, roles inherited from ancestor
classes, and **descendants** of those roles in the role hierarchy.

### 3. Split up the ontology based on structure

Classes are sorted into structural vs. functional (role) sets by
`identify_structural_vs_functional()` in
`src/chebin/preparing_data/pruning_split_up_structure.py`, which walks the descendants of
the structural and role root classes and returns three sets of class IRIs:
`structural_classes`, `functional_classes`, and `unknown_classes` (classes under
neither root, kept only for troubleshooting). These three sets are what feeds
the `Classification` column of the CSV created in step 4 below.

There are two ways to obtain these sets, and `src/chebin/preparing_data/create_files.py`
uses the fast one:

- **Automated (fast) path --- used by `src/chebin/preparing_data/create_files.py`:**
  `identify_structural_vs_functional()` is called with the already-in-memory
  flattened subclass map (`data/chebi_subclass_map.json`, built in step 2), so
  descendants are found via plain dict lookups instead of per-node ontology API
  calls. The resulting class sets are passed straight into
  `save_leaf_classes_with_smiles()` (step 4) without ever touching disk --- no
  OWL files are written for this step.
- **Manual path --- `src/chebin/preparing_data/pruning_split_up_structure.py`, task
  *"split_structural_functional"*:** Run standalone, the function is called
  without the subclass map, so it falls back to the slower ontology API. The
  three class sets are then written out as separate OWL files via
  `split_owl_by_type()`, creating `_structural.owl`, `_functional.owl`, and
  `_unknown.owl` versions of the previously filtered ontology (e.g.
  `data/filtered_chebi_no_leaves_with_smiles_no_deprecated_structural.owl`).
  `src/chebin/preparing_data/pruning_smiles.py`'s *"save_removed_leaf_classes"* task (step 4)
  can then load these OWL files back in to recover the same three class sets, if
  run outside of `src/chebin/preparing_data/create_files.py`.

Since the splice in step 2 preserves every class's reachable non-leaf ancestors,
descendant sets for these (non-leaf) roots are the same whether collected from
the flattened subclass map or from live ontology traversal --- so the two paths
produce identical class sets. The OWL files are just an on-disk,
human-inspectable form of the same information, useful for manual runs or
debugging.

### 4. Save a file with the removed leaf classes

Go back to `src/chebin/preparing_data/pruning_smiles.py` and run task
*"save_removed_leaf_classes"* to save the removed leaf classes in a CSV file.
The current file in this workspace is

- `data/removed_leaf_classes_with_smiles.csv`

The CSV contains `IRI`, `SMILES`, and `Classification`, where the classification
is inferred from the class' direct parents in the structural/functional split.
Every leaf has a row here, including classes that have subclasses but carry
their own valid SMILES (e.g. `proline`); classes whose SMILES is a
wildcard/R-group placeholder are not leaves and do not appear. In ChEBI, classes
with SMILES are expected to fall under structural roots, so entries classified
as **functional** are likely misclassified and are excluded from downstream
calculations (they are kept in the file for troubleshooting).

### 5. Fisher's Calculations

First (only needed once), run task *"build_class_to_leaf_map"* in
`src/chebin/calculations/pre_fishers_calculations.py` to create
`data/class_to_leaf_descendants_map.json`, which maps each class to all of its
removed leaf descendants using
`data/removed_leaf_classes_to_ALL_parents_map.json`. Leaf classes are **not**
keys in this map: after the splice no leaf appears as another class's ancestor,
so only the genuine (non-leaf) category terms become keys. A leaf is therefore
only ever counted as a member of its categories, never tested as a category
itself.

Enrichment calculations can be run in `src/chebin/calculations/fishers_calculations.py`,
but this is easiest done via the web application. Either use the website link
(easiest since no preparation steps to obtain all the necessary files are
needed) or run `website/app.py` locally.

### 6. Needed for human dataset

1. Download LOTUS compound--taxon data from Wikidata via the QLever SPARQL
   endpoint using `src/chebin/preparing_data/wikidata/get_lotus.py`. This is run
   automatically by `src/chebin/preparing_data/create_files.py`, but can also be run
   standalone:

   ```bash
      python -m chebin.preparing_data.wikidata.get_lotus
   ```

   Output: - `data/lotus_homo_sapiens.csv` -
   `data/lotus_arabidopsis_thaliana.csv`

2. Connect the LOTUS CSVs to ChEBI IDs using `connect_lotus_csv_to_chebi_ids()`
   in `src/chebin/preparing_data/wikidata/get_wikidata_lotus.py`.

   Output: - `data/wikidata/created/lotus_homo_sapiens_with_chebi_ids.tsv` -
   `data/wikidata/created/lotus_arabidopsis_thaliana_with_chebi_ids.tsv`

3. Extract HMDB compounds using `extract_hmdb_to_file()` in
   `src/chebin/preparing_data/hmdb/extract_hmdb.py`.

   `data/hmdb_metabolites.xml` is required and must be downloaded manually from
   https://hmdb.ca/downloads (use the 'All Metabolites' XML).

   Output: `data/hmdb_metabolites_extract.tsv`

4. Filter HMDB to only keep compounds with status "quantified" or "detected"
   using `filter_hmdb_statuses_main()` in
   `src/chebin/preparing_data/hmdb/filter_hmdb_statuses.py`.

   Output: `data/hmdb_metabolites_extract_quantified_detected.tsv`

5. Find missing ChEBI IDs using `run_find_missing_chebis(source)` in
   `src/chebin/preparing_data/wikidata/find_missing_chebis.py` (also runnable via
   `jobs/run_find_missing_chebis.sh [source]`). The `source` argument must be
   one of the presets in `SOURCE_PRESETS`: `"lotus_hs"`, `"lotus_at"`, or
   `"hmdb"`.

   ChEBI ID matching is attempted in this order: - Direct ChEBI matches (LOTUS) -
   Exact SMILES match against ChEBI leaf classes - InChIKey match against ChEBI
   leaf classes - Chebifier API

   Output (depending on source): -
   `data/wikidata/created/lotus_homo_sapiens_with_chebi_ids_updatedchebis.tsv` -
   `data/wikidata/created/lotus_arabidopsis_thaliana_with_chebi_ids_updatedchebis.tsv` -
   `data/hmdb_metabolites_extract_quantified_detected_updatedchebis.tsv`

6. Combine HMDB and LOTUS Homo sapiens sources using `combine_datasets()` in
   `src/chebin/preparing_data/wikidata/combine_human_datasets.py`. Rows with no ChEBI ID
   are dropped.

   Output: `data/combined_hmdb_wikidata.tsv`

7. Create a file with the human leaf classes using `gather_narrow_leaves()` in
   `src/chebin/preparing_data/wikidata/narrow_background_fishers.py`.

   Files needed: - `compounds_tsv = "data/combined_hmdb_wikidata.tsv"` -
   `leaves_csv = "data/removed_leaf_classes_with_smiles.csv"` -
   `class_to_leaf_map = "data/class_to_leaf_descendants_map.json"` -
   `taxon_label = "homo_sapiens"` (recorded in the output JSON for traceability)

   Output: `data/human_entities_leaves.json`

### Narrow background for a single Wikidata taxon (e.g. Arabidopsis thaliana)

This is the same workflow as above, but since there is only one source
(Wikidata), steps 3, 4, and 6 (HMDB extraction/filtering and combining datasets)
are skipped entirely.

1. The Arabidopsis thaliana LOTUS CSV (`data/lotus_arabidopsis_thaliana.csv`)
   and its ChEBI-matched TSV
   (`data/wikidata/created/lotus_arabidopsis_thaliana_with_chebi_ids.tsv`) are
   already produced in steps 1--2 above.

2. Fill in any still-missing ChEBI IDs using the `"lotus_at"` preset in
   `src/chebin/preparing_data/wikidata/find_missing_chebis.py`.

   Output:
   `data/wikidata/created/lotus_arabidopsis_thaliana_with_chebi_ids_updatedchebis.tsv`

3. Build the leaf classes with `gather_narrow_leaves()` in
   `src/chebin/preparing_data/wikidata/narrow_background_fishers.py`, passing the file from
   step 2 as `compounds_tsv` and `taxon_label="arabidopsis_thaliana"`.

Output: `data/arabidopsis_thaliana_leaves.json`

### Endogenous human background (Recon3D)

This path is independent of steps 6 and the Wikidata/HMDB workflow above; it
only needs the files from steps 1--5
(`data/removed_leaf_classes_with_smiles.csv` and
`data/class_to_leaf_descendants_map.json`).

Run `src/chebin/preparing_data/BiGG/get_model.py`. This:

1. Downloads the Recon3D model JSON from BiGG
   (`http://bigg.ucsd.edu/static/models/Recon3D.json`) to `data/Recon3D.json`.
2. Calls `gather_recon3d_leaves()`, which collapses compartment-specific
   metabolite entries into unique compounds and resolves each to leaf ChEBI
   classes (directly, via parent expansion, or via UniChem InChIKey/HMDB
   cross-reference, as described above). Running the script prints a breakdown
   of how many compounds were resolved by each method, and how many were left
   unresolved.

Output: `data/recon3d_leaves.json` (same `narrow_leaves` JSON shape as the other
narrow backgrounds above, so it plugs into the website as
`NARROW_BACKGROUND_LEAVES_JSON['endogenous_human']` without further changes).
