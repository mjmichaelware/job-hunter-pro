#!/usr/bin/env bash

# Context Anchor for Subdirectory Migration
cd "$(dirname "$0")/.."

PROJECT_ID="ai-job-agent-498702"
REGION="us-central1"
SERVICE="job-hunter-pro"

echo "=== S10-H PIPELINE STREAM TRUTH FIX ==="
echo "PWD=$(pwd)"
echo

fail() {
  echo
  echo "FAIL: $1"
  exit 1
}

[ -f app.py ] || fail "app.py not found; not in repo root"
[ -f web/static/js/api.js ] || fail "web/static/js/api.js missing"
[ -f web/static/js/charts.js ] || fail "web/static/js/charts.js missing"

echo "=== 1) Inspect current frontend SSE references ==="
grep -Rni "/api/events/pipeline\|/api/pipeline/stream\|EventSource\|SSE DISCONNECTED\|Backend SSE logic\|pipeline_stream" \
  web/templates web/static/js web/static/css app.py api 2>/dev/null || true

echo
echo "=== 2) Inspect real Flask route map ==="
python3 - <<'PY' || exit 1
from app import app
routes = sorted(str(r.rule) for r in app.url_map.iter_rules())
for r in routes:
    print(r)
print("HAS_/api/events/pipeline=", "/api/events/pipeline" in routes)
print("HAS_/api/pipeline/stream=", any(r.startswith("/api/pipeline/stream") for r in routes))
print("HAS_TEXT_EVENT_STREAM_ROUTE=", any("event" in r or "stream" in r for r in routes))
PY

echo
echo "=== 3) Decide from backend truth, not UI guess ==="
ROUTE_STATE="$(python3 - <<'PY'
from app import app
routes = sorted(str(r.rule) for r in app.url_map.iter_rules())
if "/api/events/pipeline" in routes or any(r.startswith("/api/pipeline/stream") for r in routes):
    print("present")
else:
    print("absent")
PY
)"

echo "PIPELINE_SSE_ROUTE_STATE=$ROUTE_STATE"

if [ "$ROUTE_STATE" = "present" ]; then
  echo "A pipeline SSE route exists. No frontend disabling patch applied."
else
  echo "No pipeline SSE route exists. Applying S10-H frontend feature-gate patch."
  mkdir -p .repair_backups
  TS="$(date +%Y%m%d_%H%M%S)"
  cp web/static/js/api.js ".repair_backups/api.js.s10h.${TS}"
  cp web/static/js/charts.js ".repair_backups/charts.js.s10h.${TS}"

  python3 - <<'PY' || exit 1
from pathlib import Path

api = Path("web/static/js/api.js")
charts = Path("web/static/js/charts.js")

api_text = api.read_text(encoding="utf-8")
old_api_1 = "pipeline_stream: '/api/events/pipeline'"
old_api_2 = 'pipeline_stream: "/api/events/pipeline"'

if old_api_1 in api_text:
    api_text = api_text.replace(old_api_1, "pipeline_stream: null", 1)
    print("api.js: pipeline_stream set to null")
elif old_api_2 in api_text:
    api_text = api_text.replace(old_api_2, "pipeline_stream: null", 1)
    print("api.js: pipeline_stream set to null")
elif "pipeline_stream: null" in api_text:
    print("api.js: already feature-gated")
else:
    raise SystemExit("api.js: expected pipeline_stream entry not found; inspect manually")

api.write_text(api_text, encoding="utf-8")

charts_text = charts.read_text(encoding="utf-8")

replacements = {
    "📡 Readiness: SSE DISCONNECTED": "📡 Pipeline stream unavailable",
    "The Pipeline Engine Stream requires a persistent EventSource connection to <code>${API_URLS.pipeline_stream}</code>.": "Live pipeline streaming is not enabled in this build. Static dashboard data remains authoritative.",
    "[404] Endpoint Not Found - Backend SSE logic is not yet deployed.": "SSE endpoint is not mounted in this build; no live pipeline connection is attempted.",
    "color: var(--danger);": "color: var(--muted);",
}

changed = False
for old, new in replacements.items():
    if old in charts_text:
        charts_text = charts_text.replace(old, new)
        changed = True

# Guard against actual EventSource usage to the absent route.
if "new EventSource" in charts_text and "API_URLS.pipeline_stream" in charts_text:
    raise SystemExit("charts.js contains real EventSource construction. Do not patch blindly; inspect that block manually.")

if changed:
    print("charts.js: red 404 SSE copy replaced with neutral unavailable state")
elif "Pipeline stream unavailable" in charts_text or "SSE endpoint is not mounted" in charts_text:
    print("charts.js: already has neutral unavailable state")
else:
    raise SystemExit("charts.js: expected hardcoded SSE fallback text not found; inspect manually")

charts.write_text(charts_text, encoding="utf-8")
PY
fi

echo
echo "=== 4) Post-patch inspection ==="
grep -Rni "/api/events/pipeline\|/api/pipeline/stream\|EventSource\|SSE DISCONNECTED\|Backend SSE logic\|Pipeline stream unavailable\|pipeline_stream" \
  web/templates web/static/js web/static/css app.py api 2>/dev/null || true

echo
echo "=== 5) Compile all tracked Python ==="
python3 -m py_compile $(git ls-files '*.py') || fail "Python compile failed"

echo
echo "=== 6) Local Flask proof ==="
python3 - <<'PY' || exit 1
from pathlib import Path
from app import app

c = app.test_client()

for path in ["/", "/api/health", "/api/events/pipeline"]:
    r = c.get(path)
    print(path, r.status_code, r.content_type)

root = c.get("/")
assert root.status_code == 200

health = c.get("/api/health")
assert health.status_code == 200

charts = c.get("/static/js/charts.js")
assert charts.status_code == 200
charts_text = charts.get_data(as_text=True)

api_js = c.get("/static/js/api.js")
assert api_js.status_code == 200
api_text = api_js.get_data(as_text=True)

routes = sorted(str(r.rule) for r in app.url_map.iter_rules())
sse_exists = "/api/events/pipeline" in routes or any(r.startswith("/api/pipeline/stream") for r in routes)

if not sse_exists:
    assert "Backend SSE logic is not yet deployed" not in charts_text
    assert "SSE DISCONNECTED" not in charts_text
    assert "persistent EventSource connection" not in charts_text
    assert "new EventSource" not in charts_text
    assert "pipeline_stream: null" in api_text
    print("PASS: backend SSE absent, frontend is feature-gated and neutral.")
else:
    print("PASS: backend SSE exists; no absent-route frontend disabling required.")

print("LOCAL PROOF PASSED")
PY

echo
echo "=== 7) Diff proof ==="
git diff -- web/static/js/api.js web/static/js/charts.js
git diff --check || fail "git diff --check failed"

echo
echo "=== 8) Commit only if frontend files changed ==="
if git diff --quiet -- web/static/js/api.js web/static/js/charts.js; then
  echo "No frontend changes to commit."
else
  git add web/static/js/api.js web/static/js/charts.js
  git commit -m "S10-H gate pipeline stream when SSE route is absent" || fail "commit failed"
  git push origin main || fail "push failed"
fi

echo
echo "=== 9) Wait for deploy trigger, then verify Cloud Run ==="
sleep 120

SERVICE_URL="$(gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format='value(status.url)' 2>/dev/null)"

[ -n "$SERVICE_URL" ] || fail "could not read Cloud Run service URL"

gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format="table(status.url,status.latestReadyRevisionName,status.traffic[0].revisionName,status.traffic[0].percent)" || fail "Cloud Run describe failed"

echo
echo "SERVICE_URL=$SERVICE_URL"

echo
echo "=== 10) Live health ==="
curl -fsS "$SERVICE_URL/api/health" || fail "live /api/health failed"
echo

echo
echo "=== 11) Live SSE truth proof ==="
echo "--- live route status /api/events/pipeline ---"
curl -sS -o /tmp/s10h_pipeline_route_body.txt -w "%{http_code}\n" "$SERVICE_URL/api/events/pipeline"

echo "--- live api.js check ---"
curl -fsS "$SERVICE_URL/static/js/api.js?v=$(date +%s)" \
  | grep -E "pipeline_stream|/api/events/pipeline|/api/pipeline/stream" || true

echo "--- live charts.js forbidden strings check ---"
FORBIDDEN="$(curl -fsS "$SERVICE_URL/static/js/charts.js?v=$(date +%s)" \
  | grep -E "Backend SSE logic is not yet deployed|SSE DISCONNECTED|persistent EventSource connection|new EventSource" || true)"

if [ -n "$FORBIDDEN" ]; then
  echo "$FORBIDDEN"
  fail "live charts.js still contains forbidden SSE copy or EventSource construction"
fi

echo "PASS: live UI no longer claims a 404 backend SSE failure or attempts absent SSE."
echo
echo "OPEN:"
echo "$SERVICE_URL/?v=s10h-$(date +%s)"
