"""Script de création d'un objectif d'entraînement.

Usage:
    python -m garmin_coach.create_goal --primary-goal "Finir le marathon de Paris en moins de 4h"
"""

from __future__ import annotations

import argparse

from garmin_coach.plans.write import create_goal
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Création d'un objectif d'entraînement")
    parser.add_argument("--goal-code", help="Code unique de l'objectif")
    parser.add_argument("--primary-goal", required=True, help="Description de l'objectif principal")
    parser.add_argument("--priority", default="medium", help="Priorité (low, medium, high)")
    parser.add_argument("--horizon-date", help="Date horizon ISO YYYY-MM-DD")
    parser.add_argument("--target-event-name", help="Nom de l'événement cible")
    parser.add_argument("--target-event-date", help="Date de l'événement cible ISO YYYY-MM-DD")
    parser.add_argument("--target-event-priority", help="Priorité de l'événement cible")
    parser.add_argument("--status", default="active", help="Statut initial")
    parser.add_argument("--raw-text", help="Texte brut de l'utilisateur")
    parser.add_argument("--metadata-json", help="Métadonnées JSON")
    parser.add_argument("--dry-run", action="store_true", help="Simule sans écrire")
    args = parser.parse_args()

    result = create_goal(
        primary_goal=args.primary_goal,
        goal_code=args.goal_code,
        priority=args.priority,
        horizon_date=args.horizon_date,
        target_event_name=args.target_event_name,
        target_event_date=args.target_event_date,
        target_event_priority=args.target_event_priority,
        status=args.status,
        raw_text=args.raw_text,
        metadata_json=args.metadata_json,
        dry_run=args.dry_run,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
