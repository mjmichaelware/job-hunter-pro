#!/usr/bin/env bash
set -euo pipefail
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
{
  echo "# Session State"
  echo
  echo "Updated: $TS"
  echo
  echo "## Git status"
  echo
  git status --short || true
  echo
  echo "## Diff stat"
  echo
  git diff --stat || true
  echo
  echo "## Current instructions"
  echo
  echo "- Do not deploy unless explicitly instructed."
  echo "- Do not call live /api/jobs unless explicitly instructed."
  echo "- Do not call /api/ingest unless explicitly instructed."
  echo "- Do not print secrets."
} > .claude/context/SESSION_STATE.md
cat .claude/context/SESSION_STATE.md
