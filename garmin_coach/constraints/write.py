"""Écriture de contraintes (création, suppression)."""

from __future__ import annotations

from typing import Any

from garmin_coach.db import db_connection, fetchone_dict
from garmin_coach.enums import ConstraintScope, ConstraintSeverity, ConstraintStatus, ConstraintType
from garmin_coach.jsonio import error_response, success_response


def create_constraint(
    constraint_type: str,
    raw_text: str,
    start_date: str,
    goal_id: int | None = None,
    severity: str = "medium",
    scope: str = "training",
    end_date: str | None = None,
    source: str = "user",
    confidence: float = 1.0,
    tags_json: str | None = None,
    notes_json: str | None = None,
    status: str = "active",
    dry_run: bool = False,
    db_path: Any = None,
) -> dict[str, Any]:
    """Crée une contrainte.

    Returns:
        Réponse JSON avec la contrainte créée.
    """
    warnings: list[str] = []

    # Validation des enums
    try:
        canonical_type = ConstraintType(constraint_type)
    except ValueError:
        return error_response([f"Invalid constraint type: {constraint_type}. Valid: {[e.value for e in ConstraintType]}"])

    try:
        canonical_severity = ConstraintSeverity(severity)
    except ValueError:
        return error_response([f"Invalid severity: {severity}. Valid: {[e.value for e in ConstraintSeverity]}"])

    try:
        canonical_scope = ConstraintScope(scope)
    except ValueError:
        return error_response([f"Invalid scope: {scope}. Valid: {[e.value for e in ConstraintScope]}"])

    try:
        canonical_status = ConstraintStatus(status)
    except ValueError:
        return error_response([f"Invalid status: {status}. Valid: {[e.value for e in ConstraintStatus]}"])

    if dry_run:
        return success_response({
            "constraint_id": None,
            "constraint_status": canonical_status.value,
            "dry_run": True,
        }, warnings=["Dry run — nothing written."])

    with db_connection(db_path) as conn:
        conn.execute(
            """INSERT INTO constraints (
                goal_id, type, severity, status, scope,
                start_date, end_date, source, confidence,
                raw_text, tags_json, notes_json
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                goal_id,
                canonical_type.value,
                canonical_severity.value,
                canonical_status.value,
                canonical_scope.value,
                start_date,
                end_date,
                source,
                confidence,
                raw_text,
                tags_json,
                notes_json,
            ),
        )
        conn.commit()
        constraint_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        return success_response({
            "constraint_id": constraint_id,
            "constraint_status": canonical_status.value,
        }, warnings=warnings)


def delete_constraint(
    constraint_id: int,
    dry_run: bool = False,
    db_path: Any = None,
) -> dict[str, Any]:
    """Supprime une contrainte.

    Returns:
        Réponse JSON avec la contrainte supprimée.
    """
    with db_connection(db_path) as conn:
        existing = fetchone_dict(conn, "SELECT * FROM constraints WHERE id=?", (constraint_id,))
        if not existing:
            return error_response([f"Constraint {constraint_id} not found."])

        if dry_run:
            return success_response({
                "constraint_id": constraint_id,
                "dry_run": True,
            }, warnings=["Dry run — nothing deleted."])

        conn.execute("DELETE FROM constraints WHERE id=?", (constraint_id,))
        conn.commit()

        return success_response({"constraint_id": constraint_id})
