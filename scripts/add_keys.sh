#!/usr/bin/env bash
# scripts/add_keys.sh — interactive, blind-paste wiring for the KEYED job APIs.
#
# What it does, safely:
#   • Prompts you for each keyed provider's secret(s), ONE AT A TIME.
#   • Input is read SILENTLY (read -rs) — your key never prints to the screen,
#     never lands in shell history, and is never written to a file in the repo.
#   • Each value is piped straight into Google Secret Manager (no echo, no temp
#     file). Press ENTER on a blank prompt to SKIP a provider (it stays dormant).
#   • Grants the Cloud Run runtime service account access to each secret.
#   • Redeploys job-hunter-pro with --update-secrets (existing secrets are kept),
#     turns on the matching ENABLE_* flags, then checks /api/health + /api/providers.
#
# Nothing here hardcodes a secret. Re-run it any time to add more keys later.
#
# Usage:  bash scripts/add_keys.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-ai-job-agent-498702}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-job-hunter-pro}"

echo "==> Project: $PROJECT_ID   Region: $REGION   Service: $SERVICE"
gcloud config set project "$PROJECT_ID" >/dev/null 2>&1 || true

# Cloud Run runtime service account (what the container runs as).
RUNTIME_SA="$(gcloud run services describe "$SERVICE" --region "$REGION" \
  --format='value(spec.template.spec.serviceAccountName)' 2>/dev/null || true)"
if [ -z "${RUNTIME_SA:-}" ]; then
  PROJ_NUM="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
  RUNTIME_SA="${PROJ_NUM}-compute@developer.gserviceaccount.com"
fi
echo "==> Runtime service account: $RUNTIME_SA"

# Accumulators built up as you paste keys.
SECRET_MAP=""     # for --update-secrets  ENV=SECRET:latest,...
ENV_VARS=""       # for --update-env-vars ENABLE_X=1,...

# put_secret SECRET_NAME — read a value silently and store it (create or new version).
put_secret() {
  local name="$1" val=""
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

echo
echo "================ KEYED PROVIDERS (blind paste — ENTER skips) ================"

echo "[Adzuna]  free signup → https://developer.adzuna.com/  (app id + key)"
put_secret ADZUNA_APP_ID  && add_map ADZUNA_APP_ID  || true
put_secret ADZUNA_APP_KEY && add_map ADZUNA_APP_KEY || true

echo "[USAJobs] free → https://developer.usajobs.gov/  (API key; email is your account email)"
put_secret USAJOBS_API_KEY && add_map USAJOBS_API_KEY || true
printf '   type USAJOBS_EMAIL (not secret, ENTER to skip): '
read -r USAJOBS_EMAIL || true
[ -n "${USAJOBS_EMAIL:-}" ] && add_env "USAJOBS_EMAIL=${USAJOBS_EMAIL}"

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

echo "[SerpAPI] (optional; only if rotating the key) → https://serpapi.com/manage-api-key"
put_secret SERPAPI_KEY && add_map SERPAPI_KEY || true

echo
if [ -z "$SECRET_MAP" ] && [ -z "$ENV_VARS" ]; then
  echo "==> No keys entered. Nothing to deploy. Re-run any time."
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
echo "==> Health:"
curl -fsS "$URL/api/health" | python3 -m json.tool || echo "health check failed — see logs"
echo
echo "==> Provider status (which sources are now ready):"
curl -fsS "$URL/api/providers" | python3 -c \
  'import sys,json; d=json.load(sys.stdin); [print(f"  {p[\"status\"]:>18}  {p[\"label\"]}") for p in d.get("providers",[])]' \
  || true
echo
echo "==> Done. Keyed providers you pasted are now live; the rest stay dormant until added."
