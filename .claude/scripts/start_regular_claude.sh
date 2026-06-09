#!/usr/bin/env bash
set -euo pipefail
unset CLAUDE_CODE_USE_VERTEX
unset ANTHROPIC_VERTEX_PROJECT_ID
unset CLOUD_ML_REGION
unset GOOGLE_CLOUD_PROJECT
unset CLOUDSDK_CONFIG
cd /workspaces/Job_Hunter_Platform/job-hunter-pro
. .venv/bin/activate 2>/dev/null || true
echo "Regular Claude mode requested. If your Claude usage is exhausted, wait until it resets."
echo "When Claude opens, paste:"
echo ".claude/tasks/ULTIMATE_AUTONOMOUS_REPAIR_PROMPT.txt"
echo
claude
