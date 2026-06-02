"""Tests pour garmin_coach.enums."""

from __future__ import annotations

from garmin_coach.enums import (
    ActivitySource,
    BlockType,
    ConstraintScope,
    ConstraintSeverity,
    ConstraintStatus,
    ConstraintType,
    GoalPriority,
    MatchType,
    PlanStatus,
    ReviewOutcome,
    SessionStatus,
)


def test_goal_priority_values() -> None:
    assert GoalPriority.LOW == "low"
    assert GoalPriority.MEDIUM == "medium"
    assert GoalPriority.HIGH == "high"


def test_constraint_type_values() -> None:
    assert ConstraintType.AVAILABILITY == "availability"
    assert ConstraintType.HEALTH == "health"
    assert ConstraintType.SCHEDULE == "schedule"


def test_constraint_status_values() -> None:
    assert ConstraintStatus.ACTIVE == "active"
    assert ConstraintStatus.INACTIVE == "inactive"


def test_constraint_scope_values() -> None:
    assert ConstraintScope.TRAINING == "training"
    assert ConstraintScope.LIFE == "life"
    assert ConstraintScope.DAY == "day"
    assert ConstraintScope.SESSION == "session"


def test_constraint_severity_values() -> None:
    assert ConstraintSeverity.LOW == "low"
    assert ConstraintSeverity.HIGH == "high"


def test_block_type_values() -> None:
    assert BlockType.BUILD == "build"
    assert BlockType.RECOVER == "recover"
    assert BlockType.PEAK == "peak"
    assert BlockType.TAPER == "taper"


def test_plan_status_values() -> None:
    assert PlanStatus.DRAFT == "draft"
    assert PlanStatus.ACTIVE == "active"
    assert PlanStatus.SENT == "sent"
    assert PlanStatus.ARCHIVED == "archived"


def test_session_status_values() -> None:
    assert SessionStatus.DRAFT == "draft"
    assert SessionStatus.PROPOSED == "proposed"
    assert SessionStatus.EXPORTED == "exported"
    assert SessionStatus.DONE == "done"
    assert SessionStatus.SKIPPED == "skipped"
    assert SessionStatus.CANCELED == "canceled"


def test_review_outcome_values() -> None:
    assert ReviewOutcome.KEPT == "kept"
    assert ReviewOutcome.ADAPTED == "adapted"
    assert ReviewOutcome.RESET == "reset"


def test_match_type_values() -> None:
    assert MatchType.MANUAL == "manual"
    assert MatchType.INFERRED == "inferred"
    assert MatchType.IMPORTED == "imported"


def test_activity_source_values() -> None:
    assert ActivitySource.GARMIN == "garmin"
    assert ActivitySource.MANUAL == "manual"


def test_enum_from_string() -> None:
    assert PlanStatus("draft") == PlanStatus.DRAFT
    assert SessionStatus("done") == SessionStatus.DONE
    assert ConstraintType("health") == ConstraintType.HEALTH
