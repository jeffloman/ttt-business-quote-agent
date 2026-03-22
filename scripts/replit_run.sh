#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR=".venv"
ACTIVATE="$VENV_DIR/bin/activate"

if [[ ! -f "requirements.txt" ]]; then
  echo "ERROR: requirements.txt not found in project root: $PROJECT_ROOT"
  exit 1
fi

if [[ ! -f "$ACTIVATE" ]]; then
  echo "Creating venv: $VENV_DIR"
  python -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$ACTIVATE"

# Replit sometimes forces pip --user via env/config; that breaks in venv.
unset PIP_USER PYTHONUSERBASE PIP_TARGET
export PIP_CONFIG_FILE=/dev/null

python -m pip install -U pip
python -m pip install -r requirements.txt

echo "Starting web UI..."
exec python web_app.py
