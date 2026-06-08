#!/usr/bin/env bash
set -euo pipefail

echo "=== COMPARE LEGACY REAL-DATA DASHBOARD TO CURRENT S10 WEB SHELL ==="
echo "PWD=$(pwd)"
echo

echo "=== 1) Confirm current root template path and app route ==="
grep -Rni "def index\|render_template\|render_template_string" app.py api/index.py web/templates/index.html 2>/dev/null || true
echo

echo "=== 2) Extract real-data dashboard section from api/index.py ==="
grep -n "Persistent AI Job Intelligence\|Run Live Discovery\|loadLiveJobs\|loadOpportunities\|loadHistory\|statJobs\|statRaw\|statOpps\|statSerp\|fetch('/api/jobs'\|fetch(\"/api/jobs\"\|/api/opportunities\|/api/history\|/api/usage" api/index.py || true
echo

echo "=== 3) Current S10 frontend API wiring ==="
grep -Rni "API_URLS\|prepare-discovery-btn\|trigger-discovery-btn\|loadJobs\|loadOverview\|loadOpportunities\|loadHistory\|dry_run\|/api/jobs\|/api/opportunities\|/api/history\|/api/usage" web/templates/index.html web/static/js 2>/dev/null || true
echo

echo "=== 4) Current S10 DOM IDs for stats/buttons/jobs ==="
grep -Rni "overview-accepted-count\|overview-opp-count\|overview-batch-count\|overview-budget-burn\|jobs-container\|prepare-discovery-btn\|trigger-discovery-btn\|statJobs\|statRaw\|statOpps\|statSerp" web/templates/index.html web/static/js 2>/dev/null || true
echo

echo "=== 5) Safe local endpoint shapes only, no live discovery ==="
python3 - <<'PY'
from app import app
import json

c = app.test_client()
paths = [
    "/api/usage",
    "/api/jobs?dry_run=1",
    "/api/opportunities",
    "/api/history",
]
for path in paths:
    r = c.get(path)
    print("\nPATH", path, "STATUS", r.status_code, "TYPE", r.content_type)
    txt = r.get_data(as_text=True)
    try:
        data = r.get_json()
        if isinstance(data, dict):
            print("TOP_KEYS", sorted(data.keys()))
            for key in ["jobs", "opportunities", "batches", "history", "total_searches_left", "budget", "counts", "dry_run", "message"]:
                if key in data:
                    val = data[key]
                    if isinstance(val, list):
                        print(key, "LIST_LEN", len(val))
                        if val:
                            print(key, "FIRST_KEYS", sorted(val[0].keys()) if isinstance(val[0], dict) else type(val[0]).__name__)
                    elif isinstance(val, dict):
                        print(key, "DICT_KEYS", sorted(val.keys()))
                    else:
                        print(key, repr(val))
        else:
            print("JSON_TYPE", type(data).__name__)
    except Exception:
        print(txt[:500].replace("\n"," "))
PY

echo
echo "=== 6) Demo/fake data guard ==="
grep -Rni "Customer Support Representative\|Peer Support Specialist\|Demo Jobs\|demoJobs\|sampleJobs\|mockJobs\|fake" app.py api web static templates 2>/dev/null || true
echo

echo "=== DONE: no files changed, no deploy, no live /api/jobs called ==="
