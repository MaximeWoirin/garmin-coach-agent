from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_DIR / "scripts" / "install-openclaw-agent.sh"


def _write_openclaw_config(path: Path, workspace: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "agents": {
                    "defaults": {"workspace": str(workspace.parent)},
                    "list": [
                        {
                            "id": "coach",
                            "name": "Garmin Coach",
                            "workspace": str(workspace),
                            "agentDir": str(workspace / "agent"),
                            "model": {"primary": "azure/gpt-5.4-1"},
                        }
                    ],
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _run_installer(tmp_path: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    config_path = home / ".openclaw" / "openclaw.json"
    install_root = workspace / ".garmin-coach-agent"
    home.mkdir(parents=True, exist_ok=True)
    workspace.mkdir(parents=True, exist_ok=True)
    _write_openclaw_config(config_path, workspace)

    env = os.environ.copy()
    env["HOME"] = str(home)

    cmd = [
        "bash",
        str(SCRIPT_PATH),
        "--config",
        str(config_path),
        "--agent",
        "coach",
        "--python",
        sys.executable,
        "--skip-package-install",
        "--skip-systemd-sync",
        "--skip-systemd-export",
        "--skip-weekly-planning-cron",
        *extra_args,
    ]
    result = subprocess.run(
        cmd,
        cwd=REPO_DIR,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    result.install_root = install_root  # type: ignore[attr-defined]
    result.workspace = workspace  # type: ignore[attr-defined]
    return result


def test_install_script_rejects_new_agent_option(tmp_path: Path) -> None:
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "--new-agent", "foo"],
        cwd=REPO_DIR,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "no longer supported" in result.stderr


def test_install_script_writes_json_manifest_and_config(tmp_path: Path) -> None:
    result = _run_installer(tmp_path)
    assert result.returncode == 0, result.stderr

    install_root = result.install_root  # type: ignore[attr-defined]
    coach_config = json.loads((install_root / "coach-config.json").read_text(encoding="utf-8"))
    manifest = json.loads((install_root / "manifest.json").read_text(encoding="utf-8"))

    assert coach_config["schema_version"] == 1
    assert coach_config["agent_id"] == "coach"
    assert coach_config["weekly_planning"]["enabled"] is False
    assert coach_config["garmin"] == {
        "sync_enabled": False,
        "export_tomorrow_enabled": False,
    }

    assert manifest["schema_version"] == 1
    assert manifest["install_mode"] == "install"
    assert manifest["target"]["agent_id"] == "coach"
    assert manifest["features"] == {
        "python_runtime": False,
        "agent_files": True,
        "db_migrated": False,
        "systemd_sync": False,
        "systemd_export": False,
        "weekly_planning_cron": False,
    }
    assert manifest["backup"]["last_backup_dir"].startswith(str(install_root / "backups"))

    assert "Mode:           install" in result.stdout
    assert "Systemd sync:   skipped" in result.stdout
    assert "Weekly cron:    skipped" in result.stdout


def test_install_script_preserves_existing_weekly_settings_on_update(tmp_path: Path) -> None:
    first = _run_installer(
        tmp_path,
        "--weekly-planning-session-key",
        "session:coach:telegram",
        "--weekly-planning-model",
        "azure/gpt-5.4-1",
        "--weekly-planning-tz",
        "Europe/Paris",
        "--weekly-planning-name",
        "weekly-coach",
    )
    assert first.returncode == 0, first.stderr

    second = _run_installer(tmp_path)
    assert second.returncode == 0, second.stderr

    install_root = second.install_root  # type: ignore[attr-defined]
    coach_config = json.loads((install_root / "coach-config.json").read_text(encoding="utf-8"))
    manifest = json.loads((install_root / "manifest.json").read_text(encoding="utf-8"))

    weekly = coach_config["weekly_planning"]
    assert weekly["session_key"] == "session:coach:telegram"
    assert weekly["model"] == "azure/gpt-5.4-1"
    assert weekly["timezone"] == "Europe/Paris"
    assert weekly["name"] == "weekly-coach"

    assert manifest["install_mode"] == "update"
    assert "Mode:           update" in second.stdout
