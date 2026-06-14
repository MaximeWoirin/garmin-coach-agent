"""Script de lecture des contraintes actives avec signaux de ménage."""

from __future__ import annotations

import argparse
from datetime import date

from garmin_coach.constraints.cleanup import get_constraint_cleanup
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Liste les contraintes actives et détecte celles à nettoyer / reconfirmer"
    )
    parser.add_argument("--scope", help="Filtre sur le périmètre")
    parser.add_argument("--status", default="active", help="Filtre sur le statut")
    parser.add_argument("--limit", type=int, help="Nombre max de contraintes")
    parser.add_argument(
        "--as-of",
        type=date.fromisoformat,
        help="Date de référence ISO (YYYY-MM-DD) pour évaluer l'expiration / l'ancienneté",
    )
    parser.add_argument(
        "--stale-after-days",
        type=int,
        default=21,
        help="Âge à partir duquel une contrainte temporaire ouverte mérite une reconfirmation",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.8,
        help="Seuil en dessous duquel une contrainte est considérée à faible confiance",
    )
    args = parser.parse_args()

    result = get_constraint_cleanup(
        scope=args.scope,
        status=args.status,
        limit=args.limit,
        as_of=args.as_of,
        stale_after_days=args.stale_after_days,
        confidence_threshold=args.confidence_threshold,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
