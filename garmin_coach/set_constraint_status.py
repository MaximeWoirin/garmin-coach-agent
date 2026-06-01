"""Script de changement de statut d'une contrainte.

Usage:
    python -m garmin_coach.set_constraint_status --constraint-id 12 --status inactive
"""

from __future__ import annotations

import argparse

from garmin_coach.constraints.status import set_constraint_status
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Changement de statut d'une contrainte")
    parser.add_argument("--constraint-id", type=int, required=True, help="Identifiant de contrainte")
    parser.add_argument("--status", required=True, help="Nouveau statut")
    parser.add_argument("--dry-run", action="store_true", help="Simule sans écrire")
    args = parser.parse_args()

    result = set_constraint_status(
        constraint_id=args.constraint_id,
        status=args.status,
        dry_run=args.dry_run,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
