"""Script d'export d'un plan vers Garmin.

Usage:
    python -m garmin_coach.export_plan_garmin --plan-id 42
"""

from __future__ import annotations

import argparse

from garmin_coach.garmin.export import export_plan
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Export d'un plan vers Garmin")
    parser.add_argument("--plan-id", type=int, help="Identifiant du plan")
    parser.add_argument("--week-start", help="Semaine du plan actif")
    parser.add_argument("--dry-run", action="store_true", help="Simule l'export")
    parser.add_argument("--force", action="store_true", help="Réécrit même si déjà exporté")
    args = parser.parse_args()

    if not args.plan_id and not args.week_start:
        parser.error("--plan-id ou --week-start requis")

    result = export_plan(
        plan_id=args.plan_id,
        week_start=args.week_start,
        dry_run=args.dry_run,
        force=args.force,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
