#!/usr/bin/env bash
input="$(cat)"
if command -v jq >/dev/null 2>&1; then
  MODEL="$(printf '%s' "$input" | jq -r '.model.display_name // .model.name // "model?"' 2>/dev/null || echo model?)"
  PCT="$(printf '%s' "$input" | jq -r '.context_window.used_percentage // 0' 2>/dev/null | cut -d. -f1)"
  DIR="$(printf '%s' "$input" | jq -r '.workspace.current_dir // ""' 2>/dev/null)"
else
  MODEL="model?"
  PCT="0"
  DIR="$(pwd)"
fi
BRANCH="$(git branch --show-current 2>/dev/null || true)"
WARN=""
[ "${PCT:-0}" -ge 75 ] 2>/dev/null && WARN=" | COMPACT NOW"
echo "[$MODEL] ${DIR##*/} ${BRANCH:+| $BRANCH} | ${PCT}% context${WARN}"
