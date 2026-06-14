#!/usr/bin/env bash
# Smoke-test a deployed Ironman Coach stack.
set -euo pipefail

NETLIFY_URL="${1:-https://ironman-coach.netlify.app}"

echo "Checking ${NETLIFY_URL}/api/health ..."
HEALTH=$(curl -sS -m 120 "${NETLIFY_URL}/api/health" || true)
echo "$HEALTH"

if echo "$HEALTH" | grep -q '"storage":"supabase"'; then
  echo "OK: API using Supabase"
elif echo "$HEALTH" | grep -q '"storage":"sqlite"'; then
  echo "WARN: API using SQLite — set SUPABASE_URL + SUPABASE_SERVICE_KEY on Render" >&2
  exit 1
else
  echo "FAIL: health check did not return expected JSON" >&2
  exit 1
fi

echo "Checking SPA ..."
CODE=$(curl -sS -o /dev/null -w "%{http_code}" -m 30 "${NETLIFY_URL}/")
if [[ "$CODE" == "200" ]]; then
  echo "OK: SPA returns 200"
else
  echo "FAIL: SPA returned ${CODE}" >&2
  exit 1
fi

echo "All checks passed. Share: ${NETLIFY_URL}"
