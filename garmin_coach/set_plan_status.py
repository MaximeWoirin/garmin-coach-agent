"""Script de changement du statut d'un plan.

Usage:
    python -m garmin_coach.set_plan_status --plan-id 42 --status active
"""

from __future__ import annotations

import argparse

from garmin_coach.plans.status import set_plan_status
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Changement de statut d'un plan")
    parser.add_argument("--plan-id", type=int, required=True, help="Identifiant du plan")
    parser.add_argument("--status", required=True, help="Nouveau statut")
    parser.add_argument("--cascade-sessions", action="store_true", help="Cascade aux séances")
    parser.add_argument("--dry-run", action="store_true", help="Simule sans écrire")
    args = parser.parse_args()

    result = set_plan_status(
        plan_id=args.plan_id,
        status=args.status,
        cascade_sessions=args.cascade_sessions,
        dry_run=args.dry_run,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
