#!/usr/bin/env bash
set -euo pipefail

echo "=== PROVIDER FAN-OUT GAP PROOF ==="
echo "NO DEPLOY. NO /api/jobs. NO /api/ingest."
echo "PWD=$(pwd)"
echo

echo "=== 1) Current /api/jobs path ==="
grep -n "def fetch_jobs_live\|def serpapi_jobs\|MAX_SERP_QUERIES\|raw_job_queries\|for query\|serpapi_jobs(query)\|providers\|adzuna\|usajobs\|jooble\|careerjet\|themuse\|federated" api/index.py app.py search/*.py providers/**/*.py providers/*.py 2>/dev/null || true

echo
echo "=== 2) Print fetch_jobs_live implementation ==="
python3 - <<'PY'
from pathlib import Path

p = Path("api/index.py")
lines = p.read_text(errors="replace").splitlines()

markers = []
for i, line in enumerate(lines, 1):
    if "def fetch_jobs_live" in line:
        markers.append(i)

if not markers:
    print("fetch_jobs_live not found")
else:
    start = max(1, markers[0] - 30)
    end = min(len(lines), markers[0] + 90)
    for n in range(start, end + 1):
        print(f"{n:04d}: {lines[n-1]}")
PY

echo
echo "=== 3) Provider/source files that exist ==="
find providers search api -type f \( -name "*.py" -o -name "*.js" \) | sort

echo
echo "=== 4) Provider routes currently visible ==="
python3 - <<'PY'
from app import app
for r in sorted(app.url_map.iter_rules(), key=lambda x: str(x.rule)):
    s = str(r.rule)
    if "provider" in s or "search" in s or "jobs" in s or "opportunities" in s:
        print(f"{','.join(sorted(r.methods)):<30} {s:<45} -> {r.endpoint}")
PY

echo
echo "=== 5) Safe provider/status endpoint shapes ==="
python3 - <<'PY'
from app import app
c = app.test_client()

for path in ["/api/providers", "/api/_surface", "/api/usage", "/api/opportunities"]:
    r = c.get(path)
    print("\n", path, r.status_code, r.content_type)
    txt = r.get_data(as_text=True)
    print(txt[:1200].replace("\n", " "))
PY

echo
echo "=== 6) Static import check for federated/provider modules ==="
python3 - <<'PY'
mods = [
    "providers",
    "providers.registry",
    "providers.search.serpapi_jobs",
    "providers.search.adzuna",
    "providers.search.usajobs",
    "providers.search.jooble",
    "providers.search.careerjet",
    "providers.search.themuse",
    "search.federated",
]
for m in mods:
    try:
        mod = __import__(m, fromlist=["*"])
        print("IMPORT_OK", m)
        names = [n for n in dir(mod) if not n.startswith("_")]
        print("  names:", ", ".join(names[:40]))
    except Exception as e:
        print("IMPORT_FAIL", m, type(e).__name__, str(e))
PY

echo
echo "=== 7) Compile proof ==="
python3 -m py_compile $(git ls-files '*.py')

echo
echo "=== RESULT INTERPRETATION ==="
echo "If fetch_jobs_live only calls serpapi_jobs(query), then /api/jobs is NOT using your 10 APIs."
echo "If provider files import but are not called by fetch_jobs_live, the engines exist but are not wired."
echo "If /api/providers shows configured providers but /api/jobs ignores them, the fix is to replace fetch_jobs_live with federated provider fan-out, not UI changes."
