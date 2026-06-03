"""Changement de statut de plans et séances."""

from __future__ import annotations

from typing import Any

from garmin_coach.db import db_connection, fetchall_dicts, fetchone_dict
from garmin_coach.enums import PlanStatus, SessionStatus
from garmin_coach.jsonio import error_response, success_response


# Transitions valides pour les plans
# Note: SENT is deprecated. Plans no longer transition to SENT.
# Publication is tracked at session level (proposed -> exported).
_PLAN_TRANSITIONS: dict[PlanStatus, set[PlanStatus]] = {
    PlanStatus.DRAFT: {PlanStatus.ACTIVE, PlanStatus.ARCHIVED},
    PlanStatus.ACTIVE: {PlanStatus.ARCHIVED},
    PlanStatus.SENT: {PlanStatus.ACTIVE, PlanStatus.ARCHIVED},  # compat: migrate away from sent
    PlanStatus.ARCHIVED: set(),
}

# Transitions valides pour les séances
_SESSION_TRANSITIONS: dict[SessionStatus, set[SessionStatus]] = {
    SessionStatus.DRAFT: {SessionStatus.PROPOSED, SessionStatus.CANCELED},
    SessionStatus.PROPOSED: {SessionStatus.EXPORTED, SessionStatus.SKIPPED, SessionStatus.CANCELED},
    SessionStatus.EXPORTED: {SessionStatus.DONE, SessionStatus.SKIPPED, SessionStatus.CANCELED},
    SessionStatus.DONE: set(),
    SessionStatus.SKIPPED: set(),
    SessionStatus.CANCELED: set(),
}


def set_plan_status(
    plan_id: int,
    status: str,
    cascade_sessions: bool = False,
    dry_run: bool = False,
    db_path: Any = None,
) -> dict[str, Any]:
    """Change le statut d'un plan.

    Args:
        plan_id: Identifiant du plan.
        status: Nouveau statut.
        cascade_sessions: Applique aussi une transition aux séances.
        dry_run: Simule sans écrire.
        db_path: Chemin de la base SQLite.

    Returns:
        Réponse JSON avec le plan mis à jour.
    """
    try:
        new_status = PlanStatus(status)
    except ValueError:
        return error_response([f"Invalid plan status: {status}. Valid: {[e.value for e in PlanStatus]}"])

    with db_connection(db_path) as conn:
        plan = fetchone_dict(conn, "SELECT * FROM training_plans WHERE id=?", (plan_id,))
        if not plan:
            return error_response([f"Plan {plan_id} not found."])

        current_status = PlanStatus(plan["status"])

        # Vérifier la transition
        if new_status not in _PLAN_TRANSITIONS.get(current_status, set()):
            return error_response(
                [f"Invalid transition: {current_status.value} → {new_status.value}. "
                 f"Allowed: {[s.value for s in _PLAN_TRANSITIONS.get(current_status, set())]}"]
            )

        session_status_changes: list[dict[str, Any]] = []

        if cascade_sessions:
            session_status_changes = _compute_session_cascade(conn, plan_id, new_status)

        if dry_run:
            return success_response({
                "plan_id": plan_id,
                "plan_status": new_status.value,
                "session_status_changes": session_status_changes,
                "dry_run": True,
            }, warnings=["Dry run — nothing written."])

        conn.execute(
            "UPDATE training_plans SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_status.value, plan_id),
        )

        # Appliquer la cascade
        if cascade_sessions:
            for change in session_status_changes:
                conn.execute(
                    "UPDATE plan_sessions SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (change["new_status"], change["session_id"]),
                )

        conn.commit()

        return success_response({
            "plan_id": plan_id,
            "plan_status": new_status.value,
            "session_status_changes": session_status_changes,
        })


def set_plan_session_status(
    plan_id: int,
    session_id: int,
    status: str,
    dry_run: bool = False,
    db_path: Any = None,
) -> dict[str, Any]:
    """Change le statut d'une séance de plan.

    Args:
        plan_id: Identifiant du plan.
        session_id: Identifiant de la séance.
        status: Nouveau statut.
        dry_run: Simule sans écrire.
        db_path: Chemin de la base SQLite.

    Returns:
        Réponse JSON avec la séance mise à jour.
    """
    try:
        new_status = SessionStatus(status)
    except ValueError:
        return error_response([f"Invalid session status: {status}. Valid: {[e.value for e in SessionStatus]}"])

    with db_connection(db_path) as conn:
        session = fetchone_dict(
            conn,
            "SELECT * FROM plan_sessions WHERE id=? AND plan_id=?",
            (session_id, plan_id),
        )
        if not session:
            return error_response([f"Session {session_id} not found in plan {plan_id}."])

        current_status = SessionStatus(session["status"])

        # Vérifier la transition
        if new_status not in _SESSION_TRANSITIONS.get(current_status, set()):
            return error_response(
                [f"Invalid transition: {current_status.value} → {new_status.value}. "
                 f"Allowed: {[s.value for s in _SESSION_TRANSITIONS.get(current_status, set())]}"]
            )

        if dry_run:
            return success_response({
                "plan_id": plan_id,
                "session_id": session_id,
                "session_status": new_status.value,
                "dry_run": True,
            }, warnings=["Dry run — nothing written."])

        conn.execute(
            "UPDATE plan_sessions SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_status.value, session_id),
        )
        conn.commit()

        return success_response({
            "plan_id": plan_id,
            "session_id": session_id,
            "session_status": new_status.value,
        })


def _compute_session_cascade(
    conn: Any, plan_id: int, new_plan_status: PlanStatus
) -> list[dict[str, Any]]:
    """Calcule les transitions de séances lors d'une cascade plan → sessions."""
    sessions = fetchall_dicts(
        conn,
        "SELECT id, status FROM plan_sessions WHERE plan_id=?",
        (plan_id,),
    )

    changes: list[dict[str, Any]] = []

    for session in sessions:
        current = SessionStatus(session["status"])
        target: SessionStatus | None = None

        if new_plan_status == PlanStatus.ACTIVE:
            # draft → proposed
            if current == SessionStatus.DRAFT:
                target = SessionStatus.PROPOSED
        elif new_plan_status == PlanStatus.ARCHIVED:
            # proposed/draft → canceled
            if current in (SessionStatus.DRAFT, SessionStatus.PROPOSED):
                target = SessionStatus.CANCELED

        if target and target in _SESSION_TRANSITIONS.get(current, set()):
            changes.append({
                "session_id": session["id"],
                "old_status": current.value,
                "new_status": target.value,
            })

    return changes
