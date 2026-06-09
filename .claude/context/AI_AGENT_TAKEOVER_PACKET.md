# AI Agent Takeover Packet — Job Hunter Pro

Start here:

1. .claude/context/SESSION_STATE.md
2. .claude/context/DOCUMENT_CONTRADICTION_MATRIX.md
3. .claude/context/CANONICAL_RESOLVED_SPEC.md
4. .claude/context/CURRENT_CODE_MAP.md
5. .claude/context/STUB_PLACEHOLDER_AUDIT.md
6. .claude/context/BUG_LEDGER.md
7. .claude/context/FINAL_PATCH_PLAN.md

Claude audit is complete. No app-logic patch has been authorized yet.

Highest priority findings:
- CRIT-1: api/index.py rejection_reasons() builds reasons but returns [].
- CRIT-2: /api/ingest OIDC verification is only a Bearer-prefix check.

Next recommended patch cycle:
- P1: rejection gate + resolution_flags / needs_resolution.
- P2: real OIDC verification for /api/ingest.

Hard rules:
- Do not print secrets.
- Do not deploy unless explicitly told.
- Do not push unless explicitly told.
- Do not call live /api/jobs unless explicitly told.
- Do not call /api/ingest unless explicitly told.
- LLMs are enrichment/classification only, never discovery.
