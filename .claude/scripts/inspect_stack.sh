#!/usr/bin/env bash
set -euo pipefail
pwd
git status --short
echo "=== key files ==="
ls -la app.py api/index.py api/__init__.py api/ingest.py   search/federated.py search/budget.py search/usage_tracker.py   pipeline/reject.py pipeline/normalize.py pipeline/run.py   web/templates/index.html 2>/dev/null || true
echo "=== key patterns ==="
rg -n "MAX_RADIUS_MILES|MAX_TRANSIT_SECONDS|FOOD_TERMS|resolution_flags|needs_resolution|provider_breakdown|dry_run|_surface|placeholder_blueprint|def fetch_all|def run_pipeline|def reject|def normalize"   app.py api search pipeline providers web/static/js web/templates 2>/dev/null || true
