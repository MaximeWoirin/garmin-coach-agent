"""Configuration locale du projet."""

from __future__ import annotations

import os
from pathlib import Path


def get_project_root() -> Path:
    """Retourne la racine du projet."""
    return Path(__file__).resolve().parent.parent


def get_db_path() -> Path:
    """Retourne le chemin de la base SQLite."""
    env_path = os.environ.get("GARMIN_COACH_DB")
    if env_path:
        return Path(env_path)
    return get_project_root() / "data" / "garmin_coach.db"


def get_tokens_dir() -> Path:
    """Retourne le répertoire de stockage des tokens Garmin."""
    env_path = os.environ.get("GARMIN_COACH_TOKENS_DIR")
    if env_path:
        return Path(env_path)
    return get_project_root() / "data" / "tokens"


def get_migrations_dir() -> Path:
    """Retourne le répertoire des fichiers de migration SQL."""
    return get_project_root() / "migrations"
