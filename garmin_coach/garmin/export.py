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
from math import ceil
from datetime import date, timedelta
from typing import Any

from garmin_coach.db import db_connection, fetchall_dicts, fetchone_dict
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
    warnings: list[str] = []
    errors: list[str] = []

    with db_connection(db_path) as conn:
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
                event_id = _push_to_garmin(client, payload, session)

                if event_id:
                    conn.execute(
                        """UPDATE plan_sessions
                           SET garmin_event_id=?, status=?, workout_payload_json=?, updated_at=CURRENT_TIMESTAMP
                           WHERE id=?""",
                        (event_id, SessionStatus.EXPORTED, json.dumps(payload), session["id"]),
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


def _find_plan(
    conn: sqlite3.Connection,
    plan_id: int | None,
    week_start: str | None,
) -> dict[str, Any] | None:
    """Trouve le plan par id ou par semaine."""
    if plan_id:
        return fetchone_dict(conn, "SELECT * FROM training_plans WHERE id=?", (plan_id,))
    if week_start:
        return fetchone_dict(
            conn,
            (
                "SELECT * FROM training_plans "
                "WHERE week_start=? AND status IN ('active', 'draft') "
                "ORDER BY id DESC LIMIT 1"
            ),
            (week_start,),
        )
    return None


def _build_workout_payload(session: dict[str, Any]) -> dict[str, Any]:
    """Construit le payload d'un workout pour l'export Garmin."""
    # Si un workout_payload_json est déjà défini, l'utiliser
    if session.get("workout_payload_json"):
        return json.loads(session["workout_payload_json"])  # type: ignore[no-any-return]

    if session.get("session_payload_json"):
        session_payload = json.loads(session["session_payload_json"])
        if isinstance(session_payload, dict):
            return _build_workout_payload_from_session_payload(session, session_payload)

    # Sinon, construire un payload minimal
    sport_type = _map_activity_type_to_sport(session["activity_type"])
    return {
        "workoutName": f"{session['activity_type']} - {session['planned_date']}",
        "sportType": sport_type,
        "estimatedDurationInSecs": session["duration_min"] * 60,
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": sport_type,
                "workoutSteps": [
                    {
                        "type": "ExecutableStepDTO",
                        "stepOrder": 1,
                        "stepType": {
                            "stepTypeId": 3,
                            "stepTypeKey": "interval",
                        },
                        "intensity": session.get("intensity", "ACTIVE").upper(),
                        "endCondition": {
                            "conditionTypeId": 2,
                            "conditionTypeKey": "time",
                        },
                        "endConditionValue": session["duration_min"] * 60,
                    }
                ],
            }
        ],
    }


def _build_workout_payload_from_session_payload(
    session: dict[str, Any],
    session_payload: dict[str, Any],
) -> dict[str, Any]:
    """Projette le JSON canonique d'une séance vers un payload workout Garmin."""
    sport = str(session_payload.get("sport") or session.get("activity_type") or "running")
    format_kind = session_payload.get("format")

    if sport not in {"running", "trail", "treadmill"} or format_kind != "structured":
        return _build_simple_payload_from_session_payload(session, session_payload)

    sport_type = _map_activity_type_to_sport(sport)
    items = session_payload.get("items") or []
    if not isinstance(items, list) or not items:
        raise ValueError("session_payload_json structured workout must contain a non-empty items array.")

    workout_name = (
        session_payload.get("title")
        or session_payload.get("description")
        or f"{session['activity_type']} - {session['planned_date']}"
    )
    description = _choose_workout_description(session_payload, session)

    payload = {
        "workoutName": workout_name,
        "sportType": sport_type,
        "estimatedDurationInSecs": _estimate_duration_seconds(session_payload, session),
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": sport_type,
                "workoutSteps": _build_workout_steps(items),
            }
        ],
    }
    if description:
        payload["description"] = description
    return payload


def _build_simple_payload_from_session_payload(
    session: dict[str, Any],
    session_payload: dict[str, Any],
) -> dict[str, Any]:
    """Construit un payload minimal en conservant le texte utile du JSON canonique."""
    sport_type = _map_activity_type_to_sport(session["activity_type"])
    workout_name = (
        session_payload.get("title")
        or session_payload.get("description")
        or f"{session['activity_type']} - {session['planned_date']}"
    )
    description = _choose_workout_description(session_payload, session)

    payload = {
        "workoutName": workout_name,
        "sportType": sport_type,
        "estimatedDurationInSecs": _estimate_duration_seconds(session_payload, session),
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": sport_type,
                "workoutSteps": [
                    {
                        "type": "ExecutableStepDTO",
                        "stepOrder": 1,
                        "stepType": _step_type_meta("interval"),
                        "description": description,
                        "endCondition": _end_condition_meta("time"),
                        "endConditionValue": int(session["duration_min"]) * 60,
                        "targetType": _no_target_meta(),
                    }
                ],
            }
        ],
    }
    if description:
        payload["description"] = description
    return payload


def _build_workout_steps(items: list[Any]) -> list[dict[str, Any]]:
    """Construit récursivement les étapes Garmin d'un workout."""
    result: list[dict[str, Any]] = []
    for order, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError("Each session payload item must be an object.")

        kind = item.get("kind")
        if kind == "step":
            result.append(_build_step(item, order))
        elif kind == "repeat":
            result.append(_build_repeat(item, order))
        else:
            raise ValueError(f"Unsupported session payload item kind: {kind!r}")
    return result


def _build_step(item: dict[str, Any], step_order: int) -> dict[str, Any]:
    """Construit une étape Garmin simple."""
    end_condition = item.get("endCondition")
    if not isinstance(end_condition, dict):
        raise ValueError("Structured step requires an endCondition object.")

    payload: dict[str, Any] = {
        "type": "ExecutableStepDTO",
        "stepOrder": step_order,
        "stepType": _step_type_meta(str(item.get("stepType") or "interval")),
        "endCondition": _end_condition_meta(str(end_condition.get("type") or "time")),
        "targetType": _target_meta(item.get("target")),
    }

    end_condition_value = _end_condition_value(end_condition)
    if end_condition_value is not None:
        payload["endConditionValue"] = end_condition_value

    payload.update(_target_extra_fields(item.get("target")))

    if item.get("comment"):
        payload["description"] = item["comment"]

    return payload


def _build_repeat(item: dict[str, Any], step_order: int) -> dict[str, Any]:
    """Construit un RepeatGroupDTO Garmin."""
    repeat_count = item.get("repeatCount")
    if not isinstance(repeat_count, int) or repeat_count <= 0:
        raise ValueError("Repeat item requires a positive integer repeatCount.")

    children = item.get("items")
    if not isinstance(children, list) or not children:
        raise ValueError("Repeat item requires a non-empty items array.")

    return {
        "type": "RepeatGroupDTO",
        "stepOrder": step_order,
        "stepType": _step_type_meta("repeat"),
        "numberOfIterations": repeat_count,
        "endCondition": _end_condition_meta("iterations"),
        "endConditionValue": float(repeat_count),
        "workoutSteps": _build_workout_steps(children),
    }


def _step_type_meta(step_type: str) -> dict[str, Any]:
    """Retourne les métadonnées Garmin d'un type d'étape."""
    normalized = step_type.strip().lower().replace("-", "_").replace(" ", "_")
    mapping: dict[str, tuple[int, str]] = {
        "warmup": (1, "warmup"),
        "cooldown": (2, "cooldown"),
        "interval": (3, "interval"),
        "run": (3, "interval"),
        "recovery": (4, "recovery"),
        "rest": (5, "rest"),
        "repeat": (6, "repeat"),
    }
    step_type_id, step_type_key = mapping.get(normalized, (3, "interval"))
    return {"stepTypeId": step_type_id, "stepTypeKey": step_type_key}


def _end_condition_meta(end_condition_type: str) -> dict[str, Any]:
    """Retourne les métadonnées Garmin d'une condition de fin."""
    normalized = end_condition_type.strip().lower().replace("-", "_").replace(" ", "_")
    mapping: dict[str, tuple[int, str]] = {
        "lap_button": (1, "lap.button"),
        "time": (2, "time"),
        "distance": (3, "distance"),
        "iterations": (7, "iterations"),
    }
    if normalized not in mapping:
        raise ValueError(f"Unsupported end condition type: {end_condition_type!r}")
    condition_id, condition_key = mapping[normalized]
    return {"conditionTypeId": condition_id, "conditionTypeKey": condition_key}


def _end_condition_value(end_condition: dict[str, Any]) -> float | None:
    """Retourne la valeur numérique d'une condition de fin, si applicable."""
    condition_type = str(end_condition.get("type") or "time").strip().lower().replace("-", "_")
    if condition_type == "time":
        value = end_condition.get("valueSec")
    elif condition_type == "distance":
        value = end_condition.get("valueMeters")
    elif condition_type == "lap_button":
        return None
    else:
        raise ValueError(f"Unsupported end condition type: {condition_type!r}")

    if value is None:
        raise ValueError(f"End condition {condition_type!r} requires a numeric value.")
    return float(value)


def _target_meta(target: Any) -> dict[str, Any]:
    """Retourne les métadonnées Garmin de target."""
    if not isinstance(target, dict):
        return _no_target_meta()

    target_type = str(target.get("type") or "").strip().lower().replace("-", "_")
    if target_type == "heart_rate_zone":
        return {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"}
    if target_type == "pace":
        return {"workoutTargetTypeId": 6, "workoutTargetTypeKey": "pace.zone"}
    raise ValueError(f"Unsupported target type: {target.get('type')!r}")


def _target_extra_fields(target: Any) -> dict[str, Any]:
    """Construit les champs Garmin additionnels liés à la target."""
    if not isinstance(target, dict):
        return {}

    target_type = str(target.get("type") or "").strip().lower().replace("-", "_")
    if target_type == "heart_rate_zone":
        zone = target.get("zone")
        if not isinstance(zone, int) or zone < 1 or zone > 5:
            raise ValueError("heart_rate_zone target requires zone between 1 and 5.")
        return {"zoneNumber": zone}

    if target_type == "pace":
        value_sec_per_km = target.get("valueSecPerKm")
        if not isinstance(value_sec_per_km, int | float) or value_sec_per_km <= 0:
            raise ValueError("pace target requires positive valueSecPerKm.")
        meters_per_second = 1000.0 / float(value_sec_per_km)
        return {"targetValueOne": meters_per_second, "targetValueTwo": meters_per_second}

    raise ValueError(f"Unsupported target type: {target.get('type')!r}")


def _no_target_meta() -> dict[str, Any]:
    """Retourne la target Garmin sans consigne."""
    return {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}


def _estimate_duration_seconds(session_payload: dict[str, Any], session: dict[str, Any]) -> int:
    """Estime la durée totale en secondes, avec fallback sur duration_min."""
    estimated = _sum_time_seconds(session_payload.get("items"))
    if estimated > 0:
        return estimated
    return int(session["duration_min"]) * 60


def _sum_time_seconds(items: Any) -> int:
    """Somme les durées estimables présentes dans les steps."""
    if not isinstance(items, list):
        return 0

    total = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        if kind == "step":
            total += _estimate_step_seconds(item)
        elif kind == "repeat":
            repeat_count = item.get("repeatCount")
            if isinstance(repeat_count, int) and repeat_count > 0:
                total += repeat_count * _sum_time_seconds(item.get("items"))
    return total


def _estimate_step_seconds(item: dict[str, Any]) -> int:
    """Estime la durée d'un step à partir de son endCondition et de sa target."""
    end_condition = item.get("endCondition")
    if not isinstance(end_condition, dict):
        return 0

    condition_type = str(end_condition.get("type") or "").strip().lower().replace("-", "_")
    if condition_type == "time":
        value = end_condition.get("valueSec")
        if isinstance(value, int | float) and value > 0:
            return int(value)
        return 0

    if condition_type != "distance":
        return 0

    distance_m = end_condition.get("valueMeters")
    if not isinstance(distance_m, int | float) or distance_m <= 0:
        return 0

    target = item.get("target")
    if not isinstance(target, dict):
        return 0

    target_type = str(target.get("type") or "").strip().lower().replace("-", "_")
    if target_type != "pace":
        return 0

    value_sec_per_km = target.get("valueSecPerKm")
    if not isinstance(value_sec_per_km, int | float) or value_sec_per_km <= 0:
        return 0

    seconds = float(distance_m) * float(value_sec_per_km) / 1000.0
    return ceil(seconds)


def _choose_workout_description(
    session_payload: dict[str, Any],
    session: dict[str, Any],
) -> str | None:
    """Retourne une description top-level courte et propre."""
    for candidate in (
        session_payload.get("description"),
        session_payload.get("notes"),
        session.get("notes"),
    ):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def _map_activity_type_to_sport(activity_type: str) -> dict[str, Any]:
    """Mappe un type d'activité local vers le `sportType` du workout-service Garmin.

    Important:
    - ce mapping n'utilise pas les ids de `activity-service/activityTypes`
    - il utilise les ids réellement observés via création de workouts Garmin Connect
    - plusieurs sports locaux retombent volontairement sur un fallback Garmin plus pauvre
      quand le workout-service n'expose pas de type dédié exploitable

    Référence: `docs/spec/garmin-workout-sport-mapping.md`.
    """
    normalized = activity_type.strip().lower().replace("-", " ").replace("_", " ")

    running = {"sportTypeId": 1, "sportTypeKey": "running"}
    cycling = {"sportTypeId": 2, "sportTypeKey": "cycling"}
    other = {"sportTypeId": 3, "sportTypeKey": "other"}
    swimming = {"sportTypeId": 4, "sportTypeKey": "swimming"}
    strength = {"sportTypeId": 5, "sportTypeKey": "strength_training"}
    cardio = {"sportTypeId": 6, "sportTypeKey": "cardio_training"}
    yoga = {"sportTypeId": 7, "sportTypeKey": "yoga"}
    pilates = {"sportTypeId": 8, "sportTypeKey": "pilates"}
    hiit = {"sportTypeId": 9, "sportTypeKey": "hiit"}
    mobility = {"sportTypeId": 11, "sportTypeKey": "mobility"}
    walking = {"sportTypeId": 12, "sportTypeKey": "walking"}
    rucking = {"sportTypeId": 13, "sportTypeKey": "rucking"}

    mapping: dict[str, dict[str, Any]] = {
        "run": running,
        "running": running,
        "trail": running,
        "trail running": running,
        "treadmill": running,
        "virtual run": running,
        "cycling": cycling,
        "bike": cycling,
        "biking": cycling,
        "indoor cycling": cycling,
        "spinning": cycling,
        "swimming": swimming,
        "swim": swimming,
        "pool swim": swimming,
        "lap swimming": swimming,
        "open water swim": swimming,
        "strength": strength,
        "strength training": strength,
        "cardio": cardio,
        "cardio workout": cardio,
        "fitness": cardio,
        "yoga": yoga,
        "pilates": pilates,
        "hiit": hiit,
        "walking": walking,
        "walk": walking,
        "hiking": walking,
        "hike": walking,
        "rucking": rucking,
        "mobility": mobility,
        "climbing": other,
        "rock climbing": other,
        "indoor climbing": other,
    }
    return mapping.get(normalized, other)


def _push_to_garmin(client: Any, payload: dict[str, Any], session: dict[str, Any]) -> str | None:
    """Pousse un workout vers Garmin et retourne l'event_id.

    Note: Utilise l'API de scheduling de Garmin pour associer le workout à une date.
    """
    # Créer le workout
    response = client.upload_workout(payload)
    workout_id = response.get("workoutId") if isinstance(response, dict) else None

    if not workout_id:
        raise ValueError("Garmin returned no workoutId in response.")

    # Scheduler le workout à la date prévue
    client.schedule_workout(workout_id, session["planned_date"])
    return str(workout_id)
