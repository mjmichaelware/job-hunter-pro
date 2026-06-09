#!/usr/bin/env bash
set -euo pipefail
echo "=== REPO ==="
pwd
git status --short
echo
echo "=== KEY FILES ==="
ls -la app.py api/index.py api/__init__.py search/live_provider_bridge.py web/static/js/render_jobs.js 2>/dev/null || true
echo
echo "=== IMPORTANT GREP ==="
grep -RIn "MAX_RAW_JOBS\|MAX_SERP_QUERIES\|def rejection_reasons\|provider_breakdown\|fetch_provider_raw_jobs\|dry_run\|/api/ingest\|Bearer\|OIDC\|live discovery" app.py api search providers web/static/js web/templates 2>/dev/null || true
