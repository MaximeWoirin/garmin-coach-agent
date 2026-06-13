"""Script de lecture des activités éligibles à un débrief."""

from __future__ import annotations

import argparse

from garmin_coach.debriefs.read import get_pending_debriefs
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Liste les activités récentes sans débrief complété")
    parser.add_argument("--lookback-hours", type=int, default=36, help="Fenêtre de recherche")
    parser.add_argument(
        "--min-age-minutes",
        type=int,
        default=0,
        help="Âge minimum avant de proposer un débrief",
    )
    parser.add_argument(
        "--reprompt-after-hours",
        type=int,
        default=12,
        help="Cooldown avant une nouvelle relance",
    )
    parser.add_argument(
        "--max-prompt-count",
        type=int,
        default=2,
        help="Nombre max de relances possibles",
    )
    parser.add_argument("--limit", type=int, default=20, help="Nombre max de résultats")
    args = parser.parse_args()

    result = get_pending_debriefs(
        lookback_hours=args.lookback_hours,
        min_age_minutes=args.min_age_minutes,
        reprompt_after_hours=args.reprompt_after_hours,
        max_prompt_count=args.max_prompt_count,
        limit=args.limit,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
