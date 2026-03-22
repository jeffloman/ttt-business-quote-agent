# FILE: scripts/replit_setup.sh
#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt

echo "OK: venv ready. Run: source .venv/bin/activate && python web_app.py"