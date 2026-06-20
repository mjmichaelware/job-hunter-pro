#!/usr/bin/env bash
# scripts/add_keys.sh — blind-paste wiring for NEW keyed job APIs.
#
# This script ONLY prompts for keys not yet in Secret Manager.
# Keys already stored (SERPAPI_KEY, GROQ_API_KEY, OPENAI_API_KEY,
# GEMINI_API_KEY, ANTHROPIC_API_KEY, XAI_API_KEY) are detected and
# skipped automatically — no need to re-paste them.
#
# Usage:  bash scripts/add_keys.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-ai-job-agent-498702}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-job-hunter-pro}"

echo "==> Project: $PROJECT_ID   Region: $REGION   Service: $SERVICE"
gcloud config set project "$PROJECT_ID" >/dev/null 2>&1 || true

RUNTIME_SA="$(gcloud run services describe "$SERVICE" --region "$REGION" \
  --format='value(spec.template.spec.serviceAccountName)' 2>/dev/null || true)"
if [ -z "${RUNTIME_SA:-}" ]; then
  PROJ_NUM="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
  RUNTIME_SA="${PROJ_NUM}-compute@developer.gserviceaccount.com"
fi
echo "==> Runtime service account: $RUNTIME_SA"

SECRET_MAP=""
ENV_VARS=""

# has_secret SECRET_NAME — true if the secret already has at least one version.
has_secret() {
  gcloud secrets versions list "$1" --limit=1 --format='value(name)' 2>/dev/null | grep -q .
}

# put_secret SECRET_NAME — prompt blindly; skip if already exists.
put_secret() {
  local name="$1" val=""
  if has_secret "$name"; then
    echo "   · $name already in Secret Manager — skipping"
    return 0
  fi
  printf '   paste %s (ENTER to skip): ' "$name"
  read -rs val; echo
  if [ -z "$val" ]; then echo "   · skipped $name"; return 1; fi
  if gcloud secrets describe "$name" >/dev/null 2>&1; then
    printf '%s' "$val" | gcloud secrets versions add "$name" --data-file=- >/dev/null
    echo "   · updated $name (new version)"
  else
    printf '%s' "$val" | gcloud secrets create "$name" --data-file=- \
      --replication-policy=automatic >/dev/null
    echo "   · created $name"
  fi
  gcloud secrets add-iam-policy-binding "$name" \
    --member="serviceAccount:${RUNTIME_SA}" \
    --role="roles/secretmanager.secretAccessor" >/dev/null 2>&1 || true
  unset val
  return 0
}

add_map()  { SECRET_MAP="${SECRET_MAP:+$SECRET_MAP,}$1=$1:latest"; }
add_env()  { ENV_VARS="${ENV_VARS:+$ENV_VARS,}$1"; }

# bind_if_present SECRET — if the secret already exists in Secret Manager, add it
# to the deploy's secret map (so it's injected into the service env) and grant the
# runtime SA access. Does NOT prompt — used to (re)bind keys you already stored,
# which is what makes the LLM research + Maps actually run in the container.
bind_if_present() {
  local name="$1"
  if has_secret "$name"; then
    add_map "$name"
    gcloud secrets add-iam-policy-binding "$name" \
      --member="serviceAccount:${RUNTIME_SA}" \
      --role="roles/secretmanager.secretAccessor" >/dev/null 2>&1 || true
    echo "   · $name already stored — will bind to the service on deploy"
  fi
}

echo
echo "================ BIND ALREADY-STORED KEYS (no prompt) ================"
echo "Ensuring keys already in Secret Manager are injected into the running service:"
for S in GOOGLE_MAPS_API_KEY SERPAPI_KEY OPENAI_API_KEY GEMINI_API_KEY ANTHROPIC_API_KEY GROQ_API_KEY XAI_API_KEY; do
  bind_if_present "$S"
done

echo
echo "================ NEW KEYED PROVIDERS (blind paste — ENTER skips) ================"
echo "(Keys already stored above are bound automatically — you won't be asked for them)"
echo

echo "[Adzuna]  free signup → https://developer.adzuna.com/  (app id + key)"
put_secret ADZUNA_APP_ID  && add_map ADZUNA_APP_ID  || true
put_secret ADZUNA_APP_KEY && add_map ADZUNA_APP_KEY || true

echo "[USAJobs] free → https://developer.usajobs.gov/  (API key; email is your account email)"
put_secret USAJOBS_API_KEY && add_map USAJOBS_API_KEY || true
printf '   type USAJOBS_EMAIL (your account email, ENTER to skip): '
read -r USAJOBS_EMAIL || true
if [ -n "${USAJOBS_EMAIL:-}" ]; then
  # Stored as a SECRET (not a literal env var) to match the service's existing
  # variable type. Cloud Run refuses to flip a variable from secret to literal
  # in an update ("already set with a different type"), so this keeps it a secret.
  if gcloud secrets describe USAJOBS_EMAIL >/dev/null 2>&1; then
    printf '%s' "$USAJOBS_EMAIL" | gcloud secrets versions add USAJOBS_EMAIL --data-file=- >/dev/null
  else
    printf '%s' "$USAJOBS_EMAIL" | gcloud secrets create USAJOBS_EMAIL --data-file=- \
      --replication-policy=automatic >/dev/null
  fi
  gcloud secrets add-iam-policy-binding USAJOBS_EMAIL \
    --member="serviceAccount:${RUNTIME_SA}" \
    --role="roles/secretmanager.secretAccessor" >/dev/null 2>&1 || true
  add_map USAJOBS_EMAIL
fi

echo "[CareerOneStop / US DOL] free → https://www.careeronestop.org/Developers/WebAPI/  (userId + token)"
put_secret CAREERONESTOP_USERID && add_map CAREERONESTOP_USERID || true
put_secret CAREERONESTOP_TOKEN  && add_map CAREERONESTOP_TOKEN  || true

echo "[Jooble]  free → https://jooble.org/api/about  (API key)"
if put_secret JOOBLE_API_KEY; then add_map JOOBLE_API_KEY; add_env ENABLE_JOOBLE=1; fi

echo "[Careerjet] free → https://www.careerjet.com/partners/  (affiliate id)"
if put_secret CAREERJET_AFFID; then add_map CAREERJET_AFFID; add_env ENABLE_CAREERJET=1; fi

echo "[Yelp Fusion] free → https://fusion.yelp.com/  (API key — local business/review leads)"
if put_secret YELP_API_KEY; then add_map YELP_API_KEY; add_env ENABLE_YELP=1; fi

echo "[Foursquare Places] free → https://foursquare.com/developers/  (API key — local business leads)"
if put_secret FOURSQUARE_API_KEY; then add_map FOURSQUARE_API_KEY; add_env ENABLE_FOURSQUARE=1; fi

echo
if [ -z "$SECRET_MAP" ] && [ -z "$ENV_VARS" ]; then
  echo "==> No new keys entered. Nothing to deploy. Re-run any time."
  exit 0
fi

echo "==> Redeploying $SERVICE with the new secrets/flags (existing secrets kept)…"
DEPLOY_ARGS=( run deploy "$SERVICE" --source . --region "$REGION"
  --allow-unauthenticated --timeout=300 --cpu=2 --memory=1Gi )
[ -n "$SECRET_MAP" ] && DEPLOY_ARGS+=( --update-secrets="$SECRET_MAP" )
[ -n "$ENV_VARS" ]   && DEPLOY_ARGS+=( --update-env-vars="$ENV_VARS" )
gcloud "${DEPLOY_ARGS[@]}"

URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
echo
echo "==> Health (key wiring — these must be true for Maps + AI research to run):"
curl -fsS "$URL/api/health" | python3 -c '
import sys, json
d = json.load(sys.stdin)
flags = ["maps_enabled","serpapi_enabled","openai_enabled","gemini_enabled","claude_enabled","groq_enabled","grok_xai_enabled"]
for f in flags:
    mark = "OK " if d.get(f) else "-- "
    print("   " + mark + " " + f + " = " + str(d.get(f)))
p = d.get("providers", {}) or {}
print("   providers: " + str(p.get("total")) + " total, " + str(p.get("ready")) + " ready")
' || echo "health check failed — see logs"
echo
echo "==> Provider status:"
curl -fsS "$URL/api/providers" | python3 -c '
import sys, json
d = json.load(sys.stdin)
for p in d.get("providers", []):
    print("  " + str(p.get("status", "?")).rjust(18) + "  " + str(p.get("label", "")))
' || true
echo
echo "==> Done. New keyed providers are now live; the rest stay dormant until added."
