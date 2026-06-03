"""Lecture des métriques physiologiques (daily metrics)."""

from __future__ import annotations

from typing import Any

from garmin_coach.db import db_connection, fetchall_dicts
from garmin_coach.jsonio import success_response


def get_fitness_state(
    start: str,
    end: str,
    limit: int | None = None,
    db_path: Any = None,
) -> dict[str, Any]:
    """Lit les métriques journalières sur une plage.

    Args:
        start: Date ISO YYYY-MM-DD incluse.
        end: Date ISO YYYY-MM-DD exclue.
        limit: Nombre max de jours.
        db_path: Chemin de la base SQLite.

    Returns:
        Réponse JSON avec les métriques et un résumé de tendance.
    """
    with db_connection(db_path) as conn:
        sql = """
            SELECT id, metric_date, steps, distance_m, intensity_minutes,
                   resting_hr, min_hr, max_hr, avg_hr,
                   stress_avg, stress_max,
                   body_battery_start, body_battery_end,
                   body_battery_min, body_battery_max,
                   respiration_avg, pulse_ox_avg
            FROM daily_metrics
            WHERE metric_date >= ? AND metric_date < ?
            ORDER BY metric_date ASC
        """
        params: list[Any] = [start, end]

        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        metrics = fetchall_dicts(conn, sql, tuple(params))

        # Résumé de tendances
        summary = _compute_trends(metrics)

        return success_response({
            "period": {"start": start, "end": end},
            "daily_metrics": metrics,
            "summary": summary,
        })


def _compute_trends(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    """Calcule un résumé synthétique des tendances."""
    if not metrics:
        return {"days": 0, "signal": "no_data"}

    days = len(metrics)

    def avg_non_null(key: str) -> float | None:
        values = [m[key] for m in metrics if m.get(key) is not None]
        return round(sum(values) / len(values), 1) if values else None

    avg_resting_hr = avg_non_null("resting_hr")
    avg_stress = avg_non_null("stress_avg")
    avg_body_battery_end = avg_non_null("body_battery_end")
    avg_intensity_min = avg_non_null("intensity_minutes")

    # Signal synthétique simple
    signal = "neutral"
    if avg_stress is not None and avg_body_battery_end is not None:
        if avg_stress > 50 or avg_body_battery_end < 30:
            signal = "fatigue"
        elif avg_stress < 30 and avg_body_battery_end > 60:
            signal = "fresh"

    return {
        "days": days,
        "avg_resting_hr": avg_resting_hr,
        "avg_stress": avg_stress,
        "avg_body_battery_end": avg_body_battery_end,
        "avg_intensity_minutes": avg_intensity_min,
        "signal": signal,
    }
