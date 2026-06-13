"""Lecture des activités réelles importées."""

from __future__ import annotations

from typing import Any

from garmin_coach.db import db_connection, fetchall_dicts
from garmin_coach.jsonio import error_response, success_response


def get_activities(
    start: str,
    end: str,
    limit: int | None = None,
    activity_type: str | None = None,
    db_path: Any = None,
) -> dict[str, Any]:
    """Lit les activités sur une plage de dates.

    Args:
        start: Date ISO YYYY-MM-DD incluse.
        end: Date ISO YYYY-MM-DD incluse.
        limit: Nombre max de lignes.
        activity_type: Filtre par type d'activité.
        db_path: Chemin de la base SQLite.

    Returns:
        Réponse JSON avec les activités et un résumé.
    """
    with db_connection(db_path) as conn:
        sql = """
            SELECT a.id, a.source, a.external_id, a.activity_type, a.activity_name,
                   a.start_time_utc, a.local_start_time, a.duration_s, a.moving_duration_s,
                   a.distance_m, a.elevation_gain_m, a.calories_kcal,
                   a.avg_hr, a.max_hr, a.avg_speed_mps, a.avg_pace_sec_per_km,
                   a.training_effect_aerobic, a.training_effect_anaerobic,
                   a.perceived_effort,
                   d.status AS debrief_status,
                   d.completed_at AS debrief_completed_at,
                   d.rpe AS debrief_rpe,
                   d.plan_session_id AS debrief_plan_session_id
            FROM activities a
            LEFT JOIN activity_debriefs d ON d.activity_id = a.id
            WHERE date(coalesce(a.local_start_time, a.start_time_utc)) >= ?
              AND date(coalesce(a.local_start_time, a.start_time_utc)) <= ?
        """
        params: list[Any] = [start, end]

        if activity_type:
            sql += " AND a.activity_type = ?"
            params.append(activity_type)

        sql += " ORDER BY a.start_time_utc DESC"

        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        activities = fetchall_dicts(conn, sql, tuple(params))

        # Résumé agrégé
        total_duration_min = sum(a.get("duration_s", 0) for a in activities) // 60
        total_distance_km = sum((a.get("distance_m") or 0) for a in activities) / 1000
        total_calories = sum((a.get("calories_kcal") or 0) for a in activities)

        summary = {
            "count": len(activities),
            "total_duration_min": total_duration_min,
            "total_distance_km": round(total_distance_km, 2),
            "total_calories_kcal": total_calories,
        }

        return success_response({
            "period": {"start": start, "end": end},
            "activities": activities,
            "summary": summary,
        })
