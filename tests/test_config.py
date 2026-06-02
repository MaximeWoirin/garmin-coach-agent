"""Tests pour garmin_coach.config."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from garmin_coach.config import (
    get_db_path,
    get_migrations_dir,
    get_project_root,
    get_tokens_dir,
)


def test_get_project_root() -> None:
    root = get_project_root()
    assert root.is_dir()
    assert (root / "pyproject.toml").exists()


def test_get_db_path_default() -> None:
    path = get_db_path()
    assert path.name == "garmin_coach.db"
    assert "data" in str(path)


def test_get_db_path_from_env() -> None:
    with patch.dict(os.environ, {"GARMIN_COACH_DB": "/tmp/custom.db"}):
        path = get_db_path()
        assert path == Path("/tmp/custom.db")


def test_get_tokens_dir_default() -> None:
    tdir = get_tokens_dir()
    assert tdir.name == "tokens"
    assert "data" in str(tdir)


def test_get_tokens_dir_from_env() -> None:
    with patch.dict(os.environ, {"GARMIN_COACH_TOKENS_DIR": "/tmp/tokens"}):
        tdir = get_tokens_dir()
        assert tdir == Path("/tmp/tokens")


def test_get_migrations_dir() -> None:
    mdir = get_migrations_dir()
    assert mdir.name == "migrations"
    assert mdir.is_dir()
