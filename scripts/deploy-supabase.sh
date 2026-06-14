#!/usr/bin/env bash
# Run Supabase migrations against a project.
# Requires: SUPABASE_URL and SUPABASE_DB_PASSWORD (from project settings → Database)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MIGRATIONS="$ROOT/supabase/migrations"

if [[ -z "${SUPABASE_URL:-}" ]]; then
  echo "Set SUPABASE_URL (e.g. https://abcdefgh.supabase.co)" >&2
  exit 1
fi
if [[ -z "${SUPABASE_DB_PASSWORD:-}" ]]; then
  echo "Set SUPABASE_DB_PASSWORD from Supabase → Project Settings → Database" >&2
  exit 1
fi

REF="${SUPABASE_URL#https://}"
REF="${REF%.supabase.co}"
DB_HOST="db.${REF}.supabase.co"
DB_URL="postgresql://postgres:${SUPABASE_DB_PASSWORD}@${DB_HOST}:5432/postgres"

if ! command -v psql >/dev/null 2>&1; then
  echo "Install psql (brew install libpq && brew link --force libpq)" >&2
  exit 1
fi

echo "Applying migrations to ${DB_HOST}..."
for f in "$MIGRATIONS"/*.sql; do
  echo "  → $(basename "$f")"
  psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$f"
done
echo "Done."
