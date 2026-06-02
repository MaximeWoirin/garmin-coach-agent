"""Tests pour garmin_coach.plans.write.create_goal."""

from __future__ import annotations

from pathlib import Path

from garmin_coach.plans.read import get_goals
from garmin_coach.plans.write import create_goal


# --- Création nominale ---


def test_create_goal_minimal(tmp_db: Path) -> None:
    result = create_goal(primary_goal="Courir un 10 km", db_path=tmp_db)
    assert result["status"] == "success"
    assert result["goal_id"] is not None
    assert result["goal_status"] == "active"
    assert result["warnings"] == []
    assert result["errors"] == []


def test_create_goal_full(tmp_db: Path) -> None:
    result = create_goal(
        primary_goal="Finir le marathon de Paris en moins de 4h",
        goal_code="marathon_paris_2027",
        priority="high",
        horizon_date="2027-04-11",
        target_event_name="Marathon de Paris",
        target_event_date="2027-04-11",
        target_event_priority="high",
        status="active",
        raw_text="Je veux courir le marathon de Paris l'an prochain en moins de 4h",
        metadata_json='{"distance_km": 42.195}',
        db_path=tmp_db,
    )
    assert result["status"] == "success"
    assert result["goal_id"] is not None
    assert result["goal_status"] == "active"


def test_create_goal_dry_run(tmp_db: Path) -> None:
    result = create_goal(
        primary_goal="Test dry run",
        dry_run=True,
        db_path=tmp_db,
    )
    assert result["status"] == "success"
    assert result["goal_id"] is None
    assert result["dry_run"] is True
    # Verify nothing was written
    goals = get_goals(db_path=tmp_db)
    assert goals["summary"]["count"] == 0


# --- Validations ---


def test_create_goal_empty_primary_goal(tmp_db: Path) -> None:
    result = create_goal(primary_goal="", db_path=tmp_db)
    assert result["status"] == "failed"
    assert "primary_goal must not be empty" in result["errors"][0]


def test_create_goal_whitespace_primary_goal(tmp_db: Path) -> None:
    result = create_goal(primary_goal="   ", db_path=tmp_db)
    assert result["status"] == "failed"
    assert "primary_goal must not be empty" in result["errors"][0]


def test_create_goal_invalid_priority(tmp_db: Path) -> None:
    result = create_goal(primary_goal="Test", priority="urgent", db_path=tmp_db)
    assert result["status"] == "failed"
    assert "Invalid priority" in result["errors"][0]


def test_create_goal_invalid_status(tmp_db: Path) -> None:
    result = create_goal(primary_goal="Test", status="pending", db_path=tmp_db)
    assert result["status"] == "failed"
    assert "Invalid status" in result["errors"][0]


def test_create_goal_invalid_target_event_priority(tmp_db: Path) -> None:
    result = create_goal(
        primary_goal="Test",
        target_event_priority="extreme",
        db_path=tmp_db,
    )
    assert result["status"] == "failed"
    assert "Invalid target_event_priority" in result["errors"][0]


def test_create_goal_invalid_horizon_date(tmp_db: Path) -> None:
    result = create_goal(primary_goal="Test", horizon_date="11-04-2027", db_path=tmp_db)
    assert result["status"] == "failed"
    assert "Invalid horizon_date format" in result["errors"][0]


def test_create_goal_invalid_target_event_date(tmp_db: Path) -> None:
    result = create_goal(primary_goal="Test", target_event_date="not-a-date", db_path=tmp_db)
    assert result["status"] == "failed"
    assert "Invalid target_event_date format" in result["errors"][0]


def test_create_goal_invalid_metadata_json(tmp_db: Path) -> None:
    result = create_goal(primary_goal="Test", metadata_json="{broken", db_path=tmp_db)
    assert result["status"] == "failed"
    assert "Invalid metadata_json format" in result["errors"][0]


def test_create_goal_duplicate_goal_code(tmp_db: Path) -> None:
    create_goal(primary_goal="First goal", goal_code="unique_code", db_path=tmp_db)
    result = create_goal(primary_goal="Second goal", goal_code="unique_code", db_path=tmp_db)
    assert result["status"] == "failed"
    assert "already exists" in result["errors"][0]


# --- Intégration avec get_goals ---


def test_create_goal_readable_via_get_goals(tmp_db: Path) -> None:
    create_goal(
        primary_goal="Semi-marathon en 1h45",
        goal_code="semi_2027",
        priority="medium",
        target_event_name="Semi de Paris",
        db_path=tmp_db,
    )
    goals = get_goals(db_path=tmp_db)
    assert goals["status"] == "success"
    assert goals["summary"]["count"] == 1
    goal = goals["goals"][0]
    assert goal["primary_goal"] == "Semi-marathon en 1h45"
    assert goal["goal_code"] == "semi_2027"
    assert goal["priority"] == "medium"
    assert goal["target_event_name"] == "Semi de Paris"
    assert goal["status"] == "active"
