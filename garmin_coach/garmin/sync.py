"""Synchronisation Garmin — import activités et métriques."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, date, datetime, timedelta
from typing import Any

from garmin_coach.db import db_connection, fetchall_dicts
from garmin_coach.garmin.client import get_client
from garmin_coach.jsonio import error_response, partial_response, success_response


def sync(
    start_date: date | None = None,
    end_date: date | None = None,
    lookback_days: int = 3,
    db_path: Any = None,
    tokens_dir: Any = None,
) -> dict[str, Any]:
    """Synchronise les activités et métriques depuis Garmin.

    Args:
        start_date: Début de la plage d'import (défaut: lookback_days avant aujourd'hui).
        end_date: Fin de la plage d'import (défaut: hier).
        lookback_days: Nombre de jours de lookback par défaut.
        db_path: Chemin de la base SQLite.
        tokens_dir: Répertoire des tokens Garmin.

    Returns:
        Réponse JSON avec le statut de synchronisation.
    """
    warnings: list[str] = []
    errors: list[str] = []

    with db_connection(db_path) as conn:
        today = date.today()
        if end_date is None:
            end_date = today - timedelta(days=1)
        if start_date is None:
            start_date = end_date - timedelta(days=lookback_days - 1)

        range_start = start_date.isoformat()
        range_end = end_date.isoformat()

        # Enregistrer le début de sync
        started_at = datetime.now(UTC).isoformat()
        conn.execute(
            """INSERT INTO sync_runs (source, sync_type, started_at, status, range_start, range_end)
               VALUES ('garmin', 'daily', ?, 'running', ?, ?)""",
            (started_at, range_start, range_end),
        )
        conn.commit()
        sync_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        try:
            client = get_client(tokens_dir)
        except Exception as exc:
            _finish_sync(conn, sync_id, "failed", error_message=str(exc))
            return error_response([f"Garmin client error: {exc}"])

        # Import des activités
        activities_seen = 0
        activities_inserted = 0
        activities_updated = 0

        try:
            activities = client.get_activities_by_date(
                range_start, range_end, activitytype=""
            )
            activities_seen = len(activities)

            for act in activities:
                inserted, updated = _upsert_activity(conn, act)
                activities_inserted += inserted
                activities_updated += updated
        except Exception as exc:
            errors.append(f"Activities sync error: {exc}")

        # Import des daily metrics
        daily_metrics_seen = 0
        daily_metrics_upserted = 0

        try:
            current = start_date
            while current <= end_date:
                metrics = _fetch_daily_metrics(client, current)
                if metrics:
                    daily_metrics_seen += 1
                    daily_metrics_upserted += _upsert_daily_metrics(conn, current, metrics)
                current += timedelta(days=1)
        except Exception as exc:
            errors.append(f"Daily metrics sync error: {exc}")

        # Réconciliation plan ↔ activités
        reconciled_sessions = 0
        matched_activities = 0
        try:
            reconciled_sessions, matched_activities = _reconcile_plan(conn, start_date, end_date)
        except Exception as exc:
            warnings.append(f"Reconciliation warning: {exc}")

        # Finaliser le sync run
        status = "success" if not errors else "partial"
        _finish_sync(
            conn,
            sync_id,
            status,
            activities_seen=activities_seen,
            activities_inserted=activities_inserted,
            activities_updated=activities_updated,
            daily_metrics_seen=daily_metrics_seen,
            daily_metrics_upserted=daily_metrics_upserted,
        )

        data = {
            "source": "garmin",
            "range_start": range_start,
            "range_end": range_end,
            "activities_seen": activities_seen,
            "activities_inserted": activities_inserted,
            "activities_updated": activities_updated,
            "daily_metrics_seen": daily_metrics_seen,
            "daily_metrics_upserted": daily_metrics_upserted,
            "reconciled_sessions": reconciled_sessions,
            "matched_activities": matched_activities,
        }

        if errors:
            return partial_response(data, warnings=warnings, errors=errors)
        return success_response(data, warnings=warnings)


def _upsert_activity(conn: sqlite3.Connection, act: dict[str, Any]) -> tuple[int, int]:
    """Insère ou met à jour une activité. Retourne (inserted, updated)."""
    external_id = str(act.get("activityId", ""))
    existing = conn.execute(
        "SELECT id FROM activities WHERE source='garmin' AND external_id=?",
        (external_id,),
    ).fetchone()

    activity_type = act.get("activityType", {}).get("typeKey", "unknown")
    start_time = act.get("startTimeGMT", "")
    duration = int(act.get("duration", 0))

    if existing:
        conn.execute(
            """UPDATE activities SET
                activity_type=?, activity_name=?, start_time_utc=?, duration_s=?,
                distance_m=?, elevation_gain_m=?, calories_kcal=?,
                avg_hr=?, max_hr=?, avg_speed_mps=?, max_speed_mps=?,
                avg_pace_sec_per_km=?, raw_payload_json=?,
                updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (
                activity_type,
                act.get("activityName"),
                start_time,
                duration,
                act.get("distance"),
                act.get("elevationGain"),
                act.get("calories"),
                act.get("averageHR"),
                act.get("maxHR"),
                act.get("averageSpeed"),
                act.get("maxSpeed"),
                act.get("averagePace"),
                json.dumps(act),
                existing[0],
            ),
        )
        conn.commit()
        return (0, 1)
    else:
        conn.execute(
            """INSERT INTO activities (
                source, external_id, activity_type, activity_name,
                start_time_utc, duration_s, distance_m, elevation_gain_m,
                calories_kcal, avg_hr, max_hr, avg_speed_mps, max_speed_mps,
                avg_pace_sec_per_km, raw_payload_json
               ) VALUES ('garmin', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                external_id,
                activity_type,
                act.get("activityName"),
                start_time,
                duration,
                act.get("distance"),
                act.get("elevationGain"),
                act.get("calories"),
                act.get("averageHR"),
                act.get("maxHR"),
                act.get("averageSpeed"),
                act.get("maxSpeed"),
                act.get("averagePace"),
                json.dumps(act),
            ),
        )
        conn.commit()
        return (1, 0)


def _fetch_daily_metrics(client: Any, metric_date: date) -> dict[str, Any] | None:
    """Récupère les métriques journalières pour une date donnée."""
    try:
        stats = client.get_stats(metric_date.isoformat())
        if stats:
            return stats
    except Exception:
        pass
    return None


def _upsert_daily_metrics(conn: sqlite3.Connection, metric_date: date, metrics: dict[str, Any]) -> int:
    """Insère ou met à jour les métriques journalières. Retourne 1 si upsert."""
    date_str = metric_date.isoformat()
    existing = conn.execute(
        "SELECT id FROM daily_metrics WHERE source='garmin' AND metric_date=?",
        (date_str,),
    ).fetchone()

    values = (
        date_str,
        metrics.get("totalSteps"),
        metrics.get("totalDistanceMeters"),
        metrics.get("floorsClimbed"),
        metrics.get("intensityMinutes"),
        metrics.get("activeKilocalories"),
        metrics.get("totalKilocalories"),
        metrics.get("restingHeartRate"),
        metrics.get("minHeartRate"),
        metrics.get("maxHeartRate"),
        metrics.get("averageHeartRate"),
        metrics.get("averageStressLevel"),
        metrics.get("maxStressLevel"),
        metrics.get("bodyBatteryChargedValue"),
        metrics.get("bodyBatteryDrainedValue"),
        metrics.get("bodyBatteryLowestValue"),
        metrics.get("bodyBatteryHighestValue"),
        json.dumps(metrics),
    )

    if existing:
        conn.execute(
            """UPDATE daily_metrics SET
                steps=?, distance_m=?, floors_climbed=?, intensity_minutes=?,
                active_calories_kcal=?, total_calories_kcal=?,
                resting_hr=?, min_hr=?, max_hr=?, avg_hr=?,
                stress_avg=?, stress_max=?,
                body_battery_start=?, body_battery_end=?,
                body_battery_min=?, body_battery_max=?,
                raw_payload_json=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (*values[1:], existing[0]),
        )
    else:
        conn.execute(
            """INSERT INTO daily_metrics (
                source, metric_date, steps, distance_m, floors_climbed,
                intensity_minutes, active_calories_kcal, total_calories_kcal,
                resting_hr, min_hr, max_hr, avg_hr,
                stress_avg, stress_max,
                body_battery_start, body_battery_end,
                body_battery_min, body_battery_max,
                raw_payload_json
               ) VALUES ('garmin', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            values,
        )
    conn.commit()
    return 1


def _reconcile_plan(conn: sqlite3.Connection, start_date: date, end_date: date) -> tuple[int, int]:
    """Réconcilie les séances du plan avec les activités importées.

    Returns:
        (reconciled_sessions, matched_activities)
    """
    # Chercher les séances du plan dans la plage
    sessions = fetchall_dicts(
        conn,
        """SELECT ps.id, ps.planned_date, ps.activity_type, ps.duration_min
           FROM plan_sessions ps
           JOIN training_plans tp ON ps.plan_id = tp.id
           WHERE ps.planned_date BETWEEN ? AND ?
             AND ps.status IN ('proposed', 'exported')
             AND tp.status IN ('active', 'sent')""",
        (start_date.isoformat(), end_date.isoformat()),
    )

    reconciled = 0
    matched = 0

    for session in sessions:
        # Chercher une activité correspondante
        activity = conn.execute(
            """SELECT id FROM activities
               WHERE activity_type = ?
                 AND date(start_time_utc) = ?
                 AND NOT EXISTS (
                     SELECT 1 FROM plan_activity_matches WHERE activity_id = activities.id
                 )
               ORDER BY ABS(duration_s - ? * 60) ASC
               LIMIT 1""",
            (session["activity_type"], session["planned_date"], session["duration_min"]),
        ).fetchone()

        if activity:
            # Vérifier qu'un match n'existe pas déjà
            existing_match = conn.execute(
                "SELECT 1 FROM plan_activity_matches WHERE plan_session_id=? AND activity_id=?",
                (session["id"], activity[0]),
            ).fetchone()

            if not existing_match:
                conn.execute(
                    """INSERT INTO plan_activity_matches (plan_session_id, activity_id, match_type)
                       VALUES (?, ?, 'inferred')""",
                    (session["id"], activity[0]),
                )
                conn.execute(
                    "UPDATE plan_sessions SET status='done', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (session["id"],),
                )
                matched += 1
            reconciled += 1

    conn.commit()
    return reconciled, matched


def _finish_sync(
    conn: sqlite3.Connection,
    sync_id: int,
    status: str,
    error_message: str | None = None,
    **counters: int,
) -> None:
    """Met à jour le sync_run avec le statut final."""
    sets = ["finished_at=CURRENT_TIMESTAMP", "status=?"]
    params: list[Any] = [status]

    if error_message:
        sets.append("error_message=?")
        params.append(error_message)

    for key, val in counters.items():
        sets.append(f"{key}=?")
        params.append(val)

    params.append(sync_id)
    conn.execute(f"UPDATE sync_runs SET {', '.join(sets)} WHERE id=?", params)
    conn.commit()
