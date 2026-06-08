"""Script de lecture des activités.

Usage:
    python -m garmin_coach.get_activities --start 2026-05-01 --end 2026-05-15
"""

from __future__ import annotations

import argparse

from garmin_coach.activities.read import get_activities
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Lecture des activités")
    parser.add_argument("--start", required=True, help="Date ISO YYYY-MM-DD incluse")
    parser.add_argument("--end", required=True, help="Date ISO YYYY-MM-DD incluse")
    parser.add_argument("--limit", type=int, help="Nombre max de lignes")
    parser.add_argument("--activity-type", help="Filtre par type d'activité")
    args = parser.parse_args()

    result = get_activities(
        start=args.start,
        end=args.end,
        limit=args.limit,
        activity_type=args.activity_type,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
