"""Script d'export d'un plan vers Garmin.

Usage:
    python -m garmin_coach.export_plan_garmin --plan-id 42
    python -m garmin_coach.export_plan_garmin --plan-id 42 --days-ahead 2
    python -m garmin_coach.export_plan_garmin --plan-id 42 --start-date 2026-06-03 --end-date 2026-06-05
"""

from __future__ import annotations

import argparse

from garmin_coach.garmin.export import export_plan
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Export progressif d'un plan vers Garmin")
    parser.add_argument("--plan-id", type=int, help="Identifiant du plan")
    parser.add_argument("--week-start", help="Semaine du plan actif")
    parser.add_argument("--start-date", help="Date de début de l'horizon d'export (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Date de fin de l'horizon d'export (YYYY-MM-DD)")
    parser.add_argument("--days-ahead", type=int, help="Nombre de jours à exporter à partir d'aujourd'hui")
    parser.add_argument("--dry-run", action="store_true", help="Simule l'export")
    parser.add_argument("--force", action="store_true", help="Réécrit même si déjà exporté")
    args = parser.parse_args()

    if not args.plan_id and not args.week_start:
        parser.error("--plan-id ou --week-start requis")

    result = export_plan(
        plan_id=args.plan_id,
        week_start=args.week_start,
        start_date=args.start_date,
        end_date=args.end_date,
        days_ahead=args.days_ahead,
        dry_run=args.dry_run,
        force=args.force,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
