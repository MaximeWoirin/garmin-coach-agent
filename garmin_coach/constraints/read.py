"""Lecture des contraintes."""

from __future__ import annotations

from typing import Any

from garmin_coach.db import ensure_db, fetchall_dicts
from garmin_coach.jsonio import success_response


def get_constraints(
    scope: str | None = None,
    status: str | None = "active",
    limit: int | None = None,
    db_path: Any = None,
) -> dict[str, Any]:
    """Lit les contraintes utiles à l'agent.

    Args:
        scope: Filtre sur le périmètre.
        status: Filtre sur le statut (défaut: active).
        limit: Nombre max de contraintes.
        db_path: Chemin de la base SQLite.

    Returns:
        Réponse JSON avec les contraintes.
    """
    conn = ensure_db(db_path)

    sql = """
        SELECT id, goal_id, type, severity, status, scope,
               start_date, end_date, source, confidence,
               raw_text, tags_json, notes_json,
               created_at, resolved_at
        FROM constraints
        WHERE 1=1
    """
    params: list[Any] = []

    if status:
        sql += " AND status = ?"
        params.append(status)

    if scope:
        sql += " AND scope = ?"
        params.append(scope)

    sql += " ORDER BY severity DESC, start_date ASC"

    if limit:
        sql += " LIMIT ?"
        params.append(limit)

    constraints = fetchall_dicts(conn, sql, tuple(params))

    summary = {
        "count": len(constraints),
        "by_type": _count_by(constraints, "type"),
        "by_severity": _count_by(constraints, "severity"),
    }

    return success_response({
        "constraints": constraints,
        "summary": summary,
    })


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    """Compte les items par valeur d'un champ."""
    counts: dict[str, int] = {}
    for item in items:
        val = item.get(key, "unknown")
        counts[val] = counts.get(val, 0) + 1
    return counts
