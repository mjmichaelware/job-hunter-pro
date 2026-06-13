#!/usr/bin/env bash

# Context Anchor for Subdirectory Migration
cd "$(dirname "$0")/.."
set -euo pipefail

PROJECT_ID="ai-job-agent-498702"
REGION="us-central1"
SERVICE="job-hunter-pro"
LIVE_URL="https://job-hunter-pro-5t3wttw2ua-uc.a.run.app"

echo "=== LIVE DATA REGRESSION FORENSICS: NO DEPLOY, NO INGEST, NO LIVE JOBS ==="
echo "PWD=$(pwd)"
echo

echo "=== 1) Current git state ==="
git status --short
git log --oneline -12
echo

echo "=== 2) Search current code for demo/fallback surface ==="
grep -Rni \
  "Cloud Run Online\|Demo Jobs\|Customer Support Representative\|Peer Support Specialist\|Persistent AI Job Intelligence\|Run Live Discovery\|SERPAPI LEFT\|Visible Jobs\|restaurant job discovery" \
  app.py api web templates static . 2>/dev/null || true
echo

echo "=== 3) Search commit history for the real live-data surface ==="
for TERM in \
  "Persistent AI Job Intelligence" \
  "Run Live Discovery" \
  "SERPAPI LEFT" \
  "Visible Jobs" \
  "Loaded 160 nearby restaurant opportunities" \
  "Customer Support Representative" \
  "Demo Jobs"
do
  echo
  echo "--- git grep history: $TERM ---"
  git log --all --format='%H %s' -G "$TERM" -- . 2>/dev/null | head -20 || true
done
echo

echo "=== 4) Current Flask route map ==="
python3 - <<'PY'
from app import app
for r in sorted(app.url_map.iter_rules(), key=lambda x: str(x.rule)):
    print(f"{','.join(sorted(r.methods)):<32} {r.rule:<45} -> {r.endpoint}")
PY
echo

echo "=== 5) Safe local endpoint proof only ==="
python3 - <<'PY'
from app import app
c = app.test_client()

paths = [
    "/",
    "/api/health",
    "/api/usage",
    "/api/jobs?dry_run=1",
    "/api/opportunities",
    "/api/history",
    "/api/providers",
    "/api/industries",
]

for path in paths:
    r = c.get(path)
    body = r.get_data(as_text=True)[:220].replace("\n", " ")
    print(f"{path:<28} {r.status_code:<4} {r.content_type:<30} {body}")
PY
echo

echo "=== 6) Live surface fingerprint ==="
echo "--- live root title/keywords ---"
curl -fsS "$LIVE_URL/?v=forensics-$(date +%s)" \
  | grep -oE "Cloud Run Online|Demo Jobs|Persistent AI Job Intelligence|Run Live Discovery|Job Hunter Pro|Customer Support Representative|Peer Support Specialist|SERPAPI LEFT|Visible Jobs" \
  | sort | uniq -c || true

echo
echo "--- live safe endpoints only ---"
for P in "/api/health" "/api/usage" "/api/jobs?dry_run=1" "/api/opportunities" "/api/history" "/api/providers" "/api/industries"; do
  printf "%-28s " "$P"
  curl -sS -o /tmp/jhp_probe.txt -w "%{http_code} %{content_type}\n" "$LIVE_URL$P" || true
  head -c 180 /tmp/jhp_probe.txt | tr '\n' ' '
  echo
done
echo

echo "=== 7) Current files likely controlling root/frontend ==="
for F in \
  app.py \
  api/index.py \
  web/templates/index.html \
  templates/index.html \
  web/static/js/api.js \
  web/static/js/state.js \
  web/static/js/state_sync.js \
  web/static/js/render_jobs.js \
  static/js/main.js
do
  if [ -f "$F" ]; then
    echo
    echo "--- $F ---"
    sed -n '1,220p' "$F" | grep -nE "render_template|render_template_string|Cloud Run Online|Demo Jobs|Persistent AI|API_URLS|jobs|opportunities|dry_run|Run Live Discovery|Customer Support|Peer Support|safeFetch|fetch" || true
  fi
done

echo
echo "=== DONE: paste this output. No files changed. ==="
