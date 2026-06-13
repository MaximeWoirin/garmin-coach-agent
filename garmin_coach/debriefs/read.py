"""Lecture / détection des débriefs post-activité."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from garmin_coach.db import db_connection, fetchall_dicts
from garmin_coach.enums import DebriefStatus
from garmin_coach.jsonio import error_response, success_response


def get_pending_debriefs(
    lookback_hours: int = 36,
    min_age_minutes: int = 0,
    reprompt_after_hours: int = 12,
    max_prompt_count: int = 2,
    limit: int = 20,
    db_path: Any = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Retourne les activités récentes pouvant recevoir un débrief."""
    if lookback_hours <= 0:
        return error_response(["lookback_hours must be > 0."])
    if min_age_minutes < 0:
        return error_response(["min_age_minutes must be >= 0."])
    if reprompt_after_hours < 0:
        return error_response(["reprompt_after_hours must be >= 0."])
    if max_prompt_count < 0:
        return error_response(["max_prompt_count must be >= 0."])
    if limit <= 0:
        return error_response(["limit must be > 0."])

    ref_now = now or datetime.now(UTC)
    newest_allowed = ref_now - timedelta(minutes=min_age_minutes)
    oldest_allowed = ref_now - timedelta(hours=lookback_hours)
    reprompt_before = ref_now - timedelta(hours=reprompt_after_hours)

    with db_connection(db_path) as conn:
        candidates = fetchall_dicts(
            conn,
            """
            SELECT a.id AS activity_id,
                   a.external_id,
                   a.activity_type,
                   a.activity_name,
                   a.start_time_utc,
                   a.local_start_time,
                   a.duration_s,
                   a.distance_m,
                   d.id AS debrief_id,
                   d.plan_session_id AS debrief_plan_session_id,
                   d.status AS debrief_status,
                   d.prompt_count,
                   d.first_prompted_at,
                   d.last_prompted_at,
                   d.completed_at,
                   d.dismissed_at,
                   (
                     SELECT pam.plan_session_id
                     FROM plan_activity_matches pam
                     WHERE pam.activity_id = a.id
                     ORDER BY pam.confidence DESC, pam.matched_at DESC, pam.id DESC
                     LIMIT 1
                   ) AS matched_plan_session_id
            FROM activities a
            LEFT JOIN activity_debriefs d ON d.activity_id = a.id
            WHERE datetime(a.start_time_utc) >= datetime(?)
              AND datetime(a.start_time_utc) <= datetime(?)
            ORDER BY datetime(a.start_time_utc) DESC
            LIMIT ?
            """,
            (
                oldest_allowed.strftime("%Y-%m-%dT%H:%M:%S"),
                newest_allowed.strftime("%Y-%m-%dT%H:%M:%S"),
                limit * 4,
            ),
        )

        created_rows = 0
        for row in candidates:
            if row["debrief_id"] is not None:
                continue
            conn.execute(
                """
                INSERT INTO activity_debriefs (activity_id, plan_session_id, status)
                VALUES (?, ?, 'pending')
                """,
                (row["activity_id"], row["matched_plan_session_id"]),
            )
            created_rows += 1
        if created_rows:
            conn.commit()
            candidates = fetchall_dicts(
                conn,
                """
                SELECT a.id AS activity_id,
                       a.external_id,
                       a.activity_type,
                       a.activity_name,
                       a.start_time_utc,
                       a.local_start_time,
                       a.duration_s,
                       a.distance_m,
                       d.id AS debrief_id,
                       d.plan_session_id AS debrief_plan_session_id,
                       d.status AS debrief_status,
                       d.prompt_count,
                       d.first_prompted_at,
                       d.last_prompted_at,
                       d.completed_at,
                       d.dismissed_at,
                       (
                         SELECT pam.plan_session_id
                         FROM plan_activity_matches pam
                         WHERE pam.activity_id = a.id
                         ORDER BY pam.confidence DESC, pam.matched_at DESC, pam.id DESC
                         LIMIT 1
                       ) AS matched_plan_session_id
                FROM activities a
                JOIN activity_debriefs d ON d.activity_id = a.id
                WHERE datetime(a.start_time_utc) >= datetime(?)
                  AND datetime(a.start_time_utc) <= datetime(?)
                ORDER BY datetime(a.start_time_utc) DESC
                LIMIT ?
                """,
                (
                    oldest_allowed.strftime("%Y-%m-%dT%H:%M:%S"),
                    newest_allowed.strftime("%Y-%m-%dT%H:%M:%S"),
                    limit * 4,
                ),
            )

        pending: list[dict[str, Any]] = []
        for row in candidates:
            status = DebriefStatus(row["debrief_status"])
            if status in {DebriefStatus.COMPLETED, DebriefStatus.DISMISSED}:
                continue

            prompt_count = int(row["prompt_count"] or 0)
            last_prompted_at = row["last_prompted_at"]
            ready_to_prompt = prompt_count < max_prompt_count and (
                last_prompted_at is None or last_prompted_at <= reprompt_before.strftime("%Y-%m-%dT%H:%M:%S")
            )
            if not ready_to_prompt:
                continue

            pending.append(
                {
                    "activity_id": row["activity_id"],
                    "external_id": row["external_id"],
                    "activity_type": row["activity_type"],
                    "activity_name": row["activity_name"],
                    "start_time_utc": row["start_time_utc"],
                    "local_start_time": row["local_start_time"],
                    "duration_s": row["duration_s"],
                    "distance_m": row["distance_m"],
                    "plan_session_id": row["debrief_plan_session_id"] or row["matched_plan_session_id"],
                    "debrief_status": status.value,
                    "prompt_count": prompt_count,
                    "last_prompted_at": last_prompted_at,
                    "ready_to_prompt": True,
                }
            )
            if len(pending) >= limit:
                break

        return success_response(
            {
                "window": {
                    "lookback_hours": lookback_hours,
                    "min_age_minutes": min_age_minutes,
                    "reprompt_after_hours": reprompt_after_hours,
                    "max_prompt_count": max_prompt_count,
                    "evaluated_at": ref_now.isoformat(),
                },
                "pending_debriefs": pending,
                "summary": {
                    "count": len(pending),
                    "rows_created": created_rows,
                },
            }
        )
