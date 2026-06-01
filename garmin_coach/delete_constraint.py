"""Script de suppression d'une contrainte.

Usage:
    python -m garmin_coach.delete_constraint --constraint-id 12
"""

from __future__ import annotations

import argparse

from garmin_coach.constraints.write import delete_constraint
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Suppression d'une contrainte")
    parser.add_argument("--constraint-id", type=int, required=True, help="Identifiant de contrainte")
    parser.add_argument("--dry-run", action="store_true", help="Simule sans écrire")
    args = parser.parse_args()

    result = delete_constraint(
        constraint_id=args.constraint_id,
        dry_run=args.dry_run,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
