#!/usr/bin/env bash
set -o errexit

cd "$(dirname "$0")/../backend"
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"

"$PYTHON_BIN" manage.py migrate --noinput
"$PYTHON_BIN" manage.py seed_rbac
"$PYTHON_BIN" manage.py shell -c "from apps.scheduling.services import generate_time_slots_from_config; generate_time_slots_from_config()"
echo "Migrations, RBAC roles/permissions, and default time slots initialized."
