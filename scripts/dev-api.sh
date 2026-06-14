#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/coaching-lab"
source .venv/bin/activate
exec uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
