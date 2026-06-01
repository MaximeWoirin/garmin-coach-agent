"""Script d'authentification Garmin.

Usage:
    python -m garmin_coach.auth_garmin [--tokens-dir DIR] [--email EMAIL] [--password PWD] [--force-login]
"""

from __future__ import annotations

import argparse
import getpass

from garmin_coach.garmin.auth import authenticate
from garmin_coach.jsonio import output_and_exit


def main() -> None:
    parser = argparse.ArgumentParser(description="Authentification Garmin Connect")
    parser.add_argument("--tokens-dir", help="Répertoire de stockage des tokens")
    parser.add_argument("--email", help="Email Garmin")
    parser.add_argument("--password", help="Mot de passe Garmin")
    parser.add_argument("--force-login", action="store_true", help="Force un login complet")
    args = parser.parse_args()

    from pathlib import Path

    tokens_dir = Path(args.tokens_dir) if args.tokens_dir else None

    email = args.email
    password = args.password

    # Saisie interactive si nécessaire
    if not email and args.force_login:
        email = input("Email Garmin: ")
    if not password and args.force_login:
        password = getpass.getpass("Mot de passe Garmin: ")

    result = authenticate(
        email=email,
        password=password,
        tokens_dir=tokens_dir,
        force_login=args.force_login,
    )
    output_and_exit(result)


if __name__ == "__main__":
    main()
