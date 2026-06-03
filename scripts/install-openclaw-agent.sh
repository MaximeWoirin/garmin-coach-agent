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
SKIP_PACKAGE_INSTALL=0
QUIET=0
TARGET_AGENT_ID=""
NEW_AGENT_ID=""
NEW_AGENT_NAME=""
UPDATE_SKILLS_MODE="auto"
GARMIN_SKILLS=()
SELECTED_AGENT_ID=""
SELECTED_AGENT_NAME=""
SELECTED_AGENT_WORKSPACE=""
SELECTED_AGENT_DIR=""
SELECTED_SKILLS_MODE=""
SELECTED_SKILLS_CSV=""
CREATE_AGENT_CONFIG=0
PATCH_SKILLS_ALLOWLIST=0

usage() {
  cat <<'EOF'
Install Garmin Coach Agent into an OpenClaw workspace.

Usage:
  scripts/install-openclaw-agent.sh [options]

Options:
  --config PATH             OpenClaw config path (default: ~/.openclaw/openclaw.json)
  --workspace DIR           Force workspace target, skip agent auto-selection
  --install-root DIR        Managed install dir for app snapshot + venv
  --python BIN              Python binary to use for venv creation
  --agent ID                Install into an existing OpenClaw agent
  --new-agent ID            Create config entry for a new agent, then install into it
  --agent-name NAME         Name to use when creating a new agent
  --update-skills MODE      auto|yes|no (patch skill allowlist when target agent is restricted)
  --no-bootstrap            Do not install BOOTSTRAP.md
  --skip-package-install    Copy files only; skip venv/package install
  --dry-run                 Show actions without writing
  --quiet                   Reduce logs
  -h, --help                Show help

Default behavior:
  - if a config is found and stdin/stdout are interactive, the script lists existing agents
  - you can pick main, another existing agent, or create a new one
  - if the chosen agent has a skill allowlist, the script can append Garmin skills to it

What it installs:
  - agent files -> <workspace>/
  - playbooks   -> <workspace>/playbooks/
  - skills      -> <workspace>/skills/
  - app snapshot + venv -> <install-root>/
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
  done < <(find "$REPO_DIR/agent/skills" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
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

sync_app_snapshot() {
  local app_dir="$1"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] refresh app snapshot in %s\n' "$app_dir"
    return
  fi

  rm -rf "$app_dir"
  mkdir -p "$app_dir"

  cp -a "$REPO_DIR/garmin_coach" "$app_dir/"
  cp -a "$REPO_DIR/migrations" "$app_dir/"
  cp -a "$REPO_DIR/bin" "$app_dir/"
  cp -a "$REPO_DIR/pyproject.toml" "$app_dir/"
  cp -a "$REPO_DIR/README.md" "$app_dir/"
  cp -a "$REPO_DIR/SPEC.md" "$app_dir/"
}

rewrite_runtime_paths() {
  local rewrite_python="$1"
  local managed_python="$2"
  shift 2

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] rewrite runtime paths with %s in %s\n' "$managed_python" "$*"
    return
  fi

  export MANAGED_PYTHON="$managed_python"
  "$rewrite_python" - "$@" <<'PY'
from __future__ import annotations
import os
import pathlib
import re
import sys

managed_python = os.environ["MANAGED_PYTHON"]
pattern = re.compile(r"\bpython -m garmin_coach\.")

for raw_path in sys.argv[1:]:
    path = pathlib.Path(raw_path)
    if path.is_dir():
        files = sorted(p for p in path.rglob("*") if p.is_file())
    else:
        files = [path]
    for file in files:
        text = file.read_text(encoding="utf-8")
        updated = pattern.sub(f"{managed_python} -m garmin_coach.", text)
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
    uv venv "$venv_dir" --python "$python_bin" >/dev/null
    uv pip install --python "$venv_dir/bin/python" "$app_dir" >/dev/null
  else
    "$python_bin" -m venv "$venv_dir"
    "$venv_dir/bin/python" -m ensurepip --upgrade >/dev/null
    "$venv_dir/bin/python" -m pip install --upgrade pip >/dev/null
    "$venv_dir/bin/python" -m pip install "$app_dir" >/dev/null
  fi
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
for agent_id in ordered_ids:
    entry = by_id[agent_id]
    name = entry.get("name") or ("Main Agent" if agent_id == "main" else agent_id)
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
    print("\t".join([
        agent_id,
        name,
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
  local line agent_id name workspace agent_dir skills_mode skills_csv synthetic

  while IFS=$'\t' read -r agent_id name workspace agent_dir skills_mode skills_csv synthetic; do
    [[ -z "$agent_id" ]] && continue
    if [[ "$agent_id" == "$wanted_id" ]]; then
      SELECTED_AGENT_ID="$agent_id"
      SELECTED_AGENT_NAME="$name"
      SELECTED_AGENT_WORKSPACE="$workspace"
      SELECTED_AGENT_DIR="$agent_dir"
      SELECTED_SKILLS_MODE="$skills_mode"
      SELECTED_SKILLS_CSV="$skills_csv"
      return 0
    fi
  done < <(list_agents_from_config)

  return 1
}

configure_new_agent_target() {
  local default_workspace="$1"
  local default_agent_dir=""
  local default_name=""

  if [[ -z "$NEW_AGENT_ID" ]]; then
    NEW_AGENT_ID="$(prompt_line 'Nouvel agent id' 'coach-garmin')"
  fi
  [[ "$NEW_AGENT_ID" =~ ^[A-Za-z0-9._-]+$ ]] || die "Invalid agent id: $NEW_AGENT_ID"

  default_name="$NEW_AGENT_NAME"
  if [[ -z "$default_name" ]]; then
    default_name="Garmin Coach"
  fi
  if is_tty; then
    NEW_AGENT_NAME="$(prompt_line 'Nom affiché (optionnel)' "$default_name")"
  elif [[ -z "$NEW_AGENT_NAME" ]]; then
    NEW_AGENT_NAME="$default_name"
  fi

  if [[ -n "$WORKSPACE_DIR" ]]; then
    SELECTED_AGENT_WORKSPACE="$WORKSPACE_DIR"
  else
    SELECTED_AGENT_WORKSPACE="${default_workspace%/}/$NEW_AGENT_ID"
    if is_tty; then
      SELECTED_AGENT_WORKSPACE="$(prompt_line 'Workspace agent' "$SELECTED_AGENT_WORKSPACE")"
    fi
  fi

  default_agent_dir="$HOME_DIR/.openclaw/agents/$NEW_AGENT_ID/agent"
  SELECTED_AGENT_DIR="$default_agent_dir"
  if is_tty; then
    SELECTED_AGENT_DIR="$(prompt_line 'Agent dir OpenClaw' "$SELECTED_AGENT_DIR")"
  fi

  SELECTED_AGENT_ID="$NEW_AGENT_ID"
  SELECTED_AGENT_NAME="$NEW_AGENT_NAME"
  SELECTED_SKILLS_MODE="unrestricted"
  SELECTED_SKILLS_CSV=""
  CREATE_AGENT_CONFIG=1
}

interactive_choose_target() {
  local default_workspace="$1"
  local lines=()
  local labels=()
  local line agent_id name workspace agent_dir skills_mode skills_csv synthetic
  local idx=1 choice="" skills_note=""

  while IFS=$'\t' read -r agent_id name workspace agent_dir skills_mode skills_csv synthetic; do
    [[ -z "$agent_id" ]] && continue
    lines+=("$agent_id"$'\t'"$name"$'\t'"$workspace"$'\t'"$agent_dir"$'\t'"$skills_mode"$'\t'"$skills_csv"$'\t'"$synthetic")
    case "$skills_mode" in
      unrestricted) skills_note="skills: unrestricted" ;;
      agent) skills_note="skills: allowlist agent" ;;
      defaults) skills_note="skills: allowlist defaults" ;;
      *) skills_note="skills: unknown" ;;
    esac
    printf '%s) %s (%s)\n' "$idx" "$agent_id" "$workspace" >&2
    printf '   %s\n' "$skills_note" >&2
    idx=$((idx + 1))
  done < <(list_agents_from_config)

  printf '%s) Créer un nouvel agent\n' "$idx" >&2
  printf 'q) Quitter\n' >&2

  choice="$(prompt_line 'Choix' '1')"
  case "$choice" in
    q|Q) exit 0 ;;
  esac

  if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice < idx )); then
    line="${lines[$((choice - 1))]}"
    IFS=$'\t' read -r agent_id name workspace agent_dir skills_mode skills_csv synthetic <<< "$line"
    SELECTED_AGENT_ID="$agent_id"
    SELECTED_AGENT_NAME="$name"
    SELECTED_AGENT_WORKSPACE="$workspace"
    SELECTED_AGENT_DIR="$agent_dir"
    SELECTED_SKILLS_MODE="$skills_mode"
    SELECTED_SKILLS_CSV="$skills_csv"
    if [[ -n "$WORKSPACE_DIR" ]]; then
      SELECTED_AGENT_WORKSPACE="$WORKSPACE_DIR"
    fi
    return
  fi

  if [[ "$choice" == "$idx" ]]; then
    configure_new_agent_target "$default_workspace"
    return
  fi

  die "Invalid choice: $choice"
}

maybe_select_target_from_config() {
  local default_workspace=""

  default_workspace="$(get_default_workspace_from_config)"

  if [[ -n "$NEW_AGENT_ID" ]]; then
    configure_new_agent_target "$default_workspace"
    return
  fi

  if [[ -n "$TARGET_AGENT_ID" ]]; then
    select_existing_agent_by_id "$TARGET_AGENT_ID" || die "Unknown agent id: $TARGET_AGENT_ID"
    if [[ -n "$WORKSPACE_DIR" ]]; then
      SELECTED_AGENT_WORKSPACE="$WORKSPACE_DIR"
    fi
    return
  fi

  if is_tty; then
    interactive_choose_target "$default_workspace"
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
  local action=""
  local merged_skills_csv="$SELECTED_SKILLS_CSV"

  if [[ "$CREATE_AGENT_CONFIG" -eq 0 && "$PATCH_SKILLS_ALLOWLIST" -eq 0 ]]; then
    return
  fi

  config_exists || die "Config not found: $CONFIG_PATH"

  if [[ "$CREATE_AGENT_CONFIG" -eq 1 && "$PATCH_SKILLS_ALLOWLIST" -eq 1 ]]; then
    action="create-and-update-skills"
  elif [[ "$CREATE_AGENT_CONFIG" -eq 1 ]]; then
    action="create"
  else
    action="update-skills"
  fi

  CONFIG_PATH="$CONFIG_PATH" \
  ACTION="$action" \
  AGENT_ID="$SELECTED_AGENT_ID" \
  AGENT_NAME="$SELECTED_AGENT_NAME" \
  AGENT_WORKSPACE="$SELECTED_AGENT_WORKSPACE" \
  AGENT_DIR="$SELECTED_AGENT_DIR" \
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
action = os.environ["ACTION"]
agent_id = os.environ["AGENT_ID"]
agent_name = os.environ.get("AGENT_NAME", "")
agent_workspace = os.path.expanduser(os.environ["AGENT_WORKSPACE"])
agent_dir = os.path.expanduser(os.environ["AGENT_DIR"])
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
    entry = {"id": agent_id}
    entries.append(entry)

if action in {"create", "create-and-update-skills"}:
    entry["workspace"] = agent_workspace
    entry["agentDir"] = agent_dir
    if agent_name:
        entry["name"] = agent_name

if action in {"update-skills", "create-and-update-skills"}:
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

main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --config)
        CONFIG_PATH="$2"
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
      --new-agent)
        NEW_AGENT_ID="$2"
        shift 2
        ;;
      --agent-name)
        NEW_AGENT_NAME="$2"
        shift 2
        ;;
      --update-skills)
        UPDATE_SKILLS_MODE="$2"
        shift 2
        ;;
      --no-bootstrap)
        WITH_BOOTSTRAP=0
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
      *)
        die "Unknown option: $1"
        ;;
    esac
  done

  [[ -n "$TARGET_AGENT_ID" && -n "$NEW_AGENT_ID" ]] && die "Use either --agent or --new-agent, not both"

  load_garmin_skills

  if [[ -n "$WORKSPACE_DIR" && -z "$TARGET_AGENT_ID" && -z "$NEW_AGENT_ID" && ! is_tty ]]; then
    SELECTED_AGENT_ID="main"
    SELECTED_AGENT_NAME="Main Agent"
    SELECTED_AGENT_WORKSPACE="$WORKSPACE_DIR"
    SELECTED_AGENT_DIR="$HOME_DIR/.openclaw/agents/main/agent"
    SELECTED_SKILLS_MODE="unrestricted"
    SELECTED_SKILLS_CSV=""
  else
    maybe_select_target_from_config
  fi

  [[ -n "$SELECTED_AGENT_WORKSPACE" ]] || die "No target workspace resolved"
  WORKSPACE_DIR="$SELECTED_AGENT_WORKSPACE"
  if [[ -z "$INSTALL_ROOT" ]]; then
    INSTALL_ROOT="$WORKSPACE_DIR/.garmin-coach-agent"
  fi

  maybe_prompt_or_set_skill_patch
  patch_config_for_target

  local ts backup_root app_dir managed_python
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  backup_root="$INSTALL_ROOT/backups/$ts"
  app_dir="$INSTALL_ROOT/app"
  managed_python="$(choose_python)"

  log "Agent:          $SELECTED_AGENT_ID"
  log "Workspace:      $WORKSPACE_DIR"
  log "Install root:   $INSTALL_ROOT"
  log "Python:         $managed_python"
  log "Backup root:    $backup_root"

  if [[ "$PATCH_SKILLS_ALLOWLIST" -eq 1 ]]; then
    log "Skills config:  patched allowlist for $SELECTED_AGENT_ID"
  fi
  if [[ "$CREATE_AGENT_CONFIG" -eq 1 ]]; then
    log "Agent config:   created/updated in $CONFIG_PATH"
  fi

  if [[ "$DRY_RUN" -eq 0 ]]; then
    mkdir -p "$WORKSPACE_DIR" "$INSTALL_ROOT" "$backup_root"
  fi

  sync_app_snapshot "$app_dir"
  create_venv_and_install "$managed_python" "$INSTALL_ROOT/.venv" "$app_dir"

  local root_files=(AGENTS.md HEARTBEAT.md IDENTITY.md README.md SOUL.md TOOLS.md)
  if [[ "$WITH_BOOTSTRAP" -eq 1 ]]; then
    root_files+=(BOOTSTRAP.md)
  fi

  local name
  for name in "${root_files[@]}"; do
    copy_file "$REPO_DIR/agent/$name" "$WORKSPACE_DIR/$name" "$backup_root"
  done

  copy_tree_files "$REPO_DIR/agent/playbooks" "$WORKSPACE_DIR/playbooks" "$backup_root"
  copy_tree_files "$REPO_DIR/agent/skills" "$WORKSPACE_DIR/skills" "$backup_root"

  local rewrite_targets=("$WORKSPACE_DIR/TOOLS.md" "$WORKSPACE_DIR/skills")
  if [[ "$WITH_BOOTSTRAP" -eq 1 ]]; then
    rewrite_targets+=("$WORKSPACE_DIR/BOOTSTRAP.md")
  fi

  rewrite_runtime_paths "$managed_python" "$INSTALL_ROOT/.venv/bin/python" "${rewrite_targets[@]}"

  if [[ "$DRY_RUN" -eq 0 ]]; then
    cat > "$INSTALL_ROOT/manifest.txt" <<EOF
installed_at=$ts
repo_dir=$REPO_DIR
config_path=$CONFIG_PATH
agent_id=$SELECTED_AGENT_ID
workspace_dir=$WORKSPACE_DIR
install_root=$INSTALL_ROOT
managed_python=$managed_python
managed_venv=$INSTALL_ROOT/.venv/bin/python
EOF
  fi

  log "Install done."
  log "Managed runtime: $INSTALL_ROOT/.venv/bin/python"
  log "Agent files:     $WORKSPACE_DIR"
  log "Skills:          $WORKSPACE_DIR/skills"
}

main "$@"
