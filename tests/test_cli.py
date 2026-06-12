"""Tests pour les modules CLI (wrappers argparse)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest


def test_get_activities_main(seeded_db: Path) -> None:
    """Test get_activities CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", ["get_activities", "--start", "2026-06-01", "--end", "2026-06-10"]):
            from garmin_coach.get_activities import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_get_constraints_main(seeded_db: Path) -> None:
    """Test get_constraints CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", ["get_constraints"]):
            from garmin_coach.get_constraints import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_get_current_plan_main(seeded_db: Path) -> None:
    """Test get_current_plan CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", ["get_current_plan"]):
            from garmin_coach.get_current_plan import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_get_fitness_state_main(seeded_db: Path) -> None:
    """Test get_fitness_state CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", ["get_fitness_state", "--start", "2026-06-01", "--end", "2026-06-10"]):
            from garmin_coach.get_fitness_state import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_get_goals_main(seeded_db: Path) -> None:
    """Test get_goals CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", ["get_goals"]):
            from garmin_coach.get_goals import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_get_pending_debriefs_main(seeded_db: Path) -> None:
    """Test get_pending_debriefs CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", ["get_pending_debriefs", "--lookback-hours", "48"]):
            from garmin_coach.get_pending_debriefs import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_create_constraint_main(seeded_db: Path) -> None:
    """Test create_constraint CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", [
            "create_constraint",
            "--type", "health",
            "--start-date", "2026-06-10",
            "--raw-text", "Test constraint",
            "--dry-run",
        ]):
            from garmin_coach.create_constraint import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_create_goal_main(tmp_db: Path) -> None:
    """Test create_goal CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(tmp_db)}):
        with patch("sys.argv", [
            "create_goal",
            "--primary-goal", "Courir un 10 km",
            "--priority", "high",
            "--dry-run",
        ]):
            from garmin_coach.create_goal import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_create_plan_draft_main(seeded_db: Path) -> None:
    """Test create_plan_draft CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", [
            "create_plan_draft",
            "--week-start", "2026-06-16",
            "--week-end", "2026-06-22",
            "--dry-run",
        ]):
            from garmin_coach.create_plan_draft import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_save_activity_debrief_main(seeded_db: Path) -> None:
    """Test save_activity_debrief CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", [
            "save_activity_debrief",
            "--activity-id", "1",
            "--rpe", "7",
            "--note", "Bonne séance",
            "--dry-run",
        ]):
            from garmin_coach.save_activity_debrief import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_create_plan_session_main(seeded_db: Path) -> None:
    """Test create_plan_session CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", [
            "create_plan_session",
            "--plan-id", "1",
            "--planned-date", "2026-06-04",
            "--activity-type", "running",
            "--duration-min", "30",
            "--dry-run",
        ]):
            from garmin_coach.create_plan_session import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_set_plan_status_main(seeded_db: Path) -> None:
    """Test set_plan_status CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", [
            "set_plan_status",
            "--plan-id", "2",
            "--status", "active",
            "--dry-run",
        ]):
            from garmin_coach.set_plan_status import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_set_plan_session_status_main(seeded_db: Path) -> None:
    """Test set_plan_session_status CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", [
            "set_plan_session_status",
            "--plan-id", "1",
            "--session-id", "1",
            "--status", "exported",
            "--dry-run",
        ]):
            from garmin_coach.set_plan_session_status import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_set_constraint_status_main(seeded_db: Path) -> None:
    """Test set_constraint_status CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", [
            "set_constraint_status",
            "--constraint-id", "1",
            "--status", "inactive",
            "--dry-run",
        ]):
            from garmin_coach.set_constraint_status import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_delete_constraint_main(seeded_db: Path) -> None:
    """Test delete_constraint CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", [
            "delete_constraint",
            "--constraint-id", "1",
            "--dry-run",
        ]):
            from garmin_coach.delete_constraint import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_delete_plan_session_main(seeded_db: Path) -> None:
    """Test delete_plan_session CLI."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", [
            "delete_plan_session",
            "--plan-id", "1",
            "--session-id", "2",
            "--dry-run",
        ]):
            from garmin_coach.delete_plan_session import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_export_plan_garmin_main_dry_run(seeded_db: Path) -> None:
    """Test export_plan_garmin CLI in dry-run mode."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", [
            "export_plan_garmin",
            "--plan-id", "1",
            "--dry-run",
        ]):
            from garmin_coach.export_plan_garmin import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_export_plan_garmin_main_with_dates(seeded_db: Path) -> None:
    """Test export_plan_garmin CLI with date filters."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", [
            "export_plan_garmin",
            "--plan-id", "1",
            "--start-date", "2026-06-03",
            "--end-date", "2026-06-05",
            "--dry-run",
        ]):
            from garmin_coach.export_plan_garmin import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_export_plan_garmin_main_with_days_ahead(seeded_db: Path) -> None:
    """Test export_plan_garmin CLI with --days-ahead."""
    with patch.dict("os.environ", {"GARMIN_COACH_DB": str(seeded_db)}):
        with patch("sys.argv", [
            "export_plan_garmin",
            "--plan-id", "1",
            "--days-ahead", "2",
            "--dry-run",
        ]):
            from garmin_coach.export_plan_garmin import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


def test_sync_garmin_main_no_tokens(seeded_db: Path, tmp_path: Path) -> None:
    """Test sync_garmin CLI with no tokens (should fail gracefully)."""
    tokens_dir = tmp_path / "empty_tokens"
    with patch.dict("os.environ", {
        "GARMIN_COACH_DB": str(seeded_db),
        "GARMIN_COACH_TOKENS_DIR": str(tokens_dir),
    }):
        with patch("sys.argv", ["sync_garmin"]):
            from garmin_coach.sync_garmin import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1


def test_auth_garmin_main_no_tokens(tmp_path: Path) -> None:
    """Test auth_garmin CLI without force login and empty token dir."""
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir()
    with patch("sys.argv", [
        "auth_garmin",
        "--tokens-dir", str(tokens_dir),
    ]):
        from garmin_coach.auth_garmin import main
        with pytest.raises(SystemExit) as exc_info:
            main()
        # No tokens and no force_login → should succeed with empty dir (no tokens to reuse)
        # Actually it will try to reuse tokens, fail, then ask for email
        # With empty dir it will need email/password
        assert exc_info.value.code == 1
