#!/bin/bash

# scripts/make_scheduler_oidc.sh
# Prints safe gcloud commands for creating/updating Google Cloud Scheduler jobs with OIDC.
# No secrets or real URLs are printed here.

PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "ai-job-agent-498702")
REGION="us-central1"
SERVICE_NAME="job-hunter-pro"
SERVICE_URL="https://${SERVICE_NAME}-xxxx-uc.a.run.app" # Placeholder for real URL
SERVICE_ACCOUNT="scheduler-job@${PROJECT_ID}.iam.gserviceaccount.com"

echo "### Google Cloud Scheduler OIDC Configuration Commands ###"
echo "# These commands configure a job to call your /api/ingest endpoint securely."
echo ""

echo "1. Create Service Account (if needed):"
echo "gcloud iam service-accounts create scheduler-job --display-name='Job Hunter Pro Scheduler Account'"
echo ""

echo "2. Grant Invoker role to Service Account for Cloud Run:"
echo "gcloud run services add-iam-policy-binding ${SERVICE_NAME} \\"
echo "  --member='serviceAccount:${SERVICE_ACCOUNT}' \\"
echo "  --role='roles/run.invoker' \\"
echo "  --region=${REGION}"
echo ""

echo "3. Create/Update Scheduler Job with OIDC:"
echo "gcloud scheduler jobs create http ingest-job \\"
echo "  --schedule='0 9 * * *' \\" # Every day at 9 AM
echo "  --uri='${SERVICE_URL}/api/ingest' \\"
echo "  --http-method=POST \\"
echo "  --oidc-service-account-email=${SERVICE_ACCOUNT} \\"
echo "  --oidc-token-audience='${SERVICE_URL}'"
echo ""

echo "### Security Note ###"
echo "Always use the real Cloud Run Service URL for --uri and --oidc-token-audience."
echo "No secrets are stored in these commands."
