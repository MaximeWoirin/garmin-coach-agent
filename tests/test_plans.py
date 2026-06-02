"""Tests pour garmin_coach.plans (read, status, write)."""

from __future__ import annotations

import json
from pathlib import Path

from garmin_coach.plans.read import get_current_plan, get_goals
from garmin_coach.plans.status import set_plan_session_status, set_plan_status
from garmin_coach.plans.write import create_plan_draft, create_plan_session, delete_plan_session


# --- Tests lecture plans ---


def test_get_current_plan_active(seeded_db: Path) -> None:
    result = get_current_plan(db_path=seeded_db)
    assert result["status"] == "success"
    assert result["plan_id"] == 2  # draft is also matched, most recent week
    assert result["plan_status"] in ("active", "draft")


def test_get_current_plan_by_id(seeded_db: Path) -> None:
    result = get_current_plan(plan_id=1, db_path=seeded_db)
    assert result["status"] == "success"
    assert result["plan_id"] == 1
    assert result["plan_status"] == "active"


def test_get_current_plan_by_week(seeded_db: Path) -> None:
    result = get_current_plan(week_start="2026-06-02", db_path=seeded_db)
    assert result["status"] == "success"
    assert result["plan_id"] == 1


def test_get_current_plan_with_sessions(seeded_db: Path) -> None:
    result = get_current_plan(plan_id=1, include_sessions=True, db_path=seeded_db)
    assert "sessions" in result
    assert result["sessions_count"] == 2


def test_get_current_plan_without_sessions(seeded_db: Path) -> None:
    result = get_current_plan(plan_id=1, include_sessions=False, db_path=seeded_db)
    assert "sessions" not in result


def test_get_current_plan_not_found(tmp_db: Path) -> None:
    result = get_current_plan(db_path=tmp_db)
    assert result["status"] == "failed"
    assert "No active or draft plan found" in result["errors"][0]


# --- Tests lecture goals ---


def test_get_goals(seeded_db: Path) -> None:
    result = get_goals(db_path=seeded_db)
    assert result["status"] == "success"
    assert result["summary"]["count"] == 1


def test_get_goals_with_limit(seeded_db: Path) -> None:
    result = get_goals(limit=1, db_path=seeded_db)
    assert result["summary"]["count"] == 1


def test_get_goals_include_archived(seeded_db: Path) -> None:
    result = get_goals(include_archived=True, db_path=seeded_db)
    assert result["status"] == "success"


# --- Tests statut plans ---


def test_set_plan_status_draft_to_active(seeded_db: Path) -> None:
    result = set_plan_status(plan_id=2, status="active", db_path=seeded_db)
    assert result["status"] == "success"
    assert result["plan_status"] == "active"


def test_set_plan_status_active_to_sent_rejected(seeded_db: Path) -> None:
    """SENT is no longer a valid target in the workflow."""
    result = set_plan_status(plan_id=1, status="sent", db_path=seeded_db)
    assert result["status"] == "failed"
    assert "Invalid transition" in result["errors"][0]


def test_set_plan_status_invalid_transition(seeded_db: Path) -> None:
    result = set_plan_status(plan_id=1, status="draft", db_path=seeded_db)
    assert result["status"] == "failed"
    assert "Invalid transition" in result["errors"][0]


def test_set_plan_status_invalid_value(seeded_db: Path) -> None:
    result = set_plan_status(plan_id=1, status="bogus", db_path=seeded_db)
    assert result["status"] == "failed"
    assert "Invalid plan status" in result["errors"][0]


def test_set_plan_status_not_found(seeded_db: Path) -> None:
    result = set_plan_status(plan_id=999, status="active", db_path=seeded_db)
    assert result["status"] == "failed"
    assert "not found" in result["errors"][0]


def test_set_plan_status_dry_run(seeded_db: Path) -> None:
    result = set_plan_status(plan_id=2, status="active", dry_run=True, db_path=seeded_db)
    assert result["status"] == "success"
    assert result["dry_run"] is True


def test_set_plan_status_cascade_sessions(seeded_db: Path) -> None:
    # Plan 2 is draft with session 3 in draft → activate should cascade to proposed
    result = set_plan_status(plan_id=2, status="active", cascade_sessions=True, db_path=seeded_db)
    assert result["status"] == "success"
    assert len(result["session_status_changes"]) == 1
    assert result["session_status_changes"][0]["new_status"] == "proposed"


def test_set_plan_status_cascade_archive(seeded_db: Path) -> None:
    # Plan 1 is active with proposed/draft sessions → archive should cancel them
    result = set_plan_status(plan_id=1, status="archived", cascade_sessions=True, db_path=seeded_db)
    assert result["status"] == "success"
    assert len(result["session_status_changes"]) == 2


# --- Tests statut sessions ---


def test_set_plan_session_status_proposed_to_exported(seeded_db: Path) -> None:
    result = set_plan_session_status(plan_id=1, session_id=1, status="exported", db_path=seeded_db)
    assert result["status"] == "success"
    assert result["session_status"] == "exported"


def test_set_plan_session_status_draft_to_proposed(seeded_db: Path) -> None:
    result = set_plan_session_status(plan_id=1, session_id=2, status="proposed", db_path=seeded_db)
    assert result["status"] == "success"


def test_set_plan_session_status_invalid_transition(seeded_db: Path) -> None:
    # proposed → draft not allowed
    result = set_plan_session_status(plan_id=1, session_id=1, status="draft", db_path=seeded_db)
    assert result["status"] == "failed"
    assert "Invalid transition" in result["errors"][0]


def test_set_plan_session_status_invalid_value(seeded_db: Path) -> None:
    result = set_plan_session_status(plan_id=1, session_id=1, status="bogus", db_path=seeded_db)
    assert result["status"] == "failed"


def test_set_plan_session_status_not_found(seeded_db: Path) -> None:
    result = set_plan_session_status(plan_id=1, session_id=999, status="exported", db_path=seeded_db)
    assert result["status"] == "failed"
    assert "not found" in result["errors"][0]


def test_set_plan_session_status_dry_run(seeded_db: Path) -> None:
    result = set_plan_session_status(plan_id=1, session_id=1, status="exported", dry_run=True, db_path=seeded_db)
    assert result["status"] == "success"
    assert result["dry_run"] is True


# --- Tests écriture plans ---


def test_create_plan_draft_success(seeded_db: Path) -> None:
    result = create_plan_draft(
        week_start="2026-06-16", week_end="2026-06-22", db_path=seeded_db
    )
    assert result["status"] == "success"
    assert result["plan_id"] is not None
    assert result["plan_status"] == "draft"


def test_create_plan_draft_with_block(seeded_db: Path) -> None:
    result = create_plan_draft(
        week_start="2026-06-16", week_end="2026-06-22", block_id=1, db_path=seeded_db
    )
    assert result["status"] == "success"


def test_create_plan_draft_invalid_block(seeded_db: Path) -> None:
    result = create_plan_draft(
        week_start="2026-06-16", week_end="2026-06-22", block_id=999, db_path=seeded_db
    )
    assert result["status"] == "failed"
    assert "Block 999 not found" in result["errors"][0]


def test_create_plan_draft_invalid_dates(seeded_db: Path) -> None:
    result = create_plan_draft(week_start="2026-06-22", week_end="2026-06-16", db_path=seeded_db)
    assert result["status"] == "failed"
    assert "week_start must be before week_end" in result["errors"][0]


def test_create_plan_draft_dry_run(seeded_db: Path) -> None:
    result = create_plan_draft(
        week_start="2026-06-16", week_end="2026-06-22", dry_run=True, db_path=seeded_db
    )
    assert result["status"] == "success"
    assert result["dry_run"] is True
    assert result["plan_id"] is None


def test_create_plan_draft_with_sessions(seeded_db: Path) -> None:
    sessions = json.dumps([
        {"planned_date": "2026-06-17", "activity_type": "running", "duration_min": 40},
        {"planned_date": "2026-06-19", "activity_type": "cycling", "duration_min": 60},
    ])
    result = create_plan_draft(
        week_start="2026-06-16", week_end="2026-06-22",
        sessions_json=sessions, db_path=seeded_db,
    )
    assert result["status"] == "success"
    assert result["sessions_created"] == 2


def test_create_plan_draft_invalid_metadata(seeded_db: Path) -> None:
    result = create_plan_draft(
        week_start="2026-06-16", week_end="2026-06-22",
        metadata_json="not-json{", db_path=seeded_db,
    )
    assert result["status"] == "failed"
    assert "Invalid metadata_json" in result["errors"][0]


def test_create_plan_draft_with_title(seeded_db: Path) -> None:
    result = create_plan_draft(
        week_start="2026-06-16", week_end="2026-06-22",
        title="Semaine de récupération", db_path=seeded_db,
    )
    assert result["status"] == "success"


# --- Tests sessions ---


def test_create_plan_session_success(seeded_db: Path) -> None:
    result = create_plan_session(
        plan_id=1, planned_date="2026-06-04", activity_type="swimming", duration_min=30,
        db_path=seeded_db,
    )
    assert result["status"] == "success"
    assert result["session_id"] is not None


def test_create_plan_session_invalid_status(seeded_db: Path) -> None:
    result = create_plan_session(
        plan_id=1, planned_date="2026-06-04", activity_type="running",
        duration_min=30, status="bogus", db_path=seeded_db,
    )
    assert result["status"] == "failed"


def test_create_plan_session_plan_not_found(seeded_db: Path) -> None:
    result = create_plan_session(
        plan_id=999, planned_date="2026-06-04", activity_type="running",
        duration_min=30, db_path=seeded_db,
    )
    assert result["status"] == "failed"
    assert "Plan 999 not found" in result["errors"][0]


def test_create_plan_session_dry_run(seeded_db: Path) -> None:
    result = create_plan_session(
        plan_id=1, planned_date="2026-06-04", activity_type="running",
        duration_min=30, dry_run=True, db_path=seeded_db,
    )
    assert result["status"] == "success"
    assert result["dry_run"] is True


def test_delete_plan_session_success(seeded_db: Path) -> None:
    result = delete_plan_session(plan_id=1, session_id=2, db_path=seeded_db)
    assert result["status"] == "success"


def test_delete_plan_session_not_found(seeded_db: Path) -> None:
    result = delete_plan_session(plan_id=1, session_id=999, db_path=seeded_db)
    assert result["status"] == "failed"


def test_delete_plan_session_dry_run(seeded_db: Path) -> None:
    result = delete_plan_session(plan_id=1, session_id=2, dry_run=True, db_path=seeded_db)
    assert result["status"] == "success"
    assert result["dry_run"] is True


# --- Tests workflow progressif: suppression et statuts ---


def test_delete_plan_session_draft_ok(seeded_db: Path) -> None:
    """A draft session can be deleted."""
    result = delete_plan_session(plan_id=1, session_id=2, db_path=seeded_db)
    assert result["status"] == "success"


def test_delete_plan_session_proposed_ok(seeded_db: Path) -> None:
    """A proposed session can be deleted."""
    result = delete_plan_session(plan_id=1, session_id=1, db_path=seeded_db)
    assert result["status"] == "success"


def test_delete_plan_session_exported_refused(seeded_db: Path) -> None:
    """An exported session cannot be deleted."""
    from garmin_coach.db import get_connection

    conn = get_connection(seeded_db)
    conn.execute("UPDATE plan_sessions SET status='exported' WHERE id=1")
    conn.commit()
    conn.close()

    result = delete_plan_session(plan_id=1, session_id=1, db_path=seeded_db)
    assert result["status"] == "failed"
    assert "Cannot delete" in result["errors"][0]


def test_set_plan_status_sent_to_active_compat(seeded_db: Path) -> None:
    """Legacy plans in SENT status can migrate to ACTIVE."""
    from garmin_coach.db import get_connection

    conn = get_connection(seeded_db)
    conn.execute("UPDATE training_plans SET status='sent' WHERE id=1")
    conn.commit()
    conn.close()

    result = set_plan_status(plan_id=1, status="active", db_path=seeded_db)
    assert result["status"] == "success"
    assert result["plan_status"] == "active"


def test_set_plan_status_no_implicit_export(seeded_db: Path) -> None:
    """Activating a plan does not export sessions to Garmin."""
    result = set_plan_status(plan_id=2, status="active", cascade_sessions=True, db_path=seeded_db)
    assert result["status"] == "success"
    # Sessions go from draft to proposed, not to exported
    for change in result["session_status_changes"]:
        assert change["new_status"] == "proposed"


def test_recreate_session_after_delete(seeded_db: Path) -> None:
    """After deleting a local session, a new one can be created."""
    result = delete_plan_session(plan_id=1, session_id=1, db_path=seeded_db)
    assert result["status"] == "success"

    result = create_plan_session(
        plan_id=1, planned_date="2026-06-03", activity_type="running",
        duration_min=50, db_path=seeded_db,
    )
    assert result["status"] == "success"
    assert result["session_id"] is not None
