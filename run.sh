#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] || { echo "Copy .env.example to .env and fill in client_id/secret"; exit 1; }
python -m uvicorn app:app --reload --port "${PORT:-8095}"
