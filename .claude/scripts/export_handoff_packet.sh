#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_BASE="${1:-$HOME/storage/downloads}"
PACKET_DIR="$OUT_BASE/job_hunter_pro_audit_handoff"
ARCHIVE="$OUT_BASE/job_hunter_pro_audit_handoff.tar.gz"
cd "$ROOT"
mkdir -p "$OUT_BASE"
rm -rf "$PACKET_DIR"
mkdir -p "$PACKET_DIR"
FILES=(
".claude/context/SESSION_STATE.md"
".claude/context/AI_AGENT_TAKEOVER_PACKET.md"
".claude/context/HANDOFF_WORKFLOW.md"
".claude/context/MASTER_WORKFLOW_INDEX.md"
".claude/tasks/MASTER_AGENT_START_PROMPT.md"
".claude/context/DEFCON1_AGENT_RULES.md"
".claude/tasks/NEXT_AGENT_START_HERE.md"
".claude/context/DOCUMENT_CONTRADICTION_MATRIX.md"
".claude/context/CANONICAL_RESOLVED_SPEC.md"
".claude/context/CURRENT_CODE_MAP.md"
".claude/context/CODEBASE_INDEX.md"
".claude/context/ROUTE_MAP.md"
".claude/context/DATA_FLOW_MAP.md"
".claude/context/API_CONTRACTS.md"
".claude/context/UI_CONTRACTS.md"
".claude/context/PROVIDER_MATRIX.md"
".claude/context/SECURITY_MODEL.md"
".claude/context/STUB_PLACEHOLDER_AUDIT.md"
".claude/context/BUG_LEDGER.md"
".claude/context/FINAL_PATCH_PLAN.md"
".claude/context/FINAL_PROOF_REPORT.md"
)
for f in "${FILES[@]}"; do
  [ -f "$f" ] && cp -f "$f" "$PACKET_DIR/"
done
tar -czf "$ARCHIVE" -C "$OUT_BASE" job_hunter_pro_audit_handoff
echo "Handoff packet exported:"
ls -lh "$ARCHIVE"
echo
echo "Contents:"
tar -tzf "$ARCHIVE"
