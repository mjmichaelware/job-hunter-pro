#!/usr/bin/env bash
set -euo pipefail

echo "=== JOB HUNTER PRO SURFACE TRUTH MATRIX ==="
echo "NO DEPLOY. NO /api/ingest. NO LIVE /api/jobs."
echo "PWD=$(pwd)"
echo

[ -f app.py ] || { echo "FAIL: app.py missing; not repo root"; exit 1; }

mkdir -p docs
OUT="docs/S10_SURFACE_TRUTH_MATRIX.md"

python3 - <<'PY' > "$OUT"
from pathlib import Path
import ast, re, json
from datetime import datetime, timezone

print("# S10 Surface Truth Matrix")
print()
print(f"Generated: {datetime.now(timezone.utc).isoformat()}")
print()
print("Purpose: expose every existing backend route, frontend caller, hidden UI control, and unavailable/boilerplate surface without creating fake backend code.")
print()

# ---------- Flask mounted route map ----------
print("## 1. Mounted Flask route map")
print()
try:
    from app import app
    mounted = []
    for r in sorted(app.url_map.iter_rules(), key=lambda x: str(x.rule)):
        mounted.append({
            "rule": str(r.rule),
            "endpoint": r.endpoint,
            "methods": ",".join(sorted(m for m in r.methods if m not in {"HEAD", "OPTIONS"})) or ",".join(sorted(r.methods)),
        })
    for item in mounted:
        print(f"- `{item['methods']}` `{item['rule']}` -> `{item['endpoint']}`")
except Exception as e:
    mounted = []
    print(f"FAILED TO IMPORT app: `{type(e).__name__}: {e}`")
print()

mounted_rules = {x["rule"] for x in mounted}

# ---------- Declared routes in source ----------
print("## 2. Declared backend routes found in source")
print()
declared = []
for p in list(Path("api").rglob("*.py")) + [Path("app.py")]:
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r'@(?:app|bp|api|blueprint|[\w_]+)\.route\(\s*[\'"]([^\'"]+)[\'"]', text):
        declared.append((str(p), m.start(), m.group(1)))
    for m in re.finditer(r'add_url_rule\(\s*[\'"]([^\'"]+)[\'"]', text):
        declared.append((str(p), m.start(), m.group(1)))

if not declared:
    print("- No decorator-style route declarations found.")
else:
    for file, pos, route in declared:
        status = "MOUNTED" if route in mounted_rules else "DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL"
        print(f"- `{route}` — `{status}` — `{file}`")
print()

# ---------- API dispatch/catch-all note ----------
print("## 3. Catch-all / dispatch risk")
print()
catchalls = [r for r in mounted_rules if "<path:path>" in r or "<path:" in r]
if catchalls:
    print("Mounted catch-all routes:")
    for r in catchalls:
        print(f"- `{r}`")
    print()
    print("Meaning: some API behavior may be hidden behind a dispatcher instead of visible as explicit Flask routes. A file can contain logic and still not appear as a first-class route.")
else:
    print("No catch-all API route detected.")
print()

# ---------- Backend modules that may be engines ----------
print("## 4. Engine/module inventory")
print()
engine_dirs = ["providers", "search", "pipeline", "geo", "store", "industries", "ingest", "api", "models", "core"]
for d in engine_dirs:
    root = Path(d)
    if not root.exists():
        print(f"- `{d}/` MISSING")
        continue
    files = sorted(str(p) for p in root.rglob("*.py") if "__pycache__" not in str(p))
    print(f"### `{d}/` ({len(files)} python files)")
    for f in files:
        text = Path(f).read_text(encoding="utf-8", errors="replace")
        route_hint = "ROUTE_DECLARATIONS" if "@app.route" in text or ".route(" in text else ""
        class_hint = "CLASSES" if re.search(r"^\s*class\s+\w+", text, flags=re.M) else ""
        func_count = len(re.findall(r"^\s*def\s+\w+", text, flags=re.M))
        async_count = len(re.findall(r"^\s*async\s+def\s+\w+", text, flags=re.M))
        print(f"- `{f}` funcs={func_count} async={async_count} {class_hint} {route_hint}".rstrip())
    print()

# ---------- Frontend API URLs and fetches ----------
print("## 5. Frontend API wiring")
print()
frontend_files = []
for root in ["web/templates", "web/static/js", "web/static/css", "templates", "static"]:
    rp = Path(root)
    if rp.exists():
        frontend_files.extend([p for p in rp.rglob("*") if p.is_file() and p.suffix in {".html", ".js", ".css"}])

api_refs = []
hidden_refs = []
placeholder_refs = []
for p in frontend_files:
    text = p.read_text(encoding="utf-8", errors="replace")
    for line_no, line in enumerate(text.splitlines(), 1):
        if re.search(r"/api/|fetch\(|safeFetch|API_URLS|EventSource", line):
            api_refs.append((str(p), line_no, line.strip()))
        if re.search(r"display\s*:\s*none|hidden|aria-hidden=[\"']true|disabled", line, re.I):
            hidden_refs.append((str(p), line_no, line.strip()))
        if re.search(r"demo|sample|placeholder|backend gap|not yet deployed|fake|mock|Customer Support Representative|Peer Support Specialist", line, re.I):
            placeholder_refs.append((str(p), line_no, line.strip()))

print("### API references")
for file, line, txt in api_refs:
    print(f"- `{file}:{line}` {txt[:220]}")
print()

print("### Hidden / disabled UI references")
for file, line, txt in hidden_refs:
    print(f"- `{file}:{line}` {txt[:220]}")
print()

print("### Placeholder / boilerplate / demo-language references")
if placeholder_refs:
    for file, line, txt in placeholder_refs:
        print(f"- `{file}:{line}` {txt[:220]}")
else:
    print("- No placeholder/demo strings found in scanned frontend files.")
print()

# ---------- Safe local endpoint probes ----------
print("## 6. Safe local endpoint probes")
print()
try:
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
        "/api/applications",
        "/api/_surface",
        "/api/events/pipeline",
    ]
    for path in paths:
        r = c.get(path)
        print(f"### `{path}`")
        print(f"- status: `{r.status_code}`")
        print(f"- content_type: `{r.content_type}`")
        data = None
        try:
            data = r.get_json()
        except Exception:
            pass
        if isinstance(data, dict):
            print(f"- top_keys: `{sorted(data.keys())}`")
            for key in ["status", "version", "count", "job_count", "batch_count", "dry_run", "message", "data", "jobs", "opportunities", "batches", "serpapi", "budget", "routes"]:
                if key in data:
                    v = data[key]
                    if isinstance(v, list):
                        print(f"- {key}: list[{len(v)}]")
                    elif isinstance(v, dict):
                        print(f"- {key}: dict keys `{sorted(v.keys())}`")
                    else:
                        print(f"- {key}: `{v}`")
        else:
            body = r.get_data(as_text=True)[:300].replace("\n", " ")
            print(f"- body_preview: `{body}`")
        print()
except Exception as e:
    print(f"FAILED safe probes: `{type(e).__name__}: {e}`")
print()

# ---------- Diagnosis ----------
print("## 7. Diagnosis rules")
print()
print("- If a module file exists but no route calls it, the engine exists but is not mounted.")
print("- If a route is mounted but no frontend fetch points to it, the engine is callable but not surfaced.")
print("- If a frontend element has `display:none`, `hidden`, `aria-hidden=true`, or is only shown on a tab condition, the feature is hidden/gated.")
print("- If `/api/jobs?dry_run=1` returns `dry_run: true` and no `jobs`, that is safe behavior, not live discovery.")
print("- If live `/api/jobs` is only behind a button, that is intentional budget protection.")
print("- If frontend expects `payload.opportunities` but backend returns `payload.data`, data exists but renderer is looking at the wrong key.")
print("- If `/api/events/pipeline` is 404 and no SSE route exists, S10-H requires a neutral unavailable state, not fake SSE.")
print()
PY

echo "=== 1) Report written ==="
echo "$OUT"
echo

echo "=== 2) Show the critical parts ==="
grep -nE "Mounted Flask route map|Declared backend routes|DECLARED_NOT_MOUNTED|Engine/module inventory|Hidden / disabled|Placeholder|Safe local endpoint probes|Diagnosis rules|/api/jobs\?dry_run=1|/api/opportunities|/api/events/pipeline|display:none|backend gap" "$OUT" | head -220 || true
echo

echo "=== 3) Compile proof ==="
python3 -m py_compile $(git ls-files '*.py')
echo

echo "=== 4) No deploy, no files changed except docs report ==="
git status --short
echo
echo "Open/read:"
echo "$OUT"
