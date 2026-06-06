"""Module de logging structuré pour garmin-coach-agent."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Formatter qui produit des lignes de log au format JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            log_data["stack_info"] = self.formatStack(record.stack_info)

        # Extraire les champs additionnels passés via `extra`
        standard_attrs = {
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
        }
        extra = {k: v for k, v in record.__dict__.items() if k not in standard_attrs}
        if extra:
            log_data.update(extra)

        return json.dumps(log_data, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Formatter lisible par l'homme pour la console."""

    def format(self, record: logging.LogRecord) -> str:
        dt = datetime.fromtimestamp(record.created, tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{dt}] {record.levelname:<8} {record.name}: {record.getMessage()}"

        # Extraire les champs additionnels passés via `extra`
        standard_attrs = {
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
        }
        extra = {k: v for k, v in record.__dict__.items() if k not in standard_attrs}
        if extra:
            msg += f" | extra={extra}"

        if record.exc_info:
            msg += f"\n{self.formatException(record.exc_info)}"
        if record.stack_info:
            msg += f"\n{self.formatStack(record.stack_info)}"
        return msg


def setup_logging() -> None:
    """Configure le système de logging de garmin-coach-agent."""
    # Niveau de log configurable par variable d'environnement (défaut: INFO)
    level_name = os.environ.get("GARMIN_COACH_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    # Configurer le logger spécifique au projet
    logger = logging.getLogger("garmin_coach")
    logger.setLevel(level)

    # Éviter de dupliquer les handlers si setup_logging est appelé plusieurs fois
    if logger.handlers:
        return

    # Empêcher la propagation au logger racine pour ne pas polluer stdout/stderr
    # avec d'autres formats
    logger.propagate = False

    # Format pour la console / stderr
    log_format = os.environ.get("GARMIN_COACH_LOG_FORMAT", "json").lower()
    if log_format == "console":
        stderr_formatter: logging.Formatter = ConsoleFormatter()
    else:
        stderr_formatter = JSONFormatter()

    # Configuration du handler stderr (actif par défaut)
    log_to_stderr = os.environ.get("GARMIN_COACH_LOG_STDERR", "1") == "1"
    if log_to_stderr:
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(stderr_formatter)
        logger.addHandler(stderr_handler)

    # Configuration du handler fichier
    # Par défaut, on logue dans logs/garmin_coach.log sous le répertoire de la DB
    log_file_env = os.environ.get("GARMIN_COACH_LOG_FILE")
    if log_file_env:
        log_file: Path | None = Path(log_file_env)
    else:
        from garmin_coach.config import get_db_path

        log_file = get_db_path().parent / "logs" / "garmin_coach.log"

    if log_file:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            # Le fichier est TOUJOURS au format JSON structuré pour traitement automatisé
            file_handler.setFormatter(JSONFormatter())
            logger.addHandler(file_handler)
        except Exception as e:
            sys.stderr.write(f"Warning: could not configure file logging at {log_file}: {e}\n")


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger configuré pour un module donné de l'application."""
    if not name.startswith("garmin_coach"):
        logger_name = f"garmin_coach.{name}"
    else:
        logger_name = name
    return logging.getLogger(logger_name)
