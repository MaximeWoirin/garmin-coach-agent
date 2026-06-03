#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_DIR="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
INSTALL_ROOT_DEFAULT="$WORKSPACE_DIR/.garmin-coach-agent"
INSTALL_ROOT="${OPENCLAW_INSTALL_ROOT:-$INSTALL_ROOT_DEFAULT}"
PYTHON_BIN=""
DRY_RUN=0
WITH_BOOTSTRAP=1
SKIP_PACKAGE_INSTALL=0
QUIET=0

usage() {
  cat <<'EOF'
Install Garmin Coach Agent into an OpenClaw workspace.

Usage:
  scripts/install-openclaw-agent.sh [options]

Options:
  --workspace DIR            OpenClaw workspace target (default: ~/.openclaw/workspace)
  --install-root DIR         Managed install dir for app snapshot + venv
  --python BIN              Python binary to use for venv creation
  --no-bootstrap            Do not install BOOTSTRAP.md
  --skip-package-install    Copy files only; skip venv/package install
  --dry-run                 Show actions without writing
  --quiet                   Reduce logs
  -h, --help                Show help

What it installs:
  - agent files -> <workspace>/
  - playbooks   -> <workspace>/playbooks/
  - skills      -> <workspace>/skills/
  - app snapshot + venv -> <install-root>/

Notes:
  - Existing destination files are backed up under:
      <install-root>/backups/<timestamp>/
  - Installed skill docs are rewritten to call the managed venv Python.
EOF
}

log() {
  if [[ "$QUIET" -eq 0 ]]; then
    printf '%s\n' "$*"
  fi
}

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] %s\n' "$*"
  else
    eval "$@"
  fi
}

choose_python() {
  if [[ -n "$PYTHON_BIN" ]]; then
    command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
      echo "Python not found: $PYTHON_BIN" >&2
      exit 1
    }
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

  echo "No usable Python found (need python3.13 or uv to install it)." >&2
  exit 1
}

backup_if_exists() {
  local src="$1"
  local backup_root="$2"
  if [[ -e "$src" || -L "$src" ]]; then
    local rel
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

main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
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
        echo "Unknown option: $1" >&2
        usage >&2
        exit 1
        ;;
    esac
  done

  if [[ "$INSTALL_ROOT" == "$INSTALL_ROOT_DEFAULT" ]]; then
    INSTALL_ROOT="$WORKSPACE_DIR/.garmin-coach-agent"
  fi

  local ts backup_root app_dir managed_python
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  backup_root="$INSTALL_ROOT/backups/$ts"
  app_dir="$INSTALL_ROOT/app"

  managed_python="$(choose_python)"

  log "Workspace:      $WORKSPACE_DIR"
  log "Install root:   $INSTALL_ROOT"
  log "Python:         $managed_python"
  log "Backup root:    $backup_root"

  if [[ "$DRY_RUN" -eq 0 ]]; then
    mkdir -p "$WORKSPACE_DIR" "$INSTALL_ROOT" "$backup_root"
  fi

  sync_app_snapshot "$app_dir"
  create_venv_and_install "$managed_python" "$INSTALL_ROOT/.venv" "$app_dir"

  local root_files=(AGENTS.md HEARTBEAT.md IDENTITY.md README.md SOUL.md SYSTEM.md TOOLS.md)
  if [[ "$WITH_BOOTSTRAP" -eq 1 ]]; then
    root_files+=(BOOTSTRAP.md)
  fi

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
