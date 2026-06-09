#!/usr/bin/env bash
set -euo pipefail
MSG="${1:-}"
[ -n "$MSG" ] || { echo "usage: bash .claude/scripts/jhp_commit.sh 'message'"; exit 1; }
bash .claude/scripts/safe_local_proof.sh
git add app.py api search providers pipeline web .claude CLAUDE.md docs scripts 2>/dev/null || true
git status --short
git commit -m "$MSG"
