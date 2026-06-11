#!/usr/bin/env bash
# Script utilitaire pour mettre à jour l'agent OpenClaw installé.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
CONFIG_PATH="${OPENCLAW_CONFIG:-${HOME:-~}/.openclaw/openclaw.json}"

echo "=== Mise à jour de l'agent OpenClaw (Garmin Coach) ==="

# 1. Trouver les installations existantes
if [[ ! -f "$CONFIG_PATH" ]]; then
    echo "Erreur : OpenClaw config introuvable à $CONFIG_PATH."
    echo "Spécifiez l'espace de travail avec OPENCLAW_WORKSPACE ou installez l'agent d'abord."
    exit 1
fi

declare -a installed_workspaces=()
declare -a installed_agent_ids=()
declare -a installed_versions=()
declare -a installed_db_paths=()
declare -a installed_venvs=()

# Extraction des installations depuis la config OpenClaw
readarray -t agent_lines < <(python3 - "$CONFIG_PATH" <<'PY'
from __future__ import annotations

import json
import os
import pathlib
import sys


def load_manifest(install_root: pathlib.Path) -> dict[str, str]:
    manifest_json = install_root / "manifest.json"
    if manifest_json.exists():
        data = json.loads(manifest_json.read_text(encoding="utf-8"))
        return {
            "app_version": str(data.get("app_version", "unknown")),
            "data_dir": str(data.get("paths", {}).get("data_dir", "")),
            "managed_venv": str(data.get("paths", {}).get("managed_venv", "")),
        }

    manifest_txt = install_root / "manifest.txt"
    if manifest_txt.exists():
        legacy: dict[str, str] = {}
        for line in manifest_txt.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                legacy[key] = value
        return {
            "app_version": legacy.get("app_version", "unknown"),
            "data_dir": legacy.get("data_dir", ""),
            "managed_venv": legacy.get("managed_venv", ""),
        }

    return {}


try:
    cfg = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    agents_cfg = cfg.get("agents", {})
    defaults = agents_cfg.get("defaults", {})
    default_ws = os.path.expanduser(defaults.get("workspace") or "~/.openclaw/workspace")

    entries = [{"id": "main", "workspace": default_ws}] + list(agents_cfg.get("list", []))
    seen: set[str] = set()
    for entry in entries:
        aid = entry.get("id")
        if not aid or aid in seen:
            continue
        seen.add(aid)
        ws = os.path.expanduser(entry.get("workspace") or default_ws)
        install_root = pathlib.Path(ws) / ".garmin-coach-agent"
        manifest = load_manifest(install_root)
        if not manifest:
            continue
        print(f"{aid}\t{ws}\t{manifest.get('app_version', 'unknown')}\t{manifest.get('data_dir', '')}\t{manifest.get('managed_venv', '')}")
except Exception:
    pass
PY
)

for line in "${agent_lines[@]}"; do
    [[ -z "$line" ]] && continue
    IFS=$'\t' read -r aid ws ver data_dir venv <<< "$line"
    installed_agent_ids+=("$aid")
    installed_workspaces+=("$ws")
    installed_versions+=("$ver")
    installed_db_paths+=("$data_dir/garmin_coach.db")
    installed_venvs+=("$venv")
done

if [[ ${#installed_agent_ids[@]} -eq 0 ]]; then
    echo "Aucune installation de Garmin Coach détectée dans les agents OpenClaw."
    echo "Veuillez d'abord exécuter scripts/install-openclaw-agent.sh"
    exit 1
fi

TARGET_IDX=0
if [[ ${#installed_agent_ids[@]} -gt 1 ]]; then
    echo "Plusieurs installations détectées :"
    for i in "${!installed_agent_ids[@]}"; do
        echo "$((i+1))) ${installed_agent_ids[$i]} (v${installed_versions[$i]}) - ${installed_workspaces[$i]}"
    done
    read -rp "Quel agent voulez-vous mettre à jour ? [1-${#installed_agent_ids[@]}] : " choice
    if [[ ! "$choice" =~ ^[0-9]+$ ]] || (( choice < 1 || choice > ${#installed_agent_ids[@]} )); then
        echo "Choix invalide."
        exit 1
    fi
    TARGET_IDX=$((choice-1))
fi

AGENT_ID="${installed_agent_ids[$TARGET_IDX]}"
WORKSPACE="${installed_workspaces[$TARGET_IDX]}"
OLD_VERSION="${installed_versions[$TARGET_IDX]}"
DB_PATH="${installed_db_paths[$TARGET_IDX]}"
VENV_PATH="${installed_venvs[$TARGET_IDX]}"

NEW_VERSION="unknown"
if [[ -f "$REPO_DIR/pyproject.toml" ]]; then
    NEW_VERSION="$(python3 -c 'import re; match=re.search(r"version\s*=\s*\"([^\"]+)\"", open("'"$REPO_DIR"'/pyproject.toml").read()); print(match.group(1) if match else "unknown")' 2>/dev/null || echo "unknown")"
fi

echo ">> Préparation de la mise à jour pour l'agent '$AGENT_ID'"
echo ">> Version : v$OLD_VERSION -> v$NEW_VERSION"

# 2. Sauvegarde DB
if [[ -f "$DB_PATH" ]]; then
    ts="$(date -u +%Y%m%dT%H%M%SZ)"
    backup_dir="$(dirname "$DB_PATH")/../backups/$ts"
    mkdir -p "$backup_dir"
    echo ">> Sauvegarde de la base de données dans $backup_dir/garmin_coach.db"
    cp -a "$DB_PATH" "$backup_dir/garmin_coach.db"
fi

# 3. Exécution de l'installeur
echo ">> Mise à jour du code, de l'environnement virtuel et des skills..."
"$REPO_DIR/scripts/install-openclaw-agent.sh" \
    --agent "$AGENT_ID" \
    --workspace "$WORKSPACE" \
    --preserve-agent-core \
    --no-bootstrap \
    "$@"

# 4. Migration DB
echo ">> Exécution des migrations de base de données..."
if [[ -x "$VENV_PATH" ]]; then
    export GARMIN_COACH_DB="$DB_PATH"
    "$VENV_PATH" - <<'EOF'
import sys
try:
    from garmin_coach.db import ensure_db, run_migrations, get_connection
    conn = get_connection()
    applied = run_migrations(conn)
    if applied:
        print(f"Migrations appliquées avec succès : {', '.join(applied)}")
    else:
        print("La base de données est déjà à jour.")
    conn.close()
except Exception as e:
    print(f"Erreur lors des migrations : {e}", file=sys.stderr)
    sys.exit(1)
EOF
else
    echo "Environnement virtuel introuvable à $VENV_PATH, impossible de lancer les migrations automatiquement."
fi

echo "=== Mise à jour terminée avec succès ==="
