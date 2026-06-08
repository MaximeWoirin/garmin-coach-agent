"""Tests pour garmin_coach.db."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from garmin_coach.db import (
    ensure_db,
    fetchall_dicts,
    fetchone_dict,
    get_connection,
    run_migrations,
)


def test_get_connection(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = get_connection(db_path)
    assert conn is not None
    assert db_path.exists()
    # row_factory is set
    assert conn.row_factory == sqlite3.Row
    conn.close()


def test_get_connection_creates_parent_dirs(tmp_path: Path) -> None:
    db_path = tmp_path / "subdir" / "nested" / "test.db"
    conn = get_connection(db_path)
    assert db_path.exists()
    conn.close()


def test_run_migrations(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = get_connection(db_path)
    migrations_dir = Path(__file__).resolve().parent.parent / "garmin_coach" / "migrations"
    applied = run_migrations(conn, migrations_dir)
    assert len(applied) >= 3
    assert "0001_init" in applied
    conn.close()


def test_run_migrations_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = get_connection(db_path)
    migrations_dir = Path(__file__).resolve().parent.parent / "garmin_coach" / "migrations"
    first = run_migrations(conn, migrations_dir)
    second = run_migrations(conn, migrations_dir)
    assert len(first) >= 3
    assert len(second) == 0
    conn.close()


def test_ensure_db(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = ensure_db(db_path)
    # Tables should exist
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = [t[0] for t in tables]
    assert "training_goals" in table_names
    assert "activities" in table_names
    conn.close()


def test_fetchone_dict(db_conn: sqlite3.Connection) -> None:
    db_conn.execute(
        "INSERT INTO training_goals (goal_code, primary_goal, priority) VALUES ('g1', 'Run fast', 'high')"
    )
    db_conn.commit()
    result = fetchone_dict(db_conn, "SELECT * FROM training_goals WHERE goal_code=?", ("g1",))
    assert result is not None
    assert result["goal_code"] == "g1"
    assert result["primary_goal"] == "Run fast"


def test_fetchone_dict_none(db_conn: sqlite3.Connection) -> None:
    result = fetchone_dict(db_conn, "SELECT * FROM training_goals WHERE id=?", (999,))
    assert result is None


def test_fetchall_dicts(db_conn: sqlite3.Connection) -> None:
    db_conn.execute(
        "INSERT INTO training_goals (goal_code, primary_goal, priority) VALUES ('g1', 'Run', 'high')"
    )
    db_conn.execute(
        "INSERT INTO training_goals (goal_code, primary_goal, priority) VALUES ('g2', 'Bike', 'low')"
    )
    db_conn.commit()
    results = fetchall_dicts(db_conn, "SELECT * FROM training_goals ORDER BY goal_code")
    assert len(results) == 2
    assert results[0]["goal_code"] == "g1"
    assert results[1]["goal_code"] == "g2"


def test_fetchall_dicts_empty(db_conn: sqlite3.Connection) -> None:
    results = fetchall_dicts(db_conn, "SELECT * FROM training_goals")
    assert results == []
