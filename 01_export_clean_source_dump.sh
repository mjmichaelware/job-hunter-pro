#!/usr/bin/env bash
set -euo pipefail

echo "=== 01 EXPORT CLEAN SOURCE DUMP ==="
echo "PWD=$(pwd)"
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
import subprocess
import re

repo = Path(".").resolve()
out_dir = Path("/sdcard/Download/JobHunterProExports")
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
out = out_dir / f"JOB_HUNTER_PRO_CLEAN_SOURCE_DUMP_{stamp}.txt"
manifest = out_dir / f"JOB_HUNTER_PRO_SOURCE_MANIFEST_{stamp}.txt"

def run(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as e:
        return f"UNAVAILABLE:{type(e).__name__}:{e}"

skip_dirs = {
    ".git", ".gemini", ".repair_backups", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".cache", "node_modules", ".venv",
    "venv", "env", "dist", "build", ".idea", ".vscode"
}

include_suffixes = {
    ".py", ".js", ".html", ".css", ".md", ".txt", ".json",
    ".yaml", ".yml", ".toml", ".sql", ".ini", ".cfg"
}

include_names = {
    "Dockerfile", "Procfile", "requirements.txt", "cloudbuild.yaml",
    "README.md", "GEMINI.md", ".gitignore"
}

skip_patterns = [
    r"\.bak", r"\.backup", r"s10-backup", r"\.orig$", r"\.pyc$", r"\.pyo$",
    r"\.log$", r"live_jobs.*\.json$", r"probe_.*\.json$",
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
        return True, "excluded_dir"

    for pat in secret_file_patterns:
        if re.search(pat, lower):
            return True, "secret_filename"

    for pat in skip_patterns:
        if re.search(pat, lower):
            return True, "junk_generated_backup_probe"

    if path.name in include_names:
        return False, ""

    if path.suffix.lower() in include_suffixes:
        return False, ""

    return True, "unsupported_type"

def redact(line):
    for pat in secret_line_patterns:
        if re.search(pat, line, re.I):
            return "[REDACTED_SECRET_LIKE_LINE]\n"
    return line

files = []
skipped = []

for path in sorted(repo.rglob("*")):
    if not path.is_file():
        continue
    skip, reason = should_skip(path)
    rel = str(path.relative_to(repo))
    if skip:
        skipped.append((rel, reason))
        continue
    try:
        size = path.stat().st_size
    except Exception:
        skipped.append((rel, "stat_failed"))
        continue
    if size > 2_000_000:
        skipped.append((rel, f"too_large_{size}"))
        continue
    files.append(path)

with out.open("w", encoding="utf-8", errors="replace") as f:
    f.write("JOB_HUNTER_PRO_CLEAN_SOURCE_DUMP\n")
    f.write("=" * 100 + "\n")
    f.write(f"generated_utc={datetime.now(timezone.utc).isoformat()}\n")
    f.write(f"repo={repo}\n")
    f.write(f"git_head={run(['git','rev-parse','HEAD'])}\n")
    f.write(f"git_branch={run(['git','branch','--show-current'])}\n")
    f.write("security=secret_files_excluded_secret_lines_redacted\n")
    f.write("excluded=.git .gemini backups repair_scripts probe_json logs cache venv node_modules\n")
    f.write(f"included_count={len(files)} skipped_count={len(skipped)}\n\n")
    f.write("GIT_STATUS\n" + "-" * 100 + "\n" + run(["git", "status", "--short"]) + "\n\n")
    f.write("RECENT_COMMITS\n" + "-" * 100 + "\n" + run(["git", "log", "--oneline", "-30"]) + "\n\n")

    for path in files:
        rel = path.relative_to(repo)
        f.write("\n\n" + "=" * 120 + "\n")
        f.write(f"FILE:{rel}\n")
        f.write("=" * 120 + "\n")
        try:
            with path.open("r", encoding="utf-8", errors="replace") as src:
                for line in src:
                    f.write(redact(line))
        except Exception as e:
            f.write(f"[READ_ERROR:{type(e).__name__}:{e}]\n")

with manifest.open("w", encoding="utf-8", errors="replace") as f:
    f.write("JOB_HUNTER_PRO_SOURCE_EXPORT_MANIFEST\n")
    f.write("=" * 100 + "\n")
    f.write(f"dump={out}\n")
    f.write(f"generated_utc={datetime.now(timezone.utc).isoformat()}\n\n")
    f.write("INCLUDED\n")
    for path in files:
        f.write(str(path.relative_to(repo)) + "\n")
    f.write("\nSKIPPED\n")
    for rel, reason in skipped:
        f.write(f"{rel} :: {reason}\n")

print(f"DUMP={out}")
print(f"MANIFEST={manifest}")
print(f"INCLUDED={len(files)}")
print(f"SKIPPED={len(skipped)}")
PY

DUMP="$(ls -t "$OUT_DIR"/JOB_HUNTER_PRO_CLEAN_SOURCE_DUMP_*.txt | head -1)"
MANIFEST="$(ls -t "$OUT_DIR"/JOB_HUNTER_PRO_SOURCE_MANIFEST_*.txt | head -1)"

termux-media-scan "$DUMP" 2>/dev/null || true
termux-media-scan "$MANIFEST" 2>/dev/null || true

echo "CREATED_SOURCE_DUMP=$DUMP"
echo "CREATED_MANIFEST=$MANIFEST"
ls -lh "$DUMP" "$MANIFEST"
