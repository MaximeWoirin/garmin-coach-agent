"""Script de changement du statut d'une séance de plan.

Usage:
    python -m garmin_coach.set_plan_session_status --plan-id 42 --session-id 7 --status exported
"""

from __future__ import annotations

import argparse

from garmin_coach.plans.status import set_plan_session_status
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Changement de statut d'une séance")
    parser.add_argument("--plan-id", type=int, required=True, help="Identifiant du plan")
    parser.add_argument("--session-id", type=int, required=True, help="Identifiant de la séance")
    parser.add_argument("--status", required=True, help="Nouveau statut")
    parser.add_argument("--dry-run", action="store_true", help="Simule sans écrire")
    args = parser.parse_args()

    result = set_plan_session_status(
        plan_id=args.plan_id,
        session_id=args.session_id,
        status=args.status,
        dry_run=args.dry_run,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
