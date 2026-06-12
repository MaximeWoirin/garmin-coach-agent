"""Tests pour les débriefs post-activité."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from garmin_coach.debriefs.read import get_pending_debriefs
from garmin_coach.debriefs.write import save_activity_debrief
from garmin_coach.db import get_connection


def test_save_activity_debrief_creates_completed_row(seeded_db: Path) -> None:
    result = save_activity_debrief(
        activity_id=1,
        rpe=7,
        note="Sortie ok, un peu lourd sur la fin",
        pain_after=2,
        db_path=seeded_db,
    )

    assert result["status"] == "success"
    assert result["debrief_status"] == "completed"
    assert result["plan_session_id"] == 1
    assert result["rpe"] == 7
    assert result["pain_after"] == 2

    conn = get_connection(seeded_db)
    row = conn.execute(
        "SELECT status, plan_session_id, rpe, note FROM activity_debriefs WHERE activity_id=1"
    ).fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "completed"
    assert row[1] == 1
    assert row[2] == 7
    assert row[3] == "Sortie ok, un peu lourd sur la fin"


def test_save_activity_debrief_is_immutable_once_completed(seeded_db: Path) -> None:
    first = save_activity_debrief(activity_id=1, rpe=6, db_path=seeded_db)
    assert first["status"] == "success"

    second = save_activity_debrief(activity_id=1, rpe=8, note="update", db_path=seeded_db)
    assert second["status"] == "failed"
    assert "immutable" in second["errors"][0]


def test_save_activity_debrief_completes_existing_pending_row(seeded_db: Path) -> None:
    conn = get_connection(seeded_db)
    conn.execute(
        "INSERT INTO activity_debriefs (activity_id, status, prompt_count) VALUES (2, 'pending', 1)"
    )
    conn.commit()
    conn.close()

    result = save_activity_debrief(
        activity_id=2,
        rpe=5,
        note="Séance hors plan mais bonnes sensations",
        pain_during=0,
        db_path=seeded_db,
    )

    assert result["status"] == "success"
    assert result["debrief_status"] == "completed"
    assert result["plan_session_id"] is None


def test_get_pending_debriefs_creates_rows_and_filters_completed(seeded_db: Path) -> None:
    completed = save_activity_debrief(activity_id=1, rpe=6, db_path=seeded_db)
    assert completed["status"] == "success"

    result = get_pending_debriefs(
        lookback_hours=48,
        min_age_minutes=15,
        reprompt_after_hours=12,
        max_prompt_count=2,
        limit=10,
        db_path=seeded_db,
        now=datetime(2026, 6, 4, 18, 0, 0, tzinfo=UTC),
    )

    assert result["status"] == "success"
    assert result["summary"]["rows_created"] >= 1
    assert len(result["pending_debriefs"]) == 1
    pending = result["pending_debriefs"][0]
    assert pending["activity_id"] == 2
    assert pending["debrief_status"] == "pending"
    assert pending["plan_session_id"] is None


def test_get_pending_debriefs_respects_prompt_cooldown(seeded_db: Path) -> None:
    first = save_activity_debrief(activity_id=1, rpe=6, db_path=seeded_db)
    assert first["status"] == "success"

    conn = get_connection(seeded_db)
    conn.execute(
        """
        INSERT INTO activity_debriefs (
            activity_id, status, prompt_count, first_prompted_at, last_prompted_at
        ) VALUES (2, 'prompted', 2, '2026-06-04T15:30:00', '2026-06-04T17:30:00')
        """
    )
    conn.commit()
    conn.close()

    result = get_pending_debriefs(
        lookback_hours=48,
        min_age_minutes=15,
        reprompt_after_hours=12,
        max_prompt_count=2,
        limit=10,
        db_path=seeded_db,
        now=datetime(2026, 6, 4, 18, 0, 0, tzinfo=UTC),
    )

    assert result["status"] == "success"
    assert result["pending_debriefs"] == []
