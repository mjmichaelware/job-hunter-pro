#!/usr/bin/env bash
payload="$(cat)"
cmd="$(printf '%s' "$payload" | python3 -c '
import sys, json
try:
    d=json.load(sys.stdin)
    ti=d.get("tool_input") or {}
    print(ti.get("command") or ti.get("bash_command") or "")
except Exception:
    pass
' 2>/dev/null || true)"

case "$cmd" in
  *"/api/ingest"*|*"api/ingest"*)
    echo "BLOCKED: /api/ingest is protected." >&2
    exit 2 ;;
  *"SERPAPI_KEY"*|*"OPENAI_API_KEY"*|*"ANTHROPIC_API_KEY"*|*"GEMINI_API_KEY"*|*"GROQ_API_KEY"*|*"XAI_API_KEY"*)
    echo "BLOCKED: command appears to expose secret env vars." >&2
    exit 2 ;;
  *"git push --force"*|*"push --force"*)
    echo "BLOCKED: force push forbidden." >&2
    exit 2 ;;
esac
exit 0
