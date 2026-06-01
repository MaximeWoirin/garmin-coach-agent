"""Script de création d'une séance dans un plan.

Usage:
    python -m garmin_coach.create_plan_session --plan-id 42 --planned-date 2026-06-03 --activity-type run --duration-min 45
"""

from __future__ import annotations

import argparse

from garmin_coach.plans.write import create_plan_session
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Création d'une séance de plan")
    parser.add_argument("--plan-id", type=int, required=True, help="Identifiant du plan parent")
    parser.add_argument("--planned-date", required=True, help="Date ISO YYYY-MM-DD")
    parser.add_argument("--planned-time", help="Heure locale optionnelle")
    parser.add_argument("--activity-type", required=True, help="Type d'activité")
    parser.add_argument("--duration-min", type=int, required=True, help="Durée cible en minutes")
    parser.add_argument("--intensity", help="Intensité cible")
    parser.add_argument("--target-hr-low", type=int, help="Borne basse FC")
    parser.add_argument("--target-hr-high", type=int, help="Borne haute FC")
    parser.add_argument("--target-pace-sec-per-km", type=int, help="Allure cible")
    parser.add_argument("--target-rpe", type=int, help="RPE cible")
    parser.add_argument("--status", default="draft", help="Statut initial")
    parser.add_argument("--tags-json", help="Tags supplémentaires JSON")
    parser.add_argument("--notes", help="Notes")
    parser.add_argument("--workout-payload-json", help="Payload exportable Garmin JSON")
    parser.add_argument("--dry-run", action="store_true", help="Simule sans écrire")
    args = parser.parse_args()

    result = create_plan_session(
        plan_id=args.plan_id,
        planned_date=args.planned_date,
        activity_type=args.activity_type,
        duration_min=args.duration_min,
        planned_time=args.planned_time,
        intensity=args.intensity,
        target_hr_low=args.target_hr_low,
        target_hr_high=args.target_hr_high,
        target_pace_sec_per_km=args.target_pace_sec_per_km,
        target_rpe=args.target_rpe,
        status=args.status,
        tags_json=args.tags_json,
        notes=args.notes,
        workout_payload_json=args.workout_payload_json,
        dry_run=args.dry_run,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
