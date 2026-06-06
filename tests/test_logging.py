"""Tests pour garmin_coach.logging."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch

from garmin_coach.logging import ConsoleFormatter, JSONFormatter, get_logger, setup_logging


def test_json_formatter() -> None:
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message with %s",
        args=("arg1",),
        exc_info=None,
    )
    # Champ extra
    record.__dict__["custom_key"] = "custom_val"

    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["level"] == "INFO"
    assert data["message"] == "Test message with arg1"
    assert data["logger"] == "test_logger"
    assert data["custom_key"] == "custom_val"
    assert "timestamp" in data


def test_json_formatter_exception() -> None:
    formatter = JSONFormatter()
    try:
        raise ValueError("Oops")
    except ValueError:
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=10,
        msg="Error occurred",
        args=(),
        exc_info=exc_info,
    )

    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["level"] == "ERROR"
    assert "exception" in data
    assert "ValueError: Oops" in data["exception"]


def test_console_formatter() -> None:
    formatter = ConsoleFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Hello %s",
        args=("world",),
        exc_info=None,
    )
    record.__dict__["extra_field"] = "foo"

    formatted = formatter.format(record)
    assert "INFO" in formatted
    assert "test_logger" in formatted
    assert "Hello world" in formatted
    assert "extra_field" in formatted
    assert "foo" in formatted


def test_get_logger() -> None:
    logger1 = get_logger("db")
    assert logger1.name == "garmin_coach.db"

    logger2 = get_logger("garmin_coach.sync")
    assert logger2.name == "garmin_coach.sync"


def test_setup_logging_defaults(tmp_path: Path) -> None:
    # Reset logger
    logger = logging.getLogger("garmin_coach")
    logger.handlers = []

    log_file = tmp_path / "logs" / "test.log"

    with patch.dict(
        os.environ,
        {
            "GARMIN_COACH_LOG_LEVEL": "DEBUG",
            "GARMIN_COACH_LOG_FORMAT": "json",
            "GARMIN_COACH_LOG_STDERR": "1",
            "GARMIN_COACH_LOG_FILE": str(log_file),
        },
    ):
        setup_logging()

        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 2

        # Test file output
        logger.info("Test file message", extra={"metric": 42})

        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        data = json.loads(content.strip())
        assert data["message"] == "Test file message"
        assert data["metric"] == 42


def test_setup_logging_console_format(tmp_path: Path) -> None:
    # Reset logger
    logger = logging.getLogger("garmin_coach")
    logger.handlers = []

    log_file = tmp_path / "logs" / "test.log"

    with patch.dict(
        os.environ,
        {
            "GARMIN_COACH_LOG_FORMAT": "console",
            "GARMIN_COACH_LOG_STDERR": "1",
            "GARMIN_COACH_LOG_FILE": str(log_file),
        },
    ):
        setup_logging()

        # Ce handler stderr doit utiliser ConsoleFormatter
        stderr_handler = [
            h
            for h in logger.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ][0]
        assert isinstance(stderr_handler.formatter, ConsoleFormatter)
