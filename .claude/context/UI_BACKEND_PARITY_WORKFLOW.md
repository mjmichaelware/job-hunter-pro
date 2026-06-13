# UI / Backend Parity Workflow — Job Hunter Pro

Purpose: every backend capability must have a truthful, beautiful, mobile-first UI rendering path, and every visible UI control must map to a real backend endpoint or be explicitly labeled pending.

This workflow is the authoritative sequence for any UI/backend parity cycle on Job Hunter Pro. It is derived from `APP_MISSION.md`, `MASTER_WORKFLOW_INDEX.md`, `BUG_LEDGER.md`, `FINAL_PATCH_PLAN.md`, and `CANONICAL_RESOLVED_SPEC.md`. When this workflow conflicts with a raw doc, this workflow loses to project-level instructions (`CLAUDE.md`, `PROJECT_DIGEST.md`) and to the canonical spec; otherwise it governs the audit/patch cycle.

---

## Required stages

### S0. Ground truth
Read, in this order:
1. `.claude/context/SESSION_STATE.md`
2. `.claude/context/AI_AGENT_TAKEOVER_PACKET.md`
3. `.claude/context/FINAL_PATCH_PLAN.md`
4. `.claude/context/BUG_LEDGER.md`
5. `.claude/context/CANONICAL_RESOLVED_SPEC.md`
6. `.claude/context/CURRENT_CODE_MAP.md`
7. `.claude/context/APP_MISSION.md`

Do not redo the prior audit unless these files are missing or inconsistent. Capture any contradictions in `DOCUMENT_CONTRADICTION_MATRIX.md`.

### S1. UI surface inventory
Walk every visible UI surface. Record: panel, button, card, metric, select, badge, renderer function, owning file, loading state, empty state, error state, mobile behavior, provider/cost risk.

Output: `.claude/context/UI_SURFACE_INVENTORY.md`.

### S2. Backend endpoint inventory
Walk every Flask route in `api/index.py`, `app.py`, and any active blueprint. Record: route, method, auth, side effects, cache behavior, provider calls, response schema, frontend caller, safe-on-page-load status.

Output: `.claude/context/BACKEND_ENDPOINT_INVENTORY.md`.

### S3. Contract parity matrix
Cross-reference UI surfaces against backend endpoints and vice versa. Flag:
- UI control without endpoint (label pending).
- Endpoint without UI consumer (potential dead surface).
- Payload-field mismatch (renderer expects field the API does not return, or vice versa).

Output: `.claude/context/UI_BACKEND_PARITY_MATRIX.md`.

### S4. Job visibility pipeline
Document the full path: raw provider job → `normalize_job()` → enrichment / scoring → `classify_job()` (rejection vs `resolution_flags`) → JSON payload → frontend render. Highlight where the canonical 3-bucket model (accepted, unresolved, rejected) must surface and where it currently fails (CRIT-1).

Output: `.claude/context/JOB_VISIBILITY_PIPELINE.md`.

### S5. UI/UX implementation plan
Specify: card layout, badges for `resolution_flags`, accepted/unresolved/rejected groups, provider breakdown surface, apply/source URL preservation, filter behavior (min rating, max radius, max transit, min review score, role, house, keyword), usage/budget/history/opportunities surfaces, mobile-first layout decisions.

Output: `.claude/context/UIUX_IMPLEMENTATION_PLAN.md`.

### S6. Patch plan
Sequence the edits. For each: target file, intended change, blast radius, rollback, proof command. Reference `BUG_LEDGER.md` IDs. Match patch order from `FINAL_PATCH_PLAN.md` unless a constraint requires reordering.

Output: `.claude/context/UI_BACKEND_PATCH_PLAN.md`.

### S7. Patch only confirmed defects
Inspect the live code before editing. No blind-regex large-file rewrites. Edits must trace back to a `BUG_LEDGER.md` ID and an approved patch-plan line. No speculative refactors. No unrelated housekeeping bundled in.

### S8. Proof
Run, in this order:
1. `python3 -m py_compile $(git ls-files "*.py")`
2. `bash .claude/scripts/safe_local_proof.sh`
3. `git diff --check`
4. `git diff --stat`
5. `git diff`

Any failure halts the cycle.

### S9. Final proof report
Write `.claude/context/UI_BACKEND_FINAL_PROOF_REPORT.md` summarizing:
- Which bug-ledger items were patched.
- Files touched and line counts.
- Proof command output (PASS/FAIL).
- Remaining defects deferred (with rationale).
- Explicit "stop before deploy" line.

### S10. Stop before deploy
No `gcloud run deploy`. No `git push`. No `git commit` unless explicitly authorized. Report the proof status and await instruction.

---

## Hard rules

- Do not print secrets.
- Do not hardcode secrets.
- Do not put tokens in URLs.
- Do not call live `/api/jobs` unless explicitly authorized.
- Do not call `/api/ingest` unless explicitly authorized.
- Do not deploy.
- Do not push.
- Do not commit without explicit instruction.
- Do not use LLM providers (OpenAI, Gemini, Claude, Groq, xAI) for job discovery — they are enrichment / classification / scoring only.
- Discovery providers are SerpAPI Jobs, SerpAPI Organic, Adzuna, USAJobs, Jooble, Careerjet, The Muse, and Google Places / opportunities. Nothing else.
- Missing or uncertain place / radius / transit resolution must become `resolution_flags` and `needs_resolution: true`, NOT silent rejection.
- Accepted, unresolved, and rejected jobs must be truthfully visible in the UI.
- No fake data: no fabricated jobs, provider counts, charts, metrics, AI claims, history, or success states.
- Inspect current code before patching; do not blind-regex large files.
- Compile before deploy. Run safe local proof before any deploy decision. After deploy, check `/api/health`. If health fails, check logs.

---

## Stage outputs (single source of truth)

| Stage | Output file | Status indicator |
|---|---|---|
| S1 | `UI_SURFACE_INVENTORY.md` | exists / stale / missing |
| S2 | `BACKEND_ENDPOINT_INVENTORY.md` | exists / stale / missing |
| S3 | `UI_BACKEND_PARITY_MATRIX.md` | exists / stale / missing |
| S4 | `JOB_VISIBILITY_PIPELINE.md` | exists / stale / missing |
| S5 | `UIUX_IMPLEMENTATION_PLAN.md` | exists / stale / missing |
| S6 | `UI_BACKEND_PATCH_PLAN.md` | exists / stale / missing |
| S9 | `UI_BACKEND_FINAL_PROOF_REPORT.md` | exists / stale / missing |

When a downstream file (BUG_LEDGER, FINAL_PATCH_PLAN, CANONICAL_RESOLVED_SPEC) changes in a way that invalidates a prior stage output, mark that output stale and regenerate before continuing.

---

## Authority hierarchy when this workflow is ambiguous

1. `CLAUDE.md` / `PROJECT_DIGEST.md` — wins.
2. `CANONICAL_RESOLVED_SPEC.md`.
3. Current code (source of truth for inventory).
4. `FINAL_PATCH_PLAN.md`.
5. `BUG_LEDGER.md`.
6. This workflow.
7. Raw docs `AI_JOB_AGENT_1..6`.

If a new conflict appears, add a row to `DOCUMENT_CONTRADICTION_MATRIX.md`, resolve, and update the canonical spec.
