#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

HOST_ADDRESS="${1:-}"
PORT="${2:-}"
INSTALL_DEPS="${3:-}"
CREATED_VENV=0

if [ ! -f ".venv/bin/python" ]; then
  python3 -m venv .venv
  CREATED_VENV=1
fi

source .venv/bin/activate
if [ "${CREATED_VENV}" = "1" ] || [ "${INSTALL_DEPS}" = "--install-deps" ]; then
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
else
  echo "Skipping dependency install. Pass --install-deps as 3rd arg to force reinstall."
fi

SETTINGS_RAW="$(python -c "from app.config import get_settings; s=get_settings(); print(f'{s.app_host}|{s.app_port}')")"
ENV_HOST="${SETTINGS_RAW%%|*}"
ENV_PORT="${SETTINGS_RAW##*|}"

if [ -z "${HOST_ADDRESS}" ]; then
  HOST_ADDRESS="${ENV_HOST}"
fi
if [ -z "${PORT}" ]; then
  PORT="${ENV_PORT}"
fi

python -m uvicorn app.main:app --host "${HOST_ADDRESS}" --port "${PORT}"
