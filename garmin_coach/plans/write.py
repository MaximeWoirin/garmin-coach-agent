"""Écriture de plans et séances (création, suppression)."""

from __future__ import annotations

import json
from typing import Any

from garmin_coach.db import ensure_db, fetchone_dict
from garmin_coach.enums import PlanStatus, SessionStatus
from garmin_coach.jsonio import error_response, success_response


def create_plan_draft(
    week_start: str,
    week_end: str,
    goal_id: int | None = None,
    block_id: int | None = None,
    title: str | None = None,
    notes: str | None = None,
    metadata_json: str | None = None,
    sessions_json: str | None = None,
    dry_run: bool = False,
    db_path: Any = None,
) -> dict[str, Any]:
    """Crée un plan local en draft.

    Returns:
        Réponse JSON avec le plan créé.
    """
    warnings: list[str] = []

    # Validation des dates
    if week_start >= week_end:
        return error_response(["week_start must be before week_end."])

    if dry_run:
        return success_response({
            "plan_id": None,
            "week_start": week_start,
            "week_end": week_end,
            "plan_status": PlanStatus.DRAFT.value,
            "sessions_created": 0,
            "dry_run": True,
        }, warnings=["Dry run — nothing written."])

    conn = ensure_db(db_path)

    # Vérifier le block_id si fourni
    if block_id:
        block = fetchone_dict(conn, "SELECT id FROM training_blocks WHERE id=?", (block_id,))
        if not block:
            return error_response([f"Block {block_id} not found."])

    # Construire les métadonnées
    meta = {}
    if metadata_json:
        try:
            meta = json.loads(metadata_json)
        except json.JSONDecodeError:
            return error_response(["Invalid metadata_json format."])
    if title:
        meta["title"] = title

    meta_str = json.dumps(meta) if meta else None

    conn.execute(
        """INSERT INTO training_plans (block_id, week_start, week_end, status, notes, metadata_json)
           VALUES (?, ?, ?, 'draft', ?, ?)""",
        (block_id, week_start, week_end, notes, meta_str),
    )
    conn.commit()
    plan_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Créer les séances initiales si fournies
    sessions_created = 0
    if sessions_json:
        try:
            sessions = json.loads(sessions_json)
            for s in sessions:
                _create_session_from_dict(conn, plan_id, s)
                sessions_created += 1
        except (json.JSONDecodeError, KeyError) as exc:
            warnings.append(f"Some sessions not created: {exc}")

    return success_response({
        "plan_id": plan_id,
        "week_start": week_start,
        "week_end": week_end,
        "plan_status": PlanStatus.DRAFT.value,
        "sessions_created": sessions_created,
    }, warnings=warnings)


def create_plan_session(
    plan_id: int,
    planned_date: str,
    activity_type: str,
    duration_min: int,
    planned_time: str | None = None,
    intensity: str | None = None,
    target_hr_low: int | None = None,
    target_hr_high: int | None = None,
    target_pace_sec_per_km: int | None = None,
    target_rpe: int | None = None,
    status: str = "draft",
    tags_json: str | None = None,
    notes: str | None = None,
    workout_payload_json: str | None = None,
    dry_run: bool = False,
    db_path: Any = None,
) -> dict[str, Any]:
    """Crée une séance dans un plan.

    Returns:
        Réponse JSON avec la séance créée.
    """
    # Validation du statut
    try:
        canonical_status = SessionStatus(status)
    except ValueError:
        return error_response([f"Invalid session status: {status}. Valid: {[e.value for e in SessionStatus]}"])

    if dry_run:
        return success_response({
            "plan_id": plan_id,
            "session_id": None,
            "session_status": canonical_status.value,
            "dry_run": True,
        }, warnings=["Dry run — nothing written."])

    conn = ensure_db(db_path)

    # Vérifier le plan
    plan = fetchone_dict(conn, "SELECT id, status FROM training_plans WHERE id=?", (plan_id,))
    if not plan:
        return error_response([f"Plan {plan_id} not found."])

    conn.execute(
        """INSERT INTO plan_sessions (
            plan_id, planned_date, planned_time, activity_type, duration_min,
            intensity, target_hr_low, target_hr_high, target_pace_sec_per_km,
            target_rpe, status, tags_json, notes, workout_payload_json
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            plan_id, planned_date, planned_time, activity_type, duration_min,
            intensity, target_hr_low, target_hr_high, target_pace_sec_per_km,
            target_rpe, canonical_status.value, tags_json, notes, workout_payload_json,
        ),
    )
    conn.commit()
    session_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    return success_response({
        "plan_id": plan_id,
        "session_id": session_id,
        "session_status": canonical_status.value,
    })


def delete_plan_session(
    plan_id: int,
    session_id: int,
    dry_run: bool = False,
    db_path: Any = None,
) -> dict[str, Any]:
    """Supprime une séance de plan.

    Returns:
        Réponse JSON avec la séance supprimée.
    """
    conn = ensure_db(db_path)

    session = fetchone_dict(
        conn,
        "SELECT * FROM plan_sessions WHERE id=? AND plan_id=?",
        (session_id, plan_id),
    )
    if not session:
        return error_response([f"Session {session_id} not found in plan {plan_id}."])

    # Refuser la suppression si exportée ou réalisée
    if session["status"] in (SessionStatus.EXPORTED, SessionStatus.DONE):
        return error_response(
            [f"Cannot delete session {session_id}: status is '{session['status']}'. Only draft/proposed/skipped/canceled sessions can be deleted."]
        )

    if dry_run:
        return success_response({
            "plan_id": plan_id,
            "session_id": session_id,
            "dry_run": True,
        }, warnings=["Dry run — nothing deleted."])

    conn.execute("DELETE FROM plan_sessions WHERE id=?", (session_id,))
    conn.commit()

    return success_response({
        "plan_id": plan_id,
        "session_id": session_id,
    })


def _create_session_from_dict(conn: Any, plan_id: int, s: dict[str, Any]) -> None:
    """Crée une séance à partir d'un dict."""
    conn.execute(
        """INSERT INTO plan_sessions (
            plan_id, planned_date, planned_time, activity_type, duration_min,
            intensity, target_hr_low, target_hr_high, target_pace_sec_per_km,
            target_rpe, status, tags_json, notes
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)""",
        (
            plan_id,
            s["planned_date"],
            s.get("planned_time"),
            s["activity_type"],
            s["duration_min"],
            s.get("intensity"),
            s.get("target_hr_low"),
            s.get("target_hr_high"),
            s.get("target_pace_sec_per_km"),
            s.get("target_rpe"),
            s.get("tags_json"),
            s.get("notes"),
        ),
    )
    conn.commit()
