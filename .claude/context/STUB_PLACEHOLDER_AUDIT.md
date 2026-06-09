# Stub / Placeholder / Dead-Code Audit — Job Hunter Pro

Findings against `CANONICAL_RESOLVED_SPEC.md`. Each row: file/line, evidence, severity (CRIT/HIGH/MED/LOW), real defect?, recommendation. Only real defects feed `BUG_LEDGER.md` and `FINAL_PATCH_PLAN.md`. Housekeeping items are tracked but deferred.

Search scope excluded `.venv/`, `venv/`, `.git/`, `__pycache__/`, `.claude/skills/`, `.claude/commands/`, `.claude/agents/`, `.claude_setup/`, `.claude_backup_*`, `.repair_backups/` to avoid vendored or generated noise.

---

## A. Hardcoded fake data (canonical §1.8 violation — "no fake data")

| # | Location | Evidence | Severity | Defect? | Recommendation |
|---|---|---|---|---|---|
| A1 | `providers/reasoning/openai.py:42-50` | `enrich()` returns hardcoded `{"summary": "Enriched content placeholder", "tags": ["job", "tech"]}` whenever `is_available()` (key present). Comment line 26-27: *"Real implementation would call OpenAI API here."* | HIGH | YES | Replace stub body with real OpenAI call OR mark `available=False, mode="not_implemented"` until wired. Do not return fake strings labeled as enrichment. |
| A2 | `providers/reasoning/claude.py:40-48` | `enrich()` returns hardcoded `{"summary": "Claude enriched summary"}`. Same pattern. | HIGH | YES | Same. (If we wire it for real, use `claude-opus-4-7` with adaptive thinking per project model defaults.) |
| A3 | `providers/reasoning/gemini.py`, `groq.py`, `xai.py` | Not fully read but likely follow the same `"S0 scaffold"` stub pattern. | HIGH | LIKELY | Verify each; treat consistently with A1/A2. |
| A4 | Top-level `live_jobs_now.json`, `live_jobs_federated_now.json`, `live_providers_after_fanout.json`, `probe__api_*.json` (5 files) | Captured probe responses committed to repo. Not loaded by any code, but they include partial provider output. Could be mistaken for fixtures by future readers. | LOW | NO (not loaded) | Move to `.gitignore`d `probes/` dir, or delete after this cycle. |

---

## B. Stubs that ship as code

| # | Location | Evidence | Severity | Defect? | Recommendation |
|---|---|---|---|---|---|
| B1 | `pipeline/resolve_place.py` (entire file, 8 lines) | `def resolve_place(job): ... job["resolved_place"] = f"resolved_{loc}"; return job` — fabricates a fake resolved string. | HIGH | YES — but **NOT in the live path.** `api/index.py` has its own real `resolve_place` (line 436) that calls Maps. The decoupled stub is unused. | Delete or replace with a real implementation that wraps `geo/places_text.py` + `geo/geocode.py`. Until then it lies about being a real module. |
| B2 | `pipeline/reject.py` (entire file) | Has only `reject_early` (empty title check) and `reject_late` (industry=unknown, match<40). Canonical reasons (`not_food_service`/`not_in_industry`, `ambiguous_place_resolution`, `duplicate`, `provider_error`, `budget_guard`, `missing_source_url`) absent. No `resolution_flags` logic. | HIGH | YES — but **NOT in the live path.** `api/index.py` has its own `rejection_reasons` (line 626) — though that one has the disabled-`return []` bug (see BUG_LEDGER CRIT-1). | Decide: either delete `pipeline/reject.py` (legacy) OR make it the canonical source and rewire `api/index.py` to use it. |
| B3 | `providers/reasoning/base.py` (single line) | `"""S0 scaffold placeholder."""` — empty file. | LOW | NO (unused — classes import from `providers/base.py` instead) | Delete to remove misleading scaffold. |
| B4 | `tests/test_providers_registry.py:1` | Begins with `"""S0 scaffold placeholder."""`. Test body needs verification. | MED | POSSIBLY | If body is real assertions, just remove the docstring; if skeletal, populate or delete. |
| B5 | `api/jobs.py` | Single comment line: `# Handled by proxy in app.py`. | LOW | NO (intentional) | Keep — documents the proxy pattern. |

---

## C. Dead duplicate trees (housekeeping)

| # | Location | Evidence | Severity | Defect? | Recommendation |
|---|---|---|---|---|---|
| C1 | `templates/index.html`, `templates/base.html`, `templates/partials/navbar.html` | `api/index.py` references this folder via `template_folder=str(BASE_DIR/"templates")` but the legacy app is mounted under the `app.py` proxy and serves no `/` from there. Dead. | LOW | NO (not breaking) | Delete after confirming with Michael no legacy URL fallback is intended. |
| C2 | `static/css/...`, `static/js/main.js` | Same — referenced by `api/index.py` `static_folder=...` but never reached. Dead. | LOW | NO | Delete with C1. |
| C3 | `public/static/css/...`, `public/static/js/main.js` | Vercel deploy artifact. Cloud Run is the canonical target. | LOW | NO | Delete with C1; remove `vercel.json` and `.vercel/` to remove conflicting deploy target. |
| C4 | `index.html` (top-level) | Vercel artifact, orphan. | LOW | NO | Delete. |
| C5 | `api/health.py`, `api/history.py`, `api/opportunities.py`, `api/research.py`, `api/usage.py`, `api/why_three.py` | Present but **not imported** by `api/__init__.py`. The proxy in `app.py` forwards these endpoints to `api/index.py`. Dead duplicates. | MED | NO | Either wire them in (and remove proxy fallback for the same paths) OR delete to remove the confusion. The current "two truths" wiring is a long-term hazard. |
| C6 | `api/scrape.py` | Not imported. Likely Codex-era leftover. | LOW | NO | Delete after confirming. |
| C7 | Duplicate raw docs `.claude/context/AI_JOB_AGENT_5.md`+`.txt`, `AI_JOB_AGENT_6.md`+`.txt` | Byte-identical pairs. | LOW | NO | Delete `.txt` copies; `CLAUDE.md` only references `.md`. |

---

## D. Top-level debris

| # | Location | Severity | Defect? | Recommendation |
|---|---|---|---|---|
| D1 | 14 root-level repair `.sh` scripts (`01_export_*`, `02_export_*`, `RESET_*`, `compare_real_dashboard_to_s10.sh`, `diagnose_*`, `expose_*`, `find_*`, `prove_*`, `replace_*`, `s10h_*`, `show_all_*`, `surface_*`, `wire_*`, `export_clean_*`) | LOW | NO | Move to `.claude/scripts/archive/` or delete. They burn cognitive load every time someone runs `ls`. |
| D2 | Top-level debug Python (`debug_scraper.py`, `debug_serp.py`, `full_debug.py`) | LOW | NO | Move under `.claude/scripts/` or delete. |
| D3 | Two Python virtualenvs: `.venv/` (active per `safe_local_proof.sh`) + `venv/` (root, large) | LOW | NO | Delete `venv/`; add both to `.gitignore` if not already there. |
| D4 | `.repair_backups/`, `.claude_backup_20260608_171609/` | LOW | NO | Move out of the repo. Backups don't belong in version control. |
| D5 | `.gemini/`, `.local/`, `.vercel/`, `GEMINI.md`, `gemini_r10c_filter_drawer_responsive_fix.md` | LOW | NO | `.gemini/`, `.local/`, `.vercel/` → `.gitignore`. `GEMINI.md` is Codex's instruction file for Gemini — keep if still wanted, else delete. The `gemini_r10c_...md` patch note can be archived. |
| D6 | Conflicting deploy configs: `Dockerfile`, `Procfile`, `cloudbuild.yaml`, `vercel.json`, `LIVE_URL.txt` | MED | POSSIBLY | Canonical target is Cloud Run via Buildpacks (Procfile + gunicorn `app:app`). Decide: keep `Procfile` only, or keep `Dockerfile`+`cloudbuild.yaml`. Drop `vercel.json`. `LIVE_URL.txt` exposes the production URL in the repo — fine if public, flag if anything secret. |

---

## E. Frontend "Backend gap" branches (potentially dead UI states)

| # | Location | Evidence | Severity | Defect? | Recommendation |
|---|---|---|---|---|---|
| E1 | `web/static/js/render_history.js:8` | Renders "History endpoint is currently a placeholder (Backend gap). No batches retrieved." | LOW | NO (honest fallback) | When `BATCH_BUCKET` is unset and `/api/history` returns empty `batches[]`, this copy fires correctly. Verify it doesn't fire when a real `BATCH_BUCKET` is set and batches exist. |
| E2 | `web/static/js/render_providers.js:10` | Renders "Providers endpoint is currently a placeholder (Backend gap)." | LOW | POSSIBLY | `/api/providers` returns real data. Should only show this on a failed fetch. Verify trigger condition is `!data` and not `data.providers.length === 0` (which can happen with no providers configured but is not a "backend gap"). |
| E3 | `web/static/js/render_budget.js:98` | Renders "Backend GAP: Jobs endpoint returned a placeholder. Cannot generate dry-run execution plan." | LOW | POSSIBLY | Triggered via `UI.isPlaceholder(payload)`. The dry-run response message is *"Live jobs endpoint is available. This dry run did not spend discovery provider budget."* — contains neither "placeholder" nor "not implemented". So this branch is **dead** unless `/api/jobs?dry_run=1` text changes. Confirm. |
| E4 | `web/static/js/render_why_three.js:9` | Renders "Why Three endpoint is a placeholder (Backend gap). Decision engine unavailable." | LOW | POSSIBLY | `/api/why-three` returns real `status: explained`. Trigger should be `!data` only. Confirm. |

These are not severe — they're honest UI states. The risk is a false negative (showing "Backend gap" when the backend is fine).

---

## F. Logic stubs in the live path

| # | Location | Evidence | Severity | Defect? | Recommendation |
|---|---|---|---|---|---|
| F1 | `api/index.py:1183-1190` `verify_oidc()` | Only checks `Authorization: Bearer ` prefix; admits in comment: *"For S12-Omega proof, we assume Cloud Run/App Engine is verifying the token signature ... In a full S12, we'd use google-auth."* | HIGH | YES | Replace with real verification: validate JWT signature, audience = Cloud Run URL, email = scheduler SA. The decoupled `ingest/oidc.py` likely does this — wire `api/index.py`'s `/api/ingest` to call it. Track in BUG_LEDGER as HIGH-6. |
| F2 | `api/index.py:626-648` `rejection_reasons()` | Builds `reasons` list with all 6 canonical food-only rejection reasons, then `return []`. | CRIT | YES | Track as BUG_LEDGER CRIT-1. The fix is **not** simply returning `reasons` — that would re-enable hard rejection on missing resolution and reintroduce the C23 defect. The fix is to **split** into (a) genuine rejections (`not_food_service`/`not_in_industry`, `outside_radius_X`, `transit_too_long_X`, `duplicate`, `provider_error`, `budget_guard`, `missing_source_url`) and (b) `resolution_flags` for missing-but-not-disqualifying (`address_unresolved`, `radius_unknown`, `transit_unknown`). |
| F3 | `api/index.py:436-463` `resolve_place()` | Has `bad` list at line 422 to filter spurious address regex matches (per Doc 1's known bug). | LOW | NO (already fixed defensively) | Real implementation — good. |
| F4 | `api/index.py:528` review-score formula | `min(100, max(0, (rating_float/5)*90 + min(10, math.log10(count_int+1)*4)))` — NOT the canonical 60/15/15/10 formula. Caps at `rating·90 + 10` but doesn't enforce sentiment/consistency components. | MED | YES | Replace with canonical 60/15/15/10 formula per spec §9 and Doc 1 §C14. Track in BUG_LEDGER MED. |
| F5 | `api/index.py:626-647` rejection reasons hardcoded restaurant-only | Uses `is_food_text(...)` and `not_food_service` — does not consult `industries/` registry for multi-industry classification. | HIGH | YES | Track in BUG_LEDGER HIGH. The pipeline path that wires `pipeline/classify.py` against `industries/get_all_routes()` is the canonical solution but not in the live path. |
| F6 | `api/index.py:659-670` `raw_job_queries()` | Hardcoded to `ROLE_QUERIES` (10 restaurant queries) and uses nearby restaurant names. Multi-industry registry not consulted. | HIGH | YES | Track in BUG_LEDGER HIGH. Plug `industries/get_all_routes()` to expand. |
| F7 | `api/index.py:825-892` GCS access via raw HTTP + GCE metadata token | No `google-auth` use; Doc 1 §"Security/Deployment Requirements" explicitly says to use `google-auth AuthorizedSession`. | MED | YES | Replace with `google-auth` (add to requirements.txt) or migrate to Firestore via `store/firestore_client.py`. |

---

## G. Useful tooling discovered (not defects)

| # | Location | Note |
|---|---|---|
| G1 | `scripts/current_truth_audit.py` | Has its own stub-detection grep with `STUB`/`PLACEHOLDER`/`NotImplemented`/`TODO` categories. Could be folded into the regular CI proof loop. |
| G2 | `scripts/s12_omega_audit.py`, `scripts/s12_provider_probe.py` | Audit/probe helpers. |
| G3 | `.claude/scripts/inspect_stack.sh`, `safe_local_proof.sh` | Already in use by the OS layer. |

---

## H. Summary

| Severity | Count | Action |
|---|---|---|
| CRIT | 1 (F2) | Must fix in this patch cycle. |
| HIGH | 5 (A1, A2, A3, F1, F5/F6, plus B1/B2 if we decide pipeline/ is canonical) | Schedule into patch plan. |
| MED | 5 (B4, C5, D6, F4, F7) | Schedule when paired with related HIGH fixes. |
| LOW | ~15 housekeeping items (A4, B3, B5, C1-C4, C6, C7, D1-D5, E1-E4) | Defer past current patch cycle. Track in housekeeping note. |

The single most important finding: **F2 (rejection gate returns `[]`) silently inverts the live-jobs pipeline.** Every raw provider hit becomes "accepted" with no resolution flags, no rejection reasons, and no food-service filter. This is both the cause of the symptom that triggered this audit and the keystone for the C23 fix.

The second most important finding: **F1 (`verify_oidc` is bypass)** is a security regression — `/api/ingest` is currently protected by little more than a Bearer-prefix string check.
