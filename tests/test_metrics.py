"""Tests pour garmin_coach.metrics.read."""

from __future__ import annotations

from pathlib import Path

from garmin_coach.metrics.read import get_fitness_state


def test_get_fitness_state_basic(seeded_db: Path) -> None:
    result = get_fitness_state(start="2026-06-01", end="2026-06-10", db_path=seeded_db)
    assert result["status"] == "success"
    assert len(result["daily_metrics"]) == 2


def test_get_fitness_state_summary(seeded_db: Path) -> None:
    result = get_fitness_state(start="2026-06-01", end="2026-06-10", db_path=seeded_db)
    summary = result["summary"]
    assert summary["days"] == 2
    assert summary["avg_resting_hr"] == 54.5
    assert summary["signal"] == "neutral"  # avg_stress=31.5 (not < 30)


def test_get_fitness_state_empty(seeded_db: Path) -> None:
    result = get_fitness_state(start="2026-01-01", end="2026-01-02", db_path=seeded_db)
    assert result["status"] == "success"
    assert result["daily_metrics"] == []
    assert result["summary"]["days"] == 0
    assert result["summary"]["signal"] == "no_data"


def test_get_fitness_state_with_limit(seeded_db: Path) -> None:
    result = get_fitness_state(start="2026-06-01", end="2026-06-10", limit=1, db_path=seeded_db)
    assert len(result["daily_metrics"]) == 1


def test_get_fitness_state_fatigue_signal(tmp_db: Path) -> None:
    """Test the fatigue signal path."""
    from garmin_coach.db import get_connection

    conn = get_connection(tmp_db)
    conn.execute(
        """INSERT INTO daily_metrics (source, metric_date, stress_avg, body_battery_end, resting_hr)
           VALUES ('garmin', '2026-06-01', 60, 25, 70)"""
    )
    conn.commit()
    conn.close()

    result = get_fitness_state(start="2026-06-01", end="2026-06-02", db_path=tmp_db)
    assert result["summary"]["signal"] == "fatigue"


def test_get_fitness_state_neutral_signal(tmp_db: Path) -> None:
    """Test the neutral signal path."""
    from garmin_coach.db import get_connection

    conn = get_connection(tmp_db)
    conn.execute(
        """INSERT INTO daily_metrics (source, metric_date, stress_avg, body_battery_end, resting_hr)
           VALUES ('garmin', '2026-06-01', 40, 50, 60)"""
    )
    conn.commit()
    conn.close()

    result = get_fitness_state(start="2026-06-01", end="2026-06-02", db_path=tmp_db)
    assert result["summary"]["signal"] == "neutral"
