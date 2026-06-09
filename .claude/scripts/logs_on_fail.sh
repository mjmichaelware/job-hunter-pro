#!/usr/bin/env bash
set -euo pipefail
PROJECT_ID="${PROJECT_ID:-ai-job-agent-498702}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-job-hunter-pro}"
gcloud run services describe "$SERVICE" --project "$PROJECT_ID" --region "$REGION" --format="table(metadata.name,status.url,status.latestReadyRevisionName,status.conditions[0].type,status.conditions[0].status)"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE" --project "$PROJECT_ID" --limit 80 --format="value(timestamp,severity,textPayload,jsonPayload.message)"
