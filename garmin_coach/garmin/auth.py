"""Authentification Garmin Connect."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from garminconnect import Garmin

from garmin_coach.config import get_tokens_dir
from garmin_coach.jsonio import error_response, success_response


def authenticate(
    email: str | None = None,
    password: str | None = None,
    tokens_dir: Path | None = None,
    force_login: bool = False,
) -> dict[str, Any]:
    """Réalise l'authentification Garmin et stocke les tokens.

    Args:
        email: Email Garmin (interactif si None).
        password: Mot de passe Garmin (interactif si None).
        tokens_dir: Répertoire de stockage des tokens.
        force_login: Force un login complet même si des tokens existent.

    Returns:
        Réponse JSON avec le statut d'authentification.
    """
    tdir = tokens_dir or get_tokens_dir()
    tdir.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []

    # Si tokens existants et pas de force_login, essayer de réutiliser
    if not force_login and tdir.exists() and any(tdir.iterdir()):
        try:
            client = Garmin()
            client.login(tokenstore=str(tdir))
            client.garth.dump(str(tdir))
            return success_response(
                {"tokens_path": str(tdir)},
                warnings=["Reused existing tokens."],
            )
        except Exception:
            warnings.append("Existing tokens invalid, performing full login.")

    # Login complet
    if not email or not password:
        return error_response(
            ["Email and password required for initial login."],
            warnings=warnings,
        )

    try:
        client = Garmin(email=email, password=password)
        client.login(tokenstore=str(tdir))
        client.garth.dump(str(tdir))
    except Exception as exc:
        return error_response(
            [f"Authentication failed: {exc}"],
            warnings=warnings,
        )

    return success_response({"tokens_path": str(tdir)}, warnings=warnings)
