"""Script de lecture des objectifs.

Usage:
    python -m garmin_coach.get_goals [--status active] [--limit N] [--include-archived]
"""

from __future__ import annotations

import argparse

from garmin_coach.plans.read import get_goals
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Lecture des objectifs")
    parser.add_argument("--status", default="active", help="Filtre sur le statut")
    parser.add_argument("--limit", type=int, help="Nombre max d'objectifs")
    parser.add_argument("--include-archived", action="store_true", help="Inclut les objectifs archivés")
    args = parser.parse_args()

    result = get_goals(
        status=args.status,
        limit=args.limit,
        include_archived=args.include_archived,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
