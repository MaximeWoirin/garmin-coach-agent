"""Script de synchronisation Garmin quotidien.

Usage:
    python -m garmin_coach.sync_garmin [--start DATE] [--end DATE] [--lookback-days N]
"""

from __future__ import annotations

import argparse
from datetime import date

from garmin_coach.garmin.sync import sync
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronisation quotidienne Garmin")
    parser.add_argument("--start", help="Date de début ISO YYYY-MM-DD")
    parser.add_argument("--end", help="Date de fin ISO YYYY-MM-DD")
    parser.add_argument("--lookback-days", type=int, default=3, help="Jours de lookback")
    args = parser.parse_args()

    start_date = date.fromisoformat(args.start) if args.start else None
    end_date = date.fromisoformat(args.end) if args.end else None

    result = sync(
        start_date=start_date,
        end_date=end_date,
        lookback_days=args.lookback_days,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
