"""Tests pour garmin_coach.activities.read."""

from __future__ import annotations

from pathlib import Path

from garmin_coach.activities.read import get_activities
from garmin_coach.debriefs.write import save_activity_debrief


def test_get_activities_basic(seeded_db: Path) -> None:
    result = get_activities(start="2026-06-01", end="2026-06-10", db_path=seeded_db)
    assert result["status"] == "success"
    assert len(result["activities"]) == 2
    assert result["summary"]["count"] == 2


def test_get_activities_filter_type(seeded_db: Path) -> None:
    result = get_activities(
        start="2026-06-01", end="2026-06-10", activity_type="running", db_path=seeded_db
    )
    assert result["status"] == "success"
    assert len(result["activities"]) == 1
    assert result["activities"][0]["activity_type"] == "running"


def test_get_activities_limit(seeded_db: Path) -> None:
    result = get_activities(start="2026-06-01", end="2026-06-10", limit=1, db_path=seeded_db)
    assert len(result["activities"]) == 1


def test_get_activities_empty_range(seeded_db: Path) -> None:
    result = get_activities(start="2026-01-01", end="2026-01-02", db_path=seeded_db)
    assert result["status"] == "success"
    assert result["activities"] == []
    assert result["summary"]["count"] == 0


def test_get_activities_summary(seeded_db: Path) -> None:
    result = get_activities(start="2026-06-01", end="2026-06-10", db_path=seeded_db)
    summary = result["summary"]
    assert summary["total_duration_min"] == (2700 + 3600) // 60
    assert summary["total_distance_km"] == round((5000 + 20000) / 1000, 2)
    assert summary["total_calories_kcal"] == 350 + 500


def test_get_activities_includes_debrief_info(seeded_db: Path) -> None:
    save_activity_debrief(activity_id=1, rpe=6, db_path=seeded_db)

    result = get_activities(start="2026-06-01", end="2026-06-10", db_path=seeded_db)
    activity = next(item for item in result["activities"] if item["id"] == 1)

    assert activity["debrief_status"] == "completed"
    assert activity["debrief_rpe"] == 6
    assert activity["debrief_plan_session_id"] == 1
