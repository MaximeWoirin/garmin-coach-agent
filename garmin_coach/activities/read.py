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
            SELECT id, source, external_id, activity_type, activity_name,
                   start_time_utc, local_start_time, duration_s, moving_duration_s,
                   distance_m, elevation_gain_m, calories_kcal,
                   avg_hr, max_hr, avg_speed_mps, avg_pace_sec_per_km,
                   training_effect_aerobic, training_effect_anaerobic,
                   perceived_effort
            FROM activities
            WHERE date(coalesce(local_start_time, start_time_utc)) >= ?
              AND date(coalesce(local_start_time, start_time_utc)) <= ?
        """
        params: list[Any] = [start, end]

        if activity_type:
            sql += " AND activity_type = ?"
            params.append(activity_type)

        sql += " ORDER BY start_time_utc DESC"

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
