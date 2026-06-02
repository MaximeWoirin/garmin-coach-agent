"""Script de lecture des contraintes.

Usage:
    python -m garmin_coach.get_constraints [--scope training] [--status active] [--limit N]
"""

from __future__ import annotations

import argparse

from garmin_coach.constraints.read import get_constraints
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Lecture des contraintes")
    parser.add_argument("--scope", help="Filtre sur le périmètre")
    parser.add_argument("--status", default="active", help="Filtre sur le statut")
    parser.add_argument("--limit", type=int, help="Nombre max de contraintes")
    args = parser.parse_args()

    result = get_constraints(
        scope=args.scope,
        status=args.status,
        limit=args.limit,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
