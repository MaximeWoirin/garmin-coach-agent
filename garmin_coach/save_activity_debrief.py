"""Script de persistance d'un débrief post-activité."""

from __future__ import annotations

import argparse

from garmin_coach.debriefs.write import save_activity_debrief
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Enregistre un débrief post-activité")
    parser.add_argument("--activity-id", type=int, required=True, help="Identifiant local de l'activité")
    parser.add_argument("--rpe", type=int, required=True, help="RPE de 1 à 10")
    parser.add_argument("--note", help="Note libre")
    parser.add_argument("--pain-during", type=int, help="Douleur pendant la séance (0-10)")
    parser.add_argument("--pain-after", type=int, help="Douleur juste après la séance (0-10)")
    parser.add_argument(
        "--pain-next-morning", type=int, help="Douleur ressentie le lendemain matin (0-10)"
    )
    parser.add_argument("--plan-session-id", type=int, help="Séance planifiée liée, si connue")
    parser.add_argument("--source", default="user", help="Source du débrief (default: user)")
    parser.add_argument("--dry-run", action="store_true", help="Simule sans écrire")
    args = parser.parse_args()

    result = save_activity_debrief(
        activity_id=args.activity_id,
        rpe=args.rpe,
        note=args.note,
        pain_during=args.pain_during,
        pain_after=args.pain_after,
        pain_next_morning=args.pain_next_morning,
        plan_session_id=args.plan_session_id,
        source=args.source,
        dry_run=args.dry_run,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
