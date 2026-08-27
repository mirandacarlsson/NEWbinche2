"""Where `chebin` looks for its generated data files.

The analysis functions need the files produced by
:func:`chebin.preparing_data.create_files.create_all_files` -- the leaf/parent maps, the
role maps and so on. Historically their paths were hardcoded as bare ``"data/..."``
strings, which only resolve when the process happens to be running from inside the
project folder. That is fine for the website (it chdirs on startup) but makes the package
unusable anywhere else.

Resolution order, highest priority first:

1. an explicit :func:`set_data_dir` call,
2. the ``CHEBIN_DATA_DIR`` environment variable,
3. ``<cwd>/data`` -- the historical behaviour, kept so existing callers are unaffected.

Paths are resolved when they are *used*, not when a module is imported, so
:func:`set_data_dir` still takes effect after ``import chebin``.
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_VAR = "CHEBIN_DATA_DIR"

_data_dir: Path | None = None


def set_data_dir(path: str | os.PathLike[str] | None) -> None:
    """Point chebin at the folder holding the generated data files.

    Pass ``None`` to clear an earlier call and fall back to ``$CHEBIN_DATA_DIR`` or
    ``<cwd>/data``.
    """
    global _data_dir
    _data_dir = None if path is None else Path(path)


def get_data_dir() -> Path:
    """The data folder currently in effect. Not guaranteed to exist."""
    if _data_dir is not None:
        return _data_dir
    from_env = os.environ.get(ENV_VAR)
    if from_env:
        return Path(from_env)
    return Path.cwd() / "data"


def data_path(name: str) -> str:
    """Absolute path of ``name`` inside the data folder.

    ``name`` is a path relative to the data folder, e.g.
    ``"chebi_parent_map.json"`` or ``"intermediate_files/foo.tsv"``.
    """
    return str(get_data_dir() / name)


def require_data_path(name: str) -> str:
    """Like :func:`data_path`, but fail loudly and usefully if the file is missing.

    Without this a missing data folder surfaces as a bare ``FileNotFoundError`` naming a
    relative path, which gives no hint that the *data folder* is what is misconfigured.
    """
    path = data_path(name)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. chebin is resolving data files against "
            f"'{get_data_dir()}'. Point it at the right folder with "
            f"chebin.set_data_dir(...) or the {ENV_VAR} environment variable, and make "
            f"sure create_all_files() has been run to generate the data.",
        )
    return path
