#!/usr/bin/env bash
set -euo pipefail
PROJECT_ID="${PROJECT_ID:-ai-job-agent-498702}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-job-hunter-pro}"
URL="$(gcloud run services describe "$SERVICE" --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"
echo "SERVICE_URL=$URL"
curl -fsS "$URL/api/health"
echo
