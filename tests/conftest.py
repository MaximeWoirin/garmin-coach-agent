"""Fixtures partagées pour les tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from garmin_coach.db import get_connection, run_migrations


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    """Retourne le chemin d'une base SQLite temporaire avec migrations appliquées."""
    db_path = tmp_path / "test.db"
    conn = get_connection(db_path)
    migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
    run_migrations(conn, migrations_dir)
    conn.close()
    return db_path


@pytest.fixture
def db_conn(tmp_db: Path) -> sqlite3.Connection:
    """Retourne une connexion SQLite ouverte sur la base temporaire."""
    conn = get_connection(tmp_db)
    yield conn  # type: ignore[misc]
    conn.close()


@pytest.fixture
def seeded_db(tmp_db: Path) -> Path:
    """Base avec des données de test pré-insérées."""
    conn = get_connection(tmp_db)

    # Goal
    conn.execute(
        """INSERT INTO training_goals (id, goal_code, primary_goal, priority, status)
           VALUES (1, 'marathon_2026', 'Finir un marathon', 'high', 'active')"""
    )

    # Constraint
    conn.execute(
        """INSERT INTO constraints (id, goal_id, type, severity, status, scope, start_date, raw_text)
           VALUES (1, 1, 'availability', 'medium', 'active', 'training', '2026-06-01', 'Pas dispo mardi')"""
    )
    conn.execute(
        """INSERT INTO constraints (id, goal_id, type, severity, status, scope, start_date, raw_text)
           VALUES (2, 1, 'health', 'high', 'inactive', 'life', '2026-05-15', 'Genou douloureux')"""
    )

    # Block
    conn.execute(
        """INSERT INTO training_blocks (id, goal_id, block_type, week_start, week_end)
           VALUES (1, 1, 'build', '2026-06-02', '2026-06-08')"""
    )

    # Plan
    conn.execute(
        """INSERT INTO training_plans (id, block_id, week_start, week_end, status, generated_by, confidence, needs_review)
           VALUES (1, 1, '2026-06-02', '2026-06-08', 'active', 'agent', 'high', 0)"""
    )
    conn.execute(
        """INSERT INTO training_plans (id, block_id, week_start, week_end, status, generated_by, confidence, needs_review, notes)
           VALUES (2, 1, '2026-06-09', '2026-06-15', 'draft', 'agent', 'medium', 1, 'Semaine allégée')"""
    )

    # Sessions
    conn.execute(
        """INSERT INTO plan_sessions (id, plan_id, planned_date, activity_type, duration_min, status)
           VALUES (1, 1, '2026-06-03', 'running', 45, 'proposed')"""
    )
    conn.execute(
        """INSERT INTO plan_sessions (id, plan_id, planned_date, activity_type, duration_min, status)
           VALUES (2, 1, '2026-06-05', 'running', 60, 'draft')"""
    )
    conn.execute(
        """INSERT INTO plan_sessions (id, plan_id, planned_date, activity_type, duration_min, status)
           VALUES (3, 2, '2026-06-10', 'cycling', 30, 'draft')"""
    )

    # Activities
    conn.execute(
        """INSERT INTO activities (id, source, external_id, activity_type, activity_name, start_time_utc, duration_s, distance_m, calories_kcal, avg_hr)
           VALUES (1, 'garmin', 'ext_001', 'running', 'Morning Run', '2026-06-03T07:00:00', 2700, 5000, 350, 145)"""
    )
    conn.execute(
        """INSERT INTO activities (id, source, external_id, activity_type, activity_name, start_time_utc, duration_s, distance_m, calories_kcal)
           VALUES (2, 'garmin', 'ext_002', 'cycling', 'Afternoon Ride', '2026-06-04T15:00:00', 3600, 20000, 500)"""
    )

    # Daily metrics
    conn.execute(
        """INSERT INTO daily_metrics (id, source, metric_date, steps, resting_hr, stress_avg, body_battery_end, intensity_minutes)
           VALUES (1, 'garmin', '2026-06-03', 8500, 55, 35, 65, 45)"""
    )
    conn.execute(
        """INSERT INTO daily_metrics (id, source, metric_date, steps, resting_hr, stress_avg, body_battery_end, intensity_minutes)
           VALUES (2, 'garmin', '2026-06-04', 10200, 54, 28, 70, 60)"""
    )

    conn.commit()
    conn.close()
    return tmp_db
