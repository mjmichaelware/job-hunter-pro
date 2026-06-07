#!/data/data/com.termux/files/usr/bin/bash
# scripts/deploy.sh - Deploy Job Hunter Pro to Cloud Run
set -euo pipefail

DRY_RUN=0
PROJECT_ID="ai-job-agent-498702"
SERVICE_NAME="job-hunter-pro"
REGION="us-central1"

usage() {
    echo "Usage: $0 [--dry-run]"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        *) usage ;;
    esac
done

echo "--- Deploying $SERVICE_NAME to $PROJECT_ID ($REGION) ---"

# Step 1: Compile Checks (Local)
echo "Running local compile checks..."
if ! python3 -m compileall -q . ; then
    echo "Error: Python compilation failed. Fix errors before deploying."
    exit 1
fi
echo "Running py_compile checks..."
python3 - <<'PYCOMPILE'
from pathlib import Path
import py_compile

skip_parts = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', '.mypy_cache'}
py_files = [
    p for p in Path('.').rglob('*.py')
    if not any(part in skip_parts for part in p.parts)
]
for path in py_files:
    py_compile.compile(str(path), doraise=True)
print(f"py_compile passed for {len(py_files)} Python files.")
PYCOMPILE
echo "Compile checks passed."

# Define secret mappings
SECRETS=(
    "SERPAPI_KEY=SERPAPI_KEY:latest" # Secret Manager reference only; no provider call
    "GROQ_API_KEY=GROQ_API_KEY:latest"
    "OPENAI_API_KEY=OPENAI_API_KEY:latest"
    "GEMINI_API_KEY=GEMINI_API_KEY:latest"
    "ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest"
    "XAI_API_KEY=XAI_API_KEY:latest"
    "ADZUNA_APP_ID=ADZUNA_APP_ID:latest"
    "ADZUNA_APP_KEY=ADZUNA_APP_KEY:latest"
    "USAJOBS_API_KEY=USAJOBS_API_KEY:latest,USAJOBS_EMAIL=USAJOBS_EMAIL:latest"
    "JOOBLE_API_KEY=JOOBLE_API_KEY:latest"
    "CAREERJET_AFFID=CAREERJET_AFFID:latest"
    "GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY:latest"
)

# Join secrets with commas
SECRETS_JOINED=$(IFS=,; echo "${SECRETS[*]}")

DEPLOY_CMD="gcloud run deploy $SERVICE_NAME \
    --source . \
    --project $PROJECT_ID \
    --region $REGION \
    --allow-unauthenticated \
    --set-secrets $SECRETS_JOINED"

if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY-RUN] Deploy command shape:"
    echo "[DRY-RUN] $DEPLOY_CMD"
    echo ""
    echo "[DRY-RUN] Post-deploy verification commands (for S12):"
    echo "[DRY-RUN] gcloud run services describe $SERVICE_NAME --project $PROJECT_ID --region $REGION --format='value(status.url)'"
    echo "[DRY-RUN] curl -I \$(gcloud run services describe $SERVICE_NAME --project $PROJECT_ID --region $REGION --format='value(status.url)')/api/health"
    exit 0
fi

# Real Run (belonging to S12, but implemented here for completeness)
echo "Executing real deploy..."
eval "$DEPLOY_CMD"

echo "Deploy complete."
echo "URL: $(gcloud run services describe $SERVICE_NAME --project $PROJECT_ID --region $REGION --format='value(status.url)')"
