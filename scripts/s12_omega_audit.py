#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(".").resolve()
TS = time.strftime("%Y%m%d_%H%M%S")
AUDIT_DIR = Path("audits")
AUDIT_DIR.mkdir(exist_ok=True)
REPORT_MD = AUDIT_DIR / f"s12_omega_audit_{TS}.md"
REPORT_JSON = AUDIT_DIR / f"s12_omega_audit_{TS}.json"

SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    ".mypy_cache", "node_modules", "audits", ".gemini", ".local"
}

TEXT_SUFFIXES = {
    ".py", ".sh", ".html", ".htm", ".jinja", ".jinja2", ".js", ".mjs",
    ".css", ".json", ".md", ".txt", ".toml", ".yaml", ".yml", ".webmanifest",
    ".svg", ".env", ".example", ".dockerignore", ".gcloudignore"
}

PY_SKIP_PARTS = SKIP_DIRS | {"build", "dist"}

SECRET_PATTERNS = [
    ("postgres_url", re.compile(r"postgres(?:ql)?://[^\s\"']+", re.I)),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}\b")),
    ("long_hex_token", re.compile(r"\b[a-f0-9]{48,}\b", re.I)),
    ("secret_assignment", re.compile(r"(api[_-]?key|secret|token|password|db_url|database_url)\s*=\s*['\"][^'\"]{8,}['\"]", re.I)),
    ("private_key_marker", re.compile(r"BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY", re.I)),
]

FRONTEND_FORBIDDEN = [
    "/api/ingest",
    "safeFetch(API_URLS.jobs",
    "maps.googleapis.com",
    "google.maps",
]

FAKE_TERMS = [
    "demoJobs", "mockJobs", "sampleJobs", "fakeJobs", "placeholderJobs",
    "Acme Corp", "Globex", "Initech", "Soylent", "Math.random(",
    "demoData", "mockData", "sampleData", "fakeData",
]

EXPECTED_DOCS = [
    "docs/AI_JOB_AGENT_5_UIUX_Handoff.md",
    "docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md",
    "docs/S10_API_CONTRACT_MATRIX.md",
    "docs/S10_FINAL_PARITY_GATE.md",
    "docs/S11_SCRIPT_PROOF.md",
]

EXPECTED_SCRIPTS = [
    "scripts/add_key.sh",
    "scripts/deploy.sh",
    "scripts/seed_industries.sh",
    "scripts/make_scheduler_oidc.sh",
]

SAFE_ENDPOINTS = [
    "/api/health",
    "/api/usage",
    "/api/history",
    "/api/providers",
    "/api/industries",
    "/api/jobs?dry_run=1",
]

def run(cmd: list[str], timeout: int = 120) -> dict:
    try:
        r = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return {"cmd": cmd, "returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
    except Exception as e:
        return {"cmd": cmd, "returncode": 999, "stdout": "", "stderr": repr(e)}

def is_skipped(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)

def is_text_file(path: Path) -> bool:
    if path.name in {"Procfile", "Dockerfile", ".gcloudignore", ".dockerignore", ".env.example"}:
        return True
    return path.suffix.lower() in TEXT_SUFFIXES

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def redact(s: str) -> str:
    s = re.sub(r"postgres(?:ql)?://[^\s\"']+", "postgresql://<REDACTED>", s, flags=re.I)
    s = re.sub(r"\bAIza[0-9A-Za-z_\-]{20,}\b", "<REDACTED_GOOGLE_KEY>", s)
    s = re.sub(r"\b[a-f0-9]{32,}\b", "<REDACTED_HEX>", s, flags=re.I)
    s = re.sub(r"(api[_-]?key|secret|token|password|db_url|database_url)(\s*=\s*['\"])[^'\"]+(['\"])", r"\1\2<REDACTED>\3", s, flags=re.I)
    return s

def all_files() -> list[Path]:
    files = []
    for p in Path(".").rglob("*"):
        if not p.is_file():
            continue
        if is_skipped(p):
            continue
        files.append(p)
    return sorted(files, key=lambda x: str(x).lower())

def text_files() -> list[Path]:
    files = []
    for p in all_files():
        if not is_text_file(p):
            continue
        try:
            if p.stat().st_size > 2_000_000:
                continue
        except OSError:
            continue
        files.append(p)
    return files

def py_files() -> list[Path]:
    return [
        p for p in all_files()
        if p.suffix == ".py" and not any(part in PY_SKIP_PARTS for part in p.parts)
    ]

def shell_files() -> list[Path]:
    return [p for p in all_files() if p.suffix == ".sh"]

def js_files() -> list[Path]:
    return [
        p for p in all_files()
        if p.suffix in {".js", ".mjs"} and "web/static/js" in str(p).replace("\\", "/")
    ] + [p for p in [Path("web/static/sw.js"), Path("web/static/service-worker.js")] if p.exists()]

def main() -> int:
    failures = []
    warnings = []
    data = {}

    files = all_files()
    t_files = text_files()
    data["counts"] = {
        "files_scanned": len(files),
        "text_files_scanned": len(t_files),
        "python_files": len(py_files()),
        "shell_files": len(shell_files()),
        "js_files": len(js_files()),
    }

    # Git cleanliness.
    git_status = run(["git", "status", "--short"])
    data["git_status"] = git_status["stdout"]
    if git_status["stdout"].strip():
        warnings.append("Working tree is not clean. Review before deploy.")

    # Required docs/scripts.
    missing_docs = [p for p in EXPECTED_DOCS if not Path(p).exists()]
    missing_scripts = [p for p in EXPECTED_SCRIPTS if not Path(p).exists()]
    if missing_docs:
        failures.append(f"Missing required docs: {missing_docs}")
    if missing_scripts:
        failures.append(f"Missing required scripts: {missing_scripts}")

    # Secret scan.
    secret_hits = []
    for path in t_files:
        if path == Path("scripts/s12_omega_audit.py"):
            continue
        text = read_text(path)
        for i, line in enumerate(text.splitlines(), 1):
            if path == Path("docs/MANIFEST.md") and "sha256:" in line.lower():
                continue
            for name, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    # Allow literal Secret Manager reference syntax in scripts/deploy.sh.
                    if path == Path("scripts/deploy.sh") and ":latest" in line and "Secret Manager reference" in line:
                        continue
                    secret_hits.append({
                        "file": str(path),
                        "line": i,
                        "pattern": name,
                        "excerpt": redact(line.strip())[:300],
                    })
    data["secret_hits_redacted"] = secret_hits
    if secret_hits:
        failures.append(f"Secret-pattern scan found {len(secret_hits)} redacted hit(s).")

    # Python AST/import/compile checks.
    py_compile_results = []
    py_imports = {}
    for p in py_files():
        try:
            source = read_text(p)
            ast.parse(source, filename=str(p))
            py_compile_results.append({"file": str(p), "ok": True})
            imports = []
            try:
                tree = ast.parse(source, filename=str(p))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.extend(alias.name.split(".")[0] for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imports.append(node.module.split(".")[0])
                py_imports[str(p)] = sorted(set(imports))
            except Exception:
                pass
        except Exception as e:
            py_compile_results.append({"file": str(p), "ok": False, "error": str(e)})
            failures.append(f"Python parse failure: {p}: {e}")
    data["python_parse"] = py_compile_results
    data["python_imports"] = py_imports

    compileall = run([sys.executable, "-m", "compileall", "-q", "."], timeout=300)
    data["compileall"] = {"returncode": compileall["returncode"], "stderr": compileall["stderr"][-2000:]}
    if compileall["returncode"] != 0:
        failures.append("python -m compileall failed.")

    # Import app smoke check. No network.
    import_smoke = run([sys.executable, "-c", "import app; print('import app ok')"], timeout=120)
    data["import_app"] = {"returncode": import_smoke["returncode"], "stdout": import_smoke["stdout"], "stderr": import_smoke["stderr"][-4000:]}
    if import_smoke["returncode"] != 0:
        failures.append("import app smoke check failed.")

    # Shell syntax.
    shell_syntax = []
    for p in shell_files():
        r = run(["bash", "-n", str(p)])
        shell_syntax.append({"file": str(p), "returncode": r["returncode"], "stderr": r["stderr"]})
        if r["returncode"] != 0:
            failures.append(f"bash -n failed: {p}")
    data["shell_syntax"] = shell_syntax

    # JS syntax.
    node_exists = run(["sh", "-lc", "command -v node >/dev/null 2>&1"])
    js_syntax = []
    if node_exists["returncode"] == 0:
        for p in js_files():
            r = run(["node", "--check", str(p)])
            js_syntax.append({"file": str(p), "returncode": r["returncode"], "stderr": r["stderr"]})
            if r["returncode"] != 0:
                failures.append(f"node --check failed: {p}")
    else:
        warnings.append("node not found; JS syntax check skipped.")
    data["js_syntax"] = js_syntax

    # Frontend boot/safety scan.
    frontend_hits = []
    frontend_paths = []
    for root in [Path("web/templates"), Path("web/static")]:
        if root.exists():
            frontend_paths.extend([p for p in root.rglob("*") if p.is_file() and is_text_file(p)])
    for p in frontend_paths:
        text = read_text(p)
        for i, line in enumerate(text.splitlines(), 1):
            s = line.strip()
            low = s.lower()
            for term in FRONTEND_FORBIDDEN:
                if term.lower() in low:
                    frontend_hits.append({"file": str(p), "line": i, "term": term, "excerpt": redact(s)[:300]})
            if "fetch(" in s and "/api/jobs" in s and "dry_run" not in s:
                frontend_hits.append({"file": str(p), "line": i, "term": "direct live /api/jobs fetch", "excerpt": redact(s)[:300]})
            for term in FAKE_TERMS:
                if term.lower() in low:
                    frontend_hits.append({"file": str(p), "line": i, "term": term, "excerpt": redact(s)[:300]})
    data["frontend_forbidden_hits"] = frontend_hits
    if frontend_hits:
        failures.append(f"Frontend safety scan found {len(frontend_hits)} blocker hit(s).")

    # Service worker safety.
    for sw in [Path("web/static/sw.js"), Path("web/static/service-worker.js")]:
        if sw.exists():
            text = read_text(sw).lower()
            for term in ["/api/jobs", "/api/ingest", "serpapi", "adzuna", "usajobs", "jooble", "careerjet"]:
                if term in text:
                    failures.append(f"Service worker references forbidden API/provider term {term}: {sw}")

    # Route scan.
    route_hits = []
    for p in py_files():
        text = read_text(p)
        for i, line in enumerate(text.splitlines(), 1):
            if "@app.route" in line or ".route(" in line or "Blueprint(" in line:
                route_hits.append({"file": str(p), "line": i, "excerpt": line.strip()[:240]})
    data["route_hits"] = route_hits

    # Ingest/OIDC/token scan.
    token_ingest_hits = []
    for p in t_files:
        if p == Path("scripts/s12_omega_audit.py"):
            continue
        p_str = str(p)
        if p_str.startswith("docs/AI_JOB_AGENT_"):
            continue
        if p_str.startswith("docs/S12_OMEGA_") and p.name.endswith(("_PROMPT.md", "_PROOF.md")):
            continue
        text = read_text(p)
        for i, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            if "/api/ingest?" in low or "ingest_token" in low or "?token=" in low or "token=" in low and "/api/ingest" in low:
                token_ingest_hits.append({"file": str(p), "line": i, "excerpt": redact(line.strip())[:300]})
    data["token_ingest_hits"] = token_ingest_hits
    if token_ingest_hits:
        failures.append(f"Ingest token URL scan found {len(token_ingest_hits)} hit(s).")

    # Deploy/scheduler script dry-run proof.
    dry_runs = {}
    dry_run_cmds = [
        ["scripts/add_key.sh", "--dry-run", "TEST_SECRET"],
        ["scripts/deploy.sh", "--dry-run"],
        ["scripts/seed_industries.sh", "--dry-run"],
        ["scripts/make_scheduler_oidc.sh", "--dry-run"],
    ]
    for cmd in dry_run_cmds:
        if Path(cmd[0]).exists():
            r = run(cmd, timeout=240)
            dry_runs[" ".join(cmd)] = {"returncode": r["returncode"], "stdout": r["stdout"][-4000:], "stderr": r["stderr"][-4000:]}
            if r["returncode"] != 0:
                failures.append(f"Dry-run failed: {' '.join(cmd)}")
    data["script_dry_runs"] = dry_runs

    # Deploy script proof.
    deploy = Path("scripts/deploy.sh")
    if deploy.exists():
        text = read_text(deploy)
        for term in ["--dry-run", "ai-job-agent-498702", "job-hunter-pro", "us-central1", "py_compile"]:
            if term not in text:
                failures.append(f"deploy.sh missing required term: {term}")
        if "/api/ingest" in text:
            failures.append("deploy.sh references /api/ingest; forbidden.")
    scheduler = Path("scripts/make_scheduler_oidc.sh")
    if scheduler.exists():
        text = read_text(scheduler)
        for term in ["--oidc-service-account-email", "--oidc-token-audience", "/api/ingest", "--dry-run"]:
            if term not in text:
                failures.append(f"make_scheduler_oidc.sh missing required term: {term}")
        for term in ["?token=", "INGEST_TOKEN", "token="]:
            if term in text:
                failures.append(f"make_scheduler_oidc.sh has token auth pattern: {term}")

    # Dependency checks.
    pip_check = run([sys.executable, "-m", "pip", "check"], timeout=240)
    data["pip_check"] = {"returncode": pip_check["returncode"], "stdout": pip_check["stdout"], "stderr": pip_check["stderr"]}
    if pip_check["returncode"] != 0:
        warnings.append("pip check reported dependency issues. Review output.")

    # Requirements parse.
    if Path("requirements.txt").exists():
        req_text = read_text(Path("requirements.txt"))
        if "gunicorn" not in req_text.lower():
            warnings.append("requirements.txt may be missing gunicorn.")
        if "flask" not in req_text.lower():
            failures.append("requirements.txt appears to miss Flask.")

    # Procfile/app entrypoint.
    if Path("Procfile").exists():
        proc = read_text(Path("Procfile"))
        data["procfile"] = proc
        if "gunicorn" not in proc.lower():
            warnings.append("Procfile does not mention gunicorn.")
    else:
        warnings.append("No Procfile found.")

    result = {
        "generated": TS,
        "counts": data["counts"],
        "failures": failures,
        "warnings": warnings,
        "data": data,
        "pass": not failures,
    }

    REPORT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")

    md = []
    md.append("# S12 Omega Predeploy Audit")
    md.append("")
    md.append(f"Generated: `{TS}`")
    md.append("")
    md.append(f"PASS: `{not failures}`")
    md.append(f"Failure count: `{len(failures)}`")
    md.append(f"Warning count: `{len(warnings)}`")
    md.append("")
    md.append("## Counts")
    md.append("")
    for k, v in data["counts"].items():
        md.append(f"- {k}: `{v}`")
    md.append("")
    md.append("## Failures")
    md.append("")
    if failures:
        for f in failures:
            md.append(f"- {f}")
    else:
        md.append("None.")
    md.append("")
    md.append("## Warnings")
    md.append("")
    if warnings:
        for w in warnings:
            md.append(f"- {w}")
    else:
        md.append("None.")
    md.append("")
    md.append("## Redacted secret hits")
    md.append("")
    if secret_hits:
        for h in secret_hits:
            md.append(f"- `{h['file']}:{h['line']}` `{h['pattern']}` — `{h['excerpt']}`")
    else:
        md.append("None.")
    md.append("")
    md.append("## Frontend forbidden hits")
    md.append("")
    if frontend_hits:
        for h in frontend_hits:
            md.append(f"- `{h['file']}:{h['line']}` `{h['term']}` — `{h['excerpt']}`")
    else:
        md.append("None.")
    md.append("")
    md.append("## Ingest token URL hits")
    md.append("")
    if token_ingest_hits:
        for h in token_ingest_hits:
            md.append(f"- `{h['file']}:{h['line']}` — `{h['excerpt']}`")
    else:
        md.append("None.")
    md.append("")
    md.append("## Script dry-run summaries")
    md.append("")
    for cmd, info in dry_runs.items():
        md.append(f"### `{cmd}`")
        md.append("")
        md.append(f"- returncode: `{info['returncode']}`")
        md.append("")
        md.append("```text")
        md.append((info["stdout"] + info["stderr"])[-2500:])
        md.append("```")
        md.append("")
    md.append("## Route scan")
    md.append("")
    for h in route_hits[:200]:
        md.append(f"- `{h['file']}:{h['line']}` — `{h['excerpt']}`")
    if len(route_hits) > 200:
        md.append(f"- ...truncated {len(route_hits)-200} additional route hits")
    md.append("")
    md.append("## Output files")
    md.append("")
    md.append(f"- JSON: `{REPORT_JSON}`")
    md.append(f"- Markdown: `{REPORT_MD}`")
    md.append("")

    REPORT_MD.write_text("\n".join(md), encoding="utf-8")

    print("S12 Omega audit complete.")
    print(f"PASS: {not failures}")
    print(f"Markdown: {REPORT_MD}")
    print(f"JSON:     {REPORT_JSON}")
    print()
    if failures:
        print("FAILURES:")
        for f in failures:
            print(" -", f)
    else:
        print("No failures.")
    print()
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(" -", w)
    else:
        print("No warnings.")
    print()
    print(f"Open report: less {REPORT_MD}")

    return 0 if not failures else 2

if __name__ == "__main__":
    raise SystemExit(main())
