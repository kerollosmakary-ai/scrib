#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
BOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${BOT_DIR}/.." && pwd)"
SERVICE_NAME="mybot"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script as root (example: sudo bash deploy/update-mybot.sh)." >&2
  exit 1
fi

cd "${REPO_ROOT}"
if ! git pull --ff-only; then
  echo "git pull failed. Resolve local changes/divergence and retry." >&2
  exit 1
fi

cd "${BOT_DIR}"
if [[ ! -f ".venv/bin/activate" ]]; then
  echo "Missing virtualenv at ${BOT_DIR}/.venv. Run setup first." >&2
  exit 1
fi

source .venv/bin/activate
if ! pip install --upgrade -r requirements.txt; then
  echo "Dependency installation failed. Service was not restarted." >&2
  exit 1
fi

systemctl restart "${SERVICE_NAME}"
systemctl status "${SERVICE_NAME}" --no-pager
