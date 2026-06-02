"""Tests pour garmin_coach.constraints (read, status, write)."""

from __future__ import annotations

from pathlib import Path

from garmin_coach.constraints.read import get_constraints
from garmin_coach.constraints.status import set_constraint_status
from garmin_coach.constraints.write import create_constraint, delete_constraint


# --- Tests lecture ---


def test_get_constraints_all_active(seeded_db: Path) -> None:
    result = get_constraints(db_path=seeded_db)
    assert result["status"] == "success"
    assert result["summary"]["count"] == 1  # only active
    assert result["constraints"][0]["type"] == "availability"


def test_get_constraints_all_statuses(seeded_db: Path) -> None:
    result = get_constraints(status=None, db_path=seeded_db)
    assert result["summary"]["count"] == 2


def test_get_constraints_by_scope(seeded_db: Path) -> None:
    result = get_constraints(scope="training", db_path=seeded_db)
    assert result["summary"]["count"] == 1

    result = get_constraints(scope="life", status=None, db_path=seeded_db)
    assert result["summary"]["count"] == 1


def test_get_constraints_with_limit(seeded_db: Path) -> None:
    result = get_constraints(status=None, limit=1, db_path=seeded_db)
    assert result["summary"]["count"] == 1


def test_get_constraints_summary_by_type(seeded_db: Path) -> None:
    result = get_constraints(status=None, db_path=seeded_db)
    assert result["summary"]["by_type"]["availability"] == 1
    assert result["summary"]["by_type"]["health"] == 1


# --- Tests statut ---


def test_set_constraint_status_active_to_inactive(seeded_db: Path) -> None:
    result = set_constraint_status(constraint_id=1, status="inactive", db_path=seeded_db)
    assert result["status"] == "success"
    assert result["constraint_status"] == "inactive"


def test_set_constraint_status_invalid(seeded_db: Path) -> None:
    result = set_constraint_status(constraint_id=1, status="bogus", db_path=seeded_db)
    assert result["status"] == "failed"
    assert "Invalid status" in result["errors"][0]


def test_set_constraint_status_not_found(seeded_db: Path) -> None:
    result = set_constraint_status(constraint_id=999, status="active", db_path=seeded_db)
    assert result["status"] == "failed"
    assert "not found" in result["errors"][0]


def test_set_constraint_status_dry_run(seeded_db: Path) -> None:
    result = set_constraint_status(constraint_id=1, status="inactive", dry_run=True, db_path=seeded_db)
    assert result["status"] == "success"
    assert result["dry_run"] is True
    # Verify not actually changed
    check = get_constraints(db_path=seeded_db)
    assert check["constraints"][0]["status"] == "active"


def test_set_constraint_status_reactivate(seeded_db: Path) -> None:
    # Constraint 2 is inactive
    result = set_constraint_status(constraint_id=2, status="active", db_path=seeded_db)
    assert result["status"] == "success"
    assert result["constraint_status"] == "active"


# --- Tests écriture ---


def test_create_constraint_success(seeded_db: Path) -> None:
    result = create_constraint(
        constraint_type="health",
        raw_text="Douleur épaule",
        start_date="2026-06-10",
        severity="high",
        scope="training",
        db_path=seeded_db,
    )
    assert result["status"] == "success"
    assert result["constraint_id"] is not None
    assert result["constraint_status"] == "active"


def test_create_constraint_invalid_type(seeded_db: Path) -> None:
    result = create_constraint(
        constraint_type="bogus",
        raw_text="Test",
        start_date="2026-06-10",
        db_path=seeded_db,
    )
    assert result["status"] == "failed"
    assert "Invalid constraint type" in result["errors"][0]


def test_create_constraint_invalid_severity(seeded_db: Path) -> None:
    result = create_constraint(
        constraint_type="health",
        raw_text="Test",
        start_date="2026-06-10",
        severity="extreme",
        db_path=seeded_db,
    )
    assert result["status"] == "failed"
    assert "Invalid severity" in result["errors"][0]


def test_create_constraint_invalid_scope(seeded_db: Path) -> None:
    result = create_constraint(
        constraint_type="health",
        raw_text="Test",
        start_date="2026-06-10",
        scope="global",
        db_path=seeded_db,
    )
    assert result["status"] == "failed"
    assert "Invalid scope" in result["errors"][0]


def test_create_constraint_invalid_status(seeded_db: Path) -> None:
    result = create_constraint(
        constraint_type="health",
        raw_text="Test",
        start_date="2026-06-10",
        status="pending",
        db_path=seeded_db,
    )
    assert result["status"] == "failed"
    assert "Invalid status" in result["errors"][0]


def test_create_constraint_dry_run(seeded_db: Path) -> None:
    result = create_constraint(
        constraint_type="health",
        raw_text="Test",
        start_date="2026-06-10",
        dry_run=True,
        db_path=seeded_db,
    )
    assert result["status"] == "success"
    assert result["dry_run"] is True
    assert result["constraint_id"] is None


def test_delete_constraint_success(seeded_db: Path) -> None:
    result = delete_constraint(constraint_id=1, db_path=seeded_db)
    assert result["status"] == "success"
    assert result["constraint_id"] == 1


def test_delete_constraint_not_found(seeded_db: Path) -> None:
    result = delete_constraint(constraint_id=999, db_path=seeded_db)
    assert result["status"] == "failed"
    assert "not found" in result["errors"][0]


def test_delete_constraint_dry_run(seeded_db: Path) -> None:
    result = delete_constraint(constraint_id=1, dry_run=True, db_path=seeded_db)
    assert result["status"] == "success"
    assert result["dry_run"] is True
    # Verify still exists
    check = get_constraints(db_path=seeded_db)
    assert check["summary"]["count"] == 1
