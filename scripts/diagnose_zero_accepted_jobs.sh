#!/usr/bin/env bash

# Context Anchor for Subdirectory Migration
cd "$(dirname "$0")/.."
set -euo pipefail

SERVICE_URL="https://job-hunter-pro-5t3wttw2ua-uc.a.run.app"

echo "=== ZERO ACCEPTED LIVE JOBS DIAGNOSTIC ==="
echo "NO DEPLOY. NO /api/ingest. NO NEW /api/jobs LIVE CALL."
echo "PWD=$(pwd)"
echo

echo "=== 1) Existing live /api/jobs result you already pulled ==="
if [ -f data/live_jobs_now.json ]; then
  python3 - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("data/live_jobs_now.json").read_text())
print("TOP_KEYS=", sorted(data.keys()))
for k in ["status","count","unfiltered_count","raw_count","query_count","nearby_restaurant_count","source"]:
    print(f"{k}=", data.get(k))
print("rules=", data.get("rules"))
print("data_len=", len(data.get("data", [])))
PY
else
  echo "data/live_jobs_now.json missing"
fi

echo
echo "=== 2) Inspect backend code for /api/jobs and rejection/debug support ==="
grep -n "def .*jobs\|@app.route(\"/api/jobs\"\|@app.route('/api/jobs'\|/api/debug/jobs\|rejected\|rejection\|raw_count\|nearby_restaurant_count\|outside_radius\|transit_too_long\|not_food_service\|food_only\|max_radius_miles\|max_transit_minutes" api/index.py app.py api/*.py 2>/dev/null || true

echo
echo "=== 3) Print the /api/jobs function area from api/index.py ==="
python3 - <<'PY'
from pathlib import Path

p = Path("api/index.py")
text = p.read_text(errors="replace").splitlines()

interesting = []
for i, line in enumerate(text, 1):
    if '@app.route("/api/jobs"' in line or "@app.route('/api/jobs'" in line or 'def api_jobs' in line or 'def jobs' in line:
        interesting.append(i)

if not interesting:
    print("Could not find /api/jobs marker in api/index.py")
else:
    start = max(1, interesting[0] - 40)
    end = min(len(text), interesting[0] + 260)
    for n in range(start, end + 1):
        print(f"{n:04d}: {text[n-1]}")
PY

echo
echo "=== 4) Check debug endpoint WITHOUT assuming it is safe ==="
python3 - <<'PY'
from pathlib import Path
import re

text = Path("api/index.py").read_text(errors="replace")
m = re.search(r'@app\.route\([\'"]/api/debug/jobs[\'"].*?(?=\n@app\.route|\Z)', text, flags=re.S)
if not m:
    print("NO_DEBUG_ROUTE_FOUND")
else:
    block = m.group(0)
    print("DEBUG_ROUTE_FOUND")
    risky_terms = ["serpapi", "run_live", "search_jobs", "requests.get", "places", "distance_matrix"]
    for term in risky_terms:
        if term in block.lower():
            print("DEBUG_ROUTE_CONTAINS_RISKY_TERM=", term)
    print("--- DEBUG ROUTE BLOCK PREVIEW ---")
    for line in block.splitlines()[:160]:
        print(line)
PY

echo
echo "=== 5) Safe live endpoint summaries, excluding /api/jobs ==="
for P in "/api/health" "/api/usage" "/api/opportunities" "/api/history" "/api/debug/jobs"; do
  echo
  echo "--- $P ---"
  curl -sS "$SERVICE_URL$P" -o "probe_${P//\//_}.json" -w "HTTP %{http_code}\n" || true
  python3 - "$P" "probe_${P//\//_}.json" <<'PY'
import json, sys
from pathlib import Path

path = sys.argv[1]
file = Path(sys.argv[2])
text = file.read_text(errors="replace")
print("BYTES=", len(text))
print("PREVIEW=", text[:500].replace("\n"," "))

try:
    data = json.loads(text)
except Exception as e:
    print("NOT_JSON", e)
    raise SystemExit(0)

if isinstance(data, dict):
    print("TOP_KEYS=", sorted(data.keys()))
    for key in ["status","count","raw_count","accepted_count","rejected_count","nearby_restaurant_count","job_count","batch_count","source","message"]:
        if key in data:
            print(key, "=", data[key])
    for key in ["data","jobs","accepted","rejected","raw","opportunities","batches"]:
        if key in data:
            v = data[key]
            if isinstance(v, list):
                print(key, "LIST_LEN", len(v))
                if v:
                    print(key, "FIRST_KEYS", sorted(v[0].keys()) if isinstance(v[0], dict) else type(v[0]).__name__)
            elif isinstance(v, dict):
                print(key, "DICT_KEYS", sorted(v.keys()))
PY
done

echo
echo "=== 6) Conclusion target ==="
echo "If /api/debug/jobs exposes rejected/raw records, patch frontend to render them."
echo "If /api/debug/jobs is empty or missing, patch backend /api/jobs to return rejected[] evidence from the existing pipeline, not fake jobs."
echo "If nearby_restaurant_count is 0 while /api/opportunities has data, patch /api/jobs to share the same Places/opportunities resolver path."
