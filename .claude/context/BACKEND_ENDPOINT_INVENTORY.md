# Backend Endpoint Inventory — Job Hunter Pro

S2 of `UI_BACKEND_PARITY_WORKFLOW.md`. Source of truth for every Flask route currently mounted in the running stack.

## Stack summary

- `app.py` (gunicorn entrypoint `app:app`) builds the public Flask app via `create_app()`.
- `app.py` registers the modular `api_bp` blueprint (`api/__init__.py`) — adds `/api/providers`, `/api/industries`, `/api/applications*`, `/api/ingest` (real OIDC).
- `app.py` registers its own `/api/ingest` POST handler (line 129-138) with Bearer-prefix-only check, then proxies to `api/index.py`.
- `app.py` finally registers `/api/<path:path>` catch-all that proxies every other `/api/*` request to the legacy `api/index.py` Flask app via `test_client`.
- Legacy `api/index.py` defines its own Flask app with `/`, `/api/health`, `/api/usage`, `/api/why-three`, `/api/opportunities`, `/api/jobs`, `/api/debug/jobs`, `/api/research/place`, `/api/ingest`, `/api/batches`, `/api/batch/<>`, `/api/history`, `/api/demo`, `/api/search`.
- `app.py` also exposes `/`, `/favicon.ico`, `/api/_surface` directly.

### Route resolution note (the duplicate `/api/ingest`)
The api_bp blueprint registers `/api/ingest` (real OIDC via `verify_token`) BEFORE `app.py` registers its second `@app.route('/api/ingest')`. Flask raises `AssertionError` on duplicate endpoint name; since both handlers are named `ingest`, the second registration must be using a different endpoint name (Flask deduplicates by `endpoint` not rule). In practice the app boots without error because the explicit `@app.route` registers an endpoint `ingest` and the blueprint registers `api.ingest`. Flask routing then dispatches by URL rule with first-registered winning. **This must be confirmed at boot time** — `safe_local_proof.sh` checks `/api/_surface` returns 200 so the app does boot. Whichever handler wins, the orchestration is ambiguous and is a separate defect (see `BUG_LEDGER.md` if needed).

---

## Public-shell routes (defined in `app.py`)

| Route | Method | Auth | Side effects | Provider cost | Caller | Safe on page load |
|---|---|---|---|---|---|---|
| `GET /` | GET | none | renders `web/templates/index.html` | none | browser | ✅ |
| `GET /favicon.ico` | GET | none | serves `web/static/icon.svg` | none | browser | ✅ |
| `GET /api/_surface` | GET | none | returns shell metadata JSON | none | ops / debug | ✅ |
| `POST /api/ingest` (`app.py:129-138`) | POST | Bearer-prefix only | proxies to `api.index.ingest` | runs full discovery + GCS write | Cloud Scheduler | ❌ NEVER from UI |
| `* /api/<path:path>` | ALL_METHODS | none at proxy layer | proxies to `api.index.test_client()` | varies by target | browser / shell | varies |

---

## Modular blueprint routes (`api/__init__.py` → `api/<module>.py`, prefix `/api`)

| Route | Method | Auth | Side effects | Provider cost | Frontend caller | Safe on page load |
|---|---|---|---|---|---|---|
| `GET /api/providers` | GET | none | calls `providers.get_all_providers()` → returns metadata + `is_available` | reads env presence only | `render_providers.js` | ✅ |
| `GET /api/industries` | GET | none | calls `industries.get_all_routes()` | none | not yet (no caller in JS) | ✅ |
| `GET /api/applications` | GET | none | `ApplicationsRepository.get_all()` | none (local store) | not yet | ✅ |
| `POST /api/applications` | POST | none | `repo.save_application()` | none | future | ✅ |
| `GET /api/applications/<job_id>` | GET | none | `repo.get_by_id()` | none | future | ✅ |
| `PATCH /api/applications/<job_id>` | PATCH | none | update + save | none | future | ✅ |
| `POST /api/ingest` (`api/ingest.py:7`) | POST | OIDC via `ingest.oidc.verify_token` | not yet wired to pipeline (placeholder body) | none currently | Cloud Scheduler | ❌ NEVER from UI |

---

## Legacy routes (defined in `api/index.py`, reached via proxy)

| Route | Method | Auth | Response key fields | Provider cost | Frontend caller | Safe on page load |
|---|---|---|---|---|---|---|
| `GET /` (legacy) | GET | none | inline HTML — overridden by public shell `/` | none | n/a (shadowed) | n/a |
| `GET /api/health` | GET | none | `status`, `version`, provider-enabled flags, `origin`, `origin_geocoded`, `max_radius_miles`, `max_transit_minutes`, `serpapi_budget_mode`, `serpapi_min_searches_left`, `batch_bucket`, `pipeline[]` | calls `origin_latlng()` (cached geocode) | `render_overview.js` | ✅ |
| `GET /api/usage` | GET | none | `serpapi: serpapi_account_status()`, `storage`, `budget` { `budget_mode`, `min_searches_left_guard`, `max_serp_queries_per_live_run`, `max_raw_jobs_per_live_run` }, `routes[]` | 1 SerpAPI account ping (not a search) | `render_budget.js`, `render_overview.js` | ✅ |
| `GET /api/why-three` | GET | none | `status`, `main_reason`, `current_limits`, `how_to_get_hundreds_without_burning_serpapi[]` — **NOT** `top3[]` | none | `render_why_three.js` (expects top3) | ✅ but shape-mismatch |
| `GET /api/opportunities` | GET | none | `status`, `source`, `count`, `rules`, `data: list[opportunity]` from `nearby_opportunities_cached()` | Google Places (cached) | `render_opportunities.js`, `render_overview.js` | ✅ (cached) |
| `GET /api/jobs?dry_run=1` | GET | none | `status:"ok"`, `dry_run:true`, `message`, `max_serp_queries`, `budget: serpapi_account_status()` — no `jobs[]`, no `plan` | SerpAPI account ping only | `render_overview.js` initial, `render_budget.js` dry-run, `render_jobs.js` initial | ✅ |
| `GET /api/jobs` (live) | GET | none | `status`, `source`, `count`, `unfiltered_count`, `raw_count`, `query_count`, `nearby_restaurant_count`, `rejected_count`, `rejection_summary`, `provider_breakdown`, `rules`, `data[]` (accepted), `rejected[]` | **federated provider fanout via `search.live_provider_bridge`**, falls back to `serpapi_jobs()` (4 SerpAPI queries × `MAX_RAW_JOBS=35` cap), Maps Distance Matrix per job | `render_jobs.js` (live mode) | ❌ on user confirm only |
| `GET /api/debug/jobs` | GET | none | full `accepted`, `rejected` arrays + counts + `provider_breakdown` | identical cost to `/api/jobs` live | not yet wired | ❌ |
| `GET /api/research/place?name=…` or `?place_id=…` | GET | none | `place_details` from `place_details()` | Places Details API call | not yet wired | ❌ explicit |
| `POST /api/ingest` (legacy `api/index.py:1192`) | POST | `verify_oidc()` — Bearer-prefix ONLY (CRIT-2) | runs `fetch_jobs_live()`, builds batch JSON, calls `gcs_upload_json` | full live discovery + GCS write | Cloud Scheduler | ❌ NEVER from UI |
| `GET /api/batches` | GET | none | bucket listing via `gcs_list_batches(200)` | GCS list call | not yet wired | ✅ |
| `GET /api/batch/<object_name>` | GET | none | GCS object download | GCS read | not yet wired | ✅ explicit |
| `GET /api/history?hours=…&from=…&to=…` | GET | none | `from`, `to`, `batch_count`, `job_count`, `batches[]`, `data[]` aggregated from GCS | GCS list + reads (cached HTTP) | `render_history.js`, `render_overview.js` | ✅ |
| `GET /api/demo` | GET | none | aliases `jobs()` — **CALLS LIVE DISCOVERY** despite "demo" name | full live cost | not used | ❌ dangerous alias |
| `GET POST /api/search` | GET POST | none | aliases `jobs()` — also calls live discovery | full live cost | not used | ❌ |

---

## Surface gaps the UI implies but no endpoint provides

| Missing surface | Where UI expects | Note |
|---|---|---|
| SSE pipeline stream (e.g., `/api/pipeline/stream/<batch_id>`) | `render_debug_evidence.js:48`, `api.js:10` | `API_URLS.pipeline_stream = null`. No backend route. Render only static "DISCONNECTED" state. |
| `usage.monthly_usage`, `usage.estimated_action_cost`, `usage.provider_usage{}`, `usage.budget_efficiency` | `render_budget.js`, `render_overview.js` | Not returned by `/api/usage` today. |
| `plan{}` field on `/api/jobs?dry_run=1` | `render_budget.js:99` | Dry-run returns text message only. |
| `/api/why-three` returning `top3[]` with `resonance_score`, `why_included` | `render_why_three.js` | Legacy returns explainer dict. Need to either change UI to consume explainer, or add a new endpoint. |
| Industry filter consumed by `/api/jobs` | UI sets `AppState.filters.industry` but `apply_filters()` does not read it | Coupled with HIGH-4. |
| Per-job `industry`, `industry_scores`, `dedupe_key`, `provider_id`, `query_seed`, `discovery_mode`, `timestamp` for evidence drawer | `render_debug_evidence.js:99-115` | Backend `normalize_job()` outputs `place_id`, `place_rating`, `tags`, `role_family`, `match`, `review_intelligence`, but does not produce these specific evidence keys. |
| Batch `trigger` field | `render_history.js:23` | Batch JSON in GCS does not include trigger; renders "Unknown". |

---

## Auth / security observations

- `app.py:129-138` `/api/ingest` only checks `Authorization` starts with `Bearer ` and then proxies. No signature check, no audience check, no email check (CRIT-2 root).
- `api/index.py:1183-1190` legacy `verify_oidc()` same Bearer-prefix-only check.
- `api/ingest.py` blueprint calls `ingest.oidc.verify_token` which DOES verify via `google.oauth2.id_token.verify_oauth2_token` when `google-auth` is installed. This is the only real verification path in the codebase.
- Both `/api/ingest` handlers exist simultaneously. Which one Flask routes to depends on the rule-registration order. **Determinism here is a separate audit task** — for the current cycle, treat as ambiguous and document.
- `requirements.txt` does not include `google-auth` — verify before assuming the blueprint path actually verifies.

---

## Endpoints to consider deleting or hardening

- `/api/demo` and `/api/search` aliases (`api/index.py:1272-1278`) call `jobs()` which triggers live discovery. They should either return dry-run only, be deleted, or be guarded.
- `app.py` Bearer-prefix-only OIDC handler duplicates a real OIDC handler in the blueprint. Pick one path. Recommended: delete `app.py:129-138` handler, let blueprint route win.

---

## Acceptance criteria for parity

- Every endpoint listed above has either a UI consumer or an explicit "scheduler / ops only" label.
- Every endpoint declares: method, auth, side effects, provider cost, safe-on-load.
- No endpoint silently triggers live discovery.
- `/api/ingest` has exactly one real verification path.
