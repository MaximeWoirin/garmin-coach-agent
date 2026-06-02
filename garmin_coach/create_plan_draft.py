"""Script de création d'un plan draft.

Usage:
    python -m garmin_coach.create_plan_draft --week-start 2026-06-01 --week-end 2026-06-08
"""

from __future__ import annotations

import argparse

from garmin_coach.plans.write import create_plan_draft
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Création d'un plan draft")
    parser.add_argument("--week-start", required=True, help="Date ISO YYYY-MM-DD, début de semaine")
    parser.add_argument("--week-end", required=True, help="Date ISO YYYY-MM-DD, fin de semaine")
    parser.add_argument("--goal-id", type=int, help="Identifiant d'objectif")
    parser.add_argument("--block-id", type=int, help="Identifiant de bloc macro")
    parser.add_argument("--title", help="Titre libre du plan")
    parser.add_argument("--notes", help="Notes initiales")
    parser.add_argument("--metadata-json", help="Métadonnées supplémentaires JSON")
    parser.add_argument("--sessions-json", help="Définition initiale des séances JSON")
    parser.add_argument("--dry-run", action="store_true", help="Simule sans écrire")
    args = parser.parse_args()

    result = create_plan_draft(
        week_start=args.week_start,
        week_end=args.week_end,
        goal_id=args.goal_id,
        block_id=args.block_id,
        title=args.title,
        notes=args.notes,
        metadata_json=args.metadata_json,
        sessions_json=args.sessions_json,
        dry_run=args.dry_run,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
