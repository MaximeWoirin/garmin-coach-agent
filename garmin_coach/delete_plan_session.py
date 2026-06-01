"""Script de suppression d'une séance de plan.

Usage:
    python -m garmin_coach.delete_plan_session --plan-id 42 --session-id 7
"""

from __future__ import annotations

import argparse

from garmin_coach.plans.write import delete_plan_session
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Suppression d'une séance de plan")
    parser.add_argument("--plan-id", type=int, required=True, help="Identifiant du plan")
    parser.add_argument("--session-id", type=int, required=True, help="Identifiant de la séance")
    parser.add_argument("--dry-run", action="store_true", help="Simule sans écrire")
    args = parser.parse_args()

    result = delete_plan_session(
        plan_id=args.plan_id,
        session_id=args.session_id,
        dry_run=args.dry_run,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
