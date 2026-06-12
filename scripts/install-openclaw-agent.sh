#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
HOME_DIR="${HOME:-$(cd ~ && pwd)}"
CONFIG_PATH_DEFAULT="${OPENCLAW_CONFIG:-$HOME_DIR/.openclaw/openclaw.json}"
CONFIG_PATH="$CONFIG_PATH_DEFAULT"
WORKSPACE_DIR="${OPENCLAW_WORKSPACE:-}"
INSTALL_ROOT="${OPENCLAW_INSTALL_ROOT:-}"
PYTHON_BIN=""
DRY_RUN=0
WITH_BOOTSTRAP=1
PRESERVE_AGENT_CORE=0
SKIP_PACKAGE_INSTALL=0
QUIET=0
REQUESTED_INSTALL_MODE="auto"
TARGET_AGENT_ID=""
UPDATE_SKILLS_MODE="auto"
GARMIN_SKILLS=()
SELECTED_AGENT_ID=""
SELECTED_AGENT_NAME=""
SELECTED_AGENT_WORKSPACE=""
SELECTED_AGENT_DIR=""
SELECTED_AGENT_MODEL=""
SELECTED_SKILLS_MODE=""
SELECTED_SKILLS_CSV=""
PATCH_SKILLS_ALLOWLIST=0
SKIP_SYSTEMD_SYNC=0
SKIP_SYSTEMD_EXPORT=0
SKIP_WEEKLY_PLANNING_CRON=0
SYNC_ON_CALENDAR="daily"
EXPORT_ON_CALENDAR="daily"
SYNC_LOOKBACK_DAYS=3
WEEKLY_PLANNING_ON_CALENDAR="0 18 * * 0"
WEEKLY_PLANNING_TZ="UTC"
WEEKLY_PLANNING_SESSION_KEY=""
WEEKLY_PLANNING_CHANNEL=""
WEEKLY_PLANNING_TO=""
WEEKLY_PLANNING_ACCOUNT=""
WEEKLY_PLANNING_NAME=""
WEEKLY_PLANNING_MESSAGE=""
WEEKLY_PLANNING_MODEL=""
INSTALL_MODE="install"
COACH_CONFIG_PATH=""
MANIFEST_PATH=""
PREVIOUS_BACKUP_DIR=""
PREVIOUS_WEEKLY_PLANNING_SESSION_KEY=""
PREVIOUS_WEEKLY_PLANNING_TO=""
PREVIOUS_WEEKLY_PLANNING_CHANNEL=""
PREVIOUS_WEEKLY_PLANNING_ACCOUNT=""
PREVIOUS_WEEKLY_PLANNING_TZ=""
PREVIOUS_WEEKLY_PLANNING_SCHEDULE=""
PREVIOUS_WEEKLY_PLANNING_MODEL=""
PREVIOUS_WEEKLY_PLANNING_NAME=""
INSTALL_APP_VERSION="unknown"
INSTALL_GIT_COMMIT=""
INSTALL_GIT_TAG=""
INSTALL_GIT_SOURCE="local"
INSTALL_GIT_DIRTY="false"
FEATURE_PYTHON_RUNTIME=0
FEATURE_AGENT_FILES=0
FEATURE_DB_MIGRATED=0
FEATURE_SYSTEMD_SYNC=0
FEATURE_SYSTEMD_EXPORT=0
FEATURE_WEEKLY_PLANNING=0
DB_STATUS="not-run"
LAST_SYNC_TIMER_NAME=""
LAST_EXPORT_TIMER_NAME=""
FIELD_SEP=$'\x1f'

usage() {
  cat <<'EOF'
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
  --sync-on-calendar SPEC   systemd OnCalendar spec for Garmin sync (default: daily)
  --export-on-calendar SPEC systemd OnCalendar spec for plan export (default: daily)
  --sync-lookback-days N    lookback passed to sync-garmin (default: 3)
  --skip-systemd-sync       Do not install the Garmin sync systemd user timer
  --skip-systemd-export     Do not install the plan export systemd user timer
  --skip-weekly-planning-cron
                            Do not create/update the weekly planning OpenClaw cron
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
  - persisted config     -> <install-root>/coach-config.json
  - install manifest     -> <install-root>/manifest.json
EOF
}

log() {
  if [[ "$QUIET" -eq 0 ]]; then
    printf '%s\n' "$*"
  fi
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

is_tty() {
  [[ -t 0 && -t 1 ]]
}

join_by() {
  local delim="$1"
  shift || true
  local out=""
  local first=1
  for item in "$@"; do
    if [[ "$first" -eq 1 ]]; then
      out="$item"
      first=0
    else
      out+="$delim$item"
    fi
  done
  printf '%s' "$out"
}

prompt_line() {
  local prompt="$1"
  local default_value="${2:-}"
  local value=""

  if [[ -n "$default_value" ]]; then
    printf '%s [%s]: ' "$prompt" "$default_value" >&2
  else
    printf '%s: ' "$prompt" >&2
  fi

  IFS= read -r value || true
  if [[ -z "$value" ]]; then
    value="$default_value"
  fi
  printf '%s' "$value"
}

prompt_yes_no() {
  local prompt="$1"
  local default_answer="${2:-y}"
  local answer=""

  while true; do
    if [[ "$default_answer" == "y" ]]; then
      printf '%s [Y/n]: ' "$prompt" >&2
    else
      printf '%s [y/N]: ' "$prompt" >&2
    fi
    IFS= read -r answer || true
    answer="${answer:-$default_answer}"
    case "$answer" in
      y|Y|yes|YES) return 0 ;;
      n|N|no|NO) return 1 ;;
    esac
  done
}

load_garmin_skills() {
  GARMIN_SKILLS=()
  while IFS= read -r skill; do
    [[ -n "$skill" ]] && GARMIN_SKILLS+=("$skill")
  done < <(find "$REPO_DIR/agent/skills" -mindepth 1 -maxdepth 1 -type d | sed 's|.*/||' | sort)
}

choose_python() {
  if [[ -n "$PYTHON_BIN" ]]; then
    command -v "$PYTHON_BIN" >/dev/null 2>&1 || die "Python not found: $PYTHON_BIN"
    command -v "$PYTHON_BIN"
    return
  fi

  if command -v python3.13 >/dev/null 2>&1; then
    command -v python3.13
    return
  fi

  if command -v uv >/dev/null 2>&1; then
    log "Python 3.13 not found. Installing via uv..."
    if [[ "$DRY_RUN" -eq 1 ]]; then
      echo '$HOME/.local/bin/python3.13'
      return
    fi
    uv python install 3.13 >/dev/null
    uv python update-shell >/dev/null 2>&1 || true
    uv python find 3.13
    return
  fi

  die "No usable Python found (need python3.13 or uv to install it)."
}

backup_if_exists() {
  local src="$1"
  local backup_root="$2"
  local rel=""

  if [[ -e "$src" || -L "$src" ]]; then
    rel="${src#$WORKSPACE_DIR/}"
    mkdir -p "$backup_root/$(dirname "$rel")"
    cp -a "$src" "$backup_root/$rel"
  fi
}

copy_file() {
  local src="$1"
  local dst="$2"
  local backup_root="$3"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] copy %s -> %s\n' "$src" "$dst"
    return
  fi

  mkdir -p "$(dirname "$dst")"
  backup_if_exists "$dst" "$backup_root"
  install -m 0644 "$src" "$dst"
}

copy_tree_files() {
  local src_root="$1"
  local dst_root="$2"
  local backup_root="$3"

  while IFS= read -r -d '' file; do
    local rel dst
    rel="${file#$src_root/}"
    dst="$dst_root/$rel"
    copy_file "$file" "$dst" "$backup_root"
  done < <(find "$src_root" -type f -print0 | sort -z)
}

copy_tree_files_if_exists() {
  local src_root="$1"
  local dst_root="$2"
  local backup_root="$3"

  if [[ ! -d "$src_root" ]]; then
    log "Skipping missing optional directory: $src_root"
    return
  fi

  copy_tree_files "$src_root" "$dst_root" "$backup_root"
}

sync_app_snapshot() {
  local app_dir="$1"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] refresh app snapshot in %s\n' "$app_dir"
    return
  fi

  rm -rf "$app_dir"
  mkdir -p "$app_dir"

  cp -a "$REPO_DIR/garmin_coach" "$app_dir/"
  cp -a "$REPO_DIR/pyproject.toml" "$app_dir/"
  cp -a "$REPO_DIR/README.md" "$app_dir/"
  cp -a "$REPO_DIR/SPEC.md" "$app_dir/"
}

rewrite_runtime_paths() {
  local rewrite_python="$1"
  local managed_bin_dir="$2"
  shift 2

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] rewrite runtime paths with %s in %s\n' "$managed_bin_dir" "$*"
    return
  fi

  export MANAGED_BIN_DIR="$managed_bin_dir"
  "$rewrite_python" - "$@" <<'PY'
from __future__ import annotations
import os
import pathlib
import re
import sys

managed_bin_dir = os.environ["MANAGED_BIN_DIR"]
pattern = re.compile(r"<EXEC_DIR>")

for raw_path in sys.argv[1:]:
    path = pathlib.Path(raw_path)
    if path.is_dir():
        files = sorted(p for p in path.rglob("*") if p.is_file())
    else:
        files = [path]
    for file in files:
        text = file.read_text(encoding="utf-8")
        updated = pattern.sub(managed_bin_dir, text)
        if updated != text:
            file.write_text(updated, encoding="utf-8")
PY
}

create_venv_and_install() {
  local python_bin="$1"
  local venv_dir="$2"
  local app_dir="$3"

  if [[ "$SKIP_PACKAGE_INSTALL" -eq 1 ]]; then
    log "Skipping package install."
    return
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] create venv %s with %s\n' "$venv_dir" "$python_bin"
    printf '[dry-run] install package from %s\n' "$app_dir"
    return
  fi

  if command -v uv >/dev/null 2>&1; then
    uv venv "$venv_dir" --python "$python_bin" --allow-existing >/dev/null
    uv pip install --python "$venv_dir/bin/python" "$app_dir" >/dev/null
  else
    "$python_bin" -m venv "$venv_dir"
    "$venv_dir/bin/python" -m ensurepip --upgrade >/dev/null
    "$venv_dir/bin/python" -m pip install --upgrade pip >/dev/null
    "$venv_dir/bin/python" -m pip install "$app_dir" >/dev/null
  fi
}

systemd_user_available() {
  command -v systemctl >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1
}

write_systemd_runtime_env() {
  local safe_agent_id="$1"
  local data_dir="$2"
  local backup_root="$3"
  local env_file="$INSTALL_ROOT/systemd/garmin-runtime-${safe_agent_id}.env"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] install runtime env %s\n' "$env_file" >&2
    printf '%s' "$env_file"
    return
  fi

  mkdir -p "$data_dir/tokens" "$INSTALL_ROOT/systemd"
  backup_if_exists "$env_file" "$backup_root"

  cat > "$env_file" <<EOF
GARMIN_COACH_DB=$data_dir/garmin_coach.db
GARMIN_COACH_TOKENS_DIR=$data_dir/tokens
PYTHONUNBUFFERED=1
EOF

  printf '%s' "$env_file"
}

install_systemd_sync_timer() {
  local safe_agent_id="$1"
  local managed_venv_python="$2"
  local backup_root="$3"
  local env_file="$4"
  local service_name="garmin-coach-sync-${safe_agent_id}.service"
  local timer_name="garmin-coach-sync-${safe_agent_id}.timer"
  LAST_SYNC_TIMER_NAME="$timer_name"
  local systemd_user_dir="$HOME_DIR/.config/systemd/user"
  local service_path="$systemd_user_dir/$service_name"
  local timer_path="$systemd_user_dir/$timer_name"

  if [[ "$SKIP_SYSTEMD_SYNC" -eq 1 ]]; then
    log "Skipping Garmin sync systemd timer by request."
    return
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] install systemd user service %s\n' "$service_path"
    printf '[dry-run] install systemd user timer %s (OnCalendar=%s)\n' "$timer_path" "$SYNC_ON_CALENDAR"
    FEATURE_SYSTEMD_SYNC=1
    return
  fi

  if [[ ! -x "$managed_venv_python" ]]; then
    log "Skipping Garmin sync systemd timer because runtime is missing: $managed_venv_python"
    return
  fi

  mkdir -p "$systemd_user_dir"

  backup_if_exists "$service_path" "$backup_root"
  backup_if_exists "$timer_path" "$backup_root"

  cat > "$service_path" <<EOF
[Unit]
Description=Garmin Coach sync ($SELECTED_AGENT_ID)
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
EnvironmentFile=$env_file
WorkingDirectory=$INSTALL_ROOT
ExecStart=$managed_venv_python -m garmin_coach.sync_garmin --lookback-days $SYNC_LOOKBACK_DAYS
EOF

  cat > "$timer_path" <<EOF
[Unit]
Description=Garmin Coach sync timer ($SELECTED_AGENT_ID)

[Timer]
OnCalendar=$SYNC_ON_CALENDAR
Persistent=true
RandomizedDelaySec=15m
Unit=$service_name

[Install]
WantedBy=timers.target
EOF

  if systemd_user_available; then
    systemctl --user daemon-reload
    systemctl --user enable --now "$timer_name" >/dev/null
    log "Systemd sync timer: $timer_name ($SYNC_ON_CALENDAR)"
  else
    log "Installed Garmin sync timer files, but systemctl --user is unavailable in this session."
    log "Enable later with: systemctl --user daemon-reload && systemctl --user enable --now $timer_name"
  fi
  FEATURE_SYSTEMD_SYNC=1
}

install_systemd_export_timer() {
  local safe_agent_id="$1"
  local managed_venv_python="$2"
  local backup_root="$3"
  local env_file="$4"
  local service_name="garmin-coach-export-${safe_agent_id}.service"
  local timer_name="garmin-coach-export-${safe_agent_id}.timer"
  LAST_EXPORT_TIMER_NAME="$timer_name"
  local systemd_user_dir="$HOME_DIR/.config/systemd/user"
  local helper_script="$INSTALL_ROOT/systemd/export-tomorrow-${safe_agent_id}.sh"
  local service_path="$systemd_user_dir/$service_name"
  local timer_path="$systemd_user_dir/$timer_name"

  if [[ "$SKIP_SYSTEMD_EXPORT" -eq 1 ]]; then
    log "Skipping Garmin export systemd timer by request."
    return
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] install export helper %s\n' "$helper_script"
    printf '[dry-run] install systemd user service %s\n' "$service_path"
    printf '[dry-run] install systemd user timer %s (OnCalendar=%s)\n' "$timer_path" "$EXPORT_ON_CALENDAR"
    FEATURE_SYSTEMD_EXPORT=1
    return
  fi

  if [[ ! -x "$managed_venv_python" ]]; then
    log "Skipping Garmin export systemd timer because runtime is missing: $managed_venv_python"
    return
  fi

  mkdir -p "$INSTALL_ROOT/systemd" "$systemd_user_dir"

  backup_if_exists "$helper_script" "$backup_root"
  backup_if_exists "$service_path" "$backup_root"
  backup_if_exists "$timer_path" "$backup_root"

  cat > "$helper_script" <<EOF
#!/usr/bin/env bash
set -euo pipefail

readarray -t export_info < <("$managed_venv_python" - <<'PY'
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

tomorrow="\${export_info[0]}"
week_start="\${export_info[1]}"
plan_id="\${export_info[2]:-}"

if [[ -z "\$plan_id" ]]; then
  echo "No active/draft plan found for week \$week_start; skipping Garmin export."
  exit 0
fi

exec "$managed_venv_python" -m garmin_coach.export_plan_garmin \
  --plan-id "\$plan_id" \
  --start-date "\$tomorrow" \
  --end-date "\$tomorrow"
EOF
  chmod +x "$helper_script"

  cat > "$service_path" <<EOF
[Unit]
Description=Garmin Coach export tomorrow plan ($SELECTED_AGENT_ID)
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
EnvironmentFile=$env_file
WorkingDirectory=$INSTALL_ROOT
ExecStart=$helper_script
EOF

  cat > "$timer_path" <<EOF
[Unit]
Description=Garmin Coach export timer ($SELECTED_AGENT_ID)

[Timer]
OnCalendar=$EXPORT_ON_CALENDAR
Persistent=true
RandomizedDelaySec=15m
Unit=$service_name

[Install]
WantedBy=timers.target
EOF

  if systemd_user_available; then
    systemctl --user daemon-reload
    systemctl --user enable --now "$timer_name" >/dev/null
    log "Systemd export timer: $timer_name ($EXPORT_ON_CALENDAR)"
  else
    log "Installed Garmin export timer files, but systemctl --user is unavailable in this session."
    log "Enable later with: systemctl --user daemon-reload && systemctl --user enable --now $timer_name"
  fi
  FEATURE_SYSTEMD_EXPORT=1
}

config_exists() {
  [[ -f "$CONFIG_PATH" ]]
}

get_default_workspace_from_config() {
  python3 - "$CONFIG_PATH" <<'PY'
from __future__ import annotations
import json
import os
import pathlib
import sys

path = pathlib.Path(os.path.expanduser(sys.argv[1]))
if not path.exists():
    print(os.path.expanduser("~/.openclaw/workspace"))
    raise SystemExit
cfg = json.loads(path.read_text(encoding="utf-8"))
default_ws = cfg.get("agents", {}).get("defaults", {}).get("workspace") or "~/.openclaw/workspace"
print(os.path.expanduser(default_ws))
PY
}

list_agents_from_config() {
  python3 - "$CONFIG_PATH" <<'PY'
from __future__ import annotations
import json
import os
import pathlib
import sys

path = pathlib.Path(os.path.expanduser(sys.argv[1]))
if not path.exists():
    raise SystemExit(0)
cfg = json.loads(path.read_text(encoding="utf-8"))
agents_cfg = cfg.get("agents", {})
defaults = agents_cfg.get("defaults", {})
default_ws = os.path.expanduser(defaults.get("workspace") or "~/.openclaw/workspace")
default_skills = defaults.get("skills")
entries = list(agents_cfg.get("list", []))
by_id = {entry.get("id"): entry for entry in entries if entry.get("id")}
if "main" not in by_id:
    by_id["main"] = {"id": "main", "name": "Main Agent", "workspace": default_ws, "agentDir": os.path.expanduser("~/.openclaw/agents/main/agent"), "_synthetic": True}
ordered_ids = []
if "main" in by_id:
    ordered_ids.append("main")
for entry in entries:
    agent_id = entry.get("id")
    if agent_id and agent_id != "main":
        ordered_ids.append(agent_id)
for agent_id in by_id:
    if agent_id not in ordered_ids:
        ordered_ids.append(agent_id)

def resolve_model(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        primary = value.get("primary")
        if isinstance(primary, str):
            return primary
    return ""

for agent_id in ordered_ids:
    entry = by_id[agent_id]
    name = entry.get("name") or ("Main Agent" if agent_id == "main" else agent_id)
    model = resolve_model(entry.get("model")) or resolve_model(defaults.get("model")) or ""
    workspace = entry.get("workspace")
    if workspace:
        resolved_workspace = os.path.expanduser(workspace)
    else:
        resolved_workspace = default_ws
    agent_dir = os.path.expanduser(entry.get("agentDir") or f"~/.openclaw/agents/{agent_id}/agent")
    if "skills" in entry:
        skills_mode = "agent"
        skills = entry.get("skills") or []
    elif default_skills is not None:
        skills_mode = "defaults"
        skills = default_skills or []
    else:
        skills_mode = "unrestricted"
        skills = []
    synthetic = "1" if entry.get("_synthetic") else "0"
    print(chr(31).join([
        agent_id,
        name,
        model,
        resolved_workspace,
        agent_dir,
        skills_mode,
        ",".join(skills),
        synthetic,
    ]))
PY
}

select_existing_agent_by_id() {
  local wanted_id="$1"
  local line agent_id name model workspace agent_dir skills_mode skills_csv synthetic

  while IFS="$FIELD_SEP" read -r agent_id name model workspace agent_dir skills_mode skills_csv synthetic; do
    [[ -z "$agent_id" ]] && continue
    if [[ "$agent_id" == "$wanted_id" ]]; then
      SELECTED_AGENT_ID="$agent_id"
      SELECTED_AGENT_NAME="$name"
      SELECTED_AGENT_MODEL="$model"
      SELECTED_AGENT_WORKSPACE="$workspace"
      SELECTED_AGENT_DIR="$agent_dir"
      SELECTED_SKILLS_MODE="$skills_mode"
      SELECTED_SKILLS_CSV="$skills_csv"
      return 0
    fi
  done < <(list_agents_from_config)

  return 1
}

interactive_choose_target() {
  local lines=()
  local line agent_id name model workspace agent_dir skills_mode skills_csv synthetic
  local idx=1 choice="" skills_note=""

  while IFS="$FIELD_SEP" read -r agent_id name model workspace agent_dir skills_mode skills_csv synthetic; do
    [[ -z "$agent_id" ]] && continue
    lines+=("$agent_id""$FIELD_SEP""$name""$FIELD_SEP""$model""$FIELD_SEP""$workspace""$FIELD_SEP""$agent_dir""$FIELD_SEP""$skills_mode""$FIELD_SEP""$skills_csv""$FIELD_SEP""$synthetic")
    case "$skills_mode" in
      unrestricted) skills_note="skills: unrestricted" ;;
      agent) skills_note="skills: allowlist agent" ;;
      defaults) skills_note="skills: allowlist defaults" ;;
      *) skills_note="skills: unknown" ;;
    esac
    printf '%s) %s (%s)\n' "$idx" "$agent_id" "$workspace" >&2
    if [[ -n "$model" ]]; then
      printf '   %s | model: %s\n' "$skills_note" "$model" >&2
    else
      printf '   %s\n' "$skills_note" >&2
    fi
    idx=$((idx + 1))
  done < <(list_agents_from_config)

  printf 'q) Quitter\n' >&2

  choice="$(prompt_line 'Choix' '1')"
  case "$choice" in
    q|Q) exit 0 ;;
  esac

  if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice < idx )); then
    line="${lines[$((choice - 1))]}"
    IFS="$FIELD_SEP" read -r agent_id name model workspace agent_dir skills_mode skills_csv synthetic <<< "$line"
    SELECTED_AGENT_ID="$agent_id"
    SELECTED_AGENT_NAME="$name"
    SELECTED_AGENT_MODEL="$model"
    SELECTED_AGENT_WORKSPACE="$workspace"
    SELECTED_AGENT_DIR="$agent_dir"
    SELECTED_SKILLS_MODE="$skills_mode"
    SELECTED_SKILLS_CSV="$skills_csv"
    if [[ -n "$WORKSPACE_DIR" ]]; then
      SELECTED_AGENT_WORKSPACE="$WORKSPACE_DIR"
    fi
    return
  fi

  die "Invalid choice: $choice"
}

maybe_select_target_from_config() {
  local default_workspace=""

  default_workspace="$(get_default_workspace_from_config)"

  if [[ -n "$TARGET_AGENT_ID" ]]; then
    select_existing_agent_by_id "$TARGET_AGENT_ID" || die "Unknown agent id: $TARGET_AGENT_ID"
    if [[ -n "$WORKSPACE_DIR" ]]; then
      SELECTED_AGENT_WORKSPACE="$WORKSPACE_DIR"
    fi
    return
  fi

  if is_tty; then
    interactive_choose_target
    return
  fi

  if select_existing_agent_by_id main; then
    if [[ -n "$WORKSPACE_DIR" ]]; then
      SELECTED_AGENT_WORKSPACE="$WORKSPACE_DIR"
    fi
    return
  fi

  SELECTED_AGENT_ID="main"
  SELECTED_AGENT_NAME="Main Agent"
  SELECTED_AGENT_MODEL=""
  SELECTED_AGENT_WORKSPACE="${WORKSPACE_DIR:-$default_workspace}"
  SELECTED_AGENT_DIR="$HOME_DIR/.openclaw/agents/main/agent"
  SELECTED_SKILLS_MODE="unrestricted"
  SELECTED_SKILLS_CSV=""
}

maybe_prompt_or_set_skill_patch() {
  local current_skills=()
  local merged=()
  local skill=""
  local decision="no"

  case "$UPDATE_SKILLS_MODE" in
    yes) decision="yes" ;;
    no) decision="no" ;;
    auto)
      if [[ "$SELECTED_SKILLS_MODE" == "unrestricted" ]]; then
        decision="no"
      elif is_tty; then
        if prompt_yes_no "L'agent $SELECTED_AGENT_ID a une allowlist de skills. Ajouter les skills Garmin à sa config ?" y; then
          decision="yes"
        else
          decision="no"
        fi
      else
        decision="yes"
      fi
      ;;
    *) die "Invalid --update-skills mode: $UPDATE_SKILLS_MODE" ;;
  esac

  if [[ "$decision" != "yes" ]]; then
    PATCH_SKILLS_ALLOWLIST=0
    return
  fi

  if [[ -n "$SELECTED_SKILLS_CSV" ]]; then
    IFS=',' read -r -a current_skills <<< "$SELECTED_SKILLS_CSV"
  fi

  merged=("${current_skills[@]}")
  for skill in "${GARMIN_SKILLS[@]}"; do
    if [[ " $(printf '%s ' "${merged[@]}") " != *" $skill "* ]]; then
      merged+=("$skill")
    fi
  done

  SELECTED_SKILLS_CSV="$(join_by ',' "${merged[@]}")"
  PATCH_SKILLS_ALLOWLIST=1
}

patch_config_for_target() {
  local merged_skills_csv="$SELECTED_SKILLS_CSV"

  if [[ "$PATCH_SKILLS_ALLOWLIST" -eq 0 ]]; then
    return
  fi

  config_exists || die "Config not found: $CONFIG_PATH"

  CONFIG_PATH="$CONFIG_PATH" \
  AGENT_ID="$SELECTED_AGENT_ID" \
  SKILLS_CSV="$merged_skills_csv" \
  DRY_RUN="$DRY_RUN" \
  python3 - <<'PY'
from __future__ import annotations
import json
import os
import pathlib
import shutil
from datetime import datetime, timezone

config_path = pathlib.Path(os.path.expanduser(os.environ["CONFIG_PATH"]))
agent_id = os.environ["AGENT_ID"]
skills_csv = os.environ.get("SKILLS_CSV", "")
dry_run = os.environ.get("DRY_RUN") == "1"

cfg = json.loads(config_path.read_text(encoding="utf-8"))
agents = cfg.setdefault("agents", {})
entries = agents.setdefault("list", [])
entry = None
for item in entries:
    if item.get("id") == agent_id:
        entry = item
        break
if entry is None:
    raise SystemExit(f"Agent not found in config: {agent_id}")

skills = [item for item in skills_csv.split(",") if item]
entry["skills"] = skills

if dry_run:
    print(f"[dry-run] would update config: {config_path}")
    print(json.dumps(entry, ensure_ascii=False, indent=2))
else:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = config_path.with_name(config_path.name + f".bak.garmin-install.{stamp}")
    shutil.copy2(config_path, backup)
    config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Config updated: {config_path}")
    print(f"Backup: {backup}")
PY
}

resolve_install_source() {
  local git_commit=""
  local git_tag=""
  local git_branch=""
  local git_dirty="false"
  local git_source="local"
  local app_version="unknown"

  if [[ -f "$REPO_DIR/pyproject.toml" ]]; then
    app_version="$(python3 -c 'import tomllib, pathlib; print(tomllib.loads(pathlib.Path("'"$REPO_DIR"'/pyproject.toml").read_text())["project"]["version"])' 2>/dev/null || echo "unknown")"
  fi

  if command -v git >/dev/null 2>&1 && git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git_commit="$(git -C "$REPO_DIR" rev-parse HEAD 2>/dev/null || true)"
    git_tag="$(git -C "$REPO_DIR" describe --tags --exact-match 2>/dev/null || true)"
    git_branch="$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
    if [[ -n "$(git -C "$REPO_DIR" status --porcelain 2>/dev/null || true)" ]]; then
      git_dirty="true"
    fi

    if [[ -n "$git_tag" ]]; then
      git_source="tag"
    elif [[ -n "$git_branch" && "$git_branch" != "HEAD" ]]; then
      git_source="branch"
    elif [[ -n "$git_commit" ]]; then
      git_source="commit"
    fi
  fi

  printf '%s%s%s%s%s%s%s%s%s' "$app_version" "$FIELD_SEP" "$git_commit" "$FIELD_SEP" "$git_tag" "$FIELD_SEP" "$git_source" "$FIELD_SEP" "$git_dirty"
}

load_existing_install_state() {
  local loaded=""
  local detected_mode="install"

  [[ -n "$INSTALL_ROOT" ]] || return
  COACH_CONFIG_PATH="$INSTALL_ROOT/coach-config.json"
  MANIFEST_PATH="$INSTALL_ROOT/manifest.json"

  loaded="$(COACH_CONFIG_PATH="$COACH_CONFIG_PATH" MANIFEST_PATH="$MANIFEST_PATH" python3 - <<'PY'
from __future__ import annotations
import json
import os
import pathlib

manifest_path = pathlib.Path(os.path.expanduser(os.environ["MANIFEST_PATH"]))
config_path = pathlib.Path(os.path.expanduser(os.environ["COACH_CONFIG_PATH"]))

result = {
    "manifest_exists": manifest_path.exists(),
    "config_exists": config_path.exists(),
    "backup_dir": "",
    "weekly_session_key": "",
    "weekly_to": "",
    "weekly_channel": "",
    "weekly_account": "",
    "weekly_tz": "",
    "weekly_schedule": "",
    "weekly_model": "",
    "weekly_name": "",
}

if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result["backup_dir"] = manifest.get("backup", {}).get("last_backup_dir", "")
else:
    legacy_manifest = manifest_path.with_name("manifest.txt")
    if legacy_manifest.exists():
        legacy = {}
        for line in legacy_manifest.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                legacy[key] = value
        result["backup_dir"] = legacy.get("backup_root", "")

if config_path.exists():
    config = json.loads(config_path.read_text(encoding="utf-8"))
    weekly = config.get("weekly_planning", {})
    delivery = weekly.get("delivery", {})
    result["weekly_session_key"] = weekly.get("session_key", "")
    result["weekly_to"] = delivery.get("to", "")
    result["weekly_channel"] = delivery.get("channel", "")
    result["weekly_account"] = delivery.get("account_id", "")
    result["weekly_tz"] = weekly.get("timezone", "")
    result["weekly_schedule"] = weekly.get("schedule", "")
    result["weekly_model"] = weekly.get("model", "")
    result["weekly_name"] = weekly.get("name", "")

print(chr(31).join([
    "1" if result["manifest_exists"] else "0",
    "1" if result["config_exists"] else "0",
    result["backup_dir"],
    result["weekly_session_key"],
    result["weekly_to"],
    result["weekly_channel"],
    result["weekly_account"],
    result["weekly_tz"],
    result["weekly_schedule"],
    result["weekly_model"],
    result["weekly_name"],
]))
PY
)"

  if [[ -n "$loaded" ]]; then
    local manifest_exists config_exists
    IFS="$FIELD_SEP" read -r manifest_exists config_exists PREVIOUS_BACKUP_DIR PREVIOUS_WEEKLY_PLANNING_SESSION_KEY PREVIOUS_WEEKLY_PLANNING_TO PREVIOUS_WEEKLY_PLANNING_CHANNEL PREVIOUS_WEEKLY_PLANNING_ACCOUNT PREVIOUS_WEEKLY_PLANNING_TZ PREVIOUS_WEEKLY_PLANNING_SCHEDULE PREVIOUS_WEEKLY_PLANNING_MODEL PREVIOUS_WEEKLY_PLANNING_NAME <<< "$loaded"
    if [[ "$manifest_exists" == "1" && "$config_exists" == "1" ]]; then
      detected_mode="update"
    elif [[ "$manifest_exists" == "1" || "$config_exists" == "1" || -d "$INSTALL_ROOT/.venv" || -f "$INSTALL_ROOT/data/garmin_coach.db" ]]; then
      detected_mode="repair"
    fi
  fi

  if [[ "$REQUESTED_INSTALL_MODE" != "auto" && "$REQUESTED_INSTALL_MODE" != "$detected_mode" ]]; then
    die "Requested --mode $REQUESTED_INSTALL_MODE but detected $detected_mode for $INSTALL_ROOT. Re-run with --mode $detected_mode or omit --mode."
  fi

  INSTALL_MODE="$detected_mode"
}

resolve_weekly_planning_defaults() {
  if [[ -z "$WEEKLY_PLANNING_NAME" ]]; then
    WEEKLY_PLANNING_NAME="${PREVIOUS_WEEKLY_PLANNING_NAME:-weekly-planning-$SELECTED_AGENT_ID}"
  fi

  if [[ -z "$WEEKLY_PLANNING_MODEL" ]]; then
    WEEKLY_PLANNING_MODEL="${PREVIOUS_WEEKLY_PLANNING_MODEL:-$SELECTED_AGENT_MODEL}"
  fi

  if [[ -z "$WEEKLY_PLANNING_TZ" || "$WEEKLY_PLANNING_TZ" == "UTC" ]]; then
    if [[ -n "$PREVIOUS_WEEKLY_PLANNING_TZ" ]]; then
      WEEKLY_PLANNING_TZ="$PREVIOUS_WEEKLY_PLANNING_TZ"
    elif [[ -n "${TZ:-}" ]]; then
      WEEKLY_PLANNING_TZ="$TZ"
    fi
  fi

  if [[ "$WEEKLY_PLANNING_ON_CALENDAR" == "0 18 * * 0" && -n "$PREVIOUS_WEEKLY_PLANNING_SCHEDULE" ]]; then
    WEEKLY_PLANNING_ON_CALENDAR="$PREVIOUS_WEEKLY_PLANNING_SCHEDULE"
  fi

  if [[ -z "$WEEKLY_PLANNING_SESSION_KEY" ]]; then
    WEEKLY_PLANNING_SESSION_KEY="$PREVIOUS_WEEKLY_PLANNING_SESSION_KEY"
  fi

  if [[ -z "$WEEKLY_PLANNING_TO" ]]; then
    WEEKLY_PLANNING_TO="$PREVIOUS_WEEKLY_PLANNING_TO"
  fi

  if [[ -z "$WEEKLY_PLANNING_CHANNEL" ]]; then
    WEEKLY_PLANNING_CHANNEL="$PREVIOUS_WEEKLY_PLANNING_CHANNEL"
  fi

  if [[ -z "$WEEKLY_PLANNING_ACCOUNT" ]]; then
    WEEKLY_PLANNING_ACCOUNT="$PREVIOUS_WEEKLY_PLANNING_ACCOUNT"
  fi

  if [[ -z "$WEEKLY_PLANNING_MESSAGE" ]]; then
    WEEKLY_PLANNING_MESSAGE="Rendez-vous hebdomadaire de planification. Suis playbooks/weekly_planning.md pour préparer le programme de la semaine à venir : synchronise Garmin si nécessaire, lis objectifs, contraintes, état de forme et plan courant, puis crée ou ajuste le plan local de la semaine cible. Évite les doublons si le plan existe déjà. N'exporte vers Garmin que l'horizon court, sauf demande explicite de l'utilisateur. Termine par un résumé concis de la semaine et les points de vigilance."
  fi
}

prompt_weekly_planning_if_needed() {
  if [[ "$SKIP_WEEKLY_PLANNING_CRON" -eq 1 ]]; then
    return
  fi

  if [[ -n "$WEEKLY_PLANNING_SESSION_KEY" || -n "$WEEKLY_PLANNING_TO" ]]; then
    return
  fi

  if ! is_tty; then
    return
  fi

  if ! prompt_yes_no "Créer aussi le cron OpenClaw de weekly planning pour l'agent $SELECTED_AGENT_ID ?" y; then
    SKIP_WEEKLY_PLANNING_CRON=1
    return
  fi

  WEEKLY_PLANNING_SESSION_KEY="$(prompt_line "Session key cible (recommandé; vide pour utiliser seulement une delivery explicite)" "$WEEKLY_PLANNING_SESSION_KEY")"

  if [[ -z "$WEEKLY_PLANNING_SESSION_KEY" ]]; then
    WEEKLY_PLANNING_CHANNEL="$(prompt_line "Channel de delivery (ex: telegram, discord)" "$WEEKLY_PLANNING_CHANNEL")"
    WEEKLY_PLANNING_TO="$(prompt_line "Destination de delivery (chat/user id)" "$WEEKLY_PLANNING_TO")"
    WEEKLY_PLANNING_ACCOUNT="$(prompt_line "Account id de delivery (optionnel)" "$WEEKLY_PLANNING_ACCOUNT")"
    if [[ -z "$WEEKLY_PLANNING_TO" ]]; then
      log "Skipping weekly planning cron: no session key or delivery destination provided."
      SKIP_WEEKLY_PLANNING_CRON=1
      return
    fi
  fi

  WEEKLY_PLANNING_ON_CALENDAR="$(prompt_line "Expression cron pour le weekly planning" "$WEEKLY_PLANNING_ON_CALENDAR")"
  WEEKLY_PLANNING_TZ="$(prompt_line "Timezone IANA du weekly planning" "$WEEKLY_PLANNING_TZ")"
  WEEKLY_PLANNING_MODEL="$(prompt_line "Model du weekly planning" "$WEEKLY_PLANNING_MODEL")"
}

create_or_update_weekly_planning_cron() {
  local existing_id=""
  local -a cron_cmd=()
  local action_label="create"
  local command_output=""

  resolve_weekly_planning_defaults

  if [[ "$SKIP_WEEKLY_PLANNING_CRON" -eq 1 ]]; then
    log "Skipping weekly planning cron by request."
    return
  fi

  if ! command -v openclaw >/dev/null 2>&1; then
    log "openclaw CLI not found, skipping weekly planning cron creation"
    return
  fi

  prompt_weekly_planning_if_needed

  if [[ "$SKIP_WEEKLY_PLANNING_CRON" -eq 1 ]]; then
    return
  fi

  if [[ -z "$WEEKLY_PLANNING_SESSION_KEY" && -z "$WEEKLY_PLANNING_TO" ]]; then
    log "Skipping weekly planning cron: pass --weekly-planning-session-key or --weekly-planning-to (with optional channel/account), or run interactively."
    return
  fi

  existing_id="$(WEEKLY_PLANNING_NAME="$WEEKLY_PLANNING_NAME" SELECTED_AGENT_ID="$SELECTED_AGENT_ID" python3 - <<'PY'
from __future__ import annotations
import json
import os
import subprocess

target_name = os.environ.get("WEEKLY_PLANNING_NAME", "")
target_agent = os.environ.get("SELECTED_AGENT_ID", "")

try:
    raw = subprocess.check_output(["openclaw", "cron", "list", "--json"], stderr=subprocess.DEVNULL)
    data = json.loads(raw)
except Exception:
    print("")
    raise SystemExit

for job in data.get("jobs", []):
    if job.get("name") == target_name and job.get("agentId") == target_agent:
        print(job.get("id", ""))
        break
else:
    print("")
PY
)"

  if [[ -n "$existing_id" ]]; then
    action_label="update"
    cron_cmd=(
      openclaw cron edit "$existing_id"
      --cron "$WEEKLY_PLANNING_ON_CALENDAR"
      --name "$WEEKLY_PLANNING_NAME"
      --agent "$SELECTED_AGENT_ID"
      --message "$WEEKLY_PLANNING_MESSAGE"
      --thinking high
      --light-context
    )
  else
    cron_cmd=(
      openclaw cron add
      --cron "$WEEKLY_PLANNING_ON_CALENDAR"
      --name "$WEEKLY_PLANNING_NAME"
      --agent "$SELECTED_AGENT_ID"
      --message "$WEEKLY_PLANNING_MESSAGE"
      --thinking high
      --light-context
    )
  fi

  if [[ -n "$WEEKLY_PLANNING_MODEL" ]]; then
    cron_cmd+=(--model "$WEEKLY_PLANNING_MODEL")
  fi

  if [[ -n "$WEEKLY_PLANNING_TZ" ]]; then
    cron_cmd+=(--tz "$WEEKLY_PLANNING_TZ")
  fi

  if [[ -n "$WEEKLY_PLANNING_SESSION_KEY" ]]; then
    cron_cmd+=(--session-key "$WEEKLY_PLANNING_SESSION_KEY")
  else
    cron_cmd+=(--session isolated)
  fi

  if [[ -n "$WEEKLY_PLANNING_TO" ]]; then
    cron_cmd+=(--announce --to "$WEEKLY_PLANNING_TO")
    if [[ -n "$WEEKLY_PLANNING_CHANNEL" ]]; then
      cron_cmd+=(--channel "$WEEKLY_PLANNING_CHANNEL")
    fi
    if [[ -n "$WEEKLY_PLANNING_ACCOUNT" ]]; then
      cron_cmd+=(--account "$WEEKLY_PLANNING_ACCOUNT")
    fi
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] create/update weekly planning cron: %s\n' "$WEEKLY_PLANNING_NAME"
    FEATURE_WEEKLY_PLANNING=1
    return
  fi

  if [[ -n "$existing_id" ]]; then
    log "Updating existing weekly planning cron: $WEEKLY_PLANNING_NAME"
  else
    log "Creating weekly planning cron: $WEEKLY_PLANNING_NAME"
  fi

  if command_output="$("${cron_cmd[@]}" 2>&1)"; then
    [[ -n "$command_output" ]] && printf '%s\n' "$command_output"
    FEATURE_WEEKLY_PLANNING=1
  elif [[ -n "$existing_id" ]]; then
    log "Warning: Failed to update existing weekly planning cron; keeping current job."
    [[ -n "$command_output" ]] && printf '%s\n' "$command_output" >&2
  else
    log "Warning: Failed to create weekly planning cron"
    [[ -n "$command_output" ]] && printf '%s\n' "$command_output" >&2
  fi
}

write_persisted_coach_config() {
  local backup_root="$1"

  [[ -n "$COACH_CONFIG_PATH" ]] || return

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] write coach config %s\n' "$COACH_CONFIG_PATH"
    return
  fi

  mkdir -p "$(dirname "$COACH_CONFIG_PATH")"
  backup_if_exists "$COACH_CONFIG_PATH" "$backup_root"

  COACH_CONFIG_PATH="$COACH_CONFIG_PATH" \
  SELECTED_AGENT_ID="$SELECTED_AGENT_ID" \
  WEEKLY_PLANNING_NAME="$WEEKLY_PLANNING_NAME" \
  WEEKLY_PLANNING_MODEL="$WEEKLY_PLANNING_MODEL" \
  WEEKLY_PLANNING_TZ="$WEEKLY_PLANNING_TZ" \
  WEEKLY_PLANNING_ON_CALENDAR="$WEEKLY_PLANNING_ON_CALENDAR" \
  WEEKLY_PLANNING_SESSION_KEY="$WEEKLY_PLANNING_SESSION_KEY" \
  WEEKLY_PLANNING_TO="$WEEKLY_PLANNING_TO" \
  WEEKLY_PLANNING_CHANNEL="$WEEKLY_PLANNING_CHANNEL" \
  WEEKLY_PLANNING_ACCOUNT="$WEEKLY_PLANNING_ACCOUNT" \
  FEATURE_SYSTEMD_SYNC="$FEATURE_SYSTEMD_SYNC" \
  FEATURE_SYSTEMD_EXPORT="$FEATURE_SYSTEMD_EXPORT" \
  FEATURE_WEEKLY_PLANNING="$FEATURE_WEEKLY_PLANNING" \
  python3 - <<'PY'
from __future__ import annotations
import json
import os
import pathlib

path = pathlib.Path(os.environ["COACH_CONFIG_PATH"])
delivery = {}
if os.environ.get("WEEKLY_PLANNING_TO"):
    delivery["to"] = os.environ["WEEKLY_PLANNING_TO"]
if os.environ.get("WEEKLY_PLANNING_CHANNEL"):
    delivery["channel"] = os.environ["WEEKLY_PLANNING_CHANNEL"]
if os.environ.get("WEEKLY_PLANNING_ACCOUNT"):
    delivery["account_id"] = os.environ["WEEKLY_PLANNING_ACCOUNT"]

config = {
    "schema_version": 1,
    "agent_id": os.environ["SELECTED_AGENT_ID"],
    "weekly_planning": {
        "enabled": os.environ.get("FEATURE_WEEKLY_PLANNING") == "1",
        "name": os.environ.get("WEEKLY_PLANNING_NAME", ""),
        "model": os.environ.get("WEEKLY_PLANNING_MODEL", ""),
        "timezone": os.environ.get("WEEKLY_PLANNING_TZ", ""),
        "schedule": os.environ.get("WEEKLY_PLANNING_ON_CALENDAR", ""),
        "session_key": os.environ.get("WEEKLY_PLANNING_SESSION_KEY", ""),
        "delivery": delivery,
    },
    "garmin": {
        "sync_enabled": os.environ.get("FEATURE_SYSTEMD_SYNC") == "1",
        "export_tomorrow_enabled": os.environ.get("FEATURE_SYSTEMD_EXPORT") == "1",
    },
}

path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
}

write_manifest() {
  local ts="$1"
  local backup_root="$2"
  local app_version git_commit git_tag git_source git_dirty

  [[ -n "$MANIFEST_PATH" ]] || return
  IFS="$FIELD_SEP" read -r app_version git_commit git_tag git_source git_dirty <<< "$(resolve_install_source)"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] write manifest %s\n' "$MANIFEST_PATH"
    return
  fi

  mkdir -p "$(dirname "$MANIFEST_PATH")"
  backup_if_exists "$MANIFEST_PATH" "$backup_root"

  MANIFEST_PATH="$MANIFEST_PATH" \
  APP_VERSION="$app_version" \
  GIT_COMMIT="$git_commit" \
  GIT_TAG="$git_tag" \
  GIT_SOURCE="$git_source" \
  GIT_DIRTY="$git_dirty" \
  SELECTED_AGENT_ID="$SELECTED_AGENT_ID" \
  CONFIG_PATH="$CONFIG_PATH" \
  WORKSPACE_DIR="$WORKSPACE_DIR" \
  INSTALL_ROOT="$INSTALL_ROOT" \
  DATA_DIR="$INSTALL_ROOT/data" \
  MANAGED_VENV="$INSTALL_ROOT/.venv/bin/python" \
  FEATURE_PYTHON_RUNTIME="$FEATURE_PYTHON_RUNTIME" \
  FEATURE_AGENT_FILES="$FEATURE_AGENT_FILES" \
  FEATURE_DB_MIGRATED="$FEATURE_DB_MIGRATED" \
  FEATURE_SYSTEMD_SYNC="$FEATURE_SYSTEMD_SYNC" \
  FEATURE_SYSTEMD_EXPORT="$FEATURE_SYSTEMD_EXPORT" \
  FEATURE_WEEKLY_PLANNING="$FEATURE_WEEKLY_PLANNING" \
  BACKUP_ROOT="$backup_root" \
  INSTALLED_AT="$ts" \
  INSTALL_MODE="$INSTALL_MODE" \
  python3 - <<'PY'
from __future__ import annotations
import json
import os
import pathlib

path = pathlib.Path(os.environ["MANIFEST_PATH"])
manifest = {
    "schema_version": 1,
    "install_mode": os.environ["INSTALL_MODE"],
    "app_version": os.environ.get("APP_VERSION", "unknown"),
    "git": {
        "tag": os.environ.get("GIT_TAG", ""),
        "commit": os.environ.get("GIT_COMMIT", ""),
        "source": os.environ.get("GIT_SOURCE", "local"),
        "dirty": os.environ.get("GIT_DIRTY", "false") == "true",
    },
    "paths": {
        "workspace_dir": os.environ["WORKSPACE_DIR"],
        "install_root": os.environ["INSTALL_ROOT"],
        "data_dir": os.environ["DATA_DIR"],
        "managed_venv": os.environ["MANAGED_VENV"],
    },
    "target": {
        "agent_id": os.environ["SELECTED_AGENT_ID"],
        "openclaw_config_path": os.environ["CONFIG_PATH"],
    },
    "features": {
        "python_runtime": os.environ.get("FEATURE_PYTHON_RUNTIME") == "1",
        "agent_files": os.environ.get("FEATURE_AGENT_FILES") == "1",
        "db_migrated": os.environ.get("FEATURE_DB_MIGRATED") == "1",
        "systemd_sync": os.environ.get("FEATURE_SYSTEMD_SYNC") == "1",
        "systemd_export": os.environ.get("FEATURE_SYSTEMD_EXPORT") == "1",
        "weekly_planning_cron": os.environ.get("FEATURE_WEEKLY_PLANNING") == "1",
    },
    "backup": {
        "last_backup_dir": os.environ["BACKUP_ROOT"],
    },
    "installed_at": os.environ["INSTALLED_AT"],
}
path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
}

print_install_summary() {
  log "Install done."
  log "Mode:           $INSTALL_MODE"
  log "Agent:          $SELECTED_AGENT_ID"
  log "Version:        $INSTALL_APP_VERSION"
  log "Source:         $INSTALL_GIT_SOURCE${INSTALL_GIT_TAG:+ ($INSTALL_GIT_TAG)}"
  log "Workspace:      $WORKSPACE_DIR"
  log "Install root:   $INSTALL_ROOT"
  log "DB status:      $DB_STATUS"
  log "Config:         $COACH_CONFIG_PATH"
  log "Manifest:       $MANIFEST_PATH"
  log "Backup root:    $1"
  log "Managed bin dir: $INSTALL_ROOT/.venv/bin"
  if [[ "$FEATURE_SYSTEMD_SYNC" -eq 1 ]]; then
    log "Systemd sync:   ${LAST_SYNC_TIMER_NAME:-enabled}"
  else
    log "Systemd sync:   skipped"
  fi
  if [[ "$FEATURE_SYSTEMD_EXPORT" -eq 1 ]]; then
    log "Systemd export: ${LAST_EXPORT_TIMER_NAME:-enabled}"
  else
    log "Systemd export: skipped"
  fi
  if [[ "$FEATURE_WEEKLY_PLANNING" -eq 1 ]]; then
    log "Weekly cron:    $WEEKLY_PLANNING_NAME"
  else
    log "Weekly cron:    skipped"
  fi
}

main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --config)
        CONFIG_PATH="$2"
        shift 2
        ;;
      --mode)
        REQUESTED_INSTALL_MODE="$2"
        case "$REQUESTED_INSTALL_MODE" in
          auto|install|update|repair) ;;
          *) die "Invalid --mode: $REQUESTED_INSTALL_MODE (expected auto|install|update|repair)" ;;
        esac
        shift 2
        ;;
      --workspace)
        WORKSPACE_DIR="$2"
        shift 2
        ;;
      --install-root)
        INSTALL_ROOT="$2"
        shift 2
        ;;
      --python)
        PYTHON_BIN="$2"
        shift 2
        ;;
      --agent)
        TARGET_AGENT_ID="$2"
        shift 2
        ;;
      --update-skills)
        UPDATE_SKILLS_MODE="$2"
        shift 2
        ;;
      --sync-on-calendar)
        SYNC_ON_CALENDAR="$2"
        shift 2
        ;;
      --export-on-calendar)
        EXPORT_ON_CALENDAR="$2"
        shift 2
        ;;
      --sync-lookback-days)
        SYNC_LOOKBACK_DAYS="$2"
        shift 2
        ;;
      --skip-systemd-sync)
        SKIP_SYSTEMD_SYNC=1
        shift
        ;;
      --skip-systemd-export)
        SKIP_SYSTEMD_EXPORT=1
        shift
        ;;
      --skip-weekly-planning-cron)
        SKIP_WEEKLY_PLANNING_CRON=1
        shift
        ;;
      --weekly-planning-on-calendar)
        WEEKLY_PLANNING_ON_CALENDAR="$2"
        shift 2
        ;;
      --weekly-planning-tz)
        WEEKLY_PLANNING_TZ="$2"
        shift 2
        ;;
      --weekly-planning-session-key)
        WEEKLY_PLANNING_SESSION_KEY="$2"
        shift 2
        ;;
      --weekly-planning-channel)
        WEEKLY_PLANNING_CHANNEL="$2"
        shift 2
        ;;
      --weekly-planning-to)
        WEEKLY_PLANNING_TO="$2"
        shift 2
        ;;
      --weekly-planning-account)
        WEEKLY_PLANNING_ACCOUNT="$2"
        shift 2
        ;;
      --weekly-planning-name)
        WEEKLY_PLANNING_NAME="$2"
        shift 2
        ;;
      --weekly-planning-message)
        WEEKLY_PLANNING_MESSAGE="$2"
        shift 2
        ;;
      --weekly-planning-model)
        WEEKLY_PLANNING_MODEL="$2"
        shift 2
        ;;
      --no-bootstrap)
        WITH_BOOTSTRAP=0
        shift
        ;;
      --preserve-agent-core)
        PRESERVE_AGENT_CORE=1
        shift
        ;;
      --skip-package-install)
        SKIP_PACKAGE_INSTALL=1
        shift
        ;;
      --dry-run)
        DRY_RUN=1
        shift
        ;;
      --quiet)
        QUIET=1
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      --new-agent|--agent-name)
        die "Creating a new OpenClaw agent is no longer supported by this installer. Choose --agent main or an existing agent id."
        ;;
      *)
        die "Unknown option: $1"
        ;;
    esac
  done

  load_garmin_skills

  if ! config_exists; then
    if [[ -n "$TARGET_AGENT_ID" ]]; then
      die "Cannot use --agent because OpenClaw config was not found at $CONFIG_PATH."
    fi
    log "Warning: OpenClaw configuration file not found at: $CONFIG_PATH"
    if [[ -z "$WORKSPACE_DIR" ]]; then
      if is_tty; then
        log "No OpenClaw workspace is specified."
        WORKSPACE_DIR="$(prompt_line 'OpenClaw workspace absolute path' '')"
        if [[ -z "$WORKSPACE_DIR" ]]; then
          die "OpenClaw workspace is required for installation."
        fi
        WORKSPACE_DIR="${WORKSPACE_DIR/#\~/$HOME_DIR}"
      else
        die "No OpenClaw configuration found at $CONFIG_PATH and no workspace specified via --workspace."
      fi
    fi
    SELECTED_AGENT_ID="main"
    SELECTED_AGENT_NAME="Main Agent"
    SELECTED_AGENT_MODEL=""
    SELECTED_AGENT_WORKSPACE="$WORKSPACE_DIR"
    SELECTED_AGENT_DIR="$HOME_DIR/.openclaw/agents/main/agent"
    SELECTED_SKILLS_MODE="unrestricted"
    SELECTED_SKILLS_CSV=""
    PATCH_SKILLS_ALLOWLIST=0
  else
    if [[ -n "$WORKSPACE_DIR" && -z "$TARGET_AGENT_ID" && ! is_tty ]]; then
      SELECTED_AGENT_ID="main"
      SELECTED_AGENT_NAME="Main Agent"
      SELECTED_AGENT_MODEL=""
      SELECTED_AGENT_WORKSPACE="$WORKSPACE_DIR"
      SELECTED_AGENT_DIR="$HOME_DIR/.openclaw/agents/main/agent"
      SELECTED_SKILLS_MODE="unrestricted"
      SELECTED_SKILLS_CSV=""
    else
      maybe_select_target_from_config
    fi
  fi

  [[ -n "$SELECTED_AGENT_WORKSPACE" ]] || die "No target workspace resolved"
  WORKSPACE_DIR="$SELECTED_AGENT_WORKSPACE"
  if [[ -z "$INSTALL_ROOT" ]]; then
    INSTALL_ROOT="$WORKSPACE_DIR/.garmin-coach-agent"
  fi
  load_existing_install_state

  maybe_prompt_or_set_skill_patch
  patch_config_for_target

  local ts backup_root app_dir data_dir managed_python safe_agent_id runtime_env_file
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  backup_root="$INSTALL_ROOT/backups/$ts"
  app_dir="$INSTALL_ROOT/app"
  data_dir="$INSTALL_ROOT/data"
  managed_python="$(choose_python)"
  safe_agent_id="${SELECTED_AGENT_ID//[^A-Za-z0-9_.-]/-}"

  IFS="$FIELD_SEP" read -r INSTALL_APP_VERSION INSTALL_GIT_COMMIT INSTALL_GIT_TAG INSTALL_GIT_SOURCE INSTALL_GIT_DIRTY <<< "$(resolve_install_source)"

  log "Agent:          $SELECTED_AGENT_ID"
  log "Workspace:      $WORKSPACE_DIR"
  log "Install root:   $INSTALL_ROOT"
  log "Python:         $managed_python"
  log "Backup root:    $backup_root"

  if [[ "$PATCH_SKILLS_ALLOWLIST" -eq 1 ]]; then
    log "Skills config:  patched allowlist for $SELECTED_AGENT_ID"
  fi

  if [[ "$DRY_RUN" -eq 0 ]]; then
    mkdir -p "$WORKSPACE_DIR" "$INSTALL_ROOT" "$backup_root" "$data_dir/tokens"
  fi

  sync_app_snapshot "$app_dir"
  create_venv_and_install "$managed_python" "$INSTALL_ROOT/.venv" "$app_dir"
  if [[ "$DRY_RUN" -eq 0 && -x "$INSTALL_ROOT/.venv/bin/python" ]]; then
    FEATURE_PYTHON_RUNTIME=1
  fi

  local root_files=(AGENTS.md TOOLS.md)
  if [[ "$WITH_BOOTSTRAP" -eq 1 ]]; then
    root_files+=(BOOTSTRAP.md)
  fi

  local core_files=(HEARTBEAT.md IDENTITY.md SOUL.md)
  for name in "${core_files[@]}"; do
    if [[ "$PRESERVE_AGENT_CORE" -eq 1 && -f "$WORKSPACE_DIR/$name" ]]; then
      log "Skipping $name (preserve-agent-core is set)"
    else
      root_files+=("$name")
    fi
  done

  local name
  for name in "${root_files[@]}"; do
    copy_file "$REPO_DIR/agent/$name" "$WORKSPACE_DIR/$name" "$backup_root"
  done

  copy_tree_files_if_exists "$REPO_DIR/agent/playbooks" "$WORKSPACE_DIR/playbooks" "$backup_root"
  copy_tree_files "$REPO_DIR/agent/skills" "$WORKSPACE_DIR/skills" "$backup_root"
  FEATURE_AGENT_FILES=1

  local rewrite_targets=("$WORKSPACE_DIR/TOOLS.md" "$WORKSPACE_DIR/skills")
  if [[ "$WITH_BOOTSTRAP" -eq 1 ]]; then
    rewrite_targets+=("$WORKSPACE_DIR/BOOTSTRAP.md")
  fi

  rewrite_runtime_paths "$managed_python" "$INSTALL_ROOT/.venv/bin/python" "${rewrite_targets[@]}"

  local cmds=(
    auth-garmin create-constraint create-goal create-plan-draft
    create-plan-session delete-constraint delete-plan-session
    export-plan-garmin get-activities get-constraints get-current-plan
    get-fitness-state get-goals set-constraint-status set-plan-session-status
    set-plan-status sync-garmin
  )

  if [[ "$DRY_RUN" -eq 0 ]]; then
    mkdir -p "$WORKSPACE_DIR/bin"
    mkdir -p "$HOME_DIR/.local/bin"
    for cmd in "${cmds[@]}"; do
      ln -sf "$INSTALL_ROOT/.venv/bin/$cmd" "$WORKSPACE_DIR/bin/$cmd"
      ln -sf "$INSTALL_ROOT/.venv/bin/$cmd" "$HOME_DIR/.local/bin/$cmd"
    done
  else
    printf '[dry-run] create symlinks in %s/bin and %s/.local/bin\n' "$WORKSPACE_DIR" "$HOME_DIR"
  fi
  if [[ "$DRY_RUN" -eq 0 ]]; then
    local app_version="unknown"
    if [[ -f "$REPO_DIR/pyproject.toml" ]]; then
      app_version="$(python3 -c 'import re; match=re.search(r"version\s*=\s*\"([^\"]+)\"", open("'"$REPO_DIR"'/pyproject.toml").read()); print(match.group(1) if match else "unknown")' 2>/dev/null || echo "unknown")"
    fi

    cat > "$INSTALL_ROOT/manifest.txt" <<EOF
app_version=$app_version
installed_at=$ts
repo_dir=$REPO_DIR
config_path=$CONFIG_PATH
agent_id=$SELECTED_AGENT_ID
workspace_dir=$WORKSPACE_DIR
install_root=$INSTALL_ROOT
data_dir=$data_dir
managed_python=$managed_python
managed_venv=$INSTALL_ROOT/.venv/bin/python
backup_root=$backup_root
EOF
  fi

  if [[ "$DRY_RUN" -eq 0 && -x "$INSTALL_ROOT/.venv/bin/python" ]]; then
    log "Running database migrations..."
    if migration_output="$(GARMIN_COACH_DB="$data_dir/garmin_coach.db" "$INSTALL_ROOT/.venv/bin/python" - <<'EOF'
import sys
try:
    from garmin_coach.db import run_migrations, get_connection
    conn = get_connection()
    applied = run_migrations(conn)
    if applied:
        print(f"MIGRATED:{','.join(applied)}")
    else:
        print("UP_TO_DATE")
    conn.close()
except Exception as e:
    print(f"Error during migrations: {e}", file=sys.stderr)
    sys.exit(1)
EOF
)"; then
      printf '%s\n' "$migration_output"
      FEATURE_DB_MIGRATED=1
      if [[ "$migration_output" == MIGRATED:* ]]; then
        DB_STATUS="migrated"
      else
        DB_STATUS="up-to-date"
      fi
    else
      DB_STATUS="failed"
      exit 1
    fi
  elif [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] run database migrations\n'
    DB_STATUS="dry-run"
  else
    DB_STATUS="skipped"
  fi

  runtime_env_file="$(write_systemd_runtime_env "$safe_agent_id" "$data_dir" "$backup_root")"
  install_systemd_sync_timer "$safe_agent_id" "$INSTALL_ROOT/.venv/bin/python" "$backup_root" "$runtime_env_file"
  install_systemd_export_timer "$safe_agent_id" "$INSTALL_ROOT/.venv/bin/python" "$backup_root" "$runtime_env_file"

  create_or_update_weekly_planning_cron

  write_persisted_coach_config "$backup_root"
  write_manifest "$ts" "$backup_root"

  print_install_summary "$backup_root"
}

main "$@"
