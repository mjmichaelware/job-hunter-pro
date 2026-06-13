# UI Surface Inventory — Job Hunter Pro

S1 of `UI_BACKEND_PARITY_WORKFLOW.md`. Source of truth for every visible UI surface in the active frontend tree (`web/templates/index.html` + `web/static/js/*`).

Legend for **Safe?** column: ✅ no live discovery cost · ⚠️ may use discovery provider budget · 🛑 placeholder / not wired.

---

## 0. App shell

| Element | Owner file | Renderer / wiring | Notes |
|---|---|---|---|
| Body shell, sidebar nav (8 tabs), header, drawers | `web/templates/index.html` | static HTML | Tab buttons `[data-tab=...]` → `AppState.setTab()` in `state.js:89-105`. |
| Tab routing | `web/static/js/tabs.js`, `state.js:106-173` | `AppState.syncTabUI(tabId)` dispatches per-tab `load*()` | Each tab triggers its renderer + `loadCharts()` (from `charts.js`). |
| Service worker / offline cache | `web/static/sw.js`, `offline.js` (referenced) | Registered via inline `<script>` at end of `index.html` | Caches `safeFetch` responses via `window.DB`; serves stale on offline. |
| Mobile menu toggle | `#mobile-menu-toggle` (`index.html:42`) | Wiring expected in `state.js` / `tabs.js` | Behavior not verified — likely opens sidebar. |
| Language toggle | `.lang-btn[data-lang]` (`index.html:30-32`) | `AppState.setLang()` in `state.js:38-52` | Translates the 8 nav-tab labels only. ES + RU partial. |
| `#app-status` live region | `index.html:12` | aria-live polite; static copy | "Opening this dashboard does not run live discovery." |
| `#system-status-badge` | `index.html:35` | `render_overview.js:83-90` | "SAFE" if `/api/health` returns `status:"ok"`, "UNSTABLE" otherwise. |
| Filter drawer (advanced) | `index.html:305-461` | `web/static/js/filters.js` (range/select sync) | 20+ controls — many do not map to backend filters (see parity matrix). |
| Filter bar (always-visible) | `index.html:62-122` | same | Mode / industry / provider / status / sort / radius / match. |
| Active filter chips + reset | `index.html:57-60` | `filters.js` | UI-only state. |
| Evidence drawer | `index.html:464-473` | `state.js:174-208`, `render_debug_evidence.js:79-146` | Triggered by clickable cards (currently only debug rejections). |
| Command palette | `index.html:476-482` | Wiring expected in tabs/state — keyboard shortcut not verified | UI shell only. |
| `#drawer-backdrop` | `index.html:509` | Closes drawers on click — wiring in `state.js`/`filters.js`. |

---

## 1. Overview tab (`#tab-overview`)

| Element | DOM id | Renderer | Endpoint(s) | Safe? |
|---|---|---|---|---|
| Accepted Live Jobs card | `#overview-accepted-count` | `render_overview.js:32-58` | `GET /api/jobs?dry_run=1` | ✅ dry-run |
| Opportunities Radar card | `#overview-opp-count` | `render_overview.js:61-64` | `GET /api/opportunities` | ✅ cached |
| Discovered Batches card | `#overview-batch-count` | `render_overview.js:66-69` | `GET /api/history` | ✅ |
| Budget Efficiency card | `#overview-budget-burn` | `render_overview.js:71-80` | `GET /api/usage` (reads `budget_efficiency`/`burn_rate`) | ✅ |
| Pipeline Funnel chart | `#pipeline-funnel-chart` | `charts.js` (referenced) | needs `/api/debug/jobs` or `/api/jobs` payload | 🛑 not wired yet |
| Industry Distribution chart | `#industry-dist-chart` | `charts.js` | needs accepted/unresolved per-industry counts | 🛑 not wired yet |
| Pipeline Engine Stream | `#pipeline-stream` | static fallback in HTML | needs SSE endpoint (`API_URLS.pipeline_stream = null`) | 🛑 no backend |
| Card click → tab nav | `[data-target]` on cards | wiring via `tabs.js` / `state.js` | UI navigation only | ✅ |

Counting bug: `render_overview.js:58` filters `items.filter(j => j.status === 'accepted')` but live backend `/api/jobs?dry_run=1` returns `{status:"ok", dry_run:true, ...}` with no `jobs[]` array. Accepted card therefore renders `'0'`.

---

## 2. Live Jobs tab (`#tab-live_jobs`)

| Element | DOM id | Renderer | Endpoint(s) | Safe? |
|---|---|---|---|---|
| Jobs container | `#jobs-container` | `render_jobs.js:61-154` | `GET /api/jobs?dry_run=1` initial; `GET /api/jobs` on confirm | ✅ initial / ⚠️ on confirm |
| Provider Fan-Out card | injected | `render_jobs.js:39-59` | `data.provider_breakdown` from `/api/jobs` | ⚠️ live only |
| Verified accepted jobs section | `<section>` injected | `renderAcceptedJobCard()` `render_jobs.js:170-215` | reads `data.data` / `data.jobs` / `data.accepted` | ⚠️ |
| Unresolved live candidates section | `<section>` injected | `renderUnresolvedCandidateCard()` `render_jobs.js:217-245` | reads `data.rejected` (currently mislabels rejected as unresolved) | ⚠️ |
| Rejection reason badges | injected | `renderRejectionSummary()` `render_jobs.js:156-167` | reads `data.rejection_summary` | ⚠️ |
| Run Live Discovery button | `#prepare-discovery-btn` → `#trigger-discovery-btn` | `state.js:106-142` | calls `loadJobs({live:true})` | ⚠️ |
| Cancel | `#cancel-discovery-btn` | `state.js:125-131` | UI only | ✅ |

Truth gap: backend returns only `accepted` + `rejected`; UI renders backend's `rejected` as "Unresolved live candidates". That misleads users — hard rejects (e.g., `not_food_service`) currently never appear because of CRIT-1 (`rejection_reasons` returns `[]`), and once CRIT-1 is fixed, true hard rejects would land in the "Unresolved" UI section unless we add a real third bucket.

---

## 3. Opportunities tab (`#tab-opportunities`)

| Element | DOM id | Renderer | Endpoint(s) | Safe? |
|---|---|---|---|---|
| Geography Radar (origin label) | `#geo-origin-addr` | wiring via `render_overview` or `render_opportunities` (not yet seen in JS) | `/api/health` → `origin` field | ✅ |
| Markov Vacancy Prediction (Beta) | `#markov-radar-container` | static fallback HTML | none — feature deferred | 🛑 placeholder |
| Business Opportunities list | `#opportunities-container` | `render_opportunities.js:10-67` | `GET /api/opportunities` | ✅ |
| Per-card fields | injected | name, address, category, rating, review_count | reads opportunity item | ✅ |

---

## 4. History tab (`#tab-history`)

| Element | DOM id | Renderer | Endpoint(s) | Safe? |
|---|---|---|---|---|
| Accepted Over Time chart | `#history-over-time-chart` | `charts.js` | needs batch counts over time | 🛑 not yet wired |
| Rejection Distribution chart | `#rejection-dist-chart` | `charts.js` | needs aggregate rejection reasons | 🛑 not yet wired |
| History table | `#history-rows` | `render_history.js:1-36` | `GET /api/history` | ✅ |
| Columns | batch_id, timestamp, trigger, accepted, rejected | reads `batches[]` payload | ✅ |

History tab does not have a "Trigger" field returned by the live `/api/history` (batches come from GCS; trigger is not currently persisted) — renders "Unknown".

---

## 5. Debug Evidence tab (`#tab-debug_evidence`)

| Element | DOM id | Renderer | Endpoint(s) | Safe? |
|---|---|---|---|---|
| Pipeline Stage Reactor chips | `#stage-*` | `render_debug_evidence.js:1-77` | static — needs SSE (`API_URLS.pipeline_stream`) | 🛑 no backend |
| Shedding Registry counters | `#rej-*` | static | needs aggregate rejection counts from `/api/debug/jobs` | 🛑 not wired |
| Real-time Logs panel | `#pipeline-logs` | static text | needs SSE | 🛑 |
| Evidence drawer detail | `#evidence-content` | `renderEvidence()` `render_debug_evidence.js:79-146` | reads object passed by `AppState.showEvidence(id, type)` | depends on caller |

Evidence drawer expects fields not currently returned by `/api/jobs`: `raw_title`, `normalized_title`, `provider_id`, `industry_scores`, `dedupe_key`, `place_resolution`, `budget_cost`, `query_seed`, `discovery_mode`, `timestamp`. All render as "Unavailable" today.

---

## 6. Providers tab (`#tab-providers`)

| Element | DOM id | Renderer | Endpoint(s) | Safe? |
|---|---|---|---|---|
| Provider card grid | `#providers-container` | `render_providers.js:1-35` | `GET /api/providers` (api_bp blueprint) | ✅ |
| Per-card: label, type, ready/dormant badge | injected | reads `{label, type, is_available}` | ✅ |

Backend currently returns providers from `providers/__init__.py:get_all_providers()`. UI does not split Discovery vs Reasoning explicitly — it relies on `type` value coming through.

---

## 7. Budget tab (`#tab-budget`)

| Element | DOM id | Renderer | Endpoint(s) | Safe? |
|---|---|---|---|---|
| Available Quota | `#budget-left` | `render_budget.js:1-83` | `GET /api/usage` (`total_searches_left`) | ✅ |
| Safe Load Protection badge | `#budget-safe-indicator` | computed budget state | derived | ✅ |
| Monthly Usage | `#budget-monthly-usage` | reads `usage.monthly_usage` | not currently returned by `/api/usage` | 🛑 field gap |
| Estimated Action Cost | `#budget-est-cost` | reads `usage.estimated_action_cost` | not currently returned | 🛑 field gap |
| Budget Usage Over Time chart | `#budget-usage-chart` | `charts.js` | needs time-series | 🛑 not wired |
| Provider Mix chart | `#provider-mix-chart` | `charts.js` | needs provider mix | 🛑 not wired |
| Provider Quota Health list | `#provider-budget-list` | reads `usage.provider_usage` | not currently returned | 🛑 field gap |
| Generate Dry-Run Plan button | `#dry-run-plan-btn` | `render_budget.js:86-107` | `GET /api/jobs?dry_run=1` reads `plan` (not returned) | 🛑 field gap |
| Dry-Run output `<pre>` | `#dry-run-output` | injected | depends on `plan` field | 🛑 |

---

## 8. Why Three tab (`#tab-why_three`)

| Element | DOM id | Renderer | Endpoint(s) | Safe? |
|---|---|---|---|---|
| Resonance Comparison chart | `#resonance-comparison-chart` | `charts.js` | needs `top3` payload | 🛑 not wired |
| Top-3 cards | `#why-three-container` | `render_why_three.js:1-38` | `GET /api/why-three` | ✅ |
| Per-card fields | title, company, score, why_included | reads top3 items | depends on backend |

Backend `/api/why-three` (legacy `api/index.py:1065-1083`) returns an explainer dict, NOT `top3[]`. UI therefore renders empty state.

---

## 9. Filter inventory (cross-tab)

Always-visible filters: mode, industry, provider, status, sort, radius (mi), match (%).
Drawer filters: mode, industry, provider, status, sort, radius, match, walk min, transit min, rating, review score, job type, pay hint, remote/onsite, batch id, time range, rejection reason, confidence %, place status, application state, duplicate state.

`AppState.filters` in `state.js:53-78` mirrors these. The frontend applies most filters locally on cached data. The backend filter set in `api/index.py:apply_filters()` (line 768-820) supports: `min_rating`, `max_radius`, `max_transit`, `min_score`, `role`, `house`, `q`. Most drawer filters have no backend counterpart yet (see parity matrix).

---

## 10. Mobile behavior

- `meta viewport` set; layouts use CSS grid + `var(--space-*)` tokens.
- `#mobile-menu-toggle` button only displays at narrow widths.
- Filter drawer uses fixed positioning (slide-in).
- Service worker registered; `manifest.json` references make this a PWA shell.
- No explicit reduced-motion or save-data hooks observed in current renderers.

---

## 11. Surfaces that may render fake or misleading data today

| Surface | Risk | Source |
|---|---|---|
| "Unresolved live candidates" section in Live Jobs | Currently labels backend `rejected` array as unresolved. Once CRIT-1 fix lands, hard rejects must move to a separate bucket; otherwise label lies. | `render_jobs.js:144-152` |
| Pipeline Engine Stream / Stage Reactor / Logs panel | Always reports "DISCONNECTED" and 0 counters, but UI suggests it's a live reactor. Should label "stream unavailable" only, no chip pulses. | `render_debug_evidence.js:33-74` |
| Markov Vacancy Prediction Beta | Static "Radar offline" — acceptable, but should remain explicitly Beta-labeled even when wired later. | `index.html:184-186` |
| Why Three rendering | Will render "No resonance match results" indefinitely until `top3` is returned. Need either real `top3` or honest "decision engine requires minimum n=3" copy already in fallback. | `render_why_three.js:14-16` |
| Budget tab fields (`monthly_usage`, `estimated_action_cost`, `provider_usage`) | Renders blank "Unavailable" today because `/api/usage` does not return them. Acceptable per "no fake data" rule — but UI shells suggest those data exist. | `render_budget.js` |

---

## 12. Acceptance criteria for parity

- Every interactive control listed above is either (a) backed by a real endpoint with a real payload field, or (b) explicitly labeled `unavailable / not configured / pending`.
- Accepted, unresolved, and rejected job buckets are visually distinct.
- No section claims "live", "active", or "ready" without a verified backend signal.
- Budget surface never animates faster than real usage.
- Evidence drawer fields render "Unavailable" rather than fabricating.
- Mobile width ≤ 480px collapses sidebar; drawer overlays content.
