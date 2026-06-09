# Current Code Map — Job Hunter Pro

Source of truth for what is **actually in the repo right now**, compared against `CANONICAL_RESOLVED_SPEC.md`. Consolidates what the Neutron prompt named as CODEBASE_INDEX, ROUTE_MAP, DATA_FLOW_MAP, PROVIDER_MATRIX, API_CONTRACTS, and UI_CONTRACTS into a single map (kept here for context efficiency; same coverage). Findings here feed `STUB_PLACEHOLDER_AUDIT.md`, `BUG_LEDGER.md`, and `FINAL_PATCH_PLAN.md`.

---

## 1. Repository layout (active code)

### 1.1 Backend Python tree
| Path | Role | Spec alignment |
|---|---|---|
| `app.py` | Flask factory. Mounts `api_bp` blueprint, intercepts `/api/ingest` for Bearer-prefix check, falls back to a Werkzeug-test-client proxy that forwards `/api/<path>` to legacy `api.index.app`. Serves `web/templates/index.html` at `/`. Exposes `/api/_surface` truth marker. | ✅ Decoupled factory shape; ⚠ proxy-to-legacy keeps two route truths in play. |
| `api/__init__.py` | Declares `api_bp = Blueprint('api', ...)`, imports `providers`, `industries`, `applications`, `ingest` modular routes. Comments explicitly defer `health/usage/jobs/opportunities/history/research/why_three/batches/batch` to the proxy. | ✅ Split intent documented. |
| `api/index.py` (1,281 lines) | Legacy fat module = current actual implementation of `/api/health`, `/api/usage`, `/api/jobs`, `/api/opportunities`, `/api/history`, `/api/research/place`, `/api/why-three`, `/api/batches`, `/api/batch/<...>`, `/api/ingest`, `/api/debug/jobs`, `/api/demo`, `/api/search`. Version marker: `job_hunter_v8_stable_orchestrated_dashboard`. Restaurant-specific (FOOD_TERMS, BAD_TERMS, ROLE_QUERIES, ROLE_GROUPS). Calls into `search.live_provider_bridge.fetch_provider_raw_jobs` for fair fanout (good). Re-implements `verify_oidc()` weakly. | ⚠ Restaurant-only despite 6-industry decoupled spec; ⚠ weak OIDC; ❌ rejection gate silently disabled (see Bug Ledger CRIT-1). |
| `api/jobs.py` | Empty stub: `# Handled by proxy in app.py`. | Intentional. |
| `api/scrape.py` | Not used by `app.py` or `api/__init__.py`. Likely Codex-era leftover. | ⚠ Dead. |
| `api/providers.py` | Real handler. Returns provider key/label/type/availability via `providers.get_all_providers()`. No secrets. | ✅ |
| `api/industries.py`, `api/applications.py`, `api/ingest.py` | Modular routes mounted under `api_bp`. Need individual content review (not yet inspected in detail). | — |
| `api/health.py`, `api/history.py`, `api/opportunities.py`, `api/research.py`, `api/usage.py`, `api/why_three.py` | Present in repo but **not imported** by `api/__init__.py` — superseded by the proxy-to-legacy pattern. | ⚠ Dead duplicates. |
| `core/` (config, clock, errors, http, logging) | Cross-cutting helpers. `core/config.py` reads env-only config. | ✅ |
| `models/` (10 dataclasses: search_result, job, job_snapshot, place, review, rejection, batch, application, api_usage, enums) | Pydantic v2 / dataclass shapes per Doc 4. | ✅ |
| `industries/` (6 routes: food_service, hospitality, sales, customer_service, care_social, retail_ops + base + registry) | Canonical 6 industries present. | ✅ |
| `providers/base.py` | ABC + `ProviderType` + `ProviderMetadata` used by both search and reasoning subclasses. | ✅ |
| `providers/__init__.py` | Registry: `get_all_providers()`, `get_providers_by_type()`. | ✅ |
| `providers/search/` (adzuna, careerjet, jooble, serpapi_jobs, serpapi_organic, themuse, usajobs) | 7 canonical discovery providers, one file each. | ✅ |
| `providers/reasoning/` (openai, gemini, groq, claude, xai + base.py) | 5 canonical reasoning providers. `base.py` is an empty `"""S0 scaffold placeholder."""` (unused — classes import from `..base` = `providers/base.py`). **openai.py and claude.py return hardcoded fake-enrichment strings** ("Enriched content placeholder", "Claude enriched summary") even when keys are configured. | ❌ Fake data violates canonical no-fakes rule. |
| `geo/` (geocode, distance, haversine, place_details, places_nearby, places_text) | Maps family wrappers. Not yet inspected in detail. | — |
| `pipeline/` (normalize, resolve_place, score_match, score_review, classify, dedupe, reject, run) | Decoupled pipeline stages. **`resolve_place.py` is an 8-line stub** that returns a fake `f"resolved_{loc}"` string. `reject.py` has a minimal `reject_early/reject_late` that does NOT include the canonical reasons list and has NO `resolution_flags` logic. | ❌ Stub + missing canonical logic. |
| `search/` (federated, budget, usage_tracker, live_provider_bridge) | `federated.py` is a planner-style class. `budget.py` implements `BudgetGuard` with the `SERPAPI_MIN_SEARCHES_LEFT` threshold. `live_provider_bridge.fetch_provider_raw_jobs()` is the **real fair-fanout used by `/api/jobs`** — per-provider cap, provider_breakdown with truthful status. Free providers (themuse/usajobs) hardcoded as "always affordable". | ✅ Fair fanout exists and is wired; ⚠ `_LOC_NOISE` regex is SLC-specific. |
| `ingest/` (oidc, scheduler_job) | OIDC verifier + scheduler entrypoint exist. Not yet inspected in detail. But `api/index.py` re-implements its own weaker `verify_oidc()` and that is what `/api/ingest` actually hits. | ⚠ Real OIDC verifier may be bypassed. |
| `store/` (firestore_client, repository, applications_repo, batches_repo, cache_repo, jobs_repo, places_repo, reviews_repo, usage_repo) | Firestore repos present. Not yet inspected in detail. **`api/index.py` uses raw GCS HTTP + metadata token for batches** (lines 825-892), not these repos. | ⚠ Two storage layers: Firestore repos (decoupled) vs raw GCS (legacy). Doc 2/4 says Firestore; legacy still uses GCS. |
| `scripts/` (current_truth_audit.py, s12_omega_audit.py, s12_provider_probe.py) | Audit/probe helpers. | ✅ Tooling. |
| `tests/` (14 files: api_frontend_contract, applications_api, dedupe, federated_search, industries_registry, multi_industry_pipeline, oidc_ingest, pipeline_reject, provider_search_pass1/2, providers_registry, reasoning_providers, s9_full_api_wiring, score_review) | Decent unit-test coverage. `test_providers_registry.py` begins with `"""S0 scaffold placeholder."""` — may be skeletal. | ⚠ Need verification one is not skeletal. |

### 1.2 Frontend trees (FOUR — three are dead)

| Path | Status |
|---|---|
| `web/templates/index.html` (514 lines) + `web/static/` (css/js/icon.svg/manifest.json/sw.js) | ✅ **ACTIVE** — wired in `app.py` via `template_folder=str(WEB_DIR/"templates")`, `static_folder=str(WEB_DIR/"static")`. |
| `templates/index.html` + `templates/base.html` + `templates/partials/navbar.html` | ❌ **DEAD** — `api/index.py` still references `template_folder=str(BASE_DIR/"templates")` but the legacy app is mounted under the proxy and serves no `/` route from there. Orphan tree. |
| `static/css/...` + `static/js/main.js` | ❌ **DEAD** — referenced by `api/index.py` `static_folder=...` but never reached via the proxy. |
| `public/static/css/...` + `public/static/js/main.js` | ❌ **DEAD** — looks like a Vercel deploy artifact (paired with `vercel.json` at root). |
| `index.html` (top-level, 4560 B) | ❌ **DEAD** — also a Vercel artifact. |

### 1.3 Root-level debris (housekeeping)
| Category | Items |
|---|---|
| Repair shell scripts | `01_export_clean_source_dump.sh`, `02_export_neutron_handoff.sh`, `RESET_TO_REGULAR_CLAUDE_AND_WRITE_MASTER_PROMPT.sh`, `compare_real_dashboard_to_s10.sh`, `diagnose_zero_accepted_jobs.sh`, `expose_live_engines_now.sh`, `find_live_data_regression.sh`, `prove_provider_fanout_gap.sh`, `replace_boilerplate_telemetry_with_live_truth.sh`, `s10h_fix_pipeline_stream_truth.sh`, `show_all_live_job_candidates.sh`, `surface_everything_truth_matrix.sh`, `wire_federated_providers_into_jobs.sh`, `export_clean_app_and_handoff.sh` (14 files) |
| Top-level debug Python | `debug_scraper.py`, `debug_serp.py`, `full_debug.py` |
| Probe JSON | `live_jobs_federated_now.json`, `live_jobs_now.json`, `live_providers_after_fanout.json`, `probe__api_*.json` (5 files) |
| Duplicate venvs | `.venv/` (active) + `venv/` (duplicate, large) |
| Backup dirs | `.repair_backups/`, `.claude_backup_20260608_171609/` |
| Multi-tool detritus | `.gemini/`, `.local/`, `.vercel/`, `GEMINI.md`, `gemini_r10c_filter_drawer_responsive_fix.md` |
| Conflicting deploy configs | `Dockerfile` (Docker), `Procfile` (Buildpacks), `cloudbuild.yaml` (Cloud Build), `vercel.json` (Vercel). Canonical target = Cloud Run via Buildpacks (Procfile + gunicorn `app:app`). |

### 1.4 Duplicate raw docs
- `.claude/context/AI_JOB_AGENT_5.md` ≡ `.claude/context/AI_JOB_AGENT_5.txt` (byte-identical, 55,393 B)
- `.claude/context/AI_JOB_AGENT_6.md` ≡ `.claude/context/AI_JOB_AGENT_6.txt` (byte-identical, 22,571 B)

---

## 2. Route map (live behavior)

Confirmed by reading the actual handlers. `app.py` order of resolution:
1. `/` → renders `web/templates/index.html`.
2. `/favicon.ico` → SVG from `web/static/`.
3. `/api/_surface` → JSON truth marker.
4. `/api/ingest` (POST) → intercepted by `app.py`; rejects 401 unless `Authorization: Bearer <anything>`; then proxies to `api.index`.
5. `api_bp` blueprint mounted at `/api`: `/api/providers`, `/api/industries`, `/api/applications`, `/api/ingest` (note: shadowed by app-level handler above).
6. Catch-all `/api/<path:path>` → `_proxy_to_real_api(path)` → forwards to `api.index.app` via Werkzeug test client.

### 2.1 Endpoint inventory

| URL | Method | Handler | Safe boot? | Truthful? |
|---|---|---|---|---|
| `/` | GET | `app.create_app().index` → `web/templates/index.html` | ✅ | ✅ |
| `/favicon.ico` | GET | inline | — | ✅ |
| `/api/_surface` | GET | inline | ✅ | ✅ truth marker |
| `/api/health` | GET | `api.index.health` | ✅ | ✅ reflects env flags |
| `/api/usage` | GET | `api.index.usage` | ✅ | ✅ SerpAPI account status + budget rules |
| `/api/why-three` | GET | `api.index.why_three` | ✅ | ✅ static explainer |
| `/api/opportunities` | GET | `api.index.opportunities` | ✅ (cached path) | ✅ but only if Maps key + Places nearby cached |
| `/api/jobs?dry_run=1` | GET | `api.index.jobs` short-circuit | ✅ | ✅ zero spend |
| `/api/jobs` | GET | `api.index.jobs` → `fetch_jobs_live()` | ❌ explicit only | ⚠ counts truthful, BUT all raw jobs pass through as "accepted" due to CRIT-1 |
| `/api/debug/jobs` | GET | `api.index.debug_jobs` → `fetch_jobs_live()` | ❌ explicit only | ⚠ same provider as above |
| `/api/research/place` | GET | `api.index.research_place` | explicit only | ✅ |
| `/api/batches` | GET | `api.index.batches` | ✅ | ⚠ requires `BATCH_BUCKET` env or returns empty |
| `/api/batch/<path>` | GET | `api.index.batch_by_name` | ✅ | ⚠ same |
| `/api/history` | GET | `api.index.history` → reads all GCS batches | ✅ | ⚠ requires `BATCH_BUCKET`; otherwise empty |
| `/api/ingest` | POST | `app.py` Bearer gate → proxy → `api.index.ingest` (which re-checks `verify_oidc()`) | NEVER from UI | ⚠ Both gates only check Bearer-prefix presence, not real OIDC signature/audience/email. |
| `/api/demo` | GET | aliases `jobs()` | — | ⚠ name is misleading — actually calls live jobs path. |
| `/api/search` | GET/POST | aliases `jobs()` | — | ⚠ same |
| `/api/providers` | GET | `api/providers.py` blueprint route | ✅ | ✅ |
| `/api/industries` | GET | `api/industries.py` blueprint route | ✅ | (not yet inspected) |
| `/api/applications` | GET/POST | `api/applications.py` blueprint route | ✅ | (not yet inspected) |

### 2.2 Spec endpoints currently MISSING from code
| Spec endpoint | Reality |
|---|---|
| `/api/search/providers/status` | Absent (the `/api/providers` blueprint covers the intent). |
| `/api/search/federated` | The proxy rewrites incoming `/api/search/federated` → `/api/search` (which is an alias of `/api/jobs`). Not a real federated endpoint. |
| `/api/predictions` (P5 Markov) | Absent (correctly — out of scope). |

---

## 3. Data flow

### 3.1 Page load (current, post-Codex)
1. Browser GET `/` → `web/templates/index.html` (514 lines, 8 tabs, EN/ES/RU buttons present, "Opening this dashboard does not run live discovery" copy in `aria-live` region).
2. `web/static/js/api.js` defines `API_URLS` with **no `jobs` entry** — explicit hygiene. Has `fetchJobsDryRun()` / `fetchJobsLive()` named functions.
3. Boot triggers safe fetches (per `state.js`/`tabs.js` — not exhaustively re-read here) to `/api/health`, `/api/usage`, `/api/providers`, `/api/industries`, `/api/opportunities`, `/api/history`, optional `/api/jobs?dry_run=1`. ✅ Matches canonical §8.
4. `safeFetch` caches successful responses to IndexedDB via `window.DB` for offline fallback. (PWA aspiration partial.)
5. `UI.isPlaceholder(payload)` checks for `payload.message` containing `"placeholder"` or `"not implemented"` — frontend explicitly tolerates backend gaps and renders honest unavailable states.

### 3.2 Live discovery (explicit user action)
1. User clicks "Run Live Discovery" → reveals "Confirm Live Discovery" / "Cancel" pair (in `web/templates/index.html` lines 48-54).
2. Confirm → JS calls `/api/jobs` (no `dry_run`).
3. `app.py` proxy forwards to `api.index.jobs()` → calls `fetch_jobs_live()` (line 672).
4. `fetch_jobs_live()` builds queries (`raw_job_queries()` line 659) — **hardcoded to `ROLE_QUERIES` (restaurant only)** plus dynamically extracted nearby restaurant names.
5. Calls `search.live_provider_bridge.fetch_provider_raw_jobs(queries, max_raw_jobs=Config.MAX_RAW_JOBS, location="Salt Lake City, UT")`. This is the **real fair-fanout**:
   - Iterates all registered SEARCH providers (per `providers.get_providers_by_type(ProviderType.SEARCH)`).
   - Sets per-provider cap = `ceil(max_raw_jobs / active_count)`.
   - Records truthful `provider_breakdown`: status ∈ `ok | dormant | stopped_provider_cap_reached | not_attempted_global_cap_reached | error | available_returned_zero`.
   - Preserves `source_url` / `apply_url`.
   - Returns `fair_fanout: True`.
6. Fallback if import fails: legacy SerpAPI path (line 700-715).
7. For each raw → `normalize_job(raw)`:
   - Restaurant-specific `resolve_place()` (line 436) — explicit-address regex + Places text search fallback.
   - `transit_to()`, `miles_between()` for commute + radius.
   - `match_score()` — restaurant-weighted.
   - `review_intelligence()` — score formula: `min(100, max(0, (rating/5)*90 + min(10, log10(count+1)*4)))`. **NOT the canonical 60/15/15/10 — review_score can reach 100 even with imperfect rating because cap at rating·90% only.** Diverges from spec C14.
8. `rejection_reasons(job)` (line 626): builds `reasons` list with 6 canonical reasons (`not_food_service`, `no_exact_restaurant_address_resolved`, `radius_unavailable`, `outside_radius_*mi`, `transit_unavailable`, `transit_too_long_*min`) — **then `return []`** (line 648). **All reasons are discarded; the rejection gate is dead.**
9. Caller (line 721-742): `if reasons:` is always false → every normalized job is appended to `accepted`. `rejected` stays empty.
10. Response shape: `data` = all jobs, `rejected` = empty, `rejected_count` = 0, `rejection_summary` = `{}`, `provider_breakdown` = truthful.

### 3.3 Scheduler ingest
1. Cloud Scheduler `0 */6 * * *` POSTs `/api/ingest` with OIDC Bearer.
2. `app.py` checks `Authorization: Bearer ` prefix only → proxies.
3. `api.index.ingest()` calls `verify_oidc()` — **also only checks Bearer prefix** (line 1183-1190, comment admits the bypass).
4. Runs `fetch_jobs_live()` and writes JSON batch to GCS via raw HTTP + GCE metadata token (line 825-892). Returns object name.
5. No Firestore write happens in this path — diverges from the canonical store/ Firestore-repo design.

### 3.4 History
1. `/api/history?hours=N` reads all GCS batches in time window (line 1231).
2. Returns flattened `data` (accepted jobs from all matching batches) + `batches` summaries.
3. Filtered through `apply_filters()` (UI filters).

---

## 4. Provider matrix

### 4.1 Discovery (7 search providers)
All discovery provider stubs exist as one file per provider under `providers/search/`. Status checked via `provider.is_available()` which reads env-config presence. Detailed read of each provider file deferred — all 7 are wired into `providers.__init__.get_providers_by_type(ProviderType.SEARCH)` per the registry pattern.

| Key | File | Discovery method | Available without key? |
|---|---|---|---|
| `serpapi_jobs` | `providers/search/serpapi_jobs.py` | SerpAPI `engine=google_jobs` | No (`SERPAPI_KEY`) |
| `serpapi_organic` | `providers/search/serpapi_organic.py` | SerpAPI organic web search | No (`SERPAPI_KEY`) |
| `adzuna` | `providers/search/adzuna.py` | Adzuna API | No (`ADZUNA_APP_ID`+`ADZUNA_APP_KEY`) |
| `usajobs` | `providers/search/usajobs.py` | USAJobs API (federal) | Treated as "always affordable" by budget guard even without key — verify implementation |
| `jooble` | `providers/search/jooble.py` | Jooble API | No (`JOOBLE_API_KEY`) |
| `careerjet` | `providers/search/careerjet.py` | Careerjet API | No (`CAREERJET_AFFID`) |
| `themuse` | `providers/search/themuse.py` | The Muse API | ✅ keyless |

Plus `geo/places_nearby.py` for Google Places opportunities (NOT a job-listing source; geo radar only).

Excluded (correctly): Doc 3's ASN dark funnel / Shodan recon.

### 4.2 Reasoning (5 LLMs)
| Key | File | Real or stub? |
|---|---|---|
| `openai` | `providers/reasoning/openai.py` | ❌ Returns hardcoded `{"enrichment": {"summary": "Enriched content placeholder", "tags": ["job", "tech"]}}` even when key present. NO real API call. |
| `gemini` | `providers/reasoning/gemini.py` | (not read in full — likely same stub pattern given base) |
| `claude` | `providers/reasoning/claude.py` | ❌ Returns hardcoded `{"enrichment": {"summary": "Claude enriched summary"}}` even when key present. NO real API call. |
| `groq` | `providers/reasoning/groq.py` | (not read in full) |
| `xai` | `providers/reasoning/xai.py` | (not read in full) |

The reasoning layer is **architecturally placed but unwired**. `api/index.py` does not call any reasoning provider — `normalize_job` uses purely deterministic logic. `pipeline/classify.py` exists but its integration into the active flow is not visible.

LLM grounded-search variants: **absent** (correctly — out of scope).

---

## 5. API contract (live shapes)

### 5.1 `/api/health` → ✅ truthful
Fields: `status, version, runtime, *_enabled, origin, origin_geocoded, max_radius_miles, max_transit_minutes, serpapi_budget_mode, serpapi_min_searches_left, batch_bucket, pipeline[]`.

### 5.2 `/api/usage` → ✅ truthful
Fields: `status, version, serpapi (account status), storage, budget, routes[]`.

### 5.3 `/api/jobs?dry_run=1` → ✅ no spend
`{status, dry_run: true, message, max_serp_queries, budget: serpapi_account_status()}`.

### 5.4 `/api/jobs` → ⚠ structurally OK, semantically broken
Fields: `status, source, count, unfiltered_count, raw_count, query_count, nearby_restaurant_count, rejected_count, rejection_summary, provider_breakdown, rules, data, rejected`.

Issues vs canonical spec §6:
- `data` holds everything (including unresolved + non-food); no separate `unresolved` bucket.
- `rejected_count` always 0, `rejection_summary` always `{}`, `rejected` always `[]`.
- No `resolution_flags` / `needs_resolution` field on job objects.
- `provider_breakdown` is truthful per provider (key → label, available, queries_attempted, raw_count, status, cap, error).

### 5.5 `/api/providers` → ✅ truthful (modular blueprint)
`{providers: [{key, label, type, description, is_available, requires_api_key}]}`.

### 5.6 Others
`/api/opportunities` returns Google Places nearby (no SerpAPI). `/api/history` reads GCS batches. `/api/why-three` is a static explainer.

---

## 6. UI contract (current)

`web/templates/index.html` matches canonical spec §9 for:
- 8 tabs (Overview, Live Jobs, Opportunities, History, Debug Evidence, Providers, Budget, Why Three) ✅
- "Opening this dashboard does not run live discovery" boot copy ✅
- Industry filter with 6 canonical industries ✅
- Provider filter with 6 entries (groups serpapi_jobs+organic into single `serpapi` value — minor labeling drift)
- Live action guard with "Confirm Live Discovery" / "Cancel" ✅
- EN/ES/RU language buttons present ✅
- Forbidden copy list compliance — needs confirmation from render_* files (next pass)

Frontend gaps detected (UI honestly renders "Backend gap" copy):
- `web/static/js/render_history.js:8` — "History endpoint is currently a placeholder (Backend gap). No batches retrieved." This fires when no batches returned — note `/api/history` returns `[]` if `BATCH_BUCKET` not configured. Honest. ✅
- `web/static/js/render_providers.js:10` — "Providers endpoint is currently a placeholder (Backend gap)." Triggers when provider response empty — but `/api/providers` returns real data. **Verify trigger condition (false alarm risk).**
- `web/static/js/render_budget.js:98` — "Backend GAP: Jobs endpoint returned a placeholder. Cannot generate dry-run execution plan." Triggers on `UI.isPlaceholder(payload)` — `/api/jobs?dry_run=1` does NOT return `"placeholder"` string. **Likely dead branch.**
- `web/static/js/render_why_three.js:9` — "Why Three endpoint is a placeholder (Backend gap). Decision engine unavailable." `/api/why-three` returns real explainer JSON. **Likely false alarm.**

These four "Backend gap" copies need verification that they only fire when truly missing data, not on healthy responses.

---

## 7. Summary against canonical spec

| Canonical area | Current state |
|---|---|
| 6 industries | ✅ Defined in `industries/`; ❌ NOT used by `/api/jobs` path (restaurant-only). |
| 7 search providers | ✅ Defined + fair-fanout wired. |
| 5 LLM reasoning | ⚠ Defined + scaffolded but **return fake enrichment strings**; not called from any live path. |
| Safe boot | ✅ Frontend respects it; `/` does not spend quota. |
| Live jobs visibility (C23) | ❌ Half-done: rejection gate is silently dead → all raw jobs pass through; no `resolution_flags`. |
| Fair fanout (C24) | ✅ `search/live_provider_bridge.py` implements it. |
| Review score 60/15/15/10 (C14) | ❌ Current formula `(rating/5)*90 + log10(count+1)*4` can over-reward high review count. |
| OIDC (C13) | ⚠ Only Bearer-prefix check at both `app.py` and `api/index.py:verify_oidc`. Real `ingest/oidc.py` exists but is bypassed in the active path. |
| 8 UI tabs (C26) | ✅ |
| No fake data (C19) | ⚠ Reasoning providers return fake strings; frontend handles placeholder honestly. |
| Firestore persistence (C10) | ⚠ Live ingest writes GCS JSON via raw HTTP; decoupled Firestore repos exist but unused by legacy path. |
| Auto-apply / Playwright (C1) | ✅ No code present. |
| Neo4j / CRDT / WebGPU SLM (C2/C3) | ✅ No code present. |
| Multi-industry classification | ⚠ `industries/` exists; `pipeline/classify.py` exists; not wired into `api/index.py`. |

This map is the basis for `STUB_PLACEHOLDER_AUDIT.md`, `BUG_LEDGER.md`, and `FINAL_PATCH_PLAN.md`.
