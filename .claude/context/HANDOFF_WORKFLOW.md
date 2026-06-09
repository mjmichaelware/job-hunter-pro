# Job Hunter Pro AI Handoff Workflow

This is the standard workflow for moving work between Claude, Codex, Gemini, ChatGPT, or any future CLI or web AI agent.

## Source of truth order

1. Git branch and committed repo files.
2. .claude/context/SESSION_STATE.md.
3. .claude/context/AI_AGENT_TAKEOVER_PACKET.md.
4. .claude/context/FINAL_PATCH_PLAN.md.
5. .claude/context/BUG_LEDGER.md.
6. .claude/context/CANONICAL_RESOLVED_SPEC.md.
7. Downloadable archive job_hunter_pro_audit_handoff.tar.gz.

## Required end-of-session workflow

1. Update SESSION_STATE.md.
2. Update BUG_LEDGER.md if findings changed.
3. Update FINAL_PATCH_PLAN.md if the plan changed.
4. Update FINAL_PROOF_REPORT.md after any patch cycle.
5. Run python compile.
6. Run safe local proof.
7. Run git diff check.
8. Commit only proven work.
9. Push only when explicitly authorized.
10. Export the handoff packet.

## Export command

bash .claude/scripts/export_handoff_packet.sh

## Archive rule

The tar.gz file is a transport packet, not a magic context bypass. AI tools must decompress it before reading the text.
