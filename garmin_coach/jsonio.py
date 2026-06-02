"""Sortie JSON commune pour tous les scripts."""

from __future__ import annotations

import json
import sys
from typing import Any


def success_response(data: dict[str, Any] | None = None, warnings: list[str] | None = None) -> dict[str, Any]:
    """Construit une réponse de succès."""
    response: dict[str, Any] = {"status": "success"}
    if data:
        response.update(data)
    if warnings:
        response["warnings"] = warnings
    else:
        response["warnings"] = []
    response.setdefault("errors", [])
    return response


def partial_response(data: dict[str, Any] | None = None, warnings: list[str] | None = None, errors: list[str] | None = None) -> dict[str, Any]:
    """Construit une réponse partielle."""
    response: dict[str, Any] = {"status": "partial"}
    if data:
        response.update(data)
    response["warnings"] = warnings or []
    response["errors"] = errors or []
    return response


def error_response(errors: list[str], warnings: list[str] | None = None) -> dict[str, Any]:
    """Construit une réponse d'erreur."""
    return {
        "status": "failed",
        "warnings": warnings or [],
        "errors": errors,
    }


def output(response: dict[str, Any]) -> None:
    """Écrit la réponse JSON sur stdout et quitte."""
    print(json.dumps(response, ensure_ascii=False, indent=2))


def output_and_exit(response: dict[str, Any]) -> None:
    """Écrit la réponse JSON sur stdout et quitte avec le bon code."""
    output(response)
    code = 0 if response.get("status") == "success" else 1
    sys.exit(code)
