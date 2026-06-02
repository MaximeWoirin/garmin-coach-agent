"""Script de création d'une contrainte.

Usage:
    python -m garmin_coach.create_constraint --type availability --scope training --start-date 2026-06-01 --raw-text "Pas dispo mardi soir"
"""

from __future__ import annotations

import argparse

from garmin_coach.constraints.write import create_constraint
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Création d'une contrainte")
    parser.add_argument("--goal-id", type=int, help="Objectif lié")
    parser.add_argument("--type", required=True, dest="constraint_type", help="Type de contrainte")
    parser.add_argument("--severity", default="medium", help="Sévérité")
    parser.add_argument("--scope", default="training", help="Périmètre")
    parser.add_argument("--start-date", required=True, help="Date de début ISO")
    parser.add_argument("--end-date", help="Date de fin ISO")
    parser.add_argument("--source", default="user", help="Origine")
    parser.add_argument("--confidence", type=float, default=1.0, help="Confiance")
    parser.add_argument("--raw-text", required=True, help="Texte brut")
    parser.add_argument("--tags-json", help="Tags JSON")
    parser.add_argument("--notes-json", help="Notes JSON")
    parser.add_argument("--status", default="active", help="Statut initial")
    parser.add_argument("--dry-run", action="store_true", help="Simule sans écrire")
    args = parser.parse_args()

    result = create_constraint(
        constraint_type=args.constraint_type,
        raw_text=args.raw_text,
        start_date=args.start_date,
        goal_id=args.goal_id,
        severity=args.severity,
        scope=args.scope,
        end_date=args.end_date,
        source=args.source,
        confidence=args.confidence,
        tags_json=args.tags_json,
        notes_json=args.notes_json,
        status=args.status,
        dry_run=args.dry_run,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
