# FILE: scripts/replit_web.sh
#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate
exec python web_app.py