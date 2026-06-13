#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
  export PYTHONPATH="$REPO_DIR${PYTHONPATH:+:$PYTHONPATH}"
  exec python3 -m garmin_coach.install_openclaw_agent "$@"
fi

if command -v uv >/dev/null 2>&1; then
  exec uv run --project "$REPO_DIR" python -m garmin_coach.install_openclaw_agent "$@"
fi

printf 'Error: python3 (>=3.11) or uv is required to run the installer bootstrap.\n' >&2
exit 1
