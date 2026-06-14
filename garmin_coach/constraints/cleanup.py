"""Détection des contraintes actives à nettoyer / reconfirmer."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from garmin_coach.constraints.read import get_constraints
from garmin_coach.jsonio import error_response, success_response

TEMPORARY_TYPES = {"availability", "schedule", "mental_state"}


def get_constraint_cleanup(
    scope: str | None = None,
    status: str | None = "active",
    limit: int | None = None,
    db_path: Any = None,
    *,
    as_of: date | None = None,
    stale_after_days: int = 21,
    confidence_threshold: float = 0.8,
) -> dict[str, Any]:
    """Retourne les contraintes actives enrichies de signaux de ménage.

    Les heuristiques restent volontairement simples et prudentes : on remonte surtout
    les contraintes expirées, à faible confiance, ou de nature temporaire qui semblent
    assez anciennes pour mériter une reconfirmation.
    """
    if stale_after_days < 0:
        return error_response(["stale_after_days must be >= 0."])
    if not 0 <= confidence_threshold <= 1:
        return error_response(["confidence_threshold must be between 0 and 1."])

    ref_date = as_of or datetime.now(UTC).date()
    result = get_constraints(scope=scope, status=status, limit=limit, db_path=db_path)
    if result.get("status") != "success":
        return result

    enriched_constraints: list[dict[str, Any]] = []
    cleanup_candidates: list[dict[str, Any]] = []
    reasons_count: dict[str, int] = {}

    for constraint in result.get("constraints", []):
        cleanup_reasons = _build_cleanup_reasons(
            constraint=constraint,
            as_of=ref_date,
            stale_after_days=stale_after_days,
            confidence_threshold=confidence_threshold,
        )
        enriched = dict(constraint)
        enriched["cleanup_candidate"] = bool(cleanup_reasons)
        enriched["cleanup_reasons"] = cleanup_reasons
        enriched_constraints.append(enriched)

        if cleanup_reasons:
            cleanup_candidates.append(
                {
                    "constraint_id": constraint["id"],
                    "type": constraint.get("type"),
                    "scope": constraint.get("scope"),
                    "start_date": constraint.get("start_date"),
                    "end_date": constraint.get("end_date"),
                    "confidence": constraint.get("confidence"),
                    "raw_text": constraint.get("raw_text"),
                    "reasons": cleanup_reasons,
                }
            )
            for reason in cleanup_reasons:
                code = str(reason["code"])
                reasons_count[code] = reasons_count.get(code, 0) + 1

    summary = dict(result.get("summary", {}))
    summary["cleanup_candidate_count"] = len(cleanup_candidates)
    summary["cleanup_candidates_by_reason"] = reasons_count

    return success_response(
        {
            "constraints": enriched_constraints,
            "cleanup_candidates": cleanup_candidates,
            "summary": summary,
            "heuristics": {
                "as_of": ref_date.isoformat(),
                "stale_after_days": stale_after_days,
                "confidence_threshold": confidence_threshold,
                "temporary_types": sorted(TEMPORARY_TYPES),
            },
        },
        warnings=result.get("warnings", []),
    )


def _build_cleanup_reasons(
    *,
    constraint: dict[str, Any],
    as_of: date,
    stale_after_days: int,
    confidence_threshold: float,
) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []

    end_date = _parse_date(constraint.get("end_date"))
    if end_date is not None and end_date < as_of:
        reasons.append(
            {
                "code": "expired",
                "label": "expirée",
                "details": f"end_date {end_date.isoformat()} < {as_of.isoformat()}",
            }
        )

    confidence = constraint.get("confidence")
    if isinstance(confidence, (float, int)) and float(confidence) < confidence_threshold:
        reasons.append(
            {
                "code": "low_confidence",
                "label": "confiance faible",
                "details": f"confidence {float(confidence):.2f} < {confidence_threshold:.2f}",
            }
        )

    start_date = _parse_date(constraint.get("start_date"))
    constraint_type = str(constraint.get("type") or "")
    if (
        constraint_type in TEMPORARY_TYPES
        and start_date is not None
        and end_date is None
        and (as_of - start_date).days >= stale_after_days
    ):
        reasons.append(
            {
                "code": "stale_temporary",
                "label": "temporaire ancienne à reconfirmer",
                "details": (
                    f"{constraint_type} active depuis "
                    f"{(as_of - start_date).days} jours sans end_date"
                ),
            }
        )

    return reasons


def _parse_date(raw: Any) -> date | None:
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    try:
        return date.fromisoformat(str(raw))
    except ValueError:
        return None
