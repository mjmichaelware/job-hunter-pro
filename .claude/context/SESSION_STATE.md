# Session State

## Last session: Audit & reconciliation cycle (Claude)

**Status: AUDIT COMPLETE. Awaiting Michael's go-ahead before any app-logic patch.**

### What this session produced
- `.claude/context/DOCUMENT_CONTRADICTION_MATRIX.md` — 27 numbered contradictions across Docs 1–6 with resolutions.
- `.claude/context/CANONICAL_RESOLVED_SPEC.md` — single source of truth derived from the matrix.
- `.claude/context/CURRENT_CODE_MAP.md` — consolidates CODEBASE_INDEX / ROUTE_MAP / DATA_FLOW_MAP / PROVIDER_MATRIX / API_CONTRACTS / UI_CONTRACTS into one map.
- `.claude/context/STUB_PLACEHOLDER_AUDIT.md` — every stub / dead duplicate / housekeeping item.
- `.claude/context/BUG_LEDGER.md` — 2 CRIT, 5 HIGH, 4 MED, 6 LOW defects with evidence.
- `.claude/context/FINAL_PATCH_PLAN.md` — sequenced patches with proof commands and rollback.

### Key findings (highest priority)
- **CRIT-1:** `api/index.py:626-648` `rejection_reasons()` builds the rejection list and then `return []`. Every raw job is silently accepted; `rejected` is always empty. Half-aligned with the C23 fix (don't drop on missing resolution) but missing the `resolution_flags` half.
- **CRIT-2:** `api/index.py:1183-1190` `verify_oidc()` only checks the `Authorization: Bearer ` prefix. Comment admits the bypass. `/api/ingest` is effectively unprotected against signature/audience/email forgery.
- **HIGH-3:** `providers/reasoning/{openai,claude}.py` return hardcoded fake-enrichment strings ("Enriched content placeholder", "Claude enriched summary") when keys are present. Not in any live path right now.
- **HIGH-4:** Live `/api/jobs` path is restaurant-only (`ROLE_QUERIES`, `is_food_text`, `not_food_service`). 6-industry registry exists but is not consulted.

### Safe local proof
PASSING (verified at session start, before any edits): `/`, `/api/providers`, `/api/health`, `/api/jobs?dry_run=1`, `placeholder_blueprint_registered=False`.

### Hard rules still in effect
- Do not deploy unless explicitly told.
- Do not push unless explicitly told.
- Do not commit unless explicitly told.
- Do not call `/api/ingest`.
- Do not call live `/api/jobs`.
- Do not print secrets.

### Next step
Michael reviews the patch plan and decides which patches to authorize. P1 (rejection gate + resolution_flags) and P2 (real OIDC verification) are the recommended pair for this cycle. Stop and await instruction.

Update this file when context approaches 75 percent or at the end of each session.
