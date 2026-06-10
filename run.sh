#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] || { echo "Copy .env.example to .env and fill in client_id/secret"; exit 1; }
command -v uv >/dev/null || { echo "uv is required: https://docs.astral.sh/uv/getting-started/installation/"; exit 1; }
# uv run creates the venv and syncs deps from pyproject.toml / uv.lock on demand.
exec uv run uvicorn app:app --reload --port "${PORT:-8095}"
