"""Script de marquage d'un débrief déjà sollicité."""

from __future__ import annotations

import argparse

from garmin_coach.debriefs.status import mark_activity_debrief_prompted
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Marque un ou plusieurs débriefs activité comme promptés")
    parser.add_argument(
        "--activity-id",
        type=int,
        action="append",
        required=True,
        help="Identifiant local d'activité. Répéter l'option pour plusieurs activités.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Simule sans écrire")
    args = parser.parse_args()

    result = mark_activity_debrief_prompted(
        activity_ids=args.activity_id,
        dry_run=args.dry_run,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
