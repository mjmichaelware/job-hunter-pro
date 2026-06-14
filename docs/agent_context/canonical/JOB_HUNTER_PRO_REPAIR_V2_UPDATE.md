# Job Hunter Pro — Repair v2 Canonical Update

Branch: `claude/job-hunter-pro-repair-v2a815`
Scope: broad-by-default discovery, no hidden filters, honest rejected/unresolved
visibility, provider quarantine, cost honesty, and a decoupled service layer.

This file is the current source of truth for the jobs flow. It does NOT modify
global `~/AGENTS.md`.

---

## 1. What was wrong

1. **Hidden default filters zeroed the UI.** The served cockpit
   (`web/templates/index.html` + `web/static/js/*`) applied client-side default
   filters `radius = 5 mi` and `matchScore = 60` with NO visible chip, silently
   hiding valid jobs. (The earlier `static/js/main.js` is NOT the served UI.)
2. **Food-service bias governed discovery.** `api/index.py` generated only
   restaurant queries (`ROLE_QUERIES`) and pulled Google Places restaurant names
   into the query bank, so the discovery universe was food-only.
3. **Safe-boot violation + quota burn.** `live_engine_bridge.js` auto-ran live
   discovery on page load (`runLiveDiscovery()` in `boot()`, with a
   `const ok = true || confirm(...)` bypass). Opening the page spent provider
   budget.
4. **Dead providers poisoned the run.** Jooble and Careerjet returned 403s and
   were retried across the whole keyword fanout; provider adapters swallowed the
   error so the bridge could not see it.
5. **Rejection was effectively dishonest.** `rejection_reasons()` always
   `return []`, so nothing was ever rejected OR surfaced; missing
   address/radius/transit had no honest representation.
6. **Core depended on Google Places.** Query generation called
   `nearby_opportunities_cached()` (Maps cost) on every live run.

## 2. What changed

### New decoupled modules
- `config/search_taxonomy.py` — broad, industry-neutral query seeds + helpers.
- `services/query_builder.py` — `build_queries(mode, city, postal, max_queries)`;
  broad is default and also samples every `industries/` route for cross-domain
  recall. Domain presets are explicit/optional.
- `services/provider_status.py` — policy disable (`jooble`, `careerjet` off
  unless `ENABLE_JOOBLE` / `ENABLE_CAREERJET`), hard-failure status set
  `{401,403,429}`, and a `RunQuarantine` tracker.
- `services/filtering.py` — `apply_filters(jobs, params)` narrows ONLY on
  explicitly-provided params (blank = no narrowing).
- `services/job_aggregator.py` — canonical dedupe + accepted/rejected
  partitioning. Missing resolution becomes `resolution_flags`, never deletion.

### Provider resilience
- `core/errors.py` adds `ProviderHardFailure(status_code)`.
- `providers/base.py` adds `check_hard_failure(key, response)`; adapters
  (adzuna, usajobs, jooble, careerjet, themuse) raise it on 401/403/429.
- `search/live_provider_bridge.py` quarantines a provider for the rest of the
  run on a hard failure (stops hammering), skips policy-disabled providers, and
  returns `quarantined_providers`. Empty-query fallback no longer defaults to
  `"restaurant"` (now `"jobs"`).

### Backend route layer (`api/index.py`)
- `raw_job_queries(mode, domain, extra_terms)` uses the query builder; broad
  default; legacy restaurant fallback only if the builder import fails; no
  Google Places dependency.
- `fetch_jobs_live(mode, domain, extra_terms)` uses `job_aggregator.partition`;
  returns `mode`, `resolution_flag_summary`, `quarantined_providers`.
- `/api/jobs` accepts `?mode=` (default `broad`) and `?domain=`; reports honest
  counts (`accepted_count`, `visible_count`, `raw_count`, `rejected_count`),
  `rules.food_only` is now mode-derived, and `data` (accepted) + `rejected`
  (with reasons) are both returned.
- `/api/debug/jobs` mirrors this with full accepted + rejected evidence.
- Dead food-gating `rejection_reasons()` removed.
- `/api/opportunities` is OFF by default (`ENABLE_PLACES_OPPORTUNITIES`) and
  returns an honest `status: "disabled", reason: "disabled_for_cost_control"`.
- `/api/providers` reports `disabled_by_policy`, `status`, and `reason`.

### Frontend (served cockpit)
- `live_engine_bridge.js` no longer runs discovery on boot; live discovery is
  click-only. Safe boot loads read-only surfaces only.
- `state.js` / `filters.js` / `render_jobs.js`: default `radius` and
  `matchScore` are `''` (no narrowing); render narrows only on explicit positive
  values; unknown radius/match is never excluded (unresolved-but-real jobs stay
  visible). Sliders default to "Any" (value 0). "Show All / Reset" is always
  visible.
- `render_providers.js` shows a distinct DISABLED state + reason.
- `render_opportunities.js` shows the honest cost-disabled state.
- `web/static/css/states.css` added (state concern) and imported by `base.css`.

## 3. Current discovery behavior

- **Default mode = `broad`** (all-jobs, multi-industry). Food service is one
  optional preset (`/api/jobs?mode=food_service`), no longer the universe.
- Every real provider result is ACCEPTED. Missing address/radius/transit →
  `resolution_flags` (`address_unresolved`, `radius_unverified`,
  `transit_unverified`) on the accepted job.
- REJECTED only for genuinely unusable records: `missing_title`,
  `no_link_or_company`, `duplicate`, or (domain preset only)
  `domain_mismatch_<domain>`. Rejected items keep title/provider/reasons and are
  shown in their own panel.
- Filters narrow only what the user explicitly set.

## 4. Provider disable / quarantine status

- **Disabled by policy (default off):** `jooble`, `careerjet`. Previously exposed
  credentials treated as compromised. Re-enable only via `ENABLE_JOOBLE=1` /
  `ENABLE_CAREERJET=1`.
- **Run quarantine:** any provider returning 401/403/429 is quarantined for the
  rest of that run and reported in `provider_breakdown[key].status =
  quarantined_http_<code>` and in `quarantined_providers`.
- Working providers (e.g. The Muse keyless; Adzuna/USAJobs/SerpAPI when keyed)
  continue contributing regardless of a dead peer.

## 5. How to add a new API later (low friction)

1. Create `providers/search/<name>.py` implementing `SearchProvider`
   (`metadata`, `is_available`, `search`). Call `check_hard_failure(key, resp)`
   after the HTTP call and re-raise `ProviderHardFailure`.
2. Register the instance in `providers/__init__.py` `_PROVIDER_REGISTRY`.
3. (Optional) add domain queries/terms in `industries/<domain>.py` or broad
   seeds in `config/search_taxonomy.py`.
   No route/API edits are required — the bridge fans out fairly to every
   available SEARCH provider and the aggregator normalizes results.

## 6. What remains for future scaling

- Reasoning/LLM enrichment is still classification-only and not wired into the
  accepted flow (intentional).
- Per-job Google resolution (`resolve_place`/transit/reviews) still runs on live
  jobs when a Maps key is present; consider a `MAX_RESOLVE_JOBS` cap or lazy
  on-demand resolution for very large broad runs.
- History/all-sources merge endpoint exists (`/api/history`) but a unified
  "All Sources" dataset toggle in the cockpit is not yet wired.
- Persistent store (Firestore) batches remain optional and bucket-gated.

## 7. Proof (local, no quota spent)

- `python3 -m py_compile $(git ls-files "*.py")` — all compile.
- `.claude/scripts/proof_runner.py` — `/`, `/api/providers`, `/api/health`,
  `/api/jobs?dry_run=1` all 200; dry-run spends nothing.
- Mock-provider harness verified: broad `food_only=False`; missing resolution →
  flags; duplicate/junk visibly rejected with reasons; `fake_dead` (403)
  quarantined; jooble/careerjet `disabled_by_policy`; explicit filters narrow
  only when set; `mode=food_service` preset still works.
- Deployment NOT performed here: `gcloud` is unavailable in this container and
  the project rule requires explicit deploy authorization. Changes are pushed to
  the feature branch for review/deploy.
