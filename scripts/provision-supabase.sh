#!/usr/bin/env bash
# Provision Supabase project + migrations + Render env vars.
# Requires: SUPABASE_ACCESS_TOKEN (from https://supabase.com/dashboard/account/tokens)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_NAME="${SUPABASE_PROJECT_NAME:-ironman-coach}"
DB_PASS="${SUPABASE_DB_PASSWORD:-$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)}"
REGION="${SUPABASE_REGION:-eu-west-1}"
RENDER_SERVICE_ID="${RENDER_SERVICE_ID:-srv-d8n6j8ok1i2s739cere0}"

if [[ -z "${SUPABASE_ACCESS_TOKEN:-}" ]]; then
  if [[ -f "$HOME/.supabase/access-token" ]]; then
    SUPABASE_ACCESS_TOKEN="$(cat "$HOME/.supabase/access-token")"
  else
    echo "Set SUPABASE_ACCESS_TOKEN or run: supabase login" >&2
    exit 1
  fi
fi

auth_hdr=(-H "Authorization: Bearer ${SUPABASE_ACCESS_TOKEN}" -H "Content-Type: application/json")

echo "Fetching Supabase organization..."
ORG_ID=$(curl -sS "${auth_hdr[@]}" https://api.supabase.com/v1/organizations \
  | python3 -c "import json,sys; orgs=json.load(sys.stdin); print(orgs[0]['id'] if orgs else '')")
if [[ -z "$ORG_ID" ]]; then
  echo "No Supabase organization found" >&2
  exit 1
fi

echo "Creating project '${PROJECT_NAME}' in ${REGION}..."
CREATE=$(curl -sS -X POST https://api.supabase.com/v1/projects \
  "${auth_hdr[@]}" \
  -d "{\"organization_id\":\"${ORG_ID}\",\"name\":\"${PROJECT_NAME}\",\"region\":\"${REGION}\",\"db_pass\":\"${DB_PASS}\"}")

PROJECT_REF=$(echo "$CREATE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || true)
if [[ -z "$PROJECT_REF" ]]; then
  echo "Project create response: $CREATE" >&2
  exit 1
fi

SUPABASE_URL="https://${PROJECT_REF}.supabase.co"
echo "Waiting for project ${PROJECT_REF} to become healthy..."
for i in $(seq 1 60); do
  STATUS=$(curl -sS "${auth_hdr[@]}" "https://api.supabase.com/v1/projects/${PROJECT_REF}/health" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || echo "")
  if [[ "$STATUS" == "ACTIVE_HEALTHY" ]]; then
    break
  fi
  sleep 10
done

echo "Fetching service role key..."
KEYS=$(curl -sS "${auth_hdr[@]}" "https://api.supabase.com/v1/projects/${PROJECT_REF}/api-keys?reveal=true")
SERVICE_KEY=$(echo "$KEYS" | python3 -c "
import json,sys
keys=json.load(sys.stdin)
for k in keys:
    if k.get('name')=='service_role' or k.get('type')=='secret':
        print(k.get('api_key') or k.get('secret') or '')
        break
else:
    for k in keys:
        if 'service' in (k.get('name') or '').lower():
            print(k.get('api_key',''))
            break
")

if [[ -z "$SERVICE_KEY" ]]; then
  echo "Could not extract service role key. Keys response saved for inspection." >&2
  echo "$KEYS" > /tmp/supabase-keys.json
  exit 1
fi

export SUPABASE_URL SUPABASE_DB_PASSWORD="$DB_PASS"
bash "$ROOT/scripts/deploy-supabase.sh"

echo "Updating Render service env vars..."
render services update "$RENDER_SERVICE_ID" \
  --env-var "SUPABASE_URL=${SUPABASE_URL}" \
  --env-var "SUPABASE_SERVICE_KEY=${SERVICE_KEY}" \
  --confirm --output json >/dev/null

echo "Provisioned:"
echo "  SUPABASE_URL=${SUPABASE_URL}"
echo "  DB password saved in SUPABASE_DB_PASSWORD (store securely)"
echo "Render service updated — redeploy will pick up Supabase."
