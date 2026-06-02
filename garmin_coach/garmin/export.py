"""Export de plans vers Garmin Connect.

L'export est progressif et piloté au niveau session :
- seules les séances `proposed` sont exportables
- les séances `draft` ne sont pas exportées (pas encore validées)
- les séances `exported` ne sont pas réexportées (sauf --force)
- les séances `done`, `skipped`, `canceled` sont ignorées

L'export supporte un horizon court via --start-date / --end-date / --days-ahead.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from typing import Any

from garmin_coach.db import ensure_db, fetchall_dicts, fetchone_dict
from garmin_coach.enums import SessionStatus
from garmin_coach.garmin.client import get_client
from garmin_coach.jsonio import error_response, partial_response, success_response


def export_plan(
    plan_id: int | None = None,
    week_start: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    days_ahead: int | None = None,
    dry_run: bool = False,
    force: bool = False,
    db_path: Any = None,
    tokens_dir: Any = None,
) -> dict[str, Any]:
    """Exporte les séances proposed d'un plan vers Garmin.

    Seules les séances en statut `proposed` sont exportées.
    Les séances `draft` ne sont pas considérées comme prêtes.
    Les séances déjà `exported` sont ignorées sauf si force=True.

    Args:
        plan_id: Identifiant du plan à exporter.
        week_start: Alternative pour cibler le plan actif d'une semaine.
        start_date: Date de début de l'horizon d'export (ISO YYYY-MM-DD).
        end_date: Date de fin de l'horizon d'export (ISO YYYY-MM-DD).
        days_ahead: Nombre de jours à exporter à partir d'aujourd'hui.
        dry_run: Simule l'export sans écrire.
        force: Réécrit l'export même si des séances ont un garmin_event_id.
        db_path: Chemin de la base SQLite.
        tokens_dir: Répertoire des tokens Garmin.

    Returns:
        Réponse JSON avec le statut d'export.
    """
    conn = ensure_db(db_path)
    warnings: list[str] = []
    errors: list[str] = []

    # Trouver le plan
    plan = _find_plan(conn, plan_id, week_start)
    if not plan:
        return error_response(["Plan not found."])

    # Calculer l'horizon de dates
    date_start, date_end = _resolve_date_range(start_date, end_date, days_ahead)

    # Charger les séances du plan
    sessions = fetchall_dicts(
        conn,
        """SELECT * FROM plan_sessions WHERE plan_id = ?
           ORDER BY planned_date ASC""",
        (plan["id"],),
    )

    if not sessions:
        return error_response(["No sessions found for this plan."])

    sessions_seen = len(sessions)
    sessions_exported = 0
    sessions_skipped = 0
    sessions_ignored = 0
    sessions_failed = 0
    garmin_event_ids: list[str] = []

    if not dry_run:
        try:
            client = get_client(tokens_dir)
        except Exception as exc:
            return error_response([f"Garmin client error: {exc}"])

    for session in sessions:
        # Appliquer le filtre de plage de dates
        if date_start or date_end:
            session_date = session["planned_date"]
            if date_start and session_date < date_start:
                sessions_ignored += 1
                continue
            if date_end and session_date > date_end:
                sessions_ignored += 1
                continue

        # Vérifier si déjà exporté
        if session["status"] == SessionStatus.EXPORTED:
            if not force:
                sessions_skipped += 1
                if session["garmin_event_id"]:
                    warnings.append(
                        f"Session {session['id']} already exported "
                        f"(garmin_event_id={session['garmin_event_id']})"
                    )
                continue
        # Seules les séances `proposed` sont exportables par défaut.
        # `--force` permet explicitement de réexporter une séance déjà `exported`.
        elif session["status"] != SessionStatus.PROPOSED:
            sessions_skipped += 1
            continue

        if dry_run:
            sessions_exported += 1
            garmin_event_ids.append(f"dry-run-{session['id']}")
            continue

        # Construire le payload Garmin
        try:
            payload = _build_workout_payload(session)
            event_id = _push_to_garmin(client, payload, session)  # type: ignore[arg-type]

            if event_id:
                conn.execute(
                    """UPDATE plan_sessions
                       SET garmin_event_id=?, status=?, updated_at=CURRENT_TIMESTAMP
                       WHERE id=?""",
                    (event_id, SessionStatus.EXPORTED, session["id"]),
                )
                conn.commit()
                garmin_event_ids.append(event_id)
                sessions_exported += 1
            else:
                sessions_failed += 1
                errors.append(f"Session {session['id']}: no event_id returned")
        except Exception as exc:
            sessions_failed += 1
            errors.append(f"Session {session['id']}: {exc}")

    data = {
        "plan_id": plan["id"],
        "week_start": plan["week_start"],
        "week_end": plan["week_end"],
        "sessions_seen": sessions_seen,
        "sessions_exported": sessions_exported,
        "sessions_skipped": sessions_skipped,
        "sessions_ignored": sessions_ignored,
        "sessions_failed": sessions_failed,
        "garmin_event_ids": garmin_event_ids,
    }

    if errors:
        return partial_response(data, warnings=warnings, errors=errors)
    return success_response(data, warnings=warnings)


def _resolve_date_range(
    start_date: str | None,
    end_date: str | None,
    days_ahead: int | None,
) -> tuple[str | None, str | None]:
    """Résout les paramètres de plage de dates en bornes ISO."""
    if days_ahead is not None:
        today = date.today().isoformat()
        end = (date.today() + timedelta(days=days_ahead)).isoformat()
        return start_date or today, end_date or end
    return start_date, end_date


def _find_plan(conn: sqlite3.Connection, plan_id: int | None, week_start: str | None) -> dict[str, Any] | None:
    """Trouve le plan par id ou par semaine."""
    if plan_id:
        return fetchone_dict(conn, "SELECT * FROM training_plans WHERE id=?", (plan_id,))
    if week_start:
        return fetchone_dict(
            conn,
            "SELECT * FROM training_plans WHERE week_start=? AND status IN ('active', 'draft') ORDER BY id DESC LIMIT 1",
            (week_start,),
        )
    return None


def _build_workout_payload(session: dict[str, Any]) -> dict[str, Any]:
    """Construit le payload d'un workout pour l'export Garmin."""
    # Si un workout_payload_json est déjà défini, l'utiliser
    if session.get("workout_payload_json"):
        return json.loads(session["workout_payload_json"])

    # Sinon, construire un payload minimal
    return {
        "workoutName": f"{session['activity_type']} - {session['planned_date']}",
        "sportType": _map_activity_type_to_sport(session["activity_type"]),
        "estimatedDurationInSecs": session["duration_min"] * 60,
        "steps": [
            {
                "type": "WorkoutStep",
                "stepOrder": 1,
                "intensity": session.get("intensity", "ACTIVE"),
                "durationType": "TIME",
                "durationValue": session["duration_min"] * 60 * 1000,
            }
        ],
    }


def _map_activity_type_to_sport(activity_type: str) -> dict[str, Any]:
    """Mappe un type d'activité vers le format Garmin sportType."""
    mapping: dict[str, dict[str, Any]] = {
        "run": {"sportTypeId": 1, "sportTypeKey": "running"},
        "running": {"sportTypeId": 1, "sportTypeKey": "running"},
        "cycling": {"sportTypeId": 2, "sportTypeKey": "cycling"},
        "bike": {"sportTypeId": 2, "sportTypeKey": "cycling"},
        "swimming": {"sportTypeId": 5, "sportTypeKey": "swimming"},
        "swim": {"sportTypeId": 5, "sportTypeKey": "swimming"},
        "strength": {"sportTypeId": 4, "sportTypeKey": "strength_training"},
        "yoga": {"sportTypeId": 28, "sportTypeKey": "yoga"},
        "hiking": {"sportTypeId": 3, "sportTypeKey": "hiking"},
    }
    return mapping.get(activity_type.lower(), {"sportTypeId": 1, "sportTypeKey": "running"})


def _push_to_garmin(client: Any, payload: dict[str, Any], session: dict[str, Any]) -> str | None:
    """Pousse un workout vers Garmin et retourne l'event_id.

    Note: Utilise l'API de scheduling de Garmin pour associer le workout à une date.
    """
    try:
        # Créer le workout
        response = client.add_workout(payload)
        workout_id = response.get("workoutId") if isinstance(response, dict) else None

        if workout_id:
            # Scheduler le workout à la date prévue
            client.schedule_workout(workout_id, session["planned_date"])
            return str(workout_id)
    except Exception:
        # Fallback: essayer directement
        pass
    return None
