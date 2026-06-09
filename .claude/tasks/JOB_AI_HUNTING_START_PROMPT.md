# Job AI Hunting Start Prompt

Read these files in order:

1. .claude/tasks/MASTER_AGENT_START_PROMPT.md
2. .claude/context/APP_MISSION.md
3. .claude/context/SESSION_STATE.md
4. .claude/context/AI_AGENT_TAKEOVER_PACKET.md
5. .claude/context/CANONICAL_RESOLVED_SPEC.md
6. .claude/context/BUG_LEDGER.md
7. .claude/context/FINAL_PATCH_PLAN.md
8. .claude/context/UI_BACKEND_PARITY_WORKFLOW.md

Mission: target Job Hunter Pro / Job AI Hunting.

Do not redo the full document audit unless the audit files are missing or inconsistent.

Start from the existing audit and patch plan.

Required first patch cycle:
1. Inspect current code for CRIT-1.
2. Patch rejection_reasons() so real rejection reasons are returned.
3. Preserve the canonical rule that missing or uncertain place resolution becomes resolution_flags and needs_resolution, not silent job deletion.
4. Inspect current code for CRIT-2.
5. Patch /api/ingest OIDC verification only if it can be done safely without secrets in code or URLs.
6. Update frontend/API contracts only where needed so accepted, unresolved, and rejected jobs render truthfully.

Before editing, write or update:
- .claude/context/UI_SURFACE_INVENTORY.md
- .claude/context/BACKEND_ENDPOINT_INVENTORY.md
- .claude/context/UI_BACKEND_PARITY_MATRIX.md
- .claude/context/JOB_VISIBILITY_PIPELINE.md
- .claude/context/UI_BACKEND_PATCH_PLAN.md

After patching, run:
- python3 -m py_compile $(git ls-files "*.py")
- bash .claude/scripts/safe_local_proof.sh
- git diff --check
- git diff --stat
- git diff

Write .claude/context/UI_BACKEND_FINAL_PROOF_REPORT.md.

Stop before deploy.
