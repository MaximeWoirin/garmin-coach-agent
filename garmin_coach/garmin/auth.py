"""Authentification Garmin Connect."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from garminconnect import Garmin

from garmin_coach.config import get_tokens_dir
from garmin_coach.jsonio import error_response, success_response
from garmin_coach.logging import get_logger

logger = get_logger("garmin.auth")


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

    logger.debug(
        "Starting Garmin authentication",
        extra={"tokens_dir": str(tdir), "force_login": force_login},
    )

    # Si tokens existants et pas de force_login, essayer de réutiliser
    if not force_login and tdir.exists() and any(tdir.iterdir()):
        logger.debug("Existing tokens found, attempting to reuse them")
        try:
            client = Garmin()
            client.login(tokenstore=str(tdir))
            logger.debug("Successfully authenticated using existing tokens")
            return success_response(
                {"tokens_path": str(tdir)},
                warnings=["Reused existing tokens."],
            )
        except Exception:
            logger.warning(
                "Failed to reuse existing tokens, will proceed with full login",
                exc_info=True,
            )
            warnings.append("Existing tokens invalid, performing full login.")

    # Login complet
    if not email or not password:
        logger.error(
            "Authentication failed: email or password missing for initial login"
        )
        return error_response(
            ["Email and password required for initial login."],
            warnings=warnings,
        )

    logger.debug("Performing full login with email", extra={"email": email})
    try:
        client = Garmin(email=email, password=password)
        client.login(tokenstore=str(tdir))
        logger.debug("Authentication successful, tokens stored")
    except Exception as exc:
        logger.error("Garmin authentication failed", exc_info=True)
        return error_response(
            [f"Authentication failed: {exc}"],
            warnings=warnings,
        )

    return success_response({"tokens_path": str(tdir)}, warnings=warnings)
