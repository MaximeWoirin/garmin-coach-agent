"""Script de lecture du plan courant.

Usage:
    python -m garmin_coach.get_current_plan [--plan-id N] [--week-start DATE] [--include-sessions] [--include-metadata]
"""

from __future__ import annotations

import argparse

from garmin_coach.plans.read import get_current_plan
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Lecture du plan courant")
    parser.add_argument("--plan-id", type=int, help="Plan précis")
    parser.add_argument("--week-start", help="Plan de la semaine")
    parser.add_argument("--include-sessions", action="store_true", default=True, help="Inclut les séances")
    parser.add_argument("--include-metadata", action="store_true", help="Inclut les métadonnées")
    args = parser.parse_args()

    result = get_current_plan(
        plan_id=args.plan_id,
        week_start=args.week_start,
        include_sessions=args.include_sessions,
        include_metadata=args.include_metadata,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
