"""Tests pour garmin_coach.garmin (auth, client, sync, export) avec mocks."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from garmin_coach.db import get_connection
from garmin_coach.garmin.auth import authenticate
from garmin_coach.garmin.client import get_client
from garmin_coach.garmin.export import (
    _build_workout_payload,
    _map_activity_type_to_sport,
    export_plan,
)
from garmin_coach.garmin.sync import sync

# --- Tests auth ---


def test_authenticate_no_tokens_no_creds(tmp_path: Path) -> None:
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()
    result = authenticate(tokens_dir=tokens_dir, force_login=True)
    assert result["status"] == "failed"
    assert "Email and password required" in result["errors"][0]


@patch("garmin_coach.garmin.auth.Garmin")
def test_authenticate_full_login_success(mock_garmin: MagicMock, tmp_path: Path) -> None:
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()

    mock_client = MagicMock()
    mock_garmin.return_value = mock_client

    result = authenticate(
        email="user@test.com", **{"password": "test123"},
        tokens_dir=tokens_dir, force_login=True,
    )
    assert result["status"] == "success"
    assert "tokens_path" in result
    mock_client.login.assert_called_once()


@patch("garmin_coach.garmin.auth.Garmin")
def test_authenticate_full_login_failure(mock_garmin: MagicMock, tmp_path: Path) -> None:
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()

    mock_client = MagicMock()
    mock_client.login.side_effect = Exception("Auth failed")
    mock_garmin.return_value = mock_client

    result = authenticate(
        email="user@test.com", **{"password": "test123"},
        tokens_dir=tokens_dir, force_login=True,
    )
    assert result["status"] == "failed"
    assert "Authentication failed" in result["errors"][0]


@patch("garmin_coach.garmin.auth.Garmin")
def test_authenticate_reuse_tokens(mock_garmin: MagicMock, tmp_path: Path) -> None:
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()
    (tokens_dir / "token.dat").write_text("fake")

    mock_client = MagicMock()
    mock_garmin.return_value = mock_client

    result = authenticate(tokens_dir=tokens_dir)
    assert result["status"] == "success"
    assert any("Reused existing tokens" in w for w in result["warnings"])


@patch("garmin_coach.garmin.auth.Garmin")
def test_authenticate_reuse_tokens_invalid_fallback(mock_garmin: MagicMock, tmp_path: Path) -> None:
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()
    (tokens_dir / "token.dat").write_text("fake")

    mock_client = MagicMock()
    mock_client.login.side_effect = Exception("Invalid token")
    mock_garmin.return_value = mock_client

    result = authenticate(tokens_dir=tokens_dir)
    assert result["status"] == "failed"
    assert "Email and password required" in result["errors"][0]


# --- Tests client ---


def test_get_client_no_tokens_dir(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        get_client(tokens_dir=tmp_path / "nonexistent")


# --- Tests export helpers ---


def test_build_workout_payload_from_session() -> None:
    session = {
        "activity_type": "running",
        "planned_date": "2026-06-03",
        "duration_min": 45,
        "intensity": "moderate",
        "workout_payload_json": None,
    }
    payload = _build_workout_payload(session)
    assert payload["workoutName"] == "running - 2026-06-03"
    assert payload["estimatedDurationInSecs"] == 45 * 60
    assert payload["sportType"]["sportTypeKey"] == "running"


def test_build_workout_payload_from_json() -> None:
    custom_payload = {"workoutName": "Custom", "steps": []}
    session = {
        "workout_payload_json": json.dumps(custom_payload),
    }
    result = _build_workout_payload(session)
    assert result == custom_payload


def test_build_workout_payload_from_session_payload_json() -> None:
    session_payload = {
        "schemaVersion": 1,
        "sport": "running",
        "format": "structured",
        "title": "6 x 400m",
        "description": "Séance piste",
        "items": [
            {
                "kind": "step",
                "stepType": "warmup",
                "endCondition": {"type": "time", "valueSec": 600},
            },
            {
                "kind": "repeat",
                "repeatCount": 6,
                "items": [
                    {
                        "kind": "step",
                        "stepType": "interval",
                        "endCondition": {"type": "distance", "valueMeters": 400},
                        "target": {"type": "pace", "valueSecPerKm": 240},
                        "comment": "400m vite",
                    },
                    {
                        "kind": "step",
                        "stepType": "recovery",
                        "endCondition": {"type": "time", "valueSec": 90},
                        "target": {"type": "heart_rate_zone", "zone": 2},
                    },
                ],
            },
            {
                "kind": "step",
                "stepType": "cooldown",
                "endCondition": {"type": "lap_button"},
            },
        ],
    }
    session = {
        "activity_type": "running",
        "planned_date": "2026-06-03",
        "duration_min": 45,
        "notes": "Rester propre",
        "session_payload_json": json.dumps(session_payload),
        "workout_payload_json": None,
    }

    payload = _build_workout_payload(session)

    assert payload["workoutName"] == "6 x 400m"
    assert payload["estimatedDurationInSecs"] == 1716
    assert payload["description"] == "Séance piste"
    assert payload["sportType"]["sportTypeKey"] == "running"
    steps = payload["workoutSegments"][0]["workoutSteps"]
    assert steps[0]["stepType"]["stepTypeKey"] == "warmup"
    assert steps[1]["type"] == "RepeatGroupDTO"
    assert steps[1]["numberOfIterations"] == 6
    assert steps[1]["workoutSteps"][0]["targetType"]["workoutTargetTypeKey"] == "pace.zone"
    assert steps[1]["workoutSteps"][1]["zoneNumber"] == 2
    assert steps[2]["endCondition"]["conditionTypeKey"] == "lap.button"


@patch("garmin_coach.garmin.export.get_client")
def test_export_plan_persists_generated_workout_payload(mock_get_client: MagicMock, seeded_db: Path) -> None:
    mock_client = MagicMock()
    mock_client.upload_workout.return_value = {"workoutId": 4242}
    mock_client.schedule_workout.return_value = {"ok": True}
    mock_get_client.return_value = mock_client

    session_payload = {
        "schemaVersion": 1,
        "sport": "running",
        "format": "structured",
        "title": "Tempo",
        "items": [
            {
                "kind": "step",
                "stepType": "interval",
                "endCondition": {"type": "time", "valueSec": 1200},
                "target": {"type": "heart_rate_zone", "zone": 4},
            }
        ],
    }

    conn = get_connection(seeded_db)
    conn.execute(
        "UPDATE plan_sessions SET session_payload_json=? WHERE id=1",
        (json.dumps(session_payload),),
    )
    conn.commit()
    conn.close()

    result = export_plan(plan_id=1, db_path=seeded_db)
    assert result["status"] == "success"

    conn = get_connection(seeded_db)
    row = conn.execute(
        "SELECT status, garmin_event_id, workout_payload_json FROM plan_sessions WHERE id=1",
    ).fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "exported"
    assert row[1] == "4242"
    assert json.loads(row[2])["workoutName"] == "Tempo"


def test_build_workout_payload_prefers_single_clean_description() -> None:
    session_payload = {
        "schemaVersion": 1,
        "sport": "running",
        "format": "structured",
        "title": "Tempo",
        "description": "Description propre",
        "notes": "Notes payload",
        "items": [
            {
                "kind": "step",
                "stepType": "interval",
                "endCondition": {"type": "time", "valueSec": 1200},
            }
        ],
    }
    session = {
        "activity_type": "running",
        "planned_date": "2026-06-03",
        "duration_min": 45,
        "notes": "Notes session",
        "session_payload_json": json.dumps(session_payload),
        "workout_payload_json": None,
    }

    payload = _build_workout_payload(session)

    assert payload["description"] == "Description propre"


@pytest.mark.parametrize(
    ("activity_type", "sport_type_id", "sport_type_key"),
    [
        ("running", 1, "running"),
        ("trail", 1, "running"),
        ("cycling", 2, "cycling"),
        ("swimming", 4, "swimming"),
        ("strength", 5, "strength_training"),
        ("cardio", 6, "cardio_training"),
        ("yoga", 7, "yoga"),
        ("pilates", 8, "pilates"),
        ("hiit", 9, "hiit"),
        ("mobility", 11, "mobility"),
        ("walking", 12, "walking"),
        ("hiking", 12, "walking"),
        ("rucking", 13, "rucking"),
        ("climbing", 3, "other"),
        ("unknown_type", 3, "other"),
    ],
)
def test_map_activity_type_to_sport(
    activity_type: str,
    sport_type_id: int,
    sport_type_key: str,
) -> None:
    sport = _map_activity_type_to_sport(activity_type)
    assert sport["sportTypeId"] == sport_type_id
    assert sport["sportTypeKey"] == sport_type_key


def test_export_plan_not_found(seeded_db: Path) -> None:
    result = export_plan(plan_id=999, db_path=seeded_db)
    assert result["status"] == "failed"
    assert "Plan not found" in result["errors"][0]


def test_export_plan_no_plan_id_no_week(seeded_db: Path) -> None:
    result = export_plan(db_path=seeded_db)
    assert result["status"] == "failed"
    assert "Plan not found" in result["errors"][0]


def test_export_plan_dry_run(seeded_db: Path) -> None:
    result = export_plan(plan_id=1, dry_run=True, db_path=seeded_db)
    assert result["status"] == "success"
    # Only session 1 (proposed) is exported; session 2 (draft) is skipped
    assert result["sessions_exported"] == 1
    assert result["sessions_skipped"] == 1


def test_export_plan_by_week_start(seeded_db: Path) -> None:
    result = export_plan(week_start="2026-06-02", dry_run=True, db_path=seeded_db)
    assert result["status"] == "success"
    assert result["plan_id"] == 1


# --- Tests sync ---


@patch("garmin_coach.garmin.sync.get_client")
def test_sync_client_error(mock_get_client: MagicMock, seeded_db: Path) -> None:
    mock_get_client.side_effect = Exception("No tokens")
    from datetime import date

    result = sync(
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 3),
        db_path=seeded_db,
    )
    assert result["status"] == "failed"
    assert "Garmin client error" in result["errors"][0]


@patch("garmin_coach.garmin.sync.get_client")
def test_sync_success(mock_get_client: MagicMock, seeded_db: Path) -> None:
    mock_client = MagicMock()
    mock_client.get_activities_by_date.return_value = [
        {
            "activityId": "new_001",
            "activityType": {"typeKey": "running"},
            "activityName": "Easy run",
            "startTimeGMT": "2026-06-01T08:00:00",
            "duration": 1800,
            "distance": 4000,
        }
    ]
    mock_client.get_stats.return_value = {
        "totalSteps": 9000,
        "restingHeartRate": 56,
    }
    mock_get_client.return_value = mock_client
    from datetime import date

    result = sync(
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 1),
        db_path=seeded_db,
    )
    assert result["status"] == "success"
    assert result["activities_seen"] == 1
    assert result["activities_inserted"] == 1


@patch("garmin_coach.garmin.sync.get_client")
def test_sync_activity_update(mock_get_client: MagicMock, seeded_db: Path) -> None:
    """Test updating an existing activity."""
    mock_client = MagicMock()
    # ext_001 already exists in seeded_db
    mock_client.get_activities_by_date.return_value = [
        {
            "activityId": "ext_001",
            "activityType": {"typeKey": "running"},
            "activityName": "Updated run",
            "startTimeGMT": "2026-06-03T07:00:00",
            "duration": 2800,
        }
    ]
    mock_client.get_stats.return_value = None
    mock_get_client.return_value = mock_client
    from datetime import date

    result = sync(
        start_date=date(2026, 6, 3),
        end_date=date(2026, 6, 3),
        db_path=seeded_db,
    )
    assert result["status"] == "success"
    assert result["activities_updated"] == 1
    assert result["activities_inserted"] == 0


@patch("garmin_coach.garmin.sync.get_client")
def test_sync_partial_errors(mock_get_client: MagicMock, seeded_db: Path) -> None:
    """Test partial failure during sync."""
    mock_client = MagicMock()
    mock_client.get_activities_by_date.side_effect = Exception("API error")
    mock_client.get_stats.return_value = {"totalSteps": 5000}
    mock_get_client.return_value = mock_client
    from datetime import date

    result = sync(
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 1),
        db_path=seeded_db,
    )
    assert result["status"] == "partial"
    assert any("Activities sync error" in e for e in result["errors"])


# --- Tests export workflow progressif ---


def test_export_plan_only_proposed_sessions(seeded_db: Path) -> None:
    """Only sessions with status 'proposed' are exported."""
    result = export_plan(plan_id=1, dry_run=True, db_path=seeded_db)
    assert result["status"] == "success"
    # Session 1 = proposed, session 2 = draft
    assert result["sessions_exported"] == 1
    assert result["sessions_skipped"] == 1


def test_export_plan_ignores_draft_sessions(seeded_db: Path) -> None:
    """Draft sessions are not exported."""
    # Plan 2 has only a draft session
    result = export_plan(plan_id=2, dry_run=True, db_path=seeded_db)
    assert result["status"] == "success"
    assert result["sessions_exported"] == 0
    assert result["sessions_skipped"] == 1


def test_export_plan_ignores_done_skipped_canceled(seeded_db: Path) -> None:
    """Sessions with terminal status are skipped."""
    conn = get_connection(seeded_db)
    conn.execute("UPDATE plan_sessions SET status='done' WHERE id=1")
    conn.commit()
    conn.close()

    result = export_plan(plan_id=1, dry_run=True, db_path=seeded_db)
    assert result["sessions_exported"] == 0


def test_export_plan_does_not_reexport_exported(seeded_db: Path) -> None:
    """Already exported sessions are not re-exported without --force."""
    conn = get_connection(seeded_db)
    conn.execute(
        "UPDATE plan_sessions SET status='exported', garmin_event_id='gid123' WHERE id=1"
    )
    conn.commit()
    conn.close()

    result = export_plan(plan_id=1, dry_run=True, db_path=seeded_db)
    assert result["sessions_exported"] == 0
    assert result["sessions_skipped"] >= 1


def test_export_plan_force_reexports_exported(seeded_db: Path) -> None:
    """--force allows explicit re-export of an exported session."""
    conn = get_connection(seeded_db)
    conn.execute(
        "UPDATE plan_sessions SET status='exported', garmin_event_id='gid123' WHERE id=1"
    )
    conn.commit()
    conn.close()

    result = export_plan(plan_id=1, dry_run=True, force=True, db_path=seeded_db)
    assert result["status"] == "success"
    assert result["sessions_exported"] == 1
    assert result["sessions_skipped"] == 1


def test_export_plan_date_filter_start(seeded_db: Path) -> None:
    """Start date filter excludes earlier sessions."""
    result = export_plan(plan_id=1, start_date="2026-06-04", dry_run=True, db_path=seeded_db)
    assert result["status"] == "success"
    # Session 1 is on 2026-06-03 (before filter), session 2 is draft (skipped)
    assert result["sessions_exported"] == 0
    assert result["sessions_ignored"] == 1


def test_export_plan_date_filter_end(seeded_db: Path) -> None:
    """End date filter excludes later sessions."""
    result = export_plan(plan_id=1, end_date="2026-06-03", dry_run=True, db_path=seeded_db)
    assert result["status"] == "success"
    # Session 1 is on 2026-06-03, session 2 is on 2026-06-05 (after end)
    assert result["sessions_exported"] == 1
    assert result["sessions_ignored"] == 1


def test_export_plan_days_ahead(seeded_db: Path) -> None:
    """days_ahead filter computes date range from today."""
    # Both test sessions are in the future relative to today (2026),
    # so with days_ahead=0 (today only), they're likely excluded
    result = export_plan(plan_id=1, days_ahead=0, dry_run=True, db_path=seeded_db)
    assert result["status"] == "success"
    assert "sessions_ignored" in result


def test_export_plan_sessions_ignored_counter(seeded_db: Path) -> None:
    """The sessions_ignored counter tracks sessions outside the date range."""
    result = export_plan(
        plan_id=1, start_date="2099-01-01", dry_run=True, db_path=seeded_db
    )
    assert result["sessions_ignored"] == 2
    assert result["sessions_exported"] == 0
