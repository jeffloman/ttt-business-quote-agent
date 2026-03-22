#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR=".venv"
ACTIVATE="$VENV_DIR/bin/activate"
REQ_FILE="requirements.txt"
MARKER="$VENV_DIR/.requirements_sha256"

requirements_sha() {
  python - <<'PY'
import hashlib, pathlib
p = pathlib.Path("requirements.txt")
h = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""
print(h)
PY
}

if [[ ! -f "$ACTIVATE" ]]; then
  echo "Creating venv: $VENV_DIR"
  python -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$ACTIVATE"

REQ_SHA="$(requirements_sha)"
NEEDS_INSTALL="0"

if [[ ! -f "$REQ_FILE" ]]; then
  echo "ERROR: $REQ_FILE not found in project root."
  exit 1
fi

if [[ ! -f "$MARKER" ]]; then
  NEEDS_INSTALL="1"
elif [[ "$(cat "$MARKER")" != "$REQ_SHA" ]]; then
  NEEDS_INSTALL="1"
fi

if [[ "$NEEDS_INSTALL" == "1" ]]; then
  echo "Installing dependencies (requirements changed or first run)..."
  python -m pip install -U pip
  python -m pip install -r "$REQ_FILE"
  echo "$REQ_SHA" > "$MARKER"
fi

echo "Starting web UI..."
exec python web_app.py