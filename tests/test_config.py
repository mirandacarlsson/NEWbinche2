"""Tests for chebin.config -- how the package locates its generated data files."""

import os
from pathlib import Path

import pytest

from chebin.config import (
    ENV_VAR,
    data_path,
    get_data_dir,
    require_data_path,
    set_data_dir,
)


@pytest.fixture(autouse=True)
def _clean_config(monkeypatch):
    """Each test starts with no explicit dir and no env var set."""
    monkeypatch.delenv(ENV_VAR, raising=False)
    set_data_dir(None)
    yield
    set_data_dir(None)


def test_falls_back_to_cwd_data(monkeypatch, tmp_path):
    """The historical behaviour: <cwd>/data, so existing callers are unaffected."""
    monkeypatch.chdir(tmp_path)
    assert get_data_dir() == tmp_path / "data"


def test_env_var_overrides_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(ENV_VAR, "/from/env")
    assert get_data_dir() == Path("/from/env")


def test_explicit_overrides_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(ENV_VAR, "/from/env")
    set_data_dir("/explicit")
    assert get_data_dir() == Path("/explicit")


def test_clearing_explicit_falls_back_to_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(ENV_VAR, "/from/env")
    set_data_dir("/explicit")
    set_data_dir(None)
    assert get_data_dir() == Path("/from/env")


def test_resolution_is_per_call_not_import_time(monkeypatch, tmp_path):
    """set_data_dir must still take effect after `import chebin`."""
    monkeypatch.chdir(tmp_path)
    before = get_data_dir()
    set_data_dir(tmp_path / "somewhere_else")
    assert get_data_dir() != before
    assert get_data_dir() == tmp_path / "somewhere_else"


def test_data_path_joins_relative_names():
    set_data_dir("/data/root")
    assert data_path("chebi_parent_map.json") == os.path.join(
        "/data/root",
        "chebi_parent_map.json",
    )
    assert data_path("intermediate_files/x.tsv") == os.path.join(
        "/data/root",
        "intermediate_files/x.tsv",
    )


def test_require_data_path_returns_existing_file(tmp_path):
    set_data_dir(tmp_path)
    (tmp_path / "present.json").write_text("{}")
    assert require_data_path("present.json") == str(tmp_path / "present.json")


def test_require_data_path_error_names_dir_and_remedy(tmp_path):
    """A missing file must point at the data folder, not just a bare relative path."""
    set_data_dir(tmp_path)
    with pytest.raises(FileNotFoundError) as excinfo:
        require_data_path("absent.json")

    message = str(excinfo.value)
    assert str(tmp_path) in message
    assert "set_data_dir" in message
    assert ENV_VAR in message
