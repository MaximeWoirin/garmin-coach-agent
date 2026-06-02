"""Client Garmin Connect — création et gestion du client."""

from __future__ import annotations

from pathlib import Path

from garminconnect import Garmin

from garmin_coach.config import get_tokens_dir


def get_client(tokens_dir: Path | None = None) -> Garmin:
    """Crée un client Garmin Connect à partir des tokens existants.

    Raises:
        FileNotFoundError: Si aucun token n'est trouvé.
    """
    tdir = tokens_dir or get_tokens_dir()
    if not tdir.exists():
        raise FileNotFoundError(
            f"Tokens directory not found: {tdir}. Run auth-garmin first."
        )

    client = Garmin()
    client.login(tokenstore=str(tdir))
    return client
