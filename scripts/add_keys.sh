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

echo
echo "================ NEW KEYED PROVIDERS (blind paste — ENTER skips) ================"
echo "(Already-wired keys like SERPAPI, GROQ, OPENAI, GEMINI, ANTHROPIC, XAI are auto-skipped)"
echo

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
echo "==> Health:"
curl -fsS "$URL/api/health" | python3 -m json.tool || echo "health check failed — see logs"
echo
echo "==> Provider status:"
curl -fsS "$URL/api/providers" | python3 -c \
  'import sys,json; d=json.load(sys.stdin); [print(f"  {p[\"status\"]:>18}  {p[\"label\"]}") for p in d.get("providers",[])]' \
  || true
echo
echo "==> Done. New keyed providers are now live; the rest stay dormant until added."
