"""Lecture des plans et séances."""

from __future__ import annotations

from typing import Any

from garmin_coach.db import db_connection, fetchall_dicts, fetchone_dict
from garmin_coach.jsonio import error_response, success_response


def get_current_plan(
    plan_id: int | None = None,
    week_start: str | None = None,
    include_sessions: bool = True,
    include_metadata: bool = False,
    db_path: Any = None,
) -> dict[str, Any]:
    """Lit le plan courant.

    Args:
        plan_id: Plan précis.
        week_start: Plan de la semaine.
        include_sessions: Inclut les séances détaillées.
        include_metadata: Inclut les métadonnées du plan.
        db_path: Chemin de la base SQLite.

    Returns:
        Réponse JSON avec le plan courant.
    """
    with db_connection(db_path) as conn:
        plan = _find_plan(conn, plan_id, week_start)
        if not plan:
            return error_response(["No active or draft plan found."])

        result: dict[str, Any] = {
            "plan_id": plan["id"],
            "week_start": plan["week_start"],
            "week_end": plan["week_end"],
            "plan_status": plan["status"],
            "generated_by": plan["generated_by"],
            "confidence": plan["confidence"],
            "needs_review": bool(plan["needs_review"]),
            "notes": plan["notes"],
        }

        if include_metadata and plan.get("metadata_json"):
            result["metadata"] = plan["metadata_json"]

        if include_sessions:
            sessions = fetchall_dicts(
                conn,
                """SELECT id, planned_date, planned_time, activity_type, duration_min,
                          intensity, target_hr_low, target_hr_high,
                          target_pace_sec_per_km, target_rpe, status,
                          garmin_event_id, tags_json, notes
                   FROM plan_sessions WHERE plan_id = ?
                   ORDER BY planned_date ASC, planned_time ASC""",
                (plan["id"],),
            )
            result["sessions"] = sessions
            result["sessions_count"] = len(sessions)

        return success_response(result)


def get_goals(
    status: str | None = "active",
    limit: int | None = None,
    include_archived: bool = False,
    db_path: Any = None,
) -> dict[str, Any]:
    """Lit les objectifs d'entraînement.

    Args:
        status: Filtre sur le statut (défaut: active).
        limit: Nombre max d'objectifs.
        include_archived: Inclut les objectifs archivés.
        db_path: Chemin de la base SQLite.

    Returns:
        Réponse JSON avec les objectifs.
    """
    with db_connection(db_path) as conn:
        sql = """
            SELECT id, goal_code, primary_goal, priority, horizon_date,
                   target_event_name, target_event_date, target_event_priority,
                   status, raw_text, metadata_json, created_at, updated_at
            FROM training_goals
            WHERE 1=1
        """
        params: list[Any] = []

        if status and not include_archived:
            sql += " AND status = ?"
            params.append(status)

        sql += " ORDER BY priority DESC, created_at DESC"

        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        goals = fetchall_dicts(conn, sql, tuple(params))

        summary = {
            "count": len(goals),
            "by_priority": _count_by(goals, "priority"),
        }

        return success_response({
            "goals": goals,
            "summary": summary,
        })


def _find_plan(conn: Any, plan_id: int | None, week_start: str | None) -> dict[str, Any] | None:
    """Trouve le plan par id, par semaine, ou le plus récent actif/draft."""
    if plan_id:
        return fetchone_dict(conn, "SELECT * FROM training_plans WHERE id=?", (plan_id,))
    if week_start:
        return fetchone_dict(
            conn,
            "SELECT * FROM training_plans WHERE week_start=? ORDER BY id DESC LIMIT 1",
            (week_start,),
        )
    # Par défaut, le plan le plus récent actif ou draft
    return fetchone_dict(
        conn,
        "SELECT * FROM training_plans WHERE status IN ('active', 'draft') ORDER BY week_start DESC LIMIT 1",
        (),
    )


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    """Compte les items par valeur d'un champ."""
    counts: dict[str, int] = {}
    for item in items:
        val = item.get(key, "unknown")
        counts[val] = counts.get(val, 0) + 1
    return counts
