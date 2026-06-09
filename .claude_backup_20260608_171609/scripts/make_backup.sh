#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d_%H%M%S)"
OUT=".claude/backups/job_hunter_backup_${TS}.tar.gz"
tar --exclude=.git --exclude=.venv --exclude=__pycache__ --exclude=.claude/backups -czf "$OUT" .
echo "$OUT"
