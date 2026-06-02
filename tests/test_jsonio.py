"""Tests pour garmin_coach.jsonio."""

from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

from garmin_coach.jsonio import (
    error_response,
    output,
    partial_response,
    success_response,
)


def test_success_response_minimal() -> None:
    resp = success_response()
    assert resp["status"] == "success"
    assert resp["warnings"] == []
    assert resp["errors"] == []


def test_success_response_with_data() -> None:
    resp = success_response({"plan_id": 42, "plan_status": "active"})
    assert resp["status"] == "success"
    assert resp["plan_id"] == 42
    assert resp["plan_status"] == "active"


def test_success_response_with_warnings() -> None:
    resp = success_response(warnings=["Something happened"])
    assert resp["warnings"] == ["Something happened"]


def test_partial_response() -> None:
    resp = partial_response(
        data={"count": 5},
        warnings=["Partial data"],
        errors=["One import failed"],
    )
    assert resp["status"] == "partial"
    assert resp["count"] == 5
    assert resp["warnings"] == ["Partial data"]
    assert resp["errors"] == ["One import failed"]


def test_partial_response_defaults() -> None:
    resp = partial_response()
    assert resp["status"] == "partial"
    assert resp["warnings"] == []
    assert resp["errors"] == []


def test_error_response() -> None:
    resp = error_response(["Something went wrong"])
    assert resp["status"] == "failed"
    assert resp["errors"] == ["Something went wrong"]
    assert resp["warnings"] == []


def test_error_response_with_warnings() -> None:
    resp = error_response(["Error"], warnings=["Warning"])
    assert resp["warnings"] == ["Warning"]


def test_output() -> None:
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        output({"status": "success", "data": 1})
    printed = mock_stdout.getvalue()
    parsed = json.loads(printed)
    assert parsed["status"] == "success"
    assert parsed["data"] == 1
