#!/usr/bin/env bash
set -o errexit

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL environment variable is required."
  exit 1
fi

BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"
OUT_FILE="$BACKUP_DIR/havells_sambandh_$(date +%Y%m%d_%H%M%S).dump"

pg_dump "$DATABASE_URL" --format=custom --no-owner --file="$OUT_FILE"
echo "PostgreSQL backup created at: $OUT_FILE"
