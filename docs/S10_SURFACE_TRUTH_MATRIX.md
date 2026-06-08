# S10 Surface Truth Matrix

Generated: 2026-06-07T23:45:28.230147+00:00

Purpose: expose every existing backend route, frontend caller, hidden UI control, and unavailable/boilerplate surface without creating fake backend code.

## 1. Mounted Flask route map

- `GET` `/` -> `index`
- `DELETE,GET,PATCH,POST,PUT` `/api/<path:path>` -> `api_dispatch`
- `GET` `/api/_surface` -> `surface`
- `GET` `/api/applications` -> `api.get_applications`
- `POST` `/api/applications` -> `api.create_application`
- `GET` `/api/applications/<job_id>` -> `api.get_application`
- `PATCH` `/api/applications/<job_id>` -> `api.update_application`
- `GET` `/api/industries` -> `api.industries`
- `POST` `/api/ingest` -> `api.ingest`
- `POST` `/api/ingest` -> `ingest`
- `GET` `/api/providers` -> `api.providers`
- `GET` `/favicon.ico` -> `favicon`
- `GET` `/static/<path:filename>` -> `static`

## 2. Declared backend routes found in source

- `/` — `MOUNTED` — `api/index.py`
- `/api/health` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/index.py`
- `/api/usage` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/index.py`
- `/api/why-three` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/index.py`
- `/api/opportunities` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/index.py`
- `/api/jobs` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/index.py`
- `/api/debug/jobs` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/index.py`
- `/api/research/place` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/index.py`
- `/api/ingest` — `MOUNTED` — `api/index.py`
- `/api/batches` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/index.py`
- `/api/batch/<path:object_name>` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/index.py`
- `/api/history` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/index.py`
- `/api/demo` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/index.py`
- `/api/search` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/index.py`
- `/applications` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/applications.py`
- `/applications` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/applications.py`
- `/applications/<job_id>` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/applications.py`
- `/applications/<job_id>` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/applications.py`
- `/industries` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/industries.py`
- `/ingest` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/ingest.py`
- `/providers` — `DECLARED_NOT_MOUNTED_OR_ROUTED_THROUGH_CATCHALL` — `api/providers.py`
- `/api/ingest` — `MOUNTED` — `app.py`
- `/api/<path:path>` — `MOUNTED` — `app.py`

## 3. Catch-all / dispatch risk

Mounted catch-all routes:
- `/static/<path:filename>`
- `/api/<path:path>`

Meaning: some API behavior may be hidden behind a dispatcher instead of visible as explicit Flask routes. A file can contain logic and still not appear as a first-class route.

## 4. Engine/module inventory

### `providers/` (17 python files)
- `providers/__init__.py` funcs=4 async=0
- `providers/base.py` funcs=5 async=0 CLASSES
- `providers/reasoning/__init__.py` funcs=0 async=0
- `providers/reasoning/base.py` funcs=0 async=0
- `providers/reasoning/claude.py` funcs=5 async=0 CLASSES
- `providers/reasoning/gemini.py` funcs=5 async=0 CLASSES
- `providers/reasoning/groq.py` funcs=5 async=0 CLASSES
- `providers/reasoning/openai.py` funcs=5 async=0 CLASSES
- `providers/reasoning/xai.py` funcs=5 async=0 CLASSES
- `providers/search/__init__.py` funcs=0 async=0
- `providers/search/adzuna.py` funcs=3 async=0 CLASSES
- `providers/search/careerjet.py` funcs=3 async=0 CLASSES
- `providers/search/jooble.py` funcs=3 async=0 CLASSES
- `providers/search/serpapi_jobs.py` funcs=3 async=0 CLASSES
- `providers/search/serpapi_organic.py` funcs=3 async=0 CLASSES
- `providers/search/themuse.py` funcs=3 async=0 CLASSES
- `providers/search/usajobs.py` funcs=3 async=0 CLASSES

### `search/` (4 python files)
- `search/__init__.py` funcs=0 async=0
- `search/budget.py` funcs=3 async=0 CLASSES
- `search/federated.py` funcs=3 async=0 CLASSES
- `search/usage_tracker.py` funcs=5 async=0 CLASSES

### `pipeline/` (9 python files)
- `pipeline/__init__.py` funcs=0 async=0
- `pipeline/classify.py` funcs=1 async=0
- `pipeline/dedupe.py` funcs=2 async=0
- `pipeline/normalize.py` funcs=1 async=0
- `pipeline/reject.py` funcs=2 async=0
- `pipeline/resolve_place.py` funcs=1 async=0
- `pipeline/run.py` funcs=1 async=0
- `pipeline/score_match.py` funcs=1 async=0
- `pipeline/score_review.py` funcs=1 async=0

### `geo/` (7 python files)
- `geo/__init__.py` funcs=0 async=0
- `geo/distance.py` funcs=1 async=0
- `geo/geocode.py` funcs=1 async=0
- `geo/haversine.py` funcs=1 async=0
- `geo/place_details.py` funcs=1 async=0
- `geo/places_nearby.py` funcs=1 async=0
- `geo/places_text.py` funcs=1 async=0

### `store/` (10 python files)
- `store/__init__.py` funcs=0 async=0
- `store/applications_repo.py` funcs=4 async=0 CLASSES
- `store/batches_repo.py` funcs=1 async=0 CLASSES
- `store/cache_repo.py` funcs=4 async=0 CLASSES
- `store/firestore_client.py` funcs=1 async=0
- `store/jobs_repo.py` funcs=2 async=0 CLASSES
- `store/places_repo.py` funcs=1 async=0 CLASSES
- `store/repository.py` funcs=7 async=0 CLASSES
- `store/reviews_repo.py` funcs=1 async=0 CLASSES
- `store/usage_repo.py` funcs=1 async=0 CLASSES

### `industries/` (8 python files)
- `industries/__init__.py` funcs=4 async=0
- `industries/base.py` funcs=2 async=0 CLASSES
- `industries/care_social.py` funcs=0 async=0
- `industries/customer_service.py` funcs=0 async=0
- `industries/food_service.py` funcs=0 async=0
- `industries/hospitality.py` funcs=0 async=0
- `industries/retail_ops.py` funcs=0 async=0
- `industries/sales.py` funcs=0 async=0

### `ingest/` (3 python files)
- `ingest/__init__.py` funcs=0 async=0
- `ingest/oidc.py` funcs=5 async=0 CLASSES
- `ingest/scheduler_job.py` funcs=4 async=0 CLASSES

### `api/` (14 python files)
- `api/__init__.py` funcs=0 async=0
- `api/applications.py` funcs=4 async=0  ROUTE_DECLARATIONS
- `api/health.py` funcs=0 async=0
- `api/history.py` funcs=0 async=0
- `api/index.py` funcs=51 async=0 CLASSES ROUTE_DECLARATIONS
- `api/industries.py` funcs=1 async=0  ROUTE_DECLARATIONS
- `api/ingest.py` funcs=1 async=0  ROUTE_DECLARATIONS
- `api/jobs.py` funcs=0 async=0
- `api/opportunities.py` funcs=0 async=0
- `api/providers.py` funcs=1 async=0  ROUTE_DECLARATIONS
- `api/research.py` funcs=0 async=0
- `api/scrape.py` funcs=1 async=0
- `api/usage.py` funcs=0 async=0
- `api/why_three.py` funcs=0 async=0

### `models/` (11 python files)
- `models/__init__.py` funcs=0 async=0
- `models/api_usage.py` funcs=0 async=0 CLASSES
- `models/application.py` funcs=0 async=0 CLASSES
- `models/batch.py` funcs=0 async=0 CLASSES
- `models/enums.py` funcs=0 async=0 CLASSES
- `models/job.py` funcs=0 async=0 CLASSES
- `models/job_snapshot.py` funcs=0 async=0 CLASSES
- `models/place.py` funcs=0 async=0 CLASSES
- `models/rejection.py` funcs=0 async=0 CLASSES
- `models/review.py` funcs=0 async=0 CLASSES
- `models/search_result.py` funcs=1 async=0 CLASSES

### `core/` (6 python files)
- `core/__init__.py` funcs=0 async=0
- `core/clock.py` funcs=4 async=0
- `core/config.py` funcs=1 async=0 CLASSES
- `core/errors.py` funcs=0 async=0 CLASSES
- `core/http.py` funcs=1 async=0
- `core/logging.py` funcs=2 async=0

## 5. Frontend API wiring

### API references
- `web/static/js/api.js:1` const API_URLS = Object.freeze({
- `web/static/js/api.js:2` health: '/api/health',
- `web/static/js/api.js:3` usage: '/api/usage',
- `web/static/js/api.js:4` opportunities: '/api/opportunities',
- `web/static/js/api.js:5` history: '/api/history',
- `web/static/js/api.js:6` providers: '/api/providers',
- `web/static/js/api.js:7` industries: '/api/industries',
- `web/static/js/api.js:8` applications: '/api/applications',
- `web/static/js/api.js:9` why_three: '/api/why-three',
- `web/static/js/api.js:25` async function safeFetch(url) {
- `web/static/js/api.js:27` const res = await fetch(url);
- `web/static/js/api.js:65` return safeFetch(`/api/jobs${buildQuery({ ...params, dry_run: 1 })}`);
- `web/static/js/api.js:69` return safeFetch(`/api/jobs${buildQuery({ ...params, dry_run: 0 })}`);
- `web/static/js/render_jobs.js:33` const url = live ? API_URLS.jobs : `${API_URLS.jobs}?dry_run=1`;
- `web/static/js/render_jobs.js:34` const data = await safeFetch(url);
- `web/static/js/render_opportunities.js:16` const data = await safeFetch(API_URLS.opportunities);
- `web/static/js/render_history.js:4` const data = await safeFetch(API_URLS.history);
- `web/static/js/render_providers.js:5` const data = await safeFetch(API_URLS.providers);
- `web/static/js/render_budget.js:16` const usage = await safeFetch(API_URLS.usage);
- `web/static/js/render_budget.js:95` const dryRunData = await safeFetch(`${API_URLS.jobs}?dry_run=1`);
- `web/static/js/render_overview.js:41` safeFetch(API_URLS.health),
- `web/static/js/render_overview.js:42` safeFetch(API_URLS.usage),
- `web/static/js/render_overview.js:44` safeFetch(API_URLS.opportunities),
- `web/static/js/render_overview.js:45` safeFetch(API_URLS.history)
- `web/static/js/render_why_three.js:5` const data = await safeFetch(API_URLS.why_three);
- `web/static/js/render_debug_evidence.js:48` <span style="margin-left: var(--space-md);">Stream: <code>${API_URLS.pipeline_stream}</code></span>
- `templates/index.html:9` const res = await fetch('/api/get_jobs');
- `static/js/main.js:62` ${job.place_id?`<a class="btn btn-ghost" href="/api/research/place?place_id=${escapeHTML(job.place_id)}&name=${encodeURIComponent(company)}" target="_blank">Research</a>`:""}
- `static/js/main.js:94` fetch("/api/usage").then(r=>r.json()).then(p=>{
- `static/js/main.js:104` fetch("/api/jobs"+(qs?"?"+qs:""))
- `static/js/main.js:113` fetch("/api/opportunities"+(qs?"?"+qs:""))
- `static/js/main.js:124` <td>${x.place_id?`<a href="/api/research/place?place_id=${escapeHTML(x.place_id)}&name=${encodeURIComponent(x.name||"")}" target="_blank">Research</a>`:""}</td>
- `static/js/main.js:135` fetch("/api/history?hours=24"+(qs?"&"+qs:""))

### Hidden / disabled UI references
- `web/templates/index.html:11` <canvas id="webgpu-canvas" aria-hidden="true"></canvas>
- `web/templates/index.html:42` <button id="mobile-menu-toggle" class="badge" style="display:none; cursor:pointer; background:var(--surface2); padding:8px;" aria-label="Open menu">☰</button>
- `web/templates/index.html:46` <div id="filter-count-badge" class="badge" style="display:none;background:var(--accent);">0 filters</div>
- `web/templates/index.html:48` <div id="live-action-guard" style="display:none; align-items:center; gap:var(--space-sm);">
- `web/templates/index.html:53` <button id="prepare-discovery-btn" class="badge badge-live" style="cursor:pointer;display:none;">Run Live Discovery</button>
- `web/templates/index.html:59` <button id="reset-all-filters" class="badge" style="display:none; cursor:pointer; background:var(--border);">Reset All</button>
- `web/templates/index.html:289` <pre id="dry-run-output" style="margin-top:16px;font-size:0.85rem;background:rgba(0,0,0,0.3);padding:12px;border-radius:4px;display:none;"></pre>
- `web/templates/index.html:476` <div id="command-palette" class="modal" role="dialog" aria-labelledby="cmd-title" aria-modal="true" style="display:none; position:fixed; top:20%; left:50%; transform:translateX(-50%); width:500px; max-width:90vw; backgro
- `web/static/js/state.js:191` drawer.setAttribute('aria-hidden', 'false');
- `web/static/js/tabs.js:40` evidenceDrawer.setAttribute('aria-hidden', !isOpen);
- `web/static/css/layout.css:6` overflow: hidden;
- `web/static/css/layout.css:107` display: none;
- `web/static/css/layout.css:142` visibility: hidden;
- `web/static/css/layout.css:163` visibility: hidden;
- `web/static/css/layout.css:198` visibility: hidden;
- `web/static/css/layout.css:226` display: none !important; /* Hidden on mobile by default per mission */
- `web/static/css/components.css:59` overflow: hidden;
- `web/static/css/components.css:135` overflow: hidden;
- `web/static/css/components.css:163` overflow: hidden;
- `web/static/css/charts.css:8` overflow: hidden;
- `static/css/main.css:40` .job-card{position:relative;padding:1.25rem;overflow:hidden;transition:.28s var(--ease)}
- `static/css/main.css:48` .job-card .description{max-height:0;overflow:hidden;opacity:0;transition:max-height .32s var(--ease),opacity .32s}
- `static/css/components/job-card.css:4` position:relative;overflow:hidden;box-shadow:0 10px 35px rgba(0,0,0,.24);
- `static/css/components/job-card.css:20` .job-card .description{max-height:0;overflow:hidden;color:var(--soft);transition:max-height var(--med) var(--ease),opacity var(--med);opacity:0}
- `static/css/components/buttons.css:4` color:#fff;font-weight:800;letter-spacing:.01em;cursor:pointer;position:relative;overflow:hidden;
- `static/css/components/cards.css:4` backdrop-filter:blur(22px);position:relative;overflow:hidden;
- `static/css/base/variables.css:16` color:var(--text);min-height:100vh;overflow-x:hidden;

### Placeholder / boilerplate / demo-language references
- `web/templates/index.html:412` <input type="text" id="filter-batch" placeholder="e.g. b8f2..." style="width:100%; padding:var(--space-sm); background:var(--surface2); border:1px solid var(--border); color:var(--text); margin-bottom:var(--space-md);">
- `web/templates/index.html:478` <input type="text" id="cmd-input" placeholder="Type a command (e.g. 'Go to History', 'Dark Mode')..." style="width:100%; padding:var(--space-sm); background:var(--surface2); border:1px solid var(--border); border-radius:
- `web/static/js/api.js:74` UI.isPlaceholder = function isPlaceholder(payload) {
- `web/static/js/api.js:77` return message.includes('placeholder') || message.includes('not implemented');
- `web/static/js/api.js:81` if (!payload || UI.isPlaceholder(payload)) return [];
- `web/static/js/render_history.js:7` if (UI.isPlaceholder(data)) {
- `web/static/js/render_history.js:8` table.innerHTML = '<tr><td colspan="5" class="chart-fallback">History endpoint is currently a placeholder (Backend gap). No batches retrieved.</td></tr>';
- `web/static/js/render_providers.js:7` if (UI.isPlaceholder(data)) {
- `web/static/js/render_providers.js:10` Providers endpoint is currently a placeholder (Backend gap).
- `web/static/js/render_budget.js:21` if (!usage || UI.isPlaceholder(usage)) {
- `web/static/js/render_budget.js:31` if (UI.isPlaceholder(usage)) {
- `web/static/js/render_budget.js:97` if (UI.isPlaceholder(dryRunData)) {
- `web/static/js/render_budget.js:98` dryRunOutput.textContent = 'Backend GAP: Jobs endpoint returned a placeholder. Cannot generate dry-run execution plan.';
- `web/static/js/charts.js:250` // For now, let's use a placeholder if the data isn't directly in history batch
- `web/static/js/render_overview.js:72` if (UI.isPlaceholder(usage)) {
- `web/static/js/render_why_three.js:8` if (UI.isPlaceholder(data)) {
- `web/static/js/render_why_three.js:9` container.innerHTML = '<div class="chart-fallback">Why Three endpoint is a placeholder (Backend gap). Decision engine unavailable.</div>';
- `web/static/js/render_why_three.js:23` const why = UI.safeField(j.why_included, 'No inclusion telemetry details cataloged (Backend Gap).');
- `static/css/components/forms.css:11` input::placeholder,textarea::placeholder{color:rgba(255,255,255,.45)}

## 6. Safe local endpoint probes

### `/`
- status: `200`
- content_type: `text/html; charset=utf-8`
- body_preview: `<!DOCTYPE html> <html lang="en"> <head>     <meta charset="UTF-8">     <meta name="viewport" content="width=device-width, initial-scale=1.0">     <title>Job Hunter Pro</title>     <link rel="stylesheet" href="/static/css/base.css">     <link rel="manifest" href="/static/manifest.json"> </head> <body`

### `/api/health`
- status: `200`
- content_type: `application/json`
- top_keys: `['batch_bucket', 'claude_enabled', 'gemini_enabled', 'grok_xai_enabled', 'groq_enabled', 'maps_enabled', 'max_radius_miles', 'max_transit_minutes', 'openai_enabled', 'origin', 'origin_geocoded', 'pipeline', 'runtime', 'serpapi_budget_mode', 'serpapi_enabled', 'serpapi_min_searches_left', 'status', 'version']`
- status: `ok`
- version: `job_hunter_v8_stable_orchestrated_dashboard`

### `/api/usage`
- status: `200`
- content_type: `application/json`
- top_keys: `['budget', 'routes', 'serpapi', 'status', 'storage', 'version']`
- status: `ok`
- version: `job_hunter_v8_stable_orchestrated_dashboard`
- serpapi: dict keys `['available', 'reason']`
- budget: dict keys `['budget_mode', 'max_raw_jobs_per_live_run', 'max_serp_queries_per_live_run', 'min_searches_left_guard']`
- routes: list[6]

### `/api/jobs?dry_run=1`
- status: `200`
- content_type: `application/json`
- top_keys: `['budget', 'dry_run', 'max_serp_queries', 'message', 'status']`
- status: `ok`
- dry_run: `True`
- message: `Live jobs endpoint is available. This dry run did not spend SerpAPI searches.`
- budget: dict keys `['available', 'reason']`

### `/api/opportunities`
- status: `200`
- content_type: `application/json`
- top_keys: `['count', 'data', 'rules', 'source', 'status']`
- status: `success`
- count: `0`
- data: list[0]

### `/api/history`
- status: `200`
- content_type: `application/json`
- top_keys: `['batch_count', 'batches', 'data', 'from', 'job_count', 'source', 'status', 'to']`
- status: `success`
- job_count: `0`
- batch_count: `0`
- data: list[0]
- batches: list[0]

### `/api/providers`
- status: `200`
- content_type: `application/json`
- top_keys: `['providers']`

### `/api/industries`
- status: `200`
- content_type: `application/json`
- top_keys: `['industries']`

2026-06-07 17:45:30,589 - store.repository - WARNING - Firestore unavailable for applications: google-cloud-firestore is not installed. Database operations are unavailable.
2026-06-07 17:45:30,590 - store.applications_repo - ERROR - Firestore applications stream failed: 'NoneType' object has no attribute 'stream'. Using local.
### `/api/applications`
- status: `200`
- content_type: `application/json`
- top_keys: `['applications']`

### `/api/_surface`
- status: `200`
- content_type: `application/json`
- top_keys: `['api_backend', 'api_index_proxy_routes', 'entrypoint', 'modular_routes', 'placeholder_blueprint_registered', 'static', 'status', 'truth', 'ui']`
- status: `ok`

### `/api/events/pipeline`
- status: `404`
- content_type: `text/html; charset=utf-8`
- body_preview: `<!doctype html> <html lang=en> <title>404 Not Found</title> <h1>Not Found</h1> <p>The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.</p> `


## 7. Diagnosis rules

- If a module file exists but no route calls it, the engine exists but is not mounted.
- If a route is mounted but no frontend fetch points to it, the engine is callable but not surfaced.
- If a frontend element has `display:none`, `hidden`, `aria-hidden=true`, or is only shown on a tab condition, the feature is hidden/gated.
- If `/api/jobs?dry_run=1` returns `dry_run: true` and no `jobs`, that is safe behavior, not live discovery.
- If live `/api/jobs` is only behind a button, that is intentional budget protection.
- If frontend expects `payload.opportunities` but backend returns `payload.data`, data exists but renderer is looking at the wrong key.
- If `/api/events/pipeline` is 404 and no SSE route exists, S10-H requires a neutral unavailable state, not fake SSE.

