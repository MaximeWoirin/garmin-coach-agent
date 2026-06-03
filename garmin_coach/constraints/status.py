"""Changement de statut d'une contrainte."""

from __future__ import annotations

from typing import Any

from garmin_coach.db import db_connection, fetchone_dict
from garmin_coach.enums import ConstraintStatus
from garmin_coach.jsonio import error_response, success_response


def set_constraint_status(
    constraint_id: int,
    status: str,
    dry_run: bool = False,
    db_path: Any = None,
) -> dict[str, Any]:
    """Change le statut d'une contrainte.

    Args:
        constraint_id: Identifiant de la contrainte.
        status: Nouveau statut.
        dry_run: Simule sans écrire.
        db_path: Chemin de la base SQLite.

    Returns:
        Réponse JSON avec la contrainte mise à jour.
    """
    # Validation
    try:
        canonical_status = ConstraintStatus(status)
    except ValueError:
        return error_response([f"Invalid status: {status}. Valid: {[e.value for e in ConstraintStatus]}"])

    with db_connection(db_path) as conn:
        existing = fetchone_dict(conn, "SELECT * FROM constraints WHERE id=?", (constraint_id,))
        if not existing:
            return error_response([f"Constraint {constraint_id} not found."])

        if dry_run:
            return success_response({
                "constraint_id": constraint_id,
                "constraint_status": canonical_status.value,
                "dry_run": True,
            }, warnings=["Dry run — nothing written."])

        resolved_at = "CURRENT_TIMESTAMP" if canonical_status == ConstraintStatus.INACTIVE else None

        if resolved_at:
            conn.execute(
                "UPDATE constraints SET status=?, resolved_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (canonical_status.value, constraint_id),
            )
        else:
            conn.execute(
                "UPDATE constraints SET status=?, resolved_at=NULL, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (canonical_status.value, constraint_id),
            )
        conn.commit()

        return success_response({
            "constraint_id": constraint_id,
            "constraint_status": canonical_status.value,
        })
