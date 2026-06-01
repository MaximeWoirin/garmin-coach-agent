"""Script de lecture de l'état de forme.

Usage:
    python -m garmin_coach.get_fitness_state --start 2026-05-01 --end 2026-05-15
"""

from __future__ import annotations

import argparse

from garmin_coach.metrics.read import get_fitness_state
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Lecture de l'état de forme")
    parser.add_argument("--start", required=True, help="Date ISO YYYY-MM-DD incluse")
    parser.add_argument("--end", required=True, help="Date ISO YYYY-MM-DD exclue")
    parser.add_argument("--limit", type=int, help="Nombre max de jours")
    args = parser.parse_args()

    result = get_fitness_state(
        start=args.start,
        end=args.end,
        limit=args.limit,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
