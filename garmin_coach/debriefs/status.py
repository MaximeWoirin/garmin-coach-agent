"""Transitions de statut pour les débriefs post-activité."""

from __future__ import annotations

from typing import Any

from garmin_coach.db import db_connection, fetchall_dicts
from garmin_coach.enums import DebriefStatus
from garmin_coach.jsonio import error_response, success_response


def mark_activity_debrief_prompted(
    activity_ids: list[int],
    dry_run: bool = False,
    db_path: Any = None,
) -> dict[str, Any]:
    """Marque un ou plusieurs débriefs comme déjà sollicités."""
    normalized_ids = [int(activity_id) for activity_id in activity_ids]
    if not normalized_ids:
        return error_response(["At least one activity_id is required."])

    with db_connection(db_path) as conn:
        rows = fetchall_dicts(
            conn,
            """
            SELECT activity_id, status, prompt_count, first_prompted_at, last_prompted_at
            FROM activity_debriefs
            WHERE activity_id IN ({placeholders})
            ORDER BY activity_id
            """.format(placeholders=", ".join("?" for _ in normalized_ids)),
            tuple(normalized_ids),
        )
        found_ids = {int(row["activity_id"]) for row in rows}
        missing = [activity_id for activity_id in normalized_ids if activity_id not in found_ids]
        if missing:
            return error_response([f"Debrief rows not found for activity ids: {missing}"])

        locked = [
            int(row["activity_id"])
            for row in rows
            if DebriefStatus(row["status"]) in {DebriefStatus.COMPLETED, DebriefStatus.DISMISSED}
        ]
        if locked:
            return error_response([f"Debriefs already closed for activity ids: {locked}"])

        updated = []
        for row in rows:
            updated.append(
                {
                    "activity_id": int(row["activity_id"]),
                    "previous_status": row["status"],
                    "next_status": DebriefStatus.PROMPTED.value,
                    "prompt_count": int(row["prompt_count"] or 0) + 1,
                }
            )

        if dry_run:
            return success_response({"updated": updated, "dry_run": True}, warnings=["Dry run — nothing written."])

        conn.execute(
            """
            UPDATE activity_debriefs
            SET status='prompted',
                prompt_count=prompt_count + 1,
                first_prompted_at=COALESCE(first_prompted_at, CURRENT_TIMESTAMP),
                last_prompted_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP
            WHERE activity_id IN ({placeholders})
            """.format(placeholders=", ".join("?" for _ in normalized_ids)),
            tuple(normalized_ids),
        )
        conn.commit()
        return success_response({"updated": updated})
