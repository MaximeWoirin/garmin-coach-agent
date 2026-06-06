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
import json, os, sys
try:
    cfg = json.loads(open(sys.argv[1]).read())
    default_ws = cfg.get("agents", {}).get("defaults", {}).get("workspace") or "~/.openclaw/workspace"
    for entry in cfg.get("agents", {}).get("list", []):
        aid = entry.get("id")
        if not aid: continue
        ws = entry.get("workspace") or default_ws
        ws = os.path.expanduser(ws)
        manifest_path = os.path.join(ws, ".garmin-coach-agent", "manifest.txt")
        if os.path.exists(manifest_path):
            manifest = {}
            for line in open(manifest_path).read().splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    manifest[k] = v
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
