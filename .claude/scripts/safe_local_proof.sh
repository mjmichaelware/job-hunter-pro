#!/usr/bin/env bash
set -euo pipefail
if [ -f .venv/bin/activate ]; then
  . .venv/bin/activate
fi
echo "--- compile check ---"
python3 -m py_compile $(git ls-files "*.py")
echo "--- safe flask proof ---"
python3 .claude/scripts/proof_runner.py
echo "--- diff checks ---"
git diff --check
git diff --stat
