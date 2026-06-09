#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d_%H%M%S)"
OUT="$HOME/storage/downloads/JOB_HUNTER_PRO_CLAUDE_CONTEXT_${TS}.tar.gz"
tar -czf "$OUT" .claude CLAUDE.md
echo "$OUT"
