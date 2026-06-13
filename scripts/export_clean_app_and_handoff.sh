#!/usr/bin/env bash

# Context Anchor for Subdirectory Migration
cd "$(dirname "$0")/.."
set -euo pipefail

echo "=== EXPORT CLEAN SOURCE + DENSE HANDOFF TO ANDROID DOWNLOADS ==="
echo "PWD=$(pwd)"
echo

[ -f app.py ] || { echo "ERROR: app.py not found; not repo root."; exit 1; }

if [ ! -d /sdcard/Download ]; then
  termux-setup-storage
  sleep 3
fi

OUT_DIR="/sdcard/Download/JobHunterProExports"
mkdir -p "$OUT_DIR"

python3 - <<'PY'
from pathlib import Path
from datetime import datetime, timezone
import subprocess, re, json, os

repo = Path(".").resolve()
out_dir = Path("/sdcard/Download/JobHunterProExports")
out_dir.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

dump = out_dir / f"JOB_HUNTER_PRO_CLEAN_SOURCE_DUMP_{stamp}.txt"
handoff = out_dir / f"JOB_HUNTER_PRO_DENSE_HANDOFF_{stamp}.md"
manifest = out_dir / f"JOB_HUNTER_PRO_MANIFEST_{stamp}.txt"

def run(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as e:
        return f"UNAVAILABLE: {type(e).__name__}: {e}"

git_head = run(["git","rev-parse","HEAD"])
git_branch = run(["git","branch","--show-current"])
git_status = run(["git","status","--short"])
git_log = run(["git","log","--oneline","-30"])

skip_dirs = {
    ".git",".gemini",".repair_backups","__pycache__",".pytest_cache",".mypy_cache",
    ".ruff_cache",".cache","node_modules",".venv","venv","env","dist","build",
    ".idea",".vscode"
}

include_suffixes = {".py",".js",".html",".css",".md",".txt",".json",".yaml",".yml",".toml",".sql",".ini",".cfg"}
include_names = {"Dockerfile","Procfile","requirements.txt","cloudbuild.yaml","README.md","GEMINI.md",".gitignore"}

skip_patterns = [
    r"\.bak", r"\.backup", r"s10-backup", r"\.orig$", r"\.pyc$", r"\.pyo$",
    r".*\.log$", r"live_jobs.*\.json$", r"probe_.*\.json$",
    r"repair.*\.sh$", r"fix_.*\.sh$", r"find_.*\.sh$", r"compare_.*\.sh$",
    r"diagnose_.*\.sh$", r"surface_.*\.sh$", r"export_.*\.sh$",
    r"package-lock\.json$", r"yarn\.lock$", r"pnpm-lock\.yaml$"
]

secret_file_patterns = [
    r"(^|/)\.env($|\.)", r"secret", r"secrets", r"credential", r"credentials",
    r"service[_-]?account", r"token", r"oauth", r"firebase", r"\.pem$",
    r"\.key$", r"\.p12$", r"\.pfx$", r"id_rsa", r"id_ed25519"
]

secret_line_patterns = [
    r"API[_-]?KEY\s*[:=]", r"SECRET\s*[:=]", r"TOKEN\s*[:=]",
    r"PASSWORD\s*[:=]", r"PRIVATE[_-]?KEY", r"client_secret",
    r"refresh_token", r"access_token", r"Bearer\s+[A-Za-z0-9._\-]+",
    r"sk-[A-Za-z0-9_\-]{20,}", r"AIza[0-9A-Za-z_\-]{20,}"
]

def should_skip(path):
    rel = path.relative_to(repo)
    s = str(rel)
    lower = s.lower()

    if any(part in skip_dirs for part in rel.parts):
        return True, "excluded junk/cache/private dir"

    for pat in secret_file_patterns:
        if re.search(pat, lower):
            return True, "secret-looking filename"

    for pat in skip_patterns:
        if re.search(pat, lower):
            return True, "generated/backup/probe/junk file"

    if path.name in include_names:
        return False, ""

    if path.suffix.lower() in include_suffixes:
        return False, ""

    return True, "unsupported file type"

def redact(line):
    for pat in secret_line_patterns:
        if re.search(pat, line, re.I):
            return "[REDACTED SECRET-LIKE LINE]\n"
    return line

files, skipped = [], []
 for_p = sorted(repo.rglob("*"))
for p in for_p:
    if not p.is_file():
        continue
    skip, reason = should_skip(p)
    rel = str(p.relative_to(repo))
    if skip:
        skipped.append((rel, reason))
        continue
    try:
        size = p.stat().st_size
    except Exception:
        skipped.append((rel, "stat failed"))
        continue
    if size > 2_000_000:
        skipped.append((rel, f"too large {size} bytes"))
        continue
    files.append(p)

route_map = run(["python3","-c","from app import app\nfor r in sorted(app.url_map.iter_rules(), key=lambda x: str(x.rule)):\n print(f'{str(r.rule):55} -> {r.endpoint}')"])
provider_truth = run(["python3","-c","from providers import get_all_providers\nfor p in get_all_providers():\n print(f'{p.metadata.type.value:10} {p.metadata.key:22} available={p.is_available()} requires_key={p.metadata.requires_api_key} label={p.metadata.label}')"])
safe_shapes = run(["python3","-c","from app import app\nc=app.test_client()\nfor p in ['/', '/api/health','/api/usage','/api/jobs?dry_run=1','/api/opportunities','/api/history','/api/providers','/api/_surface','/api/events/pipeline']:\n r=c.get(p); print('\\n###',p,r.status_code,r.content_type); data=None\n try: data=r.get_json()\n except Exception: pass\n print(sorted(data.keys()) if isinstance(data,dict) else r.get_data(as_text=True)[:240].replace('\\n',' '))"])
core_grep = run(["bash","-lc","grep -Rni \"fetch_provider_raw_jobs\\|provider_breakdown\\|MAX_RAW_JOBS\\|MAX_SERP_QUERIES\\|target_raw\\|per_provider\\|Run Live Discovery\\|EventSource\\|/api/events/pipeline\\|Pipeline Engine Stream\\|display:none\" app.py api providers search web 2>/dev/null | head -500 || true"])

with dump.open("w", encoding="utf-8", errors="replace") as out:
    out.write("JOB HUNTER PRO CLEAN SOURCE DUMP\n")
    out.write("="*100 + "\n")
    out.write(f"Generated UTC: {datetime.now(timezone.utc).isoformat()}\nRepo: {repo}\nBranch: {git_branch}\nHEAD: {git_head}\n")
    out.write("Secrets: secret-looking files excluded; secret-looking lines redacted.\n")
    out.write("Excluded: .git, .gemini, backups, ad hoc repair/probe/export scripts, probe JSON, logs, cache dirs, venvs.\n\n")
    out.write(f"Included files: {len(files)}\nSkipped files: {len(skipped)}\n\n")
    out.write("GIT STATUS\n" + "-"*100 + "\n" + git_status + "\n\n")
    out.write("RECENT COMMITS\n" + "-"*100 + "\n" + git_log + "\n\n")
    out.write("ROUTE MAP\n" + "-"*100 + "\n" + route_map + "\n\n")
    out.write("PROVIDERS\n" + "-"*100 + "\n" + provider_truth + "\n\n")
    out.write("SAFE ENDPOINT SHAPES\n" + "-"*100 + "\n" + safe_shapes + "\n\n")
    out.write("CORE GREP\n" + "-"*100 + "\n" + core_grep + "\n\n")

    for p in files:
        rel = p.relative_to(repo)
        out.write("\n\n" + "="*120 + "\n")
        out.write(f"FILE: {rel}\n")
        out.write("="*120 + "\n")
        try:
            with p.open("r", encoding="utf-8", errors="replace") as src:
                for line in src:
                    out.write(redact(line))
        except Exception as e:
            out.write(f"[READ ERROR {type(e).__name__}: {e}]\n")

handoff_lines = [
"# JOB HUNTER PRO — DENSE HANDOFF",
"",
f"Generated UTC: {datetime.now(timezone.utc).isoformat()}",
f"Repo: {repo}",
f"Branch: {git_branch}",
f"HEAD: {git_head}",
"",
"## ABSOLUTE RULES",
"Secrets never printed/hardcoded/exported. Keys live in Secret Manager. No Scheduler URL token. /api/ingest is OIDC-only. Page load must not burn discovery quota. /api/jobs?dry_run=1 is safe. /api/jobs without dry_run is live discovery. No fake jobs, fake provider counts, fake SSE, fake logs, fake telemetry, or fake readiness. LLM providers are enrichment/classification only: OpenAI, Gemini, Claude, Groq, xAI do not search jobs. Discovery providers are SerpAPI Jobs, SerpAPI Organic, Adzuna, USAJobs, Jooble, Careerjet, The Muse, and Google Places/opportunities.",
"",
"## CURRENT ARCHITECTURE",
"Cloud Run Flask entrypoint app.py serves S10 cockpit from web/templates/index.html and web/static. Legacy/live backend controller api/index.py contains core /api/jobs, /api/opportunities, /api/history, /api/usage, /api/debug/jobs, /api/ingest, batch/history and old embedded dashboard. Modular blueprints exist under api/. Provider registry lives under providers/. Search/fanout bridge lives under search/. UI renderers live under web/static/js. A file existing does not mean it is mounted or called.",
"",
"## ROUTE MAP",
"```text",
route_map,
"```",
"",
"## PROVIDER REGISTRY",
"```text",
provider_truth,
"```",
"",
"## SAFE ENDPOINT SHAPES",
"```text",
safe_shapes,
"```",
"",
"## CORE GREP",
"```text",
core_grep,
"```",
"",
"## PROVEN ROOT CAUSES FROM SESSION",
"1. S10 UI was served, but layout/canvas/style/drawer problems made it look broken. 2. /api/events/pipeline was not mounted, so Pipeline Engine Stream/SSE card was boilerplate. Correct behavior: unavailable or live-truth telemetry, not fake SSE. 3. Root page serves web/templates/index.html, while older real-data dashboard still exists in api/index.py, causing split-brain between legacy dashboard and S10 shell. 4. Live controls were hidden; Run Live Discovery button had display:none and needed exposure. 5. render_jobs initially ignored live option and called dry_run only. 6. /api/opportunities returns data[], not opportunities[], so frontend needed payload normalization. 7. /api/jobs initially ran only legacy serpapi_jobs over Config.MAX_SERP_QUERIES=4, producing raw_count=6. 8. Federated provider bridge was later wired; live proof showed raw_count=35, accepted=1, rejected=34, but provider_breakdown showed SerpAPI Jobs and SerpAPI Organic consumed all capacity while Adzuna/USAJobs/Jooble/Careerjet/TheMuse were available but queries_attempted=0. 9. User rejected fake-provider proof; next fix must use real provider status and real live diagnostics, not synthetic proof as final evidence.",
"",
"## CURRENT REAL DEFECT TO FIX",
"The app must not let one provider dominate before every available SEARCH provider gets a real turn. If provider_breakdown shows available=True and queries_attempted=0 for discovery providers, fanout scheduling is broken. If all providers are attempted and return zero/errors, inspect each provider implementation and API response/error. If raw jobs exist but accepted=0, address/place/radius/transit resolution is over-filtering. Rejected/unresolved jobs are real live candidates and must be displayed.",
"",
"## REQUIRED INVARIANTS",
"/api/jobs must return provider_breakdown for every search provider: available, queries_attempted, raw_count, status, error if any. /api/jobs must return data[] accepted verified jobs and rejected[] unresolved live candidates. UI must render both. Reasoning providers must not be called as search. /api/jobs?dry_run=1 must remain safe. /api/ingest must remain OIDC only. No deploy until local compile and safe proof pass.",
"",
"## NEXT ENGINEER ACTION",
"Inspect api/index.py, search/live_provider_bridge.py, providers/search/*.py, web/static/js/render_jobs.js, web/static/js/live_engine_bridge.js, and web/static/js/live_truth_telemetry.js. First prove whether current bridge attempts all real providers. Do not use fake-provider proof as final evidence. After local compile, perform one controlled live /api/jobs run only when explicitly intended, then read provider_breakdown. If providers have queries_attempted=0, fix scheduler/fanout. If queries_attempted>0 but raw_count=0, fix provider implementation/query mapping. If provider error, repair that provider. If raw_count exists but UI empty, fix renderer. If candidates rejected for no_exact_restaurant_address_resolved/radius_unavailable, fix place resolver but still display unresolved candidates.",
"",
"## GIT STATE",
"```text",
git_status,
"```",
"",
"## RECENT COMMITS",
"```text",
git_log,
"```",
"",
f"Clean source dump: {dump}",
f"Manifest: {manifest}",
]

handoff.write_text("\n".join(handoff_lines) + "\n", encoding="utf-8", errors="replace")

with manifest.open("w", encoding="utf-8", errors="replace") as mf:
    mf.write("JOB HUNTER PRO EXPORT MANIFEST\n")
    mf.write("="*100 + "\n")
    mf.write(f"Generated UTC: {datetime.now(timezone.utc).isoformat()}\n")
    mf.write(f"Dump: {dump}\nHandoff: {handoff}\n\n")
    mf.write("INCLUDED FILES\n" + "-"*100 + "\n")
    for p in files:
        mf.write(str(p.relative_to(repo)) + "\n")
    mf.write("\nSKIPPED FILES\n" + "-"*100 + "\n")
    for rel, reason in skipped:
        mf.write(f"{rel} :: {reason}\n")

print("DUMP=" + str(dump))
print("HANDOFF=" + str(handoff))
print("MANIFEST=" + str(manifest))
print("INCLUDED=" + str(len(files)))
print("SKIPPED=" + str(len(skipped)))
PY

DUMP="$(ls -t /sdcard/Download/JobHunterProExports/JOB_HUNTER_PRO_CLEAN_SOURCE_DUMP_*.txt | head -1)"
HANDOFF="$(ls -t /sdcard/Download/JobHunterProExports/JOB_HUNTER_PRO_DENSE_HANDOFF_*.md | head -1)"
MANIFEST="$(ls -t /sdcard/Download/JobHunterProExports/JOB_HUNTER_PRO_MANIFEST_*.txt | head -1)"

echo
echo "=== CREATED ==="
ls -lh "$DUMP" "$HANDOFF" "$MANIFEST"

echo
echo "=== REFRESH ANDROID DOWNLOADS ==="
termux-media-scan "$DUMP" 2>/dev/null || true
termux-media-scan "$HANDOFF" 2>/dev/null || true
termux-media-scan "$MANIFEST" 2>/dev/null || true

echo
echo "=== FILES APP LOCATION ==="
echo "Downloads/JobHunterProExports"
echo "$DUMP"
echo "$HANDOFF"
echo "$MANIFEST"
