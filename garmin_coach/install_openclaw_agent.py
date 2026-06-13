from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import tomllib
import venv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


USAGE = """\
Install Garmin Coach Agent into an OpenClaw workspace.

Usage:
  scripts/install-openclaw-agent.sh [options]

Options:
  --mode MODE               auto|install|update|repair (default: auto)
  --config PATH             OpenClaw config path (default: ~/.openclaw/openclaw.json)
  --workspace DIR           Force workspace target, skip agent auto-selection
  --install-root DIR        Managed install dir for app snapshot + venv
  --python BIN              Python binary to use for venv creation
  --agent ID                Install into an existing OpenClaw agent
  --update-skills MODE      auto|yes|no (patch skill allowlist when target agent is restricted)
  --sync-on-calendar SPEC   systemd OnCalendar spec for Garmin sync (default: hourly)
  --export-on-calendar SPEC systemd OnCalendar spec for plan export (default: daily)
  --sync-lookback-days N    lookback passed to sync-garmin (default: 3)
  --skip-systemd-sync       Do not install the Garmin sync systemd user timer
  --skip-systemd-export     Do not install the plan export systemd user timer
  --skip-weekly-planning-cron
                            Do not create/update the weekly planning OpenClaw cron
  --skip-activity-debrief-cron
                            Do not create/update the proactive activity debrief OpenClaw cron
  --weekly-planning-on-calendar EXPR
                            Cron expression for weekly planning (default: "0 18 * * 0")
  --weekly-planning-tz IANA Timezone for weekly planning cron (default: UTC)
  --weekly-planning-session-key KEY
                            Route weekly planning runs into an existing OpenClaw session
  --weekly-planning-channel CHANNEL
                            Delivery channel for weekly planning fallback announce
  --weekly-planning-to DEST Delivery destination for weekly planning fallback announce
  --weekly-planning-account ID
                            Delivery account id for weekly planning fallback announce
  --weekly-planning-name NAME
                            Cron job name override (default: weekly-planning-<agent-id>)
  --weekly-planning-message TEXT
                            Agent prompt override for weekly planning cron
  --weekly-planning-model MODEL
                            Model override for weekly planning cron
  --activity-debrief-on-calendar EXPR
                            Cron expression for proactive activity debriefs (default: "10 8-19 * * *")
  --activity-debrief-tz IANA Timezone for proactive activity debrief cron (default: UTC)
  --activity-debrief-session-key KEY
                            Route proactive activity debrief runs into an existing OpenClaw session
  --activity-debrief-channel CHANNEL
                            Delivery channel for proactive activity debrief fallback announce
  --activity-debrief-to DEST
                            Delivery destination for proactive activity debrief fallback announce
  --activity-debrief-account ID
                            Delivery account id for proactive activity debrief fallback announce
  --activity-debrief-name NAME
                            Cron job name override (default: activity-debrief-<agent-id>)
  --activity-debrief-message TEXT
                            Agent prompt override for proactive activity debrief cron
  --activity-debrief-model MODEL
                            Model override for proactive activity debrief cron
  --no-bootstrap            Do not install BOOTSTRAP.md
  --preserve-agent-core     Do not overwrite HEARTBEAT.md, IDENTITY.md, SOUL.md if they exist
  --skip-package-install    Copy files only; skip venv/package install
  --dry-run                 Show actions without writing
  --quiet                   Reduce logs
  -h, --help                Show help

Default behavior:
  - this is the single entrypoint for install/update/repair
  - by default it auto-detects whether the target needs install, update, or repair
  - if a config is found and stdin/stdout are interactive, the script lists existing agents
  - you can pick main or another existing agent
  - if the chosen agent has a skill allowlist, the script can append Garmin skills to it

What it installs:
  - agent files -> <workspace>/
  - playbooks   -> <workspace>/playbooks/ (if present in repo)
  - skills      -> <workspace>/skills/
  - app snapshot + venv -> <install-root>/
  - systemd user timer  -> Garmin sync automatique (unless --skip-systemd-sync)
  - systemd user timer  -> export quotidien des plans du lendemain (unless --skip-systemd-export)
  - OpenClaw cron        -> weekly planning, when session/delivery context is provided
  - OpenClaw cron        -> proactive activity debriefs, when session/delivery context is provided
  - persisted config     -> <install-root>/coach-config.json
  - install manifest     -> <install-root>/manifest.json
"""

WEEKLY_PLANNING_DEFAULT_MESSAGE = (
    "Rendez-vous hebdomadaire de planification. Suis playbooks/weekly_planning.md pour préparer "
    "le programme de la semaine à venir : synchronise Garmin si nécessaire, lis objectifs, "
    "contraintes, état de forme et plan courant, puis crée ou ajuste le plan local de la semaine "
    "cible. Évite les doublons si le plan existe déjà. N'exporte vers Garmin que l'horizon court, "
    "sauf demande explicite de l'utilisateur. Termine par un résumé concis de la semaine et les "
    "points de vigilance."
)

ACTIVITY_DEBRIEF_DEFAULT_MESSAGE = (
    "Débrief proactif post-séance. Suis playbooks/proactive_activity_debrief.md : lis les activités "
    "à débriefer avec get-pending-debriefs, n'envoie qu'un seul message même s'il y a plusieurs "
    "activités, demande pour chacune un RPE /10, une note libre et toute douleur ou gêne utile au "
    "suivi blessure (pendant, après, lendemain), puis marque les activités sollicitées avec "
    "mark-activity-debrief-prompted seulement si le message part réellement. Si rien n'est éligible, "
    "réponds par NO_REPLY."
)

ENTRYPOINT_COMMANDS = [
    "auth-garmin",
    "create-constraint",
    "create-goal",
    "create-plan-draft",
    "create-plan-session",
    "delete-constraint",
    "delete-plan-session",
    "export-plan-garmin",
    "get-activities",
    "get-constraints",
    "get-current-plan",
    "get-fitness-state",
    "get-goals",
    "get-pending-debriefs",
    "mark-activity-debrief-prompted",
    "save-activity-debrief",
    "set-constraint-status",
    "set-plan-session-status",
    "set-plan-status",
    "sync-garmin",
]


class InstallerError(Exception):
    pass


@dataclass
class InstallOptions:
    repo_dir: Path
    home_dir: Path
    config_path: Path
    workspace_dir: Path | None = None
    install_root: Path | None = None
    python_bin: str = ""
    dry_run: bool = False
    with_bootstrap: bool = True
    preserve_agent_core: bool = False
    skip_package_install: bool = False
    quiet: bool = False
    requested_install_mode: str = "auto"
    target_agent_id: str = ""
    update_skills_mode: str = "auto"
    skip_systemd_sync: bool = False
    skip_systemd_export: bool = False
    skip_weekly_planning_cron: bool = False
    skip_activity_debrief_cron: bool = False
    sync_on_calendar: str = "hourly"
    export_on_calendar: str = "daily"
    sync_lookback_days: int = 3
    weekly_planning_on_calendar: str = "0 18 * * 0"
    weekly_planning_tz: str = "UTC"
    weekly_planning_session_key: str = ""
    weekly_planning_channel: str = ""
    weekly_planning_to: str = ""
    weekly_planning_account: str = ""
    weekly_planning_name: str = ""
    weekly_planning_message: str = ""
    weekly_planning_model: str = ""
    activity_debrief_on_calendar: str = "10 8-19 * * *"
    activity_debrief_tz: str = "UTC"
    activity_debrief_session_key: str = ""
    activity_debrief_channel: str = ""
    activity_debrief_to: str = ""
    activity_debrief_account: str = ""
    activity_debrief_name: str = ""
    activity_debrief_message: str = ""
    activity_debrief_model: str = ""


@dataclass
class AgentInfo:
    agent_id: str
    name: str
    model: str
    workspace: Path
    agent_dir: Path
    skills_mode: str
    skills: list[str] = field(default_factory=list)
    synthetic: bool = False


@dataclass
class ExistingInstallState:
    manifest_exists: bool = False
    config_exists: bool = False
    backup_dir: str = ""
    weekly_session_key: str = ""
    weekly_to: str = ""
    weekly_channel: str = ""
    weekly_account: str = ""
    weekly_tz: str = ""
    weekly_schedule: str = ""
    weekly_model: str = ""
    weekly_name: str = ""
    debrief_session_key: str = ""
    debrief_to: str = ""
    debrief_channel: str = ""
    debrief_account: str = ""
    debrief_tz: str = ""
    debrief_schedule: str = ""
    debrief_model: str = ""
    debrief_name: str = ""


@dataclass
class InstallSource:
    app_version: str = "unknown"
    git_commit: str = ""
    git_tag: str = ""
    git_source: str = "local"
    git_dirty: bool = False


@dataclass
class RuntimeState:
    garmin_skills: list[str] = field(default_factory=list)
    selected_agent: AgentInfo | None = None
    patch_skills_allowlist: bool = False
    feature_python_runtime: bool = False
    feature_agent_files: bool = False
    feature_db_migrated: bool = False
    feature_systemd_sync: bool = False
    feature_systemd_export: bool = False
    feature_weekly_planning: bool = False
    feature_activity_debrief: bool = False
    db_status: str = "not-run"
    last_sync_timer_name: str = ""
    last_export_timer_name: str = ""
    install_mode: str = "install"
    coach_config_path: Path | None = None
    manifest_path: Path | None = None
    previous: ExistingInstallState = field(default_factory=ExistingInstallState)
    install_source: InstallSource = field(default_factory=InstallSource)


class Installer:
    def __init__(self, options: InstallOptions):
        self.options = options
        self.state = RuntimeState()

    def log(self, message: str) -> None:
        if not self.options.quiet:
            print(message)

    def is_tty(self) -> bool:
        return sys.stdin.isatty() and sys.stdout.isatty()

    def prompt_line(self, prompt: str, default: str = "") -> str:
        suffix = f" [{default}]" if default else ""
        value = input(f"{prompt}{suffix}: ")
        return value or default

    def prompt_yes_no(self, prompt: str, default: str = "y") -> bool:
        while True:
            label = "[Y/n]" if default == "y" else "[y/N]"
            answer = input(f"{prompt} {label}: ").strip() or default
            lowered = answer.lower()
            if lowered in {"y", "yes"}:
                return True
            if lowered in {"n", "no"}:
                return False

    def expand(self, raw: str | Path) -> Path:
        return Path(os.path.expanduser(str(raw)))

    def load_garmin_skills(self) -> None:
        skills_root = self.options.repo_dir / "agent" / "skills"
        self.state.garmin_skills = sorted(
            child.name for child in skills_root.iterdir() if child.is_dir()
        ) if skills_root.exists() else []

    def choose_python(self) -> str:
        if self.options.python_bin:
            found = shutil.which(self.options.python_bin)
            if not found:
                raise InstallerError(f"Python not found: {self.options.python_bin}")
            return found

        found = shutil.which("python3.13")
        if found:
            return found

        uv = shutil.which("uv")
        if uv:
            self.log("Python 3.13 not found. Installing via uv...")
            if self.options.dry_run:
                return "$HOME/.local/bin/python3.13"
            subprocess.run([uv, "python", "install", "3.13"], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(
                [uv, "python", "update-shell"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            result = subprocess.run(
                [uv, "python", "find", "3.13"],
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()

        raise InstallerError("No usable Python found (need python3.13 or uv to install it).")

    def _backup_relative(self, src: Path) -> Path:
        workspace = self.options.workspace_dir
        src_str = str(src)
        if workspace is not None:
            workspace_str = str(workspace)
            prefix = workspace_str.rstrip("/") + "/"
            if src_str.startswith(prefix):
                return Path(src_str[len(prefix):])
        return Path(src_str.lstrip("/"))

    def backup_if_exists(self, src: Path, backup_root: Path) -> None:
        if not src.exists() and not src.is_symlink():
            return
        rel = self._backup_relative(src)
        dest = backup_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir() and not src.is_symlink():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest, symlinks=True)
        else:
            shutil.copy2(src, dest, follow_symlinks=False)

    def copy_file(self, src: Path, dst: Path, backup_root: Path) -> None:
        if self.options.dry_run:
            print(f"[dry-run] copy {src} -> {dst}")
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        self.backup_if_exists(dst, backup_root)
        shutil.copyfile(src, dst)
        os.chmod(dst, 0o644)

    def copy_tree_files(self, src_root: Path, dst_root: Path, backup_root: Path) -> None:
        for file_path in sorted(p for p in src_root.rglob("*") if p.is_file()):
            rel = file_path.relative_to(src_root)
            self.copy_file(file_path, dst_root / rel, backup_root)

    def copy_tree_files_if_exists(self, src_root: Path, dst_root: Path, backup_root: Path) -> None:
        if not src_root.is_dir():
            self.log(f"Skipping missing optional directory: {src_root}")
            return
        self.copy_tree_files(src_root, dst_root, backup_root)

    def sync_app_snapshot(self, app_dir: Path) -> None:
        if self.options.dry_run:
            print(f"[dry-run] refresh app snapshot in {app_dir}")
            return
        if app_dir.exists():
            shutil.rmtree(app_dir)
        app_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.options.repo_dir / "garmin_coach", app_dir / "garmin_coach")
        for name in ["pyproject.toml", "README.md", "SPEC.md"]:
            shutil.copy2(self.options.repo_dir / name, app_dir / name)

    def rewrite_runtime_paths(self, managed_bin_dir: str, targets: list[Path]) -> None:
        if self.options.dry_run:
            joined = " ".join(str(target) for target in targets)
            print(f"[dry-run] rewrite runtime paths with {managed_bin_dir} in {joined}")
            return
        pattern = re.compile(r"<EXEC_DIR>")
        for target in targets:
            files = sorted(p for p in target.rglob("*") if p.is_file()) if target.is_dir() else [target]
            for file_path in files:
                text = file_path.read_text(encoding="utf-8")
                updated = pattern.sub(managed_bin_dir, text)
                if updated != text:
                    file_path.write_text(updated, encoding="utf-8")

    def create_venv_and_install(self, python_bin: str, venv_dir: Path, app_dir: Path) -> None:
        if self.options.skip_package_install:
            self.log("Skipping package install.")
            return
        if self.options.dry_run:
            print(f"[dry-run] create venv {venv_dir} with {python_bin}")
            print(f"[dry-run] install package from {app_dir}")
            return
        uv = shutil.which("uv")
        if uv:
            subprocess.run(
                [uv, "venv", str(venv_dir), "--python", python_bin, "--allow-existing"],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            subprocess.run(
                [uv, "pip", "install", "--python", str(venv_dir / "bin" / "python"), str(app_dir)],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            return
        builder = venv.EnvBuilder(with_pip=True, upgrade_deps=True)
        builder.create(venv_dir)
        subprocess.run(
            [str(venv_dir / "bin" / "python"), "-m", "pip", "install", str(app_dir)],
            check=True,
            stdout=subprocess.DEVNULL,
        )

    def systemd_user_available(self) -> bool:
        systemctl = shutil.which("systemctl")
        if not systemctl:
            return False
        return (
            subprocess.run(
                [systemctl, "--user", "show-environment"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            ).returncode
            == 0
        )

    def write_systemd_runtime_env(self, safe_agent_id: str, data_dir: Path, backup_root: Path) -> Path:
        install_root = self.require_install_root()
        env_file = install_root / "systemd" / f"garmin-runtime-{safe_agent_id}.env"
        if self.options.dry_run:
            print(f"[dry-run] install runtime env {env_file}", file=sys.stderr)
            return env_file
        (data_dir / "tokens").mkdir(parents=True, exist_ok=True)
        env_file.parent.mkdir(parents=True, exist_ok=True)
        self.backup_if_exists(env_file, backup_root)
        env_file.write_text(
            f"GARMIN_COACH_DB={data_dir / 'garmin_coach.db'}\n"
            f"GARMIN_COACH_TOKENS_DIR={data_dir / 'tokens'}\n"
            "PYTHONUNBUFFERED=1\n",
            encoding="utf-8",
        )
        return env_file

    def install_systemd_sync_timer(
        self, safe_agent_id: str, managed_venv_python: Path, backup_root: Path, env_file: Path
    ) -> None:
        self.state.last_sync_timer_name = f"garmin-coach-sync-{safe_agent_id}.timer"
        service_name = f"garmin-coach-sync-{safe_agent_id}.service"
        timer_name = self.state.last_sync_timer_name
        systemd_user_dir = self.options.home_dir / ".config" / "systemd" / "user"
        service_path = systemd_user_dir / service_name
        timer_path = systemd_user_dir / timer_name

        if self.options.skip_systemd_sync:
            self.log("Skipping Garmin sync systemd timer by request.")
            return
        if self.options.dry_run:
            print(f"[dry-run] install systemd user service {service_path}")
            print(
                f"[dry-run] install systemd user timer {timer_path} (OnCalendar={self.options.sync_on_calendar})"
            )
            self.state.feature_systemd_sync = True
            return
        if not managed_venv_python.exists():
            self.log(
                f"Skipping Garmin sync systemd timer because runtime is missing: {managed_venv_python}"
            )
            return

        install_root = self.require_install_root()
        selected = self.require_selected_agent()
        systemd_user_dir.mkdir(parents=True, exist_ok=True)
        self.backup_if_exists(service_path, backup_root)
        self.backup_if_exists(timer_path, backup_root)
        service_path.write_text(
            textwrap.dedent(
                f"""\
                [Unit]
                Description=Garmin Coach sync ({selected.agent_id})
                Wants=network-online.target
                After=network-online.target

                [Service]
                Type=oneshot
                EnvironmentFile={env_file}
                WorkingDirectory={install_root}
                ExecStart={managed_venv_python} -m garmin_coach.sync_garmin --lookback-days {self.options.sync_lookback_days}
                """
            ),
            encoding="utf-8",
        )
        timer_path.write_text(
            textwrap.dedent(
                f"""\
                [Unit]
                Description=Garmin Coach sync timer ({selected.agent_id})

                [Timer]
                OnCalendar={self.options.sync_on_calendar}
                Persistent=true
                RandomizedDelaySec=15m
                Unit={service_name}

                [Install]
                WantedBy=timers.target
                """
            ),
            encoding="utf-8",
        )
        if self.systemd_user_available():
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "--user", "enable", "--now", timer_name], check=True, stdout=subprocess.DEVNULL)
            self.log(f"Systemd sync timer: {timer_name} ({self.options.sync_on_calendar})")
        else:
            self.log("Installed Garmin sync timer files, but systemctl --user is unavailable in this session.")
            self.log(
                f"Enable later with: systemctl --user daemon-reload && systemctl --user enable --now {timer_name}"
            )
        self.state.feature_systemd_sync = True

    def install_systemd_export_timer(
        self, safe_agent_id: str, managed_venv_python: Path, backup_root: Path, env_file: Path
    ) -> None:
        self.state.last_export_timer_name = f"garmin-coach-export-{safe_agent_id}.timer"
        service_name = f"garmin-coach-export-{safe_agent_id}.service"
        timer_name = self.state.last_export_timer_name
        systemd_user_dir = self.options.home_dir / ".config" / "systemd" / "user"
        install_root = self.require_install_root()
        helper_script = install_root / "systemd" / f"export-tomorrow-{safe_agent_id}.sh"
        service_path = systemd_user_dir / service_name
        timer_path = systemd_user_dir / timer_name

        if self.options.skip_systemd_export:
            self.log("Skipping Garmin export systemd timer by request.")
            return
        if self.options.dry_run:
            print(f"[dry-run] install export helper {helper_script}")
            print(f"[dry-run] install systemd user service {service_path}")
            print(
                f"[dry-run] install systemd user timer {timer_path} (OnCalendar={self.options.export_on_calendar})"
            )
            self.state.feature_systemd_export = True
            return
        if not managed_venv_python.exists():
            self.log(
                f"Skipping Garmin export systemd timer because runtime is missing: {managed_venv_python}"
            )
            return

        selected = self.require_selected_agent()
        helper_script.parent.mkdir(parents=True, exist_ok=True)
        systemd_user_dir.mkdir(parents=True, exist_ok=True)
        self.backup_if_exists(helper_script, backup_root)
        self.backup_if_exists(service_path, backup_root)
        self.backup_if_exists(timer_path, backup_root)
        helper_script.write_text(
            textwrap.dedent(
                f"""\
                #!/usr/bin/env bash
                set -euo pipefail

                readarray -t export_info < <(\"{managed_venv_python}\" - <<'PY'
                import os
                import sqlite3
                from datetime import date, timedelta

                db_path = os.environ.get("GARMIN_COACH_DB", "")
                tomorrow = date.today() + timedelta(days=1)
                week_start = tomorrow - timedelta(days=tomorrow.weekday())
                plan_id = ""

                if db_path and os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    try:
                        row = conn.execute(
                            "SELECT id FROM training_plans WHERE week_start=? AND status IN ('active', 'draft') ORDER BY id DESC LIMIT 1",
                            (week_start.isoformat(),),
                        ).fetchone()
                        if row:
                            plan_id = str(row[0])
                    finally:
                        conn.close()

                print(tomorrow.isoformat())
                print(week_start.isoformat())
                print(plan_id)
                PY
                )

                tomorrow=\"${{export_info[0]}}\"
                week_start=\"${{export_info[1]}}\"
                plan_id=\"${{export_info[2]:-}}\"

                if [[ -z \"$plan_id\" ]]; then
                  echo "No active/draft plan found for week $week_start; skipping Garmin export."
                  exit 0
                fi

                exec \"{managed_venv_python}\" -m garmin_coach.export_plan_garmin \
                  --plan-id \"$plan_id\" \
                  --start-date \"$tomorrow\" \
                  --end-date \"$tomorrow\"
                """
            ),
            encoding="utf-8",
        )
        os.chmod(helper_script, 0o755)
        service_path.write_text(
            textwrap.dedent(
                f"""\
                [Unit]
                Description=Garmin Coach export tomorrow plan ({selected.agent_id})
                Wants=network-online.target
                After=network-online.target

                [Service]
                Type=oneshot
                EnvironmentFile={env_file}
                WorkingDirectory={install_root}
                ExecStart={helper_script}
                """
            ),
            encoding="utf-8",
        )
        timer_path.write_text(
            textwrap.dedent(
                f"""\
                [Unit]
                Description=Garmin Coach export timer ({selected.agent_id})

                [Timer]
                OnCalendar={self.options.export_on_calendar}
                Persistent=true
                RandomizedDelaySec=15m
                Unit={service_name}

                [Install]
                WantedBy=timers.target
                """
            ),
            encoding="utf-8",
        )
        if self.systemd_user_available():
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "--user", "enable", "--now", timer_name], check=True, stdout=subprocess.DEVNULL)
            self.log(f"Systemd export timer: {timer_name} ({self.options.export_on_calendar})")
        else:
            self.log("Installed Garmin export timer files, but systemctl --user is unavailable in this session.")
            self.log(
                f"Enable later with: systemctl --user daemon-reload && systemctl --user enable --now {timer_name}"
            )
        self.state.feature_systemd_export = True

    def config_exists(self) -> bool:
        return self.options.config_path.is_file()

    def get_default_workspace_from_config(self) -> Path:
        if not self.options.config_path.exists():
            return self.options.home_dir / ".openclaw" / "workspace"
        cfg = json.loads(self.options.config_path.read_text(encoding="utf-8"))
        raw = cfg.get("agents", {}).get("defaults", {}).get("workspace") or "~/.openclaw/workspace"
        return self.expand(raw)

    @staticmethod
    def _resolve_model(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            primary = value.get("primary")
            if isinstance(primary, str):
                return primary
        return ""

    def list_agents_from_config(self) -> list[AgentInfo]:
        if not self.options.config_path.exists():
            return []
        cfg = json.loads(self.options.config_path.read_text(encoding="utf-8"))
        agents_cfg = cfg.get("agents", {})
        defaults = agents_cfg.get("defaults", {})
        default_ws = self.expand(defaults.get("workspace") or "~/.openclaw/workspace")
        default_skills = defaults.get("skills")
        entries = list(agents_cfg.get("list", []))
        by_id: dict[str, dict[str, Any]] = {
            entry["id"]: entry for entry in entries if isinstance(entry, dict) and entry.get("id")
        }
        if "main" not in by_id:
            by_id["main"] = {
                "id": "main",
                "name": "Main Agent",
                "workspace": str(default_ws),
                "agentDir": str(self.expand("~/.openclaw/agents/main/agent")),
                "_synthetic": True,
            }
        ordered_ids: list[str] = []
        if "main" in by_id:
            ordered_ids.append("main")
        for entry in entries:
            agent_id = entry.get("id")
            if isinstance(agent_id, str) and agent_id != "main" and agent_id not in ordered_ids:
                ordered_ids.append(agent_id)
        for agent_id in by_id:
            if agent_id not in ordered_ids:
                ordered_ids.append(agent_id)

        result: list[AgentInfo] = []
        for agent_id in ordered_ids:
            entry = by_id[agent_id]
            name = entry.get("name") or ("Main Agent" if agent_id == "main" else agent_id)
            model = self._resolve_model(entry.get("model")) or self._resolve_model(defaults.get("model"))
            workspace = self.expand(entry.get("workspace") or str(default_ws))
            agent_dir = self.expand(entry.get("agentDir") or f"~/.openclaw/agents/{agent_id}/agent")
            if "skills" in entry:
                skills_mode = "agent"
                skills = [str(item) for item in (entry.get("skills") or [])]
            elif default_skills is not None:
                skills_mode = "defaults"
                skills = [str(item) for item in (default_skills or [])]
            else:
                skills_mode = "unrestricted"
                skills = []
            result.append(
                AgentInfo(
                    agent_id=agent_id,
                    name=str(name),
                    model=model,
                    workspace=workspace,
                    agent_dir=agent_dir,
                    skills_mode=skills_mode,
                    skills=skills,
                    synthetic=bool(entry.get("_synthetic")),
                )
            )
        return result

    def select_existing_agent_by_id(self, wanted_id: str) -> AgentInfo | None:
        for agent in self.list_agents_from_config():
            if agent.agent_id == wanted_id:
                return agent
        return None

    def interactive_choose_target(self) -> AgentInfo:
        agents = self.list_agents_from_config()
        for index, agent in enumerate(agents, start=1):
            if agent.skills_mode == "unrestricted":
                skills_note = "skills: unrestricted"
            elif agent.skills_mode == "agent":
                skills_note = "skills: allowlist agent"
            else:
                skills_note = "skills: allowlist defaults"
            print(f"{index}) {agent.agent_id} ({agent.workspace})", file=sys.stderr)
            if agent.model:
                print(f"   {skills_note} | model: {agent.model}", file=sys.stderr)
            else:
                print(f"   {skills_note}", file=sys.stderr)
        print("q) Quitter", file=sys.stderr)
        choice = self.prompt_line("Choix", "1")
        if choice.lower() == "q":
            raise SystemExit(0)
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(agents):
                selected = agents[idx - 1]
                if self.options.workspace_dir is not None:
                    selected.workspace = self.options.workspace_dir
                return selected
        raise InstallerError(f"Invalid choice: {choice}")

    def maybe_select_target_from_config(self) -> AgentInfo:
        default_workspace = self.get_default_workspace_from_config()
        if self.options.target_agent_id:
            selected = self.select_existing_agent_by_id(self.options.target_agent_id)
            if selected is None:
                raise InstallerError(f"Unknown agent id: {self.options.target_agent_id}")
            if self.options.workspace_dir is not None:
                selected.workspace = self.options.workspace_dir
            return selected
        if self.is_tty():
            return self.interactive_choose_target()
        selected = self.select_existing_agent_by_id("main")
        if selected is not None:
            if self.options.workspace_dir is not None:
                selected.workspace = self.options.workspace_dir
            return selected
        return AgentInfo(
            agent_id="main",
            name="Main Agent",
            model="",
            workspace=self.options.workspace_dir or default_workspace,
            agent_dir=self.expand("~/.openclaw/agents/main/agent"),
            skills_mode="unrestricted",
            skills=[],
            synthetic=True,
        )

    def maybe_prompt_or_set_skill_patch(self) -> None:
        selected = self.require_selected_agent()
        decision = "no"
        if self.options.update_skills_mode == "yes":
            decision = "yes"
        elif self.options.update_skills_mode == "no":
            decision = "no"
        elif self.options.update_skills_mode == "auto":
            if selected.skills_mode == "unrestricted":
                decision = "no"
            elif self.is_tty():
                decision = "yes" if self.prompt_yes_no(
                    f"L'agent {selected.agent_id} a une allowlist de skills. Ajouter les skills Garmin à sa config ?",
                    "y",
                ) else "no"
            else:
                decision = "yes"
        else:
            raise InstallerError(f"Invalid --update-skills mode: {self.options.update_skills_mode}")

        if decision != "yes":
            self.state.patch_skills_allowlist = False
            return

        merged = list(selected.skills)
        for skill in self.state.garmin_skills:
            if skill not in merged:
                merged.append(skill)
        selected.skills = merged
        self.state.patch_skills_allowlist = True

    def patch_config_for_target(self) -> None:
        if not self.state.patch_skills_allowlist:
            return
        if not self.config_exists():
            raise InstallerError(f"Config not found: {self.options.config_path}")
        selected = self.require_selected_agent()
        cfg = json.loads(self.options.config_path.read_text(encoding="utf-8"))
        entries = cfg.setdefault("agents", {}).setdefault("list", [])
        entry = next((item for item in entries if item.get("id") == selected.agent_id), None)
        if entry is None:
            raise InstallerError(f"Agent not found in config: {selected.agent_id}")
        entry["skills"] = selected.skills
        if self.options.dry_run:
            print(f"[dry-run] would update config: {self.options.config_path}")
            print(json.dumps(entry, ensure_ascii=False, indent=2))
            return
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = self.options.config_path.with_name(
            self.options.config_path.name + f".bak.garmin-install.{stamp}"
        )
        shutil.copy2(self.options.config_path, backup)
        self.options.config_path.write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Config updated: {self.options.config_path}")
        print(f"Backup: {backup}")

    def resolve_install_source(self) -> InstallSource:
        source = InstallSource()
        pyproject = self.options.repo_dir / "pyproject.toml"
        if pyproject.exists():
            try:
                data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
                source.app_version = str(data["project"]["version"])
            except Exception:
                source.app_version = "unknown"
        git = shutil.which("git")
        if git and subprocess.run(
            [git, "-C", str(self.options.repo_dir), "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode == 0:
            source.git_commit = self._git_output("rev-parse", "HEAD")
            source.git_tag = self._git_output("describe", "--tags", "--exact-match")
            git_branch = self._git_output("rev-parse", "--abbrev-ref", "HEAD")
            source.git_dirty = bool(self._git_output("status", "--porcelain"))
            if source.git_tag:
                source.git_source = "tag"
            elif git_branch and git_branch != "HEAD":
                source.git_source = "branch"
            elif source.git_commit:
                source.git_source = "commit"
        return source

    def _git_output(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.options.repo_dir), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    def load_existing_install_state(self) -> None:
        install_root = self.require_install_root()
        coach_config_path = install_root / "coach-config.json"
        manifest_path = install_root / "manifest.json"
        self.state.coach_config_path = coach_config_path
        self.state.manifest_path = manifest_path
        previous = ExistingInstallState(
            manifest_exists=manifest_path.exists(),
            config_exists=coach_config_path.exists(),
        )
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            previous.backup_dir = str(manifest.get("backup", {}).get("last_backup_dir", ""))
        else:
            legacy_manifest = install_root / "manifest.txt"
            if legacy_manifest.exists():
                for line in legacy_manifest.read_text(encoding="utf-8").splitlines():
                    if "=" in line:
                        key, value = line.split("=", 1)
                        if key == "backup_root":
                            previous.backup_dir = value
        if coach_config_path.exists():
            config = json.loads(coach_config_path.read_text(encoding="utf-8"))
            weekly = config.get("weekly_planning", {})
            delivery = weekly.get("delivery", {})
            previous.weekly_session_key = str(weekly.get("session_key", ""))
            previous.weekly_to = str(delivery.get("to", ""))
            previous.weekly_channel = str(delivery.get("channel", ""))
            previous.weekly_account = str(delivery.get("account_id", ""))
            previous.weekly_tz = str(weekly.get("timezone", ""))
            previous.weekly_schedule = str(weekly.get("schedule", ""))
            previous.weekly_model = str(weekly.get("model", ""))
            previous.weekly_name = str(weekly.get("name", ""))
            debrief = config.get("activity_debrief", {})
            debrief_delivery = debrief.get("delivery", {})
            previous.debrief_session_key = str(debrief.get("session_key", ""))
            previous.debrief_to = str(debrief_delivery.get("to", ""))
            previous.debrief_channel = str(debrief_delivery.get("channel", ""))
            previous.debrief_account = str(debrief_delivery.get("account_id", ""))
            previous.debrief_tz = str(debrief.get("timezone", ""))
            previous.debrief_schedule = str(debrief.get("schedule", ""))
            previous.debrief_model = str(debrief.get("model", ""))
            previous.debrief_name = str(debrief.get("name", ""))
        self.state.previous = previous

        detected_mode = "install"
        if previous.manifest_exists and previous.config_exists:
            detected_mode = "update"
        elif previous.manifest_exists or previous.config_exists or (install_root / ".venv").exists() or (install_root / "data" / "garmin_coach.db").exists():
            detected_mode = "repair"
        if (
            self.options.requested_install_mode != "auto"
            and self.options.requested_install_mode != detected_mode
        ):
            raise InstallerError(
                f"Requested --mode {self.options.requested_install_mode} but detected {detected_mode} "
                f"for {install_root}. Re-run with --mode {detected_mode} or omit --mode."
            )
        self.state.install_mode = detected_mode

    def resolve_weekly_planning_defaults(self) -> None:
        previous = self.state.previous
        selected = self.require_selected_agent()
        if not self.options.weekly_planning_name:
            self.options.weekly_planning_name = previous.weekly_name or f"weekly-planning-{selected.agent_id}"
        if not self.options.weekly_planning_model:
            self.options.weekly_planning_model = previous.weekly_model or selected.model
        if not self.options.weekly_planning_tz or self.options.weekly_planning_tz == "UTC":
            if previous.weekly_tz:
                self.options.weekly_planning_tz = previous.weekly_tz
            elif os.environ.get("TZ"):
                self.options.weekly_planning_tz = os.environ["TZ"]
        if (
            self.options.weekly_planning_on_calendar == "0 18 * * 0"
            and previous.weekly_schedule
        ):
            self.options.weekly_planning_on_calendar = previous.weekly_schedule
        if not self.options.weekly_planning_session_key:
            self.options.weekly_planning_session_key = previous.weekly_session_key
        if not self.options.weekly_planning_to:
            self.options.weekly_planning_to = previous.weekly_to
        if not self.options.weekly_planning_channel:
            self.options.weekly_planning_channel = previous.weekly_channel
        if not self.options.weekly_planning_account:
            self.options.weekly_planning_account = previous.weekly_account
        if not self.options.weekly_planning_message:
            self.options.weekly_planning_message = WEEKLY_PLANNING_DEFAULT_MESSAGE

    def resolve_activity_debrief_defaults(self) -> None:
        previous = self.state.previous
        selected = self.require_selected_agent()
        if not self.options.activity_debrief_name:
            self.options.activity_debrief_name = previous.debrief_name or f"activity-debrief-{selected.agent_id}"
        if not self.options.activity_debrief_model:
            self.options.activity_debrief_model = previous.debrief_model or selected.model
        if not self.options.activity_debrief_tz or self.options.activity_debrief_tz == "UTC":
            if previous.debrief_tz:
                self.options.activity_debrief_tz = previous.debrief_tz
            elif os.environ.get("TZ"):
                self.options.activity_debrief_tz = os.environ["TZ"]
        if (
            self.options.activity_debrief_on_calendar == "10 8-19 * * *"
            and previous.debrief_schedule
        ):
            self.options.activity_debrief_on_calendar = previous.debrief_schedule
        if not self.options.activity_debrief_session_key:
            self.options.activity_debrief_session_key = previous.debrief_session_key
        if not self.options.activity_debrief_to:
            self.options.activity_debrief_to = previous.debrief_to
        if not self.options.activity_debrief_channel:
            self.options.activity_debrief_channel = previous.debrief_channel
        if not self.options.activity_debrief_account:
            self.options.activity_debrief_account = previous.debrief_account
        if not self.options.activity_debrief_message:
            self.options.activity_debrief_message = ACTIVITY_DEBRIEF_DEFAULT_MESSAGE

    def prompt_weekly_planning_if_needed(self) -> None:
        if self.options.skip_weekly_planning_cron:
            return
        if self.options.weekly_planning_session_key or self.options.weekly_planning_to:
            return
        if not self.is_tty():
            return
        selected = self.require_selected_agent()
        if not self.prompt_yes_no(
            f"Créer aussi le cron OpenClaw de weekly planning pour l'agent {selected.agent_id} ?",
            "y",
        ):
            self.options.skip_weekly_planning_cron = True
            return
        self.options.weekly_planning_session_key = self.prompt_line(
            "Session key cible (recommandé; vide pour utiliser seulement une delivery explicite)",
            self.options.weekly_planning_session_key,
        )
        if not self.options.weekly_planning_session_key:
            self.options.weekly_planning_channel = self.prompt_line(
                "Channel de delivery (ex: telegram, discord)", self.options.weekly_planning_channel
            )
            self.options.weekly_planning_to = self.prompt_line(
                "Destination de delivery (chat/user id)", self.options.weekly_planning_to
            )
            self.options.weekly_planning_account = self.prompt_line(
                "Account id de delivery (optionnel)", self.options.weekly_planning_account
            )
            if not self.options.weekly_planning_to:
                self.log("Skipping weekly planning cron: no session key or delivery destination provided.")
                self.options.skip_weekly_planning_cron = True
                return
        self.options.weekly_planning_on_calendar = self.prompt_line(
            "Expression cron pour le weekly planning", self.options.weekly_planning_on_calendar
        )
        self.options.weekly_planning_tz = self.prompt_line(
            "Timezone IANA du weekly planning", self.options.weekly_planning_tz
        )
        self.options.weekly_planning_model = self.prompt_line(
            "Model du weekly planning", self.options.weekly_planning_model
        )

    def prompt_activity_debrief_if_needed(self) -> None:
        if self.options.skip_activity_debrief_cron:
            return
        if self.options.activity_debrief_session_key or self.options.activity_debrief_to:
            return
        if not self.is_tty():
            return
        selected = self.require_selected_agent()
        if not self.prompt_yes_no(
            f"Créer aussi le cron OpenClaw de débrief proactif pour l'agent {selected.agent_id} ?",
            "y",
        ):
            self.options.skip_activity_debrief_cron = True
            return
        self.options.activity_debrief_session_key = self.prompt_line(
            "Session key cible du débrief proactif (recommandé; vide pour utiliser seulement une delivery explicite)",
            self.options.activity_debrief_session_key or self.options.weekly_planning_session_key,
        )
        if not self.options.activity_debrief_session_key:
            self.options.activity_debrief_channel = self.prompt_line(
                "Channel de delivery du débrief proactif (ex: telegram, discord)",
                self.options.activity_debrief_channel or self.options.weekly_planning_channel,
            )
            self.options.activity_debrief_to = self.prompt_line(
                "Destination de delivery du débrief proactif (chat/user id)",
                self.options.activity_debrief_to or self.options.weekly_planning_to,
            )
            self.options.activity_debrief_account = self.prompt_line(
                "Account id de delivery du débrief proactif (optionnel)",
                self.options.activity_debrief_account or self.options.weekly_planning_account,
            )
            if not self.options.activity_debrief_to:
                self.log("Skipping activity debrief cron: no session key or delivery destination provided.")
                self.options.skip_activity_debrief_cron = True
                return
        self.options.activity_debrief_on_calendar = self.prompt_line(
            "Expression cron pour le débrief proactif", self.options.activity_debrief_on_calendar
        )
        self.options.activity_debrief_tz = self.prompt_line(
            "Timezone IANA du débrief proactif", self.options.activity_debrief_tz
        )
        self.options.activity_debrief_model = self.prompt_line(
            "Model du débrief proactif", self.options.activity_debrief_model
        )

    def find_existing_cron_id(self, name: str, agent_id: str) -> str:
        try:
            raw = subprocess.check_output(
                ["openclaw", "cron", "list", "--json"],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            data = json.loads(raw)
        except Exception:
            return ""
        for job in data.get("jobs", []):
            if job.get("name") == name and job.get("agentId") == agent_id:
                return str(job.get("id", ""))
        return ""

    def create_or_update_weekly_planning_cron(self) -> None:
        self.resolve_weekly_planning_defaults()
        if self.options.skip_weekly_planning_cron:
            self.log("Skipping weekly planning cron by request.")
            return
        if shutil.which("openclaw") is None:
            self.log("openclaw CLI not found, skipping weekly planning cron creation")
            return
        self.prompt_weekly_planning_if_needed()
        if self.options.skip_weekly_planning_cron:
            return
        if not self.options.weekly_planning_session_key and not self.options.weekly_planning_to:
            self.log(
                "Skipping weekly planning cron: pass --weekly-planning-session-key or --weekly-planning-to "
                "(with optional channel/account), or run interactively."
            )
            return

        selected = self.require_selected_agent()
        existing_id = self.find_existing_cron_id(
            self.options.weekly_planning_name,
            selected.agent_id,
        )
        command = [
            "openclaw",
            "cron",
            "edit" if existing_id else "add",
        ]
        if existing_id:
            command.append(existing_id)
        command.extend(
            [
                "--cron",
                self.options.weekly_planning_on_calendar,
                "--name",
                self.options.weekly_planning_name,
                "--agent",
                selected.agent_id,
                "--message",
                self.options.weekly_planning_message,
                "--thinking",
                "high",
                "--light-context",
            ]
        )
        if self.options.weekly_planning_model:
            command.extend(["--model", self.options.weekly_planning_model])
        if self.options.weekly_planning_tz:
            command.extend(["--tz", self.options.weekly_planning_tz])
        if self.options.weekly_planning_session_key:
            command.extend(["--session-key", self.options.weekly_planning_session_key])
        else:
            command.extend(["--session", "isolated"])
        if self.options.weekly_planning_to:
            command.extend(["--announce", "--to", self.options.weekly_planning_to])
            if self.options.weekly_planning_channel:
                command.extend(["--channel", self.options.weekly_planning_channel])
            if self.options.weekly_planning_account:
                command.extend(["--account", self.options.weekly_planning_account])

        if self.options.dry_run:
            print(f"[dry-run] create/update weekly planning cron: {self.options.weekly_planning_name}")
            self.state.feature_weekly_planning = True
            return

        if existing_id:
            self.log(f"Updating existing weekly planning cron: {self.options.weekly_planning_name}")
        else:
            self.log(f"Creating weekly planning cron: {self.options.weekly_planning_name}")

        result = subprocess.run(command, capture_output=True, text=True, check=False)
        output = result.stdout + result.stderr
        if result.returncode == 0:
            if output.strip():
                print(output.rstrip())
            self.state.feature_weekly_planning = True
        elif existing_id:
            self.log("Warning: Failed to update existing weekly planning cron; keeping current job.")
            if output.strip():
                print(output.rstrip(), file=sys.stderr)
        else:
            self.log("Warning: Failed to create weekly planning cron")
            if output.strip():
                print(output.rstrip(), file=sys.stderr)

    def create_or_update_activity_debrief_cron(self) -> None:
        self.resolve_activity_debrief_defaults()
        if self.options.skip_activity_debrief_cron:
            self.log("Skipping activity debrief cron by request.")
            return
        if shutil.which("openclaw") is None:
            self.log("openclaw CLI not found, skipping activity debrief cron creation")
            return
        self.prompt_activity_debrief_if_needed()
        if self.options.skip_activity_debrief_cron:
            return
        if not self.options.activity_debrief_session_key and not self.options.activity_debrief_to:
            self.log(
                "Skipping activity debrief cron: pass --activity-debrief-session-key or --activity-debrief-to "
                "(with optional channel/account), or run interactively."
            )
            return

        selected = self.require_selected_agent()
        existing_id = self.find_existing_cron_id(
            self.options.activity_debrief_name,
            selected.agent_id,
        )
        command = [
            "openclaw",
            "cron",
            "edit" if existing_id else "add",
        ]
        if existing_id:
            command.append(existing_id)
        command.extend(
            [
                "--cron",
                self.options.activity_debrief_on_calendar,
                "--name",
                self.options.activity_debrief_name,
                "--agent",
                selected.agent_id,
                "--message",
                self.options.activity_debrief_message,
                "--thinking",
                "medium",
                "--light-context",
            ]
        )
        if self.options.activity_debrief_model:
            command.extend(["--model", self.options.activity_debrief_model])
        if self.options.activity_debrief_tz:
            command.extend(["--tz", self.options.activity_debrief_tz])
        if self.options.activity_debrief_session_key:
            command.extend(["--session-key", self.options.activity_debrief_session_key])
        else:
            command.extend(["--session", "isolated"])
        if self.options.activity_debrief_to:
            command.extend(["--announce", "--to", self.options.activity_debrief_to])
            if self.options.activity_debrief_channel:
                command.extend(["--channel", self.options.activity_debrief_channel])
            if self.options.activity_debrief_account:
                command.extend(["--account", self.options.activity_debrief_account])

        if self.options.dry_run:
            print(f"[dry-run] create/update activity debrief cron: {self.options.activity_debrief_name}")
            self.state.feature_activity_debrief = True
            return

        if existing_id:
            self.log(f"Updating existing activity debrief cron: {self.options.activity_debrief_name}")
        else:
            self.log(f"Creating activity debrief cron: {self.options.activity_debrief_name}")

        result = subprocess.run(command, capture_output=True, text=True, check=False)
        output = result.stdout + result.stderr
        if result.returncode == 0:
            if output.strip():
                print(output.rstrip())
            self.state.feature_activity_debrief = True
        elif existing_id:
            self.log("Warning: Failed to update existing activity debrief cron; keeping current job.")
            if output.strip():
                print(output.rstrip(), file=sys.stderr)
        else:
            self.log("Warning: Failed to create activity debrief cron")
            if output.strip():
                print(output.rstrip(), file=sys.stderr)

    def write_persisted_coach_config(self, backup_root: Path) -> None:
        path = self.require_coach_config_path()
        if self.options.dry_run:
            print(f"[dry-run] write coach config {path}")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_if_exists(path, backup_root)
        delivery: dict[str, str] = {}
        if self.options.weekly_planning_to:
            delivery["to"] = self.options.weekly_planning_to
        if self.options.weekly_planning_channel:
            delivery["channel"] = self.options.weekly_planning_channel
        if self.options.weekly_planning_account:
            delivery["account_id"] = self.options.weekly_planning_account
        debrief_delivery: dict[str, str] = {}
        if self.options.activity_debrief_to:
            debrief_delivery["to"] = self.options.activity_debrief_to
        if self.options.activity_debrief_channel:
            debrief_delivery["channel"] = self.options.activity_debrief_channel
        if self.options.activity_debrief_account:
            debrief_delivery["account_id"] = self.options.activity_debrief_account
        config = {
            "schema_version": 1,
            "agent_id": self.require_selected_agent().agent_id,
            "weekly_planning": {
                "enabled": self.state.feature_weekly_planning,
                "name": self.options.weekly_planning_name,
                "model": self.options.weekly_planning_model,
                "timezone": self.options.weekly_planning_tz,
                "schedule": self.options.weekly_planning_on_calendar,
                "session_key": self.options.weekly_planning_session_key,
                "delivery": delivery,
            },
            "activity_debrief": {
                "enabled": self.state.feature_activity_debrief,
                "name": self.options.activity_debrief_name,
                "model": self.options.activity_debrief_model,
                "timezone": self.options.activity_debrief_tz,
                "schedule": self.options.activity_debrief_on_calendar,
                "session_key": self.options.activity_debrief_session_key,
                "delivery": debrief_delivery,
            },
            "garmin": {
                "sync_enabled": self.state.feature_systemd_sync,
                "export_tomorrow_enabled": self.state.feature_systemd_export,
            },
        }
        path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def write_manifest(self, ts: str, backup_root: Path) -> None:
        path = self.require_manifest_path()
        source = self.state.install_source
        if self.options.dry_run:
            print(f"[dry-run] write manifest {path}")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_if_exists(path, backup_root)
        manifest = {
            "schema_version": 1,
            "install_mode": self.state.install_mode,
            "app_version": source.app_version,
            "git": {
                "tag": source.git_tag,
                "commit": source.git_commit,
                "source": source.git_source,
                "dirty": source.git_dirty,
            },
            "paths": {
                "workspace_dir": str(self.options.workspace_dir),
                "install_root": str(self.require_install_root()),
                "data_dir": str(self.require_install_root() / "data"),
                "managed_venv": str(self.require_install_root() / ".venv" / "bin" / "python"),
            },
            "target": {
                "agent_id": self.require_selected_agent().agent_id,
                "openclaw_config_path": str(self.options.config_path),
            },
            "features": {
                "python_runtime": self.state.feature_python_runtime,
                "agent_files": self.state.feature_agent_files,
                "db_migrated": self.state.feature_db_migrated,
                "systemd_sync": self.state.feature_systemd_sync,
                "systemd_export": self.state.feature_systemd_export,
                "weekly_planning_cron": self.state.feature_weekly_planning,
                "activity_debrief_cron": self.state.feature_activity_debrief,
            },
            "backup": {
                "last_backup_dir": str(backup_root),
            },
            "installed_at": ts,
        }
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def write_legacy_manifest(self, ts: str, backup_root: Path, managed_python: str) -> None:
        if self.options.dry_run:
            return
        install_root = self.require_install_root()
        data_dir = install_root / "data"
        legacy = install_root / "manifest.txt"
        app_version = self.state.install_source.app_version
        legacy.write_text(
            "\n".join(
                [
                    f"app_version={app_version}",
                    f"installed_at={ts}",
                    f"repo_dir={self.options.repo_dir}",
                    f"config_path={self.options.config_path}",
                    f"agent_id={self.require_selected_agent().agent_id}",
                    f"workspace_dir={self.options.workspace_dir}",
                    f"install_root={install_root}",
                    f"data_dir={data_dir}",
                    f"managed_python={managed_python}",
                    f"managed_venv={install_root / '.venv' / 'bin' / 'python'}",
                    f"backup_root={backup_root}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def print_install_summary(self, backup_root: Path) -> None:
        self.log("Install done.")
        self.log(f"Mode:           {self.state.install_mode}")
        self.log(f"Agent:          {self.require_selected_agent().agent_id}")
        self.log(f"Version:        {self.state.install_source.app_version}")
        source = self.state.install_source.git_source
        tag_suffix = f" ({self.state.install_source.git_tag})" if self.state.install_source.git_tag else ""
        self.log(f"Source:         {source}{tag_suffix}")
        self.log(f"Workspace:      {self.options.workspace_dir}")
        self.log(f"Install root:   {self.require_install_root()}")
        self.log(f"DB status:      {self.state.db_status}")
        self.log(f"Config:         {self.require_coach_config_path()}")
        self.log(f"Manifest:       {self.require_manifest_path()}")
        self.log(f"Backup root:    {backup_root}")
        self.log(f"Managed bin dir: {self.require_install_root() / '.venv' / 'bin'}")
        self.log(
            f"Systemd sync:   {self.state.last_sync_timer_name if self.state.feature_systemd_sync else 'skipped'}"
        )
        self.log(
            f"Systemd export: {self.state.last_export_timer_name if self.state.feature_systemd_export else 'skipped'}"
        )
        self.log(
            f"Weekly cron:    {self.options.weekly_planning_name if self.state.feature_weekly_planning else 'skipped'}"
        )
        self.log(
            "Activity debrief cron:    "
            f"{self.options.activity_debrief_name if self.state.feature_activity_debrief else 'skipped'}"
        )

    def require_selected_agent(self) -> AgentInfo:
        if self.state.selected_agent is None:
            raise InstallerError("No target workspace resolved")
        return self.state.selected_agent

    def require_install_root(self) -> Path:
        if self.options.install_root is None:
            raise InstallerError("Install root is not resolved")
        return self.options.install_root

    def require_coach_config_path(self) -> Path:
        if self.state.coach_config_path is None:
            raise InstallerError("Coach config path is not resolved")
        return self.state.coach_config_path

    def require_manifest_path(self) -> Path:
        if self.state.manifest_path is None:
            raise InstallerError("Manifest path is not resolved")
        return self.state.manifest_path

    def safe_symlink(self, target: Path, link: Path) -> None:
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(target)

    def run_db_migrations(self, venv_python: Path, db_path: Path) -> None:
        if self.options.dry_run:
            print("[dry-run] run database migrations")
            self.state.db_status = "dry-run"
            return
        if not venv_python.exists():
            self.state.db_status = "skipped"
            return
        self.log("Running database migrations...")
        env = os.environ.copy()
        env["GARMIN_COACH_DB"] = str(db_path)
        code = (
            "import sys\n"
            "from garmin_coach.db import run_migrations, get_connection\n"
            "try:\n"
            "    conn = get_connection()\n"
            "    applied = run_migrations(conn)\n"
            "    if applied:\n"
            "        print(f\"MIGRATED:{','.join(applied)}\")\n"
            "    else:\n"
            "        print('UP_TO_DATE')\n"
            "    conn.close()\n"
            "except Exception as e:\n"
            "    print(f\"Error during migrations: {e}\", file=sys.stderr)\n"
            "    sys.exit(1)\n"
        )
        result = subprocess.run(
            [str(venv_python), "-c", code],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        if result.stdout:
            print(result.stdout.rstrip())
        if result.returncode != 0:
            if result.stderr:
                print(result.stderr.rstrip(), file=sys.stderr)
            self.state.db_status = "failed"
            raise InstallerError("Database migrations failed")
        self.state.feature_db_migrated = True
        self.state.db_status = "migrated" if result.stdout.startswith("MIGRATED:") else "up-to-date"

    def run(self) -> None:
        self.load_garmin_skills()

        if not self.config_exists():
            if self.options.target_agent_id:
                raise InstallerError(
                    f"Cannot use --agent because OpenClaw config was not found at {self.options.config_path}."
                )
            self.log(f"Warning: OpenClaw configuration file not found at: {self.options.config_path}")
            if self.options.workspace_dir is None:
                if self.is_tty():
                    self.log("No OpenClaw workspace is specified.")
                    raw = self.prompt_line("OpenClaw workspace absolute path", "")
                    if not raw:
                        raise InstallerError("OpenClaw workspace is required for installation.")
                    self.options.workspace_dir = self.expand(raw)
                else:
                    raise InstallerError(
                        f"No OpenClaw configuration found at {self.options.config_path} and no workspace specified via --workspace."
                    )
            self.state.selected_agent = AgentInfo(
                agent_id="main",
                name="Main Agent",
                model="",
                workspace=self.options.workspace_dir,
                agent_dir=self.expand("~/.openclaw/agents/main/agent"),
                skills_mode="unrestricted",
                skills=[],
                synthetic=True,
            )
            self.state.patch_skills_allowlist = False
        else:
            if self.options.workspace_dir is not None and not self.options.target_agent_id and not self.is_tty():
                self.state.selected_agent = AgentInfo(
                    agent_id="main",
                    name="Main Agent",
                    model="",
                    workspace=self.options.workspace_dir,
                    agent_dir=self.expand("~/.openclaw/agents/main/agent"),
                    skills_mode="unrestricted",
                    skills=[],
                    synthetic=True,
                )
            else:
                self.state.selected_agent = self.maybe_select_target_from_config()

        selected = self.require_selected_agent()
        self.options.workspace_dir = selected.workspace
        if self.options.install_root is None:
            self.options.install_root = self.options.workspace_dir / ".garmin-coach-agent"
        self.load_existing_install_state()
        self.maybe_prompt_or_set_skill_patch()
        self.patch_config_for_target()

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = self.require_install_root() / "backups" / ts
        app_dir = self.require_install_root() / "app"
        data_dir = self.require_install_root() / "data"
        managed_python = self.choose_python()
        safe_agent_id = re.sub(r"[^A-Za-z0-9_.-]", "-", selected.agent_id)
        self.state.install_source = self.resolve_install_source()

        self.log(f"Agent:          {selected.agent_id}")
        self.log(f"Workspace:      {self.options.workspace_dir}")
        self.log(f"Install root:   {self.require_install_root()}")
        self.log(f"Python:         {managed_python}")
        self.log(f"Backup root:    {backup_root}")
        if self.state.patch_skills_allowlist:
            self.log(f"Skills config:  patched allowlist for {selected.agent_id}")

        if not self.options.dry_run:
            self.options.workspace_dir.mkdir(parents=True, exist_ok=True)
            self.require_install_root().mkdir(parents=True, exist_ok=True)
            backup_root.mkdir(parents=True, exist_ok=True)
            (data_dir / "tokens").mkdir(parents=True, exist_ok=True)

        self.sync_app_snapshot(app_dir)
        self.create_venv_and_install(managed_python, self.require_install_root() / ".venv", app_dir)
        if not self.options.dry_run and (self.require_install_root() / ".venv" / "bin" / "python").exists():
            self.state.feature_python_runtime = True

        root_files = ["AGENTS.md", "TOOLS.md"]
        if self.options.with_bootstrap:
            root_files.append("BOOTSTRAP.md")
        for name in ["HEARTBEAT.md", "IDENTITY.md", "SOUL.md"]:
            if self.options.preserve_agent_core and (self.options.workspace_dir / name).exists():
                self.log(f"Skipping {name} (preserve-agent-core is set)")
            else:
                root_files.append(name)
        for name in root_files:
            self.copy_file(self.options.repo_dir / "agent" / name, self.options.workspace_dir / name, backup_root)

        self.copy_tree_files_if_exists(
            self.options.repo_dir / "agent" / "playbooks",
            self.options.workspace_dir / "playbooks",
            backup_root,
        )
        self.copy_tree_files(
            self.options.repo_dir / "agent" / "skills",
            self.options.workspace_dir / "skills",
            backup_root,
        )
        self.state.feature_agent_files = True

        rewrite_targets = [self.options.workspace_dir / "TOOLS.md", self.options.workspace_dir / "skills"]
        if self.options.with_bootstrap:
            rewrite_targets.append(self.options.workspace_dir / "BOOTSTRAP.md")
        self.rewrite_runtime_paths(str(self.require_install_root() / ".venv" / "bin"), rewrite_targets)

        if self.options.dry_run:
            print(
                f"[dry-run] create symlinks in {self.options.workspace_dir}/bin and {self.options.home_dir}/.local/bin"
            )
        else:
            workspace_bin = self.options.workspace_dir / "bin"
            home_bin = self.options.home_dir / ".local" / "bin"
            workspace_bin.mkdir(parents=True, exist_ok=True)
            home_bin.mkdir(parents=True, exist_ok=True)
            for command in ENTRYPOINT_COMMANDS:
                target = self.require_install_root() / ".venv" / "bin" / command
                self.safe_symlink(target, workspace_bin / command)
                self.safe_symlink(target, home_bin / command)

        self.write_legacy_manifest(ts, backup_root, managed_python)
        self.run_db_migrations(self.require_install_root() / ".venv" / "bin" / "python", data_dir / "garmin_coach.db")
        runtime_env_file = self.write_systemd_runtime_env(safe_agent_id, data_dir, backup_root)
        self.install_systemd_sync_timer(
            safe_agent_id,
            self.require_install_root() / ".venv" / "bin" / "python",
            backup_root,
            runtime_env_file,
        )
        self.install_systemd_export_timer(
            safe_agent_id,
            self.require_install_root() / ".venv" / "bin" / "python",
            backup_root,
            runtime_env_file,
        )
        self.create_or_update_weekly_planning_cron()
        self.create_or_update_activity_debrief_cron()
        self.write_persisted_coach_config(backup_root)
        self.write_manifest(ts, backup_root)
        self.print_install_summary(backup_root)


def parse_args(argv: list[str], repo_dir: Path) -> InstallOptions:
    home_dir = Path(os.environ.get("HOME") or str(Path.home())).expanduser()
    config_path = Path(os.environ.get("OPENCLAW_CONFIG", str(home_dir / ".openclaw" / "openclaw.json"))).expanduser()
    workspace_env = os.environ.get("OPENCLAW_WORKSPACE")
    install_root_env = os.environ.get("OPENCLAW_INSTALL_ROOT")
    options = InstallOptions(
        repo_dir=repo_dir,
        home_dir=home_dir,
        config_path=config_path,
        workspace_dir=Path(workspace_env).expanduser() if workspace_env else None,
        install_root=Path(install_root_env).expanduser() if install_root_env else None,
    )

    index = 0
    while index < len(argv):
        arg = argv[index]

        def require_value() -> str:
            nonlocal index
            if index + 1 >= len(argv):
                raise InstallerError(f"Missing value for {arg}")
            value = argv[index + 1]
            index += 2
            return value

        if arg == "--config":
            options.config_path = Path(require_value()).expanduser()
        elif arg == "--mode":
            value = require_value()
            if value not in {"auto", "install", "update", "repair"}:
                raise InstallerError(f"Invalid --mode: {value} (expected auto|install|update|repair)")
            options.requested_install_mode = value
        elif arg == "--workspace":
            options.workspace_dir = Path(require_value()).expanduser()
        elif arg == "--install-root":
            options.install_root = Path(require_value()).expanduser()
        elif arg == "--python":
            options.python_bin = require_value()
        elif arg == "--agent":
            options.target_agent_id = require_value()
        elif arg == "--update-skills":
            options.update_skills_mode = require_value()
        elif arg == "--sync-on-calendar":
            options.sync_on_calendar = require_value()
        elif arg == "--export-on-calendar":
            options.export_on_calendar = require_value()
        elif arg == "--sync-lookback-days":
            options.sync_lookback_days = int(require_value())
        elif arg == "--skip-systemd-sync":
            options.skip_systemd_sync = True
            index += 1
        elif arg == "--skip-systemd-export":
            options.skip_systemd_export = True
            index += 1
        elif arg == "--skip-weekly-planning-cron":
            options.skip_weekly_planning_cron = True
            index += 1
        elif arg == "--skip-activity-debrief-cron":
            options.skip_activity_debrief_cron = True
            index += 1
        elif arg == "--weekly-planning-on-calendar":
            options.weekly_planning_on_calendar = require_value()
        elif arg == "--weekly-planning-tz":
            options.weekly_planning_tz = require_value()
        elif arg == "--weekly-planning-session-key":
            options.weekly_planning_session_key = require_value()
        elif arg == "--weekly-planning-channel":
            options.weekly_planning_channel = require_value()
        elif arg == "--weekly-planning-to":
            options.weekly_planning_to = require_value()
        elif arg == "--weekly-planning-account":
            options.weekly_planning_account = require_value()
        elif arg == "--weekly-planning-name":
            options.weekly_planning_name = require_value()
        elif arg == "--weekly-planning-message":
            options.weekly_planning_message = require_value()
        elif arg == "--weekly-planning-model":
            options.weekly_planning_model = require_value()
        elif arg == "--activity-debrief-on-calendar":
            options.activity_debrief_on_calendar = require_value()
        elif arg == "--activity-debrief-tz":
            options.activity_debrief_tz = require_value()
        elif arg == "--activity-debrief-session-key":
            options.activity_debrief_session_key = require_value()
        elif arg == "--activity-debrief-channel":
            options.activity_debrief_channel = require_value()
        elif arg == "--activity-debrief-to":
            options.activity_debrief_to = require_value()
        elif arg == "--activity-debrief-account":
            options.activity_debrief_account = require_value()
        elif arg == "--activity-debrief-name":
            options.activity_debrief_name = require_value()
        elif arg == "--activity-debrief-message":
            options.activity_debrief_message = require_value()
        elif arg == "--activity-debrief-model":
            options.activity_debrief_model = require_value()
        elif arg == "--no-bootstrap":
            options.with_bootstrap = False
            index += 1
        elif arg == "--preserve-agent-core":
            options.preserve_agent_core = True
            index += 1
        elif arg == "--skip-package-install":
            options.skip_package_install = True
            index += 1
        elif arg == "--dry-run":
            options.dry_run = True
            index += 1
        elif arg == "--quiet":
            options.quiet = True
            index += 1
        elif arg in {"-h", "--help"}:
            print(USAGE)
            raise SystemExit(0)
        elif arg in {"--new-agent", "--agent-name"}:
            raise InstallerError(
                "Creating a new OpenClaw agent is no longer supported by this installer. "
                "Choose --agent main or an existing agent id."
            )
        else:
            raise InstallerError(f"Unknown option: {arg}")
    return options


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    repo_dir = Path(__file__).resolve().parent.parent
    try:
        options = parse_args(raw_argv, repo_dir)
        Installer(options).run()
        return 0
    except InstallerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
