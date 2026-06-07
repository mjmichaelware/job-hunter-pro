#!/data/data/com.termux/files/usr/bin/bash
# scripts/make_scheduler_oidc.sh - Create Cloud Scheduler job with OIDC auth
set -euo pipefail

DRY_RUN=0

# Default or Environment Variables
PROJECT_ID=${PROJECT_ID:-"ai-job-agent-498702"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="job-hunter-pro"
JOB_NAME=${JOB_NAME:-"job-hunter-daily-ingest"}
SCHEDULE=${SCHEDULE:-"0 9 * * *"} # 9 AM daily
SCHEDULER_SA=${SCHEDULER_SA:-"job-hunter-scheduler@${PROJECT_ID}.iam.gserviceaccount.com"}

usage() {
    echo "Usage: $0 [--dry-run]"
    echo "Requires environment variables or defaults: PROJECT_ID, REGION, JOB_NAME, SCHEDULE, SCHEDULER_SA"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        *) usage ;;
    esac
done

echo "--- Creating Cloud Scheduler Job (OIDC) ---"

# Validate required variables
MISSING=()
[[ -z "$PROJECT_ID" ]] && MISSING+=("PROJECT_ID")
[[ -z "$REGION" ]] && MISSING+=("REGION")
[[ -z "$JOB_NAME" ]] && MISSING+=("JOB_NAME")
[[ -z "$SCHEDULE" ]] && MISSING+=("SCHEDULE")
[[ -z "$SCHEDULER_SA" ]] && MISSING+=("SCHEDULER_SA")

if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo "Error: Missing required variables: ${MISSING[*]}"
    exit 1
fi

# Fetch Service URL (Requires gcloud access)
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)' 2>/dev/null || echo "https://job-hunter-pro-placeholder.a.run.app")

INGEST_URL="${SERVICE_URL}/api/ingest"

# Note: Using --oidc-token-audience which is the same as the target URL by default
SCHEDULER_CMD="gcloud scheduler jobs create http $JOB_NAME \
    --project $PROJECT_ID \
    --location $REGION \
    --schedule "$SCHEDULE" \
    --uri "$INGEST_URL" \
    --http-method POST \
    --oidc-service-account-email $SCHEDULER_SA \

    --oidc-token-audience $SERVICE_URL"

if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY-RUN] Scheduler command shape (NO TOKEN IN URL):"
    echo "[DRY-RUN] $SCHEDULER_CMD"
    exit 0
fi

# Real Run (Belongs to S12)
echo "Executing real scheduler creation..."
eval "$SCHEDULER_CMD"

echo "Scheduler job $JOB_NAME created/updated."
