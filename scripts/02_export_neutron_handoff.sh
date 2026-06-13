#!/usr/bin/env bash

# Context Anchor for Subdirectory Migration
cd "$(dirname "$0")/.."
set -euo pipefail

echo "=== 02 EXPORT NEUTRON-DENSE MACHINE HANDOFF ==="
echo "PWD=$(pwd)"
[ -f app.py ] || { echo "ERROR: app.py not found; not repo root."; exit 1; }

OUT_DIR="/sdcard/Download/JobHunterProExports"
mkdir -p "$OUT_DIR"

python3 - <<'PY'
from pathlib import Path
from datetime import datetime, timezone
import subprocess
import json
import hashlib
import re

repo = Path(".").resolve()
out_dir = Path("/sdcard/Download/JobHunterProExports")
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
out = out_dir / f"JOB_HUNTER_PRO_NEUTRON_HANDOFF_{stamp}.jsonl.txt"

def run(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as e:
        return f"UNAVAILABLE:{type(e).__name__}:{e}"

def emit(f, typ, **obj):
    obj = {"type": typ, **obj}
    f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")

def py_lines(path, patterns):
    p = Path(path)
    if not p.exists():
        return []
    out = []
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, line in enumerate(lines, 1):
        if any(re.search(pat, line) for pat in patterns):
            out.append({"file": path, "line": i, "text": line[:500]})
    return out

route_map = run([
    "python3", "-c",
    "from app import app\n"
    "for r in sorted(app.url_map.iter_rules(), key=lambda x: str(x.rule)):\n"
    " print(f'{str(r.rule)} -> {r.endpoint} -> {sorted(r.methods)}')"
])

providers = run([
    "python3", "-c",
    "from providers import get_all_providers\n"
    "for p in get_all_providers():\n"
    " print(f'{p.metadata.type.value}|{p.metadata.key}|available={p.is_available()}|requires_key={p.metadata.requires_api_key}|label={p.metadata.label}')"
])

safe = run([
    "python3", "-c",
    "from app import app\n"
    "c=app.test_client()\n"
    "paths=['/','/api/health','/api/usage','/api/jobs?dry_run=1','/api/opportunities','/api/history','/api/providers','/api/_surface','/api/events/pipeline']\n"
    "for p in paths:\n"
    " r=c.get(p); print('PATH',p,'STATUS',r.status_code,'TYPE',r.content_type); data=None\n"
    " try: data=r.get_json()\n"
    " except Exception: pass\n"
    " print('KEYS', sorted(data.keys()) if isinstance(data,dict) else 'NONJSON')"
])

core_grep = run([
    "bash", "-lc",
    "grep -Rni \"fetch_provider_raw_jobs\\|provider_breakdown\\|MAX_RAW_JOBS\\|MAX_SERP_QUERIES\\|target_raw\\|per_provider\\|Run Live Discovery\\|EventSource\\|/api/events/pipeline\\|Pipeline Engine Stream\\|display:none\\|dry_run\" app.py api providers search web 2>/dev/null | head -800 || true"
])

tracked = run(["git", "ls-files"])
tracked_files = tracked.splitlines() if tracked and not tracked.startswith("UNAVAILABLE") else []

file_index = []
for name in tracked_files:
    p = repo / name
    if not p.is_file():
        continue
    if any(x in name for x in [".git", ".gemini", ".repair_backups"]):
        continue
    try:
        data = p.read_bytes()
    except Exception:
        continue
    file_index.append({
        "path": name,
        "bytes": len(data),
        "sha256_12": hashlib.sha256(data).hexdigest()[:12],
        "suffix": p.suffix
    })

with out.open("w", encoding="utf-8", errors="replace") as f:
    emit(f, "meta", generated_utc=datetime.now(timezone.utc).isoformat(), repo=str(repo), branch=run(["git","branch","--show-current"]), head=run(["git","rev-parse","HEAD"]))
    emit(f, "law", secrets="never_print_never_hardcode_secret_manager_only", scheduler="/api/ingest_oidc_only_no_url_token", page_load="no_live_discovery_no_serpapi_burn", llms="openai_gemini_claude_groq_xai_are_enrichment_not_discovery", discovery="serpapi_jobs_serpapi_organic_adzuna_usajobs_jooble_careerjet_themuse_google_places")
    emit(f, "architecture", entrypoint="app.py", ui="web/templates/index.html+web/static", legacy_backend="api/index.py", modular_api="api/*.py", provider_registry="providers/__init__.py", search_bridge="search/live_provider_bridge.py", truth="file_exists_not_equal_mounted_or_called")
    emit(f, "git_status", text=run(["git", "status", "--short"]))
    emit(f, "git_log", text=run(["git", "log", "--oneline", "-40"]))
    emit(f, "route_map", text=route_map)
    emit(f, "providers", text=providers)
    emit(f, "safe_endpoint_shapes", text=safe)
    emit(f, "core_grep", text=core_grep)
    emit(f, "proven_session_chain", facts=[
        "root served S10 web/templates/index.html not old api/index.py embedded dashboard",
        "SSE pipeline stream unavailable because /api/events/pipeline not mounted",
        "old UI hid live discovery button and dry-run-only behavior masked live function",
        "api/jobs originally serpapi-only via raw_job_queries and MAX_SERP_QUERIES=4",
        "federated bridge added provider_breakdown and moved raw_count from 6 to 35",
        "provider_breakdown proved serpapi_jobs+serpapi_organic filled cap while adzuna_usajobs_jooble_careerjet_themuse had queries_attempted=0",
        "rejected/unresolved candidates are real live jobs and must render, not vanish",
        "common rejection reasons no_exact_restaurant_address_resolved radius_unavailable indicate resolver/filter issue not fake absence"
    ])
    emit(f, "current_defect", invariant="all_available_SEARCH_providers_must_be_attempted_before_one_provider_dominates", failure_signature="available_true_and_queries_attempted_0_for_discovery_provider", not_solution="fake_provider_proof_as_final_evidence", required_live_evidence="real_provider_breakdown_after_one_controlled_live_run")
    emit(f, "next_actions", steps=[
        "inspect search/live_provider_bridge.py and api/index.py",
        "ensure /api/jobs calls fetch_provider_raw_jobs over ProviderType.SEARCH",
        "ensure provider_breakdown includes every search provider",
        "ensure scheduling cannot let serpapi consume entire global cap before other providers are attempted",
        "compile python -m py_compile $(git ls-files '*.py')",
        "safe local proof only: / /api/health /api/usage /api/jobs?dry_run=1 /api/providers",
        "only after review deploy and run one live /api/jobs proof",
        "if provider queries_attempted=0 fix fanout",
        "if queries_attempted>0 raw_count=0 fix provider query/API implementation",
        "if raw_count>0 UI empty fix render_jobs",
        "if rejected due address/radius fix place resolver while still displaying unresolved"
    ])
    emit(f, "critical_code_lines", items=py_lines("api/index.py", ["def raw_job_queries", "def fetch_jobs_live", "fetch_provider_raw_jobs", "provider_breakdown", "MAX_RAW_JOBS", "MAX_SERP_QUERIES", "@app.route\\(\"/api/jobs\""]) + py_lines("search/live_provider_bridge.py", ["def fetch_provider_raw_jobs", "get_providers_by_type", "ProviderType.SEARCH", "queries_attempted", "raw_count", "provider_breakdown", "max_raw_jobs"]) + py_lines("web/static/js/render_jobs.js", ["loadJobs", "API_URLS.jobs", "dry_run", "rejected", "All Live Job Candidates", "Unresolved"]))
    emit(f, "file_index", count=len(file_index), files=file_index)

print(f"HANDOFF={out}")
print(f"LINES={sum(1 for _ in out.open('r', encoding='utf-8', errors='replace'))}")
PY

HANDOFF="$(ls -t "$OUT_DIR"/JOB_HUNTER_PRO_NEUTRON_HANDOFF_*.jsonl.txt | head -1)"
termux-media-scan "$HANDOFF" 2>/dev/null || true
echo "CREATED_HANDOFF=$HANDOFF"
ls -lh "$HANDOFF"
