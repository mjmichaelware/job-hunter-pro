#!/usr/bin/env bash
set -euo pipefail
unset CLAUDE_CODE_USE_VERTEX
unset ANTHROPIC_VERTEX_PROJECT_ID
unset CLOUD_ML_REGION
unset GOOGLE_CLOUD_PROJECT
unset CLOUDSDK_CONFIG
cd /workspaces/Job_Hunter_Platform/job-hunter-pro
. .venv/bin/activate 2>/dev/null || true
echo "Regular Claude mode. If usage is exhausted, wait until reset."
echo
echo "Paste this prompt into Claude:"
echo "/read .claude/tasks/NEUTRON_STAR_AUTONOMOUS_REPAIR_PROMPT.txt"
echo
echo "Or open it manually:"
echo "cat .claude/tasks/NEUTRON_STAR_AUTONOMOUS_REPAIR_PROMPT.txt"
echo
claude
