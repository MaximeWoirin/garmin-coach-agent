"""Écriture des débriefs post-activité."""

from __future__ import annotations

from typing import Any

from garmin_coach.db import db_connection, fetchone_dict
from garmin_coach.enums import DebriefStatus
from garmin_coach.jsonio import error_response, success_response


PAIN_FIELDS = ("pain_during", "pain_after", "pain_next_morning")


def save_activity_debrief(
    activity_id: int,
    rpe: int,
    note: str | None = None,
    pain_during: int | None = None,
    pain_after: int | None = None,
    pain_next_morning: int | None = None,
    plan_session_id: int | None = None,
    source: str = "user",
    dry_run: bool = False,
    db_path: Any = None,
) -> dict[str, Any]:
    """Persiste un débrief immuable rattaché à une activité réelle."""
    if rpe < 1 or rpe > 10:
        return error_response(["rpe must be between 1 and 10."])

    pains = {
        "pain_during": pain_during,
        "pain_after": pain_after,
        "pain_next_morning": pain_next_morning,
    }
    for field, value in pains.items():
        if value is not None and (value < 0 or value > 10):
            return error_response([f"{field} must be between 0 and 10."])

    cleaned_note = note.strip() if note is not None else None
    if cleaned_note == "":
        cleaned_note = None

    if dry_run:
        return success_response(
            {
                "activity_id": activity_id,
                "plan_session_id": plan_session_id,
                "debrief_status": DebriefStatus.COMPLETED.value,
                "rpe": rpe,
                "note": cleaned_note,
                **pains,
                "dry_run": True,
            },
            warnings=["Dry run — nothing written."],
        )

    with db_connection(db_path) as conn:
        activity = fetchone_dict(
            conn,
            "SELECT id, source, external_id, activity_type, activity_name, start_time_utc FROM activities WHERE id=?",
            (activity_id,),
        )
        if activity is None:
            return error_response([f"Activity {activity_id} not found."])

        resolved_plan_session_id = plan_session_id
        if resolved_plan_session_id is None:
            match = fetchone_dict(
                conn,
                """
                SELECT plan_session_id
                FROM plan_activity_matches
                WHERE activity_id=?
                ORDER BY confidence DESC, matched_at DESC, id DESC
                LIMIT 1
                """,
                (activity_id,),
            )
            if match is not None:
                resolved_plan_session_id = int(match["plan_session_id"])

        if resolved_plan_session_id is not None:
            session = fetchone_dict(
                conn,
                "SELECT id FROM plan_sessions WHERE id=?",
                (resolved_plan_session_id,),
            )
            if session is None:
                return error_response([f"Plan session {resolved_plan_session_id} not found."])

        existing = fetchone_dict(
            conn,
            "SELECT * FROM activity_debriefs WHERE activity_id=?",
            (activity_id,),
        )
        if existing is not None:
            existing_status = DebriefStatus(existing["status"])
            if existing_status in {DebriefStatus.COMPLETED, DebriefStatus.DISMISSED}:
                return error_response(
                    [
                        f"Debrief for activity {activity_id} is immutable once {existing_status.value}."
                    ]
                )
            existing_plan_session_id = existing.get("plan_session_id")
            if (
                existing_plan_session_id is not None
                and resolved_plan_session_id is not None
                and int(existing_plan_session_id) != resolved_plan_session_id
            ):
                return error_response(
                    [
                        "Existing debrief row already targets another plan_session_id; refusing overwrite."
                    ]
                )

            conn.execute(
                """
                UPDATE activity_debriefs
                SET plan_session_id=COALESCE(plan_session_id, ?),
                    status='completed',
                    rpe=?,
                    pain_during=?,
                    pain_after=?,
                    pain_next_morning=?,
                    note=?,
                    source=?,
                    completed_at=CURRENT_TIMESTAMP,
                    updated_at=CURRENT_TIMESTAMP
                WHERE activity_id=?
                """,
                (
                    resolved_plan_session_id,
                    rpe,
                    pain_during,
                    pain_after,
                    pain_next_morning,
                    cleaned_note,
                    source,
                    activity_id,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO activity_debriefs (
                    activity_id,
                    plan_session_id,
                    status,
                    rpe,
                    pain_during,
                    pain_after,
                    pain_next_morning,
                    note,
                    source,
                    completed_at
                ) VALUES (?, ?, 'completed', ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    activity_id,
                    resolved_plan_session_id,
                    rpe,
                    pain_during,
                    pain_after,
                    pain_next_morning,
                    cleaned_note,
                    source,
                ),
            )
        conn.commit()

        saved = fetchone_dict(
            conn,
            """
            SELECT d.id, d.activity_id, d.plan_session_id, d.status, d.rpe,
                   d.pain_during, d.pain_after, d.pain_next_morning,
                   d.note, d.source, d.completed_at,
                   a.external_id, a.activity_type, a.activity_name, a.start_time_utc
            FROM activity_debriefs d
            JOIN activities a ON a.id = d.activity_id
            WHERE d.activity_id=?
            """,
            (activity_id,),
        )
        if saved is None:
            return error_response([f"Debrief for activity {activity_id} could not be reloaded."])

        return success_response(
            {
                "activity_id": saved["activity_id"],
                "plan_session_id": saved["plan_session_id"],
                "debrief_status": saved["status"],
                "rpe": saved["rpe"],
                "pain_during": saved["pain_during"],
                "pain_after": saved["pain_after"],
                "pain_next_morning": saved["pain_next_morning"],
                "note": saved["note"],
                "completed_at": saved["completed_at"],
                "activity": {
                    "id": saved["activity_id"],
                    "external_id": saved["external_id"],
                    "activity_type": saved["activity_type"],
                    "activity_name": saved["activity_name"],
                    "start_time_utc": saved["start_time_utc"],
                },
            }
        )
