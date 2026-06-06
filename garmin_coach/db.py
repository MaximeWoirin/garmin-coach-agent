"""Couche d'accès SQLite et runner de migrations."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from garmin_coach.config import get_db_path, get_migrations_dir
from garmin_coach.logging import get_logger

logger = get_logger("db")


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Ouvre une connexion SQLite avec row_factory."""
    path = db_path or get_db_path()
    logger.debug("Opening SQLite connection", extra={"db_path": str(path)})
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def run_migrations(conn: sqlite3.Connection, migrations_dir: Path | None = None) -> list[str]:
    """Applique les migrations manquantes dans l'ordre.

    Returns:
        Liste des versions appliquées lors de cet appel.
    """
    mdir = migrations_dir or get_migrations_dir()
    logger.debug("Running SQL migrations", extra={"migrations_dir": str(mdir)})

    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    applied: set[str] = {
        row[0] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
    }

    migration_files = sorted(mdir.glob("*.sql"))
    newly_applied: list[str] = []

    for mfile in migration_files:
        version = mfile.stem
        if version in applied:
            continue
        logger.info("Applying database migration", extra={"version": version})
        sql = mfile.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
        conn.commit()
        newly_applied.append(version)

    if newly_applied:
        logger.info("Applied migrations successfully", extra={"applied_versions": newly_applied})
    else:
        logger.debug("Database schema is up to date")

    return newly_applied


def ensure_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Ouvre la base et applique les migrations manquantes."""
    conn = get_connection(db_path)
    run_migrations(conn)
    return conn


@contextmanager
def db_connection(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Ouvre une connexion SQLite prête à l'emploi et la referme toujours."""
    conn = ensure_db(db_path)
    try:
        yield conn
    finally:
        conn.close()


def fetchone_dict(
    conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()
) -> dict[str, Any] | None:
    """Exécute une requête et retourne une seule ligne comme dict."""
    row = conn.execute(sql, params).fetchone()
    if row is None:
        return None
    return dict(row)


def fetchall_dicts(
    conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()
) -> list[dict[str, Any]]:
    """Exécute une requête et retourne toutes les lignes comme liste de dicts."""
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]
