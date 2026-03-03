#!/usr/bin/env bash
set -euo pipefail

HOST_ADDRESS="${1:-}"
PORT="${2:-}"

if [ ! -f ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

SETTINGS_RAW="$(python -c "from app.config import get_settings; s=get_settings(); print(f'{s.app_host}|{s.app_port}')")"
ENV_HOST="${SETTINGS_RAW%%|*}"
ENV_PORT="${SETTINGS_RAW##*|}"

if [ -z "${HOST_ADDRESS}" ]; then
  HOST_ADDRESS="${ENV_HOST}"
fi
if [ -z "${PORT}" ]; then
  PORT="${ENV_PORT}"
fi

uvicorn app.main:app --host "${HOST_ADDRESS}" --port "${PORT}"
