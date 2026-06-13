AI JOB AGENT 6.0
PROJECT UI/UX (6) (ChatGPT)


PROJECT UI/UX (Frontend) Plan: Job Hunter Pro /  Fully Autonomous, Predictive, Persistent, Native, Multi-Industry, multimodalIntelligence, Headless Execution, and Edge-Inference P2P Swarm Engine


cd "$HOME/Workspaces/Job_Hunter_Platform/job-hunter-pro" 2>/dev/null || cd "$HOME/job-hunter-pro" || exit 1


mkdir -p docs


cat > docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md <<'EOF'
# AI JOB AGENT 6.0
# S10 UI/UX SESSION MASTERPLAN
# Job Hunter Pro — Document 6


Owner: Michael Ware  
Project: Job Hunter Pro  
Repository: mjmichaelware/job-hunter-pro  
Cloud Project: ai-job-agent-498702  
Cloud Run Service: job-hunter-pro  
Region: us-central1  
Development Environment: Android ARM64 Termux  
Frontend Stage: S10  
Previous Build State: S0-S9 complete or minimally verified  
Current Status: S10-A safe cockpit shell committed locally  
Deployment Rule: Do not deploy until S12  


---


# 0. Purpose of Document 6


Document 6 converts Document 5 from a broad UI/UX imagination and handoff document into a controlled implementation plan.


Document 5 is the UI/UX authority. Document 6 is the execution map.


Document 6 exists because Document 5 is too large and too concept-dense to implement in one Gemini CLI session. S10 must be split into multiple narrow sessions, each with a clear objective, file scope, forbidden actions, proof gate, and commit.


This document prevents false completion claims.


S10-A is not all of S10.  
S10-A is only the safe cockpit shell checkpoint.  
Full Document 5 parity requires S10-B through S10-M.


---


# 1. Global S10 Laws


These laws apply to every S10 session.


## 1.1 No Deploy Before S12


No S10 session deploys to Cloud Run.


No `gcloud run deploy`.


No Cloud Scheduler edits.


No production traffic changes.


S10 is local implementation and proof only.


## 1.2 No Secret Exposure


Never hardcode secrets.


Never print secrets.


Never commit secrets.


Never put tokens in URLs.


All real keys belong in Secret Manager only.


Any discovered exposed key or password must be treated as compromised and rotated before deployment.


## 1.3 LLM Truth


OpenAI, Gemini, Claude, Groq, xAI, and similar providers are reasoning, enrichment, scoring, explanation, extraction, classification, and ghostwriting providers only.


They are not job discovery sources.


The UI must never imply that LLMs search for jobs.


## 1.4 Discovery Truth


Discovery providers are:


- SerpAPI Jobs
- SerpAPI Organic
- Adzuna
- USAJobs
- Jooble
- Careerjet
- The Muse
- Any already configured non-LLM discovery provider in the repo


## 1.5 Data Truth


The UI is a report of the machine, not a simulation.


Forbidden:


- fake jobs
- fake companies
- fake counts
- fake metrics
- fake provider status
- fake budget usage
- fake AI claims
- fake charts
- demo arrays
- sample rows
- lorem ipsum
- “AI found these jobs” without evidence
- provider active status without real status
- confidence without computed confidence
- maps or pins without returned location data
- pipeline motion without real pipeline state or explicit idle/unavailable state


If data is missing, render:


- loading
- empty
- error
- stale
- unavailable
- not configured
- cached
- dry run
- live
- partial
- blocked
- budget guarded
- needs action


## 1.6 Safe Boot


Initial page load may call only safe/status/cached/dry-run endpoints.


Allowed safe boot concepts:


- `/api/health`
- `/api/usage`
- `/api/opportunities` if cached/safe
- `/api/history`
- `/api/providers` if status-only
- `/api/industries`
- `/api/jobs?dry_run=1` only if used as a dry-run query plan and proven not to hit discovery providers
- cached budget/status surfaces
- cached/dry-run planning endpoints if present


Forbidden on boot:


- live `/api/jobs`
- `/api/ingest`
- SerpAPI spend
- paid discovery provider execution
- live all-jobs crawl
- scheduler ingestion
- tokenized ingest URL
- automatic live discovery


## 1.7 UI Scope


S10 is web/UI layer.


Allowed file areas:


- `web/templates/`
- `web/static/css/`
- `web/static/js/`
- possibly `templates/` or `static/` if inspection proves the app uses those
- `docs/` for S10 planning/proof
- tiny backend compatibility fixes only if inspection proves they are required


Forbidden:


- backend rewrite
- architecture rewrite
- provider rewrite
- ingestion rewrite
- scheduler work
- deployment work
- Secret Manager edits
- database migrations unless a later approved stage requires it


---


# 2. S10 Session Inventory


S10 is split into 13 sessions:


- S10-A: Safe Cockpit Shell
- S10-B: API Contract Reality Pass
- S10-C: Core Renderer Truth Upgrade
- S10-D: Advanced Filter System
- S10-E: Evidence Drawer System
- S10-F: Budget Reactor and Live Action Guard
- S10-G: Charts From Real Data Only
- S10-H: Pipeline Reactor / SSE Readiness
- S10-I: Geo Radar and Review Geometry
- S10-J: Premium Motion and Visual Enhancement Tier
- S10-K: PWA and Offline History
- S10-L: Accessibility, Bilingual, Keyboard
- S10-M: Final S10 Parity Gate


Current completed checkpoint:


- S10-A committed locally as safe shell baseline.


Remaining sessions:


- S10-B through S10-M.


---


# 3. S10-A — Safe Cockpit Shell


## Status


Done / committed locally.


## Purpose


Create the first safe UI shell that proves the web app can render the S10 cockpit without violating safety rules.


## Raw Document 5 data points covered


- 8-tab shell exists.
- Premium dark cockpit baseline exists.
- Safe boot idea exists.
- Frontend `/api/ingest` is absent.
- No direct live `/api/jobs` fetch exists.
- No fake/demo frontend terms were detected.
- Known unsafe debug scripts were disabled.
- Document 5 exists in `docs/`.
- S10 local safety snapshot passed.


## Required tabs covered


- Overview
- Live Jobs
- Opportunities
- History
- Debug Evidence
- Providers
- Budget
- Why Three


## Files changed in S10-A


Expected committed files include:


- `GEMINI.md`
- `docs/AI_JOB_AGENT_5_UIUX_Handoff.md`
- `api/scrape.py`
- `debug_serp.py`
- `full_debug.py`
- `web/templates/index.html`
- `web/static/css/base.css`
- `web/static/css/layout.css`
- `web/static/css/components.css`
- `web/static/css/charts.css`
- `web/static/js/api.js`
- `web/static/js/state.js`
- `web/static/js/tabs.js`
- `web/static/js/filters.js`
- `web/static/js/charts.js`
- `web/static/js/render_jobs.js`
- `web/static/js/render_opportunities.js`
- `web/static/js/render_history.js`
- `web/static/js/render_providers.js`
- `web/static/js/render_budget.js`
- `web/static/js/render_debug_evidence.js`
- `web/static/js/render_overview.js`
- `web/static/js/render_why_three.js`


## Exit proof already achieved


- Document 5 SHA matched.
- All 8 tabs present.
- No frontend `/api/ingest`.
- No `API_URLS.jobs`.
- No direct live `/api/jobs` fetch.
- No configured fake/demo frontend terms.
- Known unsafe debug files contain no matching hardcoded secret patterns.
- Changed Python files compile.


## What S10-A does not complete


S10-A does not complete full Document 5 parity.


Missing:


- full advanced filters
- full evidence drawers
- real provider contract handling
- real budget reactor
- real chart system
- SSE pipeline reactor
- WebGL/WebGPU telemetry
- PWA/offline mode
- Markov radar
- bilingual system
- accessibility pass
- command palette
- full advanced animation tier
- backend endpoint gap resolution


## Commit message


`S10-A implement safe cockpit shell and local safety gates`


---


# 4. S10-B — API Contract Reality Pass


## Purpose


Before adding more UI complexity, inspect the real backend API contract.


Document 5 describes many frontend needs. S10-B determines which data is actually available and which UI features must render honest unavailable states.


## Objective


Create a precise API-to-UI contract map.


## Raw data points from Document 5 to verify


### Safe API Map


Verify current behavior of:


- `/api/health`
- `/api/usage`
- `/api/jobs?dry_run=1`
- `/api/opportunities`
- `/api/history`
- `/api/research`
- `/api/providers`
- `/api/industries`
- `/api/applications`
- `/api/why-three`


Verify restricted/non-UI behavior of:


- live `/api/jobs`
- `/api/ingest`


### UI payload needs


Document exact returned fields for:


- jobs
- opportunities
- history batches
- provider status
- usage/budget
- industries
- applications
- why-three results
- research/place details
- dry-run query plan
- rejection reasons
- evidence fields
- review score components
- place resolution notes
- commute/radius fields


## Allowed files


- `docs/S10_API_CONTRACT_MATRIX.md`
- optional `scripts/s10_api_contract_snapshot.py`
- frontend files only if required to render honest missing endpoint states


## Forbidden actions


- no live provider calls
- no SerpAPI spend
- no `/api/ingest`
- no backend rewrite
- no fake endpoint data
- no deploy


## Implementation tasks


1. Inspect local route definitions.
2. Run safe endpoint checks only.
3. Record status codes.
4. Record JSON shapes.
5. Record missing fields.
6. Record frontend dependencies.
7. Mark features as:
   - supported now
   - supported partially
   - missing endpoint
   - endpoint exists but missing fields
   - future/S11 backend dependency
8. Update UI only to show honest missing/unavailable states if needed.


## Exit proof


A matrix exists with columns:


- Endpoint
- Safety class
- Method
- Boot allowed
- Payload fields returned
- UI features depending on it
- Status
- Gap
- Next action


## Commit message


`S10-B document API contract reality for UI parity`


## Stop rule


Stop after contract proof. Do not build advanced visuals yet.


---


# 5. S10-C — Core Renderer Truth Upgrade


## Purpose


Make every tab renderer resilient to the actual backend data shapes found in S10-B.


## Objective


Every tab must render real, empty, loading, error, stale, partial, and unavailable states without crashing or faking data.


## Raw UI components


### Overview


Must render:


- health
- last safe refresh
- last ingest if available
- accepted count if real
- opportunity count if real
- batch count if real
- provider summary if real
- budget summary if real
- current mode
- active filters
- stale/missing/unavailable warnings


### Live Jobs


Must render job cards/rows with real returned fields only:


- title
- company
- place
- source
- industry
- match score
- review score
- place status
- commute or walk status
- application status
- why-this summary
- evidence availability
- rejection risk flags


### Opportunities


Must render:


- business name
- category
- industry alignment
- rating if real
- review count if real
- distance/radius if real
- commute if real
- opportunity strength if real
- missing data explanation


### History


Must render:


- batch list
- timestamps
- accepted count
- rejected count
- deduped count
- provider mix
- budget per batch
- selected batch detail
- no-history state


### Debug Evidence


Must render:


- pipeline counts
- rejection reasons
- dedupe keys
- classifier scores
- raw vs normalized
- provider evidence
- place resolution notes
- review score effects
- low-rating caps
- ambiguous classification notes


### Providers


Must render:


- Discovery providers
- Reasoning providers
- configured/missing key state
- dormant/live state
- budget guarded state
- last used if real
- allowed actions


### Budget


Must render:


- budget limit
- current usage
- provider usage
- estimated action cost
- dry-run vs live state
- blocked over-budget events
- safe load explanation


### Why Three


Must render:


- top three if real
- ranking factors
- evidence matrix
- why included
- why excluded
- missing data
- no-rank state when fewer than three valid candidates exist


## Allowed files


- `web/static/js/render_overview.js`
- `web/static/js/render_jobs.js`
- `web/static/js/render_opportunities.js`
- `web/static/js/render_history.js`
- `web/static/js/render_debug_evidence.js`
- `web/static/js/render_providers.js`
- `web/static/js/render_budget.js`
- `web/static/js/render_why_three.js`
- `web/static/js/api.js`
- `web/static/js/state.js`
- `web/static/css/components.css`
- `web/templates/index.html`


## Forbidden actions


- no fake rows
- no fake provider status
- no fake metrics
- no fake chart data
- no live discovery on boot
- no `/api/ingest`
- no deploy


## Exit proof


For each renderer, prove:


- null input does not crash
- empty input shows allowed empty state
- partial input shows unavailable fields
- malformed input shows error/partial state
- real returned fields render
- no demo arrays exist


## Commit message


`S10-C harden UI renderers against real API payloads`


---


# 6. S10-D — Advanced Filter System


## Purpose


Implement the full Document 5 filter architecture.


## Objective


Replace basic filters with a powerful but controlled advanced drawer.


## Raw filter data points


Always visible filters:


- search mode
- radius/location
- industry
- provider
- status
- sort
- min match score


Advanced drawer filters:


- max walk minutes
- max transit minutes
- min rating
- min review score
- job type
- pay hint
- remote/onsite
- provider include/exclude
- batch
- time range
- rejection reason
- classification confidence
- place status
- application state
- duplicate state


Applied filter UI:


- chips
- remove chip
- reset all
- active filter summary
- filter count
- drawer open/close state
- local filtering only unless safe query refresh is explicitly required


## Search modes


- all jobs
- industry seeded
- dry run
- live run
- cached/history mode


## Required rule


Filters must use only fields present in returned data.


If a filter depends on missing data, it must be disabled with honest copy.


## Allowed files


- `web/static/js/filters.js`
- `web/static/js/state.js`
- `web/static/js/render_jobs.js`
- `web/static/js/render_opportunities.js`
- `web/static/js/render_history.js`
- `web/static/css/components.css`
- `web/static/css/layout.css`
- `web/templates/index.html`


## Forbidden actions


- no backend calls on every filter change unless safe and intentional
- no fake filter values
- no fake provider options
- no hidden live calls
- no deploy


## Exit proof


- All filter controls exist or are explicitly marked unavailable.
- Chips update.
- Reset works.
- Filtering does not spend provider budget.
- Missing data disables relevant filter rather than faking values.


## Commit message


`S10-D implement advanced filter drawer and chips`


---


# 7. S10-E — Evidence Drawer System


## Purpose


Trust is the product. Evidence drawers expose why a job, opportunity, or rejection exists.


## Objective


Build expandable evidence panels using only returned fields.


## Mandatory evidence fields


- raw_title
- normalized_title
- company
- source
- provider_id
- industry_scores
- accepted/rejected status
- rejection_reasons
- dedupe_key
- place_resolution
- review_score
- match_score
- budget_cost
- query_seed
- discovery_mode
- timestamp


Additional Document 5 evidence concepts:


- match score components
- transit duration
- place id
- role family scores
- classification confidence
- place resolution notes
- review score effects
- low rating cap explanation
- ambiguous place resolution notes


## UI behavior


- Job card opens evidence drawer.
- Opportunity card opens evidence drawer if data exists.
- Debug Evidence tab shows pipeline evidence.
- Missing fields show unavailable.
- Rejection reasons render as badges.
- Raw vs normalized comparison is visible.
- Dedupe key is visible if real.
- Budget cost is visible if real.


## Allowed files


- `web/static/js/render_debug_evidence.js`
- `web/static/js/render_jobs.js`
- `web/static/js/render_opportunities.js`
- `web/static/js/state.js`
- `web/static/css/components.css`
- `web/static/css/layout.css`
- `web/templates/index.html`


## Forbidden actions


- no invented evidence
- no generic “AI decided”
- no hidden JSON dump as primary UI
- no fake rejection reasons
- no deploy


## Exit proof


- Drawer opens and closes.
- Every mandatory field has a render path.
- Missing fields are labeled unavailable.
- No evidence value is fabricated.


## Commit message


`S10-E implement evidence drawer trust surfaces`


---


# 8. S10-F — Budget Reactor and Live Action Guard


## Purpose


Budget anxiety is central. The user must trust that opening the app costs nothing.


## Objective


Create a clear budget panel and live-action guard.


## Raw budget concepts


- quota limit
- current usage
- provider usage
- estimated action cost
- dry-run projected cost
- live run actual spend
- budget guarded state
- blocked over budget
- safe load explanation
- historical/cached fallback
- quota lock when below threshold
- live action warning


## Budget states


- Safe
- Dry_Run
- Live
- Cached
- Budget_Guarded
- Blocked
- Not_Configured
- Partial
- Failed


## Required controls


- dry-run query plan
- run live discovery
- view provider budget
- reset filters
- explain safe boot


## Required copy


Live action label:


“May use discovery provider budget.”


Safe boot copy:


“Opening this dashboard does not run live discovery.”


## Allowed files


- `web/static/js/render_budget.js`
- `web/static/js/api.js`
- `web/static/js/state.js`
- `web/static/js/render_overview.js`
- `web/static/css/components.css`
- `web/templates/index.html`


## Forbidden actions


- no live discovery on boot
- no quiet live call
- no modal spam
- no fake quota numbers
- no fake usage
- no deploy


## Exit proof


- Dry-run path is visually separate from live path.
- Live path requires explicit confirmation.
- Budget panel renders real usage or unavailable.
- No boot path can spend provider budget.


## Commit message


`S10-F implement budget reactor and live action guard`


---


# 9. S10-G — Charts From Real Data Only


## Purpose


Create chart surfaces without violating data truth.


## Objective


Implement chart shells and real-data-only chart renderers.


## Chart inventory


- pipeline funnel
- provider mix
- budget usage
- accepted over time
- rejection distribution
- industry distribution
- opportunity categories
- review rating distribution
- budget per batch
- top-three evidence comparison


## Chart rules


If data is missing:


- show empty state
- show required data explanation
- show table fallback if possible
- do not render fake values
- do not render random demo shapes


## Possible library


Chart.js may be used if added deliberately.


Vanilla SVG/CSS charts are preferred first for lightweight Termux/mobile safety.


## Allowed files


- `web/static/js/charts.js`
- `web/static/js/render_history.js`
- `web/static/js/render_budget.js`
- `web/static/js/render_debug_evidence.js`
- `web/static/css/charts.css`
- `web/static/css/components.css`
- `web/templates/index.html`


## Forbidden actions


- no demo data arrays
- no fake chart metrics
- no CDN dependency unless intentionally approved
- no heavy dashboard template
- no deploy


## Exit proof


- Each chart has data-required condition.
- Each chart has no-data state.
- No chart renders from hardcoded data.
- No chart crashes on empty payload.


## Commit message


# 10. S10-H — Pipeline Reactor / SSE Readiness


## Purpose


Document 5 imagines a live pipeline that can be watched as it processes results.


## Objective


Prepare UI for pipeline telemetry without faking activity.


## Pipeline stages


- discover
- normalize
- resolve_place
- classify
- score
- filter
- dedupe
- store


## Rejection shedding reasons


- not_food_service
- outside_radius
- ambiguous_place_resolution
- duplicate
- budget guard
- provider error
- missing source URL
- transit unavailable
- low confidence fit
- low rating cap
- place resolution unavailable


## Behavior


If SSE endpoint exists:


- connect safely only when user enters debug/pipeline tab or explicitly starts live run
- show stage counts
- show accepted/rejected flow
- show rejection reasons


If SSE endpoint does not exist:


- render “pipeline stream unavailable”
- render static last batch evidence if available
- do not animate fake counts


## Allowed files


- `web/static/js/render_debug_evidence.js`
- `web/static/js/state.js`
- `web/static/js/api.js`
- `web/static/css/components.css`
- `web/static/css/charts.css`
- `web/templates/index.html`
- possibly `docs/S10_BACKEND_GAPS.md`


## Forbidden actions


- no fake live stream
- no synthetic counts
- no backend SSE implementation unless approved separately
- no live discovery on boot
- no deploy


## Exit proof


- Pipeline UI exists.
- No-stream state exists.
- No fake animation runs without data.
- SSE dependency is documented.


## Commit message


`S10-H prepare pipeline reactor without fake telemetry`


---


# 11. S10-I — Geo Radar and Review Geometry


## Purpose


Make place resolution, distance, commute, and review quality visible and trustworthy.


## Objective


Implement geography and review-trust UI components.


## Geo data points


- origin address
- resolved address
- place id
- lat/lng if returned
- radius miles
- distance
- walk duration
- transit duration
- drive duration
- place status
- ambiguous place resolution
- outside radius
- unavailable