# Job Hunter Pro — Canonical Master Context

Scope: project-local agent context for Job Hunter Pro.
This is not the global `~/AGENTS.md`.
This file was created from the internal-storage / Drive-upload source document.

## Hardcoded Project Identity

Repository:
`https://github.com/mjmichaelware/job-hunter-pro`

GCP project:
`ai-job-agent-498702`

Cloud Run service:
`job-hunter-pro`

Cloud Run region:
`us-central1`

Production URL:
`https://job-hunter-pro-5t3wttw2ua-uc.a.run.app`

Primary route to verify:
`https://job-hunter-pro-5t3wttw2ua-uc.a.run.app`

## Source Material

Raw preserved source:
`docs/agent_context/source_drop/job_hunter_pro_canonical_master/JOB_HUNTER_PRO_CANONICAL_MASTER_SOURCE.txt`

Source SHA-256:
`237972c5c1d0cc6aaaaa703f5c7c165ff391aa1673c1d3751444eba848cd2533`

Source bytes:
`33377`

## Agent Rule

Agents must read this file as project-local context.
Do not copy this into global `~/AGENTS.md`.
Do not claim production is live without checking the production URL.
Do not expose secrets.
Do not deploy without explicit approval.

## Canonical Master Source Text

```text
﻿JOB HUNTER PRO CANONICAL MASTER DOCUMENT (v7.0)


AI-Orchestrated Local Opportunity Intelligence Platform — single source of truth
Supersedes AI_JOB_AGENT 1.0–6.0. Merges every data point from all six sources with zero loss, deduplicates, and resolves every contradiction/scope-drift. Where the six planning docs disagree with the actual repo state (git head 6627349, branch main, exported 2026-06-08), the repo is ground truth and the discrepancy is logged in PART 12.


Owner: Michael Ware · Repo: mjmichaelware/job-hunter-pro · GCP: ai-job-agent-498702 · Cloud Run: job-hunter-pro · Region: us-central1 · Dev: Android ARM64 Termux.


PART 0 — RECONCILIATION OF THE SIX SOURCES
1.0 (ChatGPT, Handoff) — THE FACTS. Project IDs, confirmed bugs, the proven v3/v5 pipeline, budget reality, security requirements, ~18-entity data model, multi-industry intent.
2.0 (Claude, Blueprint) — THE STRUCTURE. ~118-file decoupled tree, Firestore Native, one-file-per-provider/industry, thin HTTP layer. The architectural spine.
3.0 (Gemini, Omega) — THE AMBITION. Neo4j graph matching, Playwright auto-apply, CRDT/WebRTC P2P swarm, WASM edge inference, Eventarc, Cloud Armor, Markov prediction, Pydantic v2, ASN/Shodan "dark funnel." Most deferred, some excluded (PART 12). The doc that "changed everything."
4.0 (Claude, Convergence) — THE VERDICT. Reconciled 1+2+3, counted the work, fixed build order, adjudicated 3.0's scope. This canonical doc inherits 4.0's verdicts.
5.0 (ChatGPT, UI/UX) — THE INTERFACE AUTHORITY. Premium dark cockpit, data-truth rendering laws, 100-word lexicon, imagination brief, working safe baseline.
6.0 (ChatGPT, S10 Masterplan) — THE EXECUTION MAP. Splits UI work into 13 provable sessions (S10-A…M).
Converged honest product statement (replaces 3.0's grandiose title): a persistent, budget-aware, multi-provider, multi-industry local opportunity intelligence dashboard. It budget-safely discovers local jobs across industries; resolves exact locations; scores commute/radius from the owner's origin; enriches with Google Places ratings/reviews + public web evidence; uses LLMs for extraction/classification/consensus (never discovery); stores timestamped batches; exposes history/time-ranges and accepted AND rejected evidence; and presents a data-honest UI. It separates live accepted jobs vs nearby hiring targets vs historical jobs vs rejected/needs-review — Places reveals hundreds of targets; SerpAPI/web reveal actual postings. The inflated subtitle ("Fully Autonomous… P2P Swarm Engine") is deprecated.


PART 1 — IDENTITY, ENVIRONMENT, SECRETS
Owner: Michael Ware · repo mjmichaelware/job-hunter-pro · GCP ai-job-agent-498702 · Cloud Run job-hunter-pro / us-central1 · observed URL https://job-hunter-pro-5t3wttw2ua-uc.a.run.app (verify live) · dev Android ARM64 Termux, gcloud in ~/google-cloud-sdk · scheduler SA job-hunter-scheduler@ai-job-agent-498702.iam.gserviceaccount.com.
Working preferences: work backwards like a computer scientist; never guess, diagnose with terminal; single copy-paste blocks, minimal whitespace, no fake confidence; proof loop inspect → py_compile → commit/push → deploy → health → endpoint → logs on failure; never expose secrets anywhere.
Secrets (Secret Manager only, names not values): GOOGLE_MAPS_API_KEY, SERPAPI_KEY, GROQ_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY, XAI_API_KEY (7 stored). INGEST_TOKEN deprecated → Cloud Scheduler OIDC. Groq (GROQ_API_KEY) ≠ Grok/xAI (XAI_API_KEY).
Free keys to add via add_key.sh (live on next revision, no code redeploy): Adzuna ADZUNA_APP_ID+ADZUNA_APP_KEY; USAJobs USAJOBS_API_KEY+USAJOBS_EMAIL; Jooble JOOBLE_API_KEY; Careerjet CAREERJET_AFFID. The Muse needs no key (proves pipeline day one).
Candidate profile (manual apply / resume / bilingual copy only — NOT automated submission): origin 28 E Bryan Ave, SLC (~40.71, -111.89); contact michaelware433@yahoo.com, (801) 386-4047; languages EN C2 / ES C1 / RU B1; seeded signals: de-escalation, inventory/expo flow, amusement/hospitality ops.


PART 2 — HISTORY, BUGS, AND ACTUAL CURRENT STATE
2A. Working phases: v3 definitive_food_fix → 11 accepted from 21 raw + 20 nearby restaurants. v5 review_filter_intelligence → /api/health all provider flags true, origin_geocoded:true, max_radius_miles:2.5, max_transit_minutes:35, nearby_restaurant_count:20; filters + review layer live. Later "Service Unavailable" reported (no logs captured). Once showed "3 jobs / raw 5 / 20 restaurants" — symptom of MAX_SERP_QUERIES/MAX_RAW_JOBS caps.
2B. Confirmed bugs → fixes:
Substring false-reject ("rn" inside words) → word-boundary regex (v3).
Wrong place resolution (Grand America pool server → Quality Inn) → prioritize explicit company/address queries.
Over-aggressive address extraction (sentence fragments as addresses) → stricter extraction + dedupe (proposed v4).
Duplicate jobs → canonical key title + normalized place/address, not job-ID/URL.
lru_cache not durable (Cloud Run scales to zero) → persistent cache_repo.
Ingest token in URL exposure → Scheduler OIDC; /api/ingest verifies audience + SA email.
Brittle GCS metadata-token auth → google-auth AuthorizedSession (auto-refresh).
Cold-start Places calls → precomputed batches + cache + scheduled ingest.
SerpAPI budget is the central constraint; no live SerpAPI on page load.
Naive review score (3.7★ IHOP = 100) → capped 60/15/15/10 (PART 6).
2C. "Service Unavailable" doctrine: = boot/worker failure (syntax, missing dep, import error, incompatible Google lib, timeout, memory, route-patch dup, undefined fn, GCS auth, /tmp perms, bad --set-env-vars). Recovery: read logs → traceback → py_compile → grep version marker → deploy clean known-good if patch stack corrupt. gcloud run services logs read job-hunter-pro --region us-central1 --limit 160.
2D. ACTUAL REPO STATE (ground truth, head 6627349, 212 files) — most important reconciliation: The 6 docs describe work as upcoming; the repo shows it largely done. Entrypoint app.py (Flask factory); UI web/templates/index.html+web/static/*; legacy api/index.py preserved; modular api/*.py; registry providers/__init__.py; bridge search/live_provider_bridge.py. Encoded law: secrets→SM only; scheduler→/api/ingest OIDC only; page-load→no live discovery/no SerpAPI burn; LLMs→enrichment not discovery; discovery→serpapi_jobs/organic, adzuna, usajobs, jooble, careerjet, themuse, google_places. Commits prove S10-A…M, S11, S12, plus repair series R0–R10 (R0 truth matrix, R1 taxonomy, R2-3 providers, R4-6 federated+applications, R7-9 OIDC reasoning+frontend contract, R10B api.index live parity, R10C responsive filters), then "Wire federated providers into live jobs" + "Show all live job candidates." Caveat from the repo itself: "file_exists ≠ mounted_or_called." → Do not rebuild from zero; inspect live /api/health and close gaps.


PART 3 — CANONICAL ARCHITECTURE (2.0 spine, 1.0 facts, 4.0 verdict, repo-reconciled)
Principle: single responsibility per file. Add source = 1 file + 1 registry line; add industry = 1 file; swap DB = change store/ only.
Code
Decoupling invariants: (1) api/ = zero business logic. (2)(3) one file per provider/industry behind ABC. (4) LLMs only in reasoning/, physically separated from search/ → never wired as discovery → no hallucinated jobs. (5) only store/ talks to Firestore. (6) budget.py before every paid call; cache_repo before every external fetch. (7) no hardcoded secrets; providers dormant if key absent.
Hard counts (4.0): 118 files / 20 dirs; 102 need real code (Py 81, JS 10, CSS 4, HTML 3, sh 4); 16 trivial; 5 tests. Core libs (6): Flask, gunicorn, requests, python-dotenv, google-auth, google-cloud-firestore. Optional LLM SDKs (4, deferrable): openai, google-generativeai, anthropic, groq (xAI via raw HTTP). Excluded bloat: neo4j, playwright, opentelemetry, numpy, scipy. 14 Google services; 10 Firestore collections; 1 SA; 1 scheduler job (6h, OIDC); 1 GCS bucket; 1 Firestore DB (Native, free). 17 endpoints; 6 industries; 7 search providers; 5 LLM enrichers.


PART 4 — DATA MODEL & SCHEMAS
4A. ~18 entities (1.0): providers, search_runs, batches, queries, raw_results, jobs, job_snapshots, places, place_snapshots, reviews, review_sources, people/chefs, companies, rejections, scores, applications, user_filters, industry_taxonomies, api_usage.
4B. Firestore (Native, canonical):
Code
4C. Cloud Storage JSON batch: batch_schema, created_at_utc, source_version, trigger, budget, providers_used, rules, counts, queries, accepted, rejected, opportunities, errors.
4D. Pydantic v2 (kept from 3.0): MasterJobSnapshot(canonical_key 64-char SHA-256 title+address, place_id, industry_taxonomy Literal of 6, source_url HttpUrl, commute_matrix_seconds≥0, haversine_radius_miles≥0, review_heuristic_score 0–100, rejection_flags, ats_application_status Literal PREDICTED|DISCOVERED|INTERVIEWING|REJECTED|SUBMITTED_MANUALLY — "INJECTED" removed with auto-apply, telemetry). BatchIngestionPayload(batch_id, trigger_type Literal MANUAL|SCHEDULER_OIDC — CRDT_PEER_SYNC removed, budget_state float, metrics).
4E. SQL upgrade path (if Firestore outgrown): job_batches, search_queries, raw_results, places, jobs, job_snapshots, rejections, reviews, people, applications, api_usage — columns as detailed in 1.0.


PART 5 — PROVIDERS, KEYS, BUDGET
5A. Discovery vs Reasoning (most important rule). Discovery (retrieve real postings/targets): SerpAPI Jobs, SerpAPI Organic (off by default), Adzuna, USAJobs, Jooble, Careerjet, The Muse (keyless), + Google Places/Maps for opportunity discovery; future Google Custom Search + direct job-board APIs. Reasoning (LLMs, enrichment only): OpenAI, Gemini, Claude, Groq, xAI — they do NOT search just because keys exist; they reason over text we pass; MAY search only if explicitly implemented with grounding tools behind flags; never hallucinate listings. Flags: ENABLE_{OPENAI_WEB_SEARCH,GEMINI_GROUNDING,CLAUDE_WEB_SEARCH,XAI_WEB_SEARCH,SERPAPI_GOOGLE_JOBS,SERPAPI_ORGANIC,GOOGLE_CUSTOM_SEARCH} + per-batch quotas.
5B. Normalized SearchResult: provider, query, title, url, snippet, published_date, source_name, raw_json, confidence, cost_units. Federated dedupes by URL/title/company/place, resolves places, classifies, stores evidence.
5C. LLM policy (cheap-first): deterministic extraction first; ambiguous/weak → one model; disagreement → Claude/Grok validator; store outputs + confidence; claims need evidence or "unknown." Extract: business name, chain/local, role category, FOH/BOH/mgmt, salary, schedule, permits, warning signs, chef/hiring-manager, apply link, dup flag, confidence.
5D. SerpAPI budget (central constraint): quota small + volatile — /api/usage is the source of truth, not this doc (1.0 said ~200, 4.0 said ~155). Cadence 4/batch × 4 batches/day = 16/day → 112/week. Guard: if total_searches_left ≤ SERPAPI_MIN_SEARCHES_LEFT (e.g. 40) skip SerpAPI, return budget-guard, UI → cached/Places/history. /api/usage calls SerpAPI Account API (doesn't count as a search), used sparingly. Public web review search off by default (use Place Details first). Never live /api/jobs on load.
5E. Review/reputation: Place rating, review_count, sample reviews, business_status, website, Maps URL, phone, price_level, types; budget-permitting public snippets (Reddit/Yelp/Glassdoor/Indeed/news/chef bios). Score review_score, consistency_score, risk_level, +/- signal counts, evidence_links. UI: "Review score is a heuristic from public data, not moral truth."


PART 6 — THE PIPELINE
6A. Funnel: discovery → normalize → resolve place (explicit address OR Places Text Search; ambiguity→rejection) → Distance Matrix transit from 28 E Bryan Ave → radius (geocode/haversine) → industry phrase match (word-boundary, never substring) → rejection reasons → review intelligence (Place Details) → role tags/family → dedupe (canonical key) → store batch → filter UI → display + explain. Reactor stages: discover→normalize→resolve_place→classify→score→dedupe→store.
6B. Rejection reasons: not_food_service, no_exact_restaurant_address_resolved, ambiguous_place_resolution (UI pin-oscillation), radius_unavailable, outside_radius_Xmi, transit_unavailable, transit_too_long_Xmin, duplicate, provider_error, budget_guard, missing_source_url, + near-miss low_confidence_fit, low_rating_cap, place_resolution_unavailable. Accepted AND rejected always stored/inspectable.
6C. Scoring: Review (capped): rating 60% + count-confidence 15% + sentiment 15% + consistency 10%, penalties for negative workplace terms/contradictions; rating caps the max (fixes 3.7★=100); UI gauge geometry enforces the cap. Match: 0–100 with component breakdown in evidence drawer. Dedupe key: SHA-256 of title + normalized_address.


PART 7 — INDUSTRIES & TAXONOMY
7A. Six core routes: food_service, hospitality, sales, customer_service, care_social, retail_ops. Each: queries, match (whitelist), negative, role_families, resolution_strategy, credentials, background_sensitive. Deterministic regex runs before any LLM.
7B. Deterministic matrix (word-boundary regex):
| Industry | Whitelist (examples) | Negative | License/background |
|---|---|---|---|
| food_service | \bcook\b,\bchef\b,\bdishwasher\b,\bexpo\b,server,busser,host,barista,prep,line,runner,steward | \bregistered\s+nurse\b,\bcnc\b | Utah Food Handler, ServSafe |
| hospitality | \bhotel\b,\bfront\s+desk\b,\bbanquet\b,housekeeping,pool server,F&B | \bwarehouse\b,\bphlebotomist\b | background clearance |
| care_social | \bdsp\b,\bpeer\s+support\b,\bcase\s+aide\b,BHT,recovery coach,intake | \bculinary\b,\bretail\s+cashier\b | BHT/CPSS, CPR, UT Dept Health clear |
| customer_service | \binbound\b,\bhelp\s+desk\b,\bticket\b,sales agent,scheduling | \bheavy\s+lifting\b,\bfield\b | remote/hybrid internet check |
| sales | inside/outside sales, account, retail sales | route-specific | route-specific |
| retail_ops | cashier, stocker, associate, merchandiser | route-specific | route-specific |
7C. Future industries (1.0): behavioral health/peer support, recovery centers, social services/case mgmt, call centers, warehouses/logistics, delivery/driver, entry-level healthcare support, education/youth, trades/apprenticeships, tech/admin — each with own taxonomy/resolution/sources/credentials/filters. Don't force restaurant-only filtering in multi-industry mode. Role-family examples — food: server/busser/host/dishwasher/cook/prep/line/kitchen-supervisor/barista/runner/steward; behavioral health: peer-support-specialist/case-aide/BHT/recovery-coach/residential-support/intake-coordinator; hospitality: banquet/steward/front-desk/housekeeping/pool-server/F&B.


PART 8 — HTTP API (17) & SAFE BOOT
8A. /api/health(Safe, version+flags) · /api/usage(Safe, never a search) · /api/jobs?dry_run=1(Safe, zero SerpAPI) · /api/jobs(RESTRICTED, explicit) · /api/debug/jobs · /api/opportunities(Safe if cached, Places no SerpAPI) · /api/research/place(explicit) · /api/ingest(POST, OIDC, scheduler-only, never from UI) · /api/batches + /api/batch/<id>(Safe) · /api/history?hours=24 & ?from=&to=(Safe) · /api/providers/status(Safe) · /api/search/federated · /api/industries & /api/search?industry= · /api/applications(manual tracker) · /api/why-three(top-3 + evidence matrix + budget explainer; one canonical route) · future /api/predictions(flagged), /api/pipeline/stream/<id>(SSE if implemented).
8B. Safe Boot (default load spends nothing): DOMContentLoaded → initState → bindTabs → bindFilters → loadSafeDashboard. May call only: health, usage, opportunities(cached), history, providers(status), industries, jobs?dry_run=1(proven no provider hit), cached budget/status. MUST NOT: live /api/jobs, /api/ingest, SerpAPI spend, paid provider exec, all-jobs crawl, scheduler ingest, tokenized URL, any auto discovery. Live discovery = explicit action + cost-naming confirm.


PART 9 — SECURITY & DEPLOYMENT
9A. Secrets in SM only; never print/commit/echo; no tokens in URLs; exposed key = compromised → rotate. Public app may be unauthenticated; mutation/scheduled endpoints authenticated. google-auth AuthorizedSession for GCS. .gcloudignore excludes .git, venv, env, debug, __pycache__, backups.
9B. Scheduler OIDC (replaces INGEST_TOKEN): SA job-hunter-scheduler@…, grant roles/run.invoker; Scheduler HTTP target uses OIDC; /api/ingest verifies audience==Cloud Run URL and email==scheduler SA. No URL token.
9C. Canonical deploy block:
Bash
gunicorn: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0. Post-deploy proofs: health 200; dry_run spends 0; opportunities returns many; batches/history work empty; one OIDC run stores a batch.
9D. Google services (enable only what's used, free-first): Cloud Run, Build, Artifact Registry, Secret Manager, IAM, IAM Credentials, Service Usage, Resource Manager, Scheduler, Storage, Logging, Monitoring, Places, Geocoding, Distance Matrix, Routes, Address Validation, Time Zone, Geolocation, Firestore; optional/future: Vertex AI, Gemini, Discovery Engine, Natural Language, Document AI, Custom Search, Knowledge Graph, BigQuery, Cloud SQL, Pub/Sub, Cloud Tasks, Workflows, Eventarc. Enabled ≠ integrated.


PART 10 — UI/UX CANONICAL SPEC (5.0 authority + 6.0 execution)
10A. Philosophy: "Premium Dark Intelligence Cockpit" — not a job board/chatbot/admin/fake-AI page; a high-fidelity instrument showing a real machine.
10B. DATA-TRUTH LAWS (the fix for every "boilerplate/fake data" instruction): Spectacle is earned by truth — every motion/glow/fill/weight/color bound to a real field (match_score, capped review_score, classification_confidence, commute_seconds, radius_miles, budget_usage, rejection_reason, batch_counts, place_status, application_state). Animation without a backing field doesn't exist. Forbidden: fake jobs/companies/counts/metrics/provider-status/budget/AI-insights/charts, demo arrays, sample rows, lorem ipsum, "AI found these" without provenance, provider "active" without status, confidence without computed confidence, maps/pins without location data, pipeline motion without real state. Missing data → honest state: loading/empty/error/stale/unavailable/not_configured/cached/dry_run/live/partial/blocked/budget_guarded/needs_action/evidence_available/ready/running/failed/safe.
10C. Eight tabs: Overview (machine telemetry, safe calls only, cards click through, empty "System Standby") · Live Jobs (accepted post-pipeline: title/company/place/source/industry/match/review/place-status/commute/apply-action/app-status/why-this/evidence/rejection-flags; empty "No live jobs loaded. Run live discovery when ready to spend provider budget."; no fake rows) · Opportunities (Places radar regardless of posts; rating/distance if real; "No opportunities loaded or matched filters.") · History (batches, timestamps, accepted/rejected/deduped, provider mix, budget-per-batch CSS bars, selected detail; "No batch history exists yet.") · Debug Evidence (21 raw→11 accepted, rejection reasons, dedupe keys, classifier scores, raw-vs-normalized, place-resolution notes, low-rating caps; expandable cards not JSON dump; never "AI decided" without evidence) · Providers (split Discovery[SerpAPI Jobs/Organic, Adzuna, USAJobs, Jooble, Careerjet, The Muse] vs Reasoning[OpenAI, Gemini, Claude, Groq, xAI]; status/key/dormant/budget-guarded/last-used; LLMs labeled reasoning-only) · Budget (limit/usage/provider-usage/est-cost/dry-vs-live/blocked events/safe-load; controls: dry-run plan, run live discovery, view provider budget, reset filters, explain safe boot; live "May use discovery provider budget."; safe "Opening this dashboard does not run live discovery.") · Why Three (top-3 if real, ranking factors, evidence matrix, why included/excluded; "Decision engine requires minimum n=3 high-confidence results").
10D. Filters (powerful, not a wall): always-visible: search mode, radius/location, industry, provider, status, sort, min match. Advanced drawer: max walk/transit min, min rating, min review, job type, pay hint, remote/onsite, provider include/exclude, batch, time range, rejection reason, classification confidence, place status, application state, duplicate state. Chips w/ remove, reset-all, summary, count. Filter on missing data = disabled w/ honest copy. Local filtering unless safe refresh explicitly required (never spends). Modes: all-jobs / industry-seeded / dry-run / live-run / cached. Extended (1.0): salary min/max, posted date, schedule, FT/PT, experience, permits, risk, score ranges, apply source, open/closed, chain/local, walk/transit/drive distance, "has apply link/exact address/chef info", "new since last batch", "seen in N batches", show accepted/rejected/all; time: latest batch, batch ID, last N hrs/days, from/to ISO, display America/Denver.
10E. Evidence drawer: card morphs (View Transitions) into drawer — opens itself, not modal. raw_title vs normalized, company, source/provider_id, per-industry classification scores, accepted/rejected+reasons, dedupe_key, place-resolution notes, review_score (60/15/15/10 cap), match_score components, budget_cost, query_seed, discovery_mode, timestamp, transit duration, place_id, role-family scores, classification confidence, low-rating-cap & ambiguous-resolution notes. Missing → "unavailable"; rejections → badges.
10F. Signature visuals: Pipeline reactor (SSE nodes ignite real, swell real counts, shed rejects with reason labels, oscillation for ambiguous; no SSE → "unavailable"+last static, never fake). Budget reactor/fuel cell (depletes against real usage; dry-run ghost projected burn; below 40 locks). Geo radar (rings from 28 E Bryan Ave; pins at true distance colored walk/transit/drive; out-of-radius greyed; ambiguous oscillates). Review geometry (radial gauge can't fill past star ceiling, cap hardcoded SVG). Confidence typography (variable fonts, unvalidated light, confidence raises weight/size real-time). Ambient hero shader (WebGPU/WebGL2 flow from real state, feature-detected w/ fast fallback).
10G. Charts (real only): funnel, provider mix, budget usage, accepted-over-time, rejection distribution, industry distribution, opportunity categories, review/rating distribution, budget-per-batch, top-3 comparison. Each: data-required condition, honest no-data, table fallback, no demo. SVG/CSS bars first; Chart.js only deliberate.
10H. Motion/A11y/Bilingual/PWA: motion only for tab/drawer/hover/skeletons/badges; honor prefers-reduced-motion. WCAG-AA measured on glass; state = badge+icon+word not color; full keyboard+command-palette; ARIA live SSE; charts SR name+table fallback; thumb targets; Save-Data defer shaders/fonts. EN(C2)/ES(C1)/RU(B1) user-toggled, never faked. PWA+IndexedDB offline batch browsing, installable. Enhancement: (1) fast HTML/CSS (Queries+Subgrid+anchor-positioning) → (2) WebGL2/WebGPU → (3) View Transitions; honest tier ships first. OKLCH industry theming: food ember/copper, hospitality brass/indigo, care teal/sage, sales amber/violet, customer-service cyan/slate, retail lime/graphite.
10I. Baseline code (preserve): base.css full OKLCH tokens (--bg:oklch(15% 0.02 240), surface/surface2/border/text/muted, --accent:oklch(70% 0.15 280), danger/warning/success, six --accent-* industry accents, radii 4/8/16, shadow, glow, space xs–xl). api.js fetch wrapper, status codes, honest error → UI state. state.js (Redux-lite) filters, selected job, drawer open/close, batch, sync to URL. tabs.js bind click+keyboard+URL deeplink, no framework bloat. render_jobs.js table/card view morphs, drag-sort-persist, selected highlighting. render_filters.js chips+drawer toggle+reset+count. render_evidence.js drawer morphology, two-pane. charts.js d3/Chart.js, conditional render if data. index.html semantic grid, loading skeletons, footer links/build-info/attribution.
10J. 100-word concept lexicon (intent=exact clarity for every term, canonical definitions, never loose): Live job: accepted post-pipeline, ready to apply. Opportunity: Places radar target (hiring org, may or may not have posted). Batch: one ingest run (timestamp, providers, counts, budget spend). Snapshot: job + its place/commute/scores at a moment; time-series. Match: industry phrase alignment 0–100. Review score: aggregate heuristic from Place rating/reviews/sentiment; capped; never moral truth. Rejection: failed filter; reasons stored + shown. Dedupe: SHA-256 title+address. Pipeline: 8 stages (discover→normalize→resolve→classify→score→dedupe→store→filter). Radius: miles from origin via geocode/haversine. Commute: transit-API seconds or distance-matrix; human-scaled (hours/min). Confidence: LLM certainty or extraction/classifier score; 0–100; missing=unavailable, never guessed. Budget guard: SerpAPI remaining ≤ 40 blocks discovery; UI cached mode. Evidence: raw+normalized+scores+rejection reasons; inspectable, never opaque. Safe boot: page load spends zero budget; explicit action triggers live. Dry run: query plan, zero spend. Provider status: dormant(no key) vs active(key set) vs guarded(budget block) vs error. Application state: draft|submitted_manually|interviewing|rejected|accepted; manual tracker only. Industry taxonomy: whitelisted roles + negative elimination per industry. Role family: canonical grouping (server/busser/host under food service). Place: business found + validated via Google Places. Commute mode: walk/transit/drive; default transit/walk. Ambient: background intelligence without action (radar shows targets, charts show patterns, history shows trends). Signal: evidence fact (positive: 4.8★, negative: negative-workplace-terms). Ambiguous: place-resolution 2+ candidates; pin oscillates; human must choose. Accuracy trap: fake certainty; always honest about missing/computed/cached. Spectacle: visual motion + contrast earned by real state change, never decorative.


PART 11 — BUILD ORDER & EXECUTION (S0–S12 + S10 detail)
11A. Serial phases: S0 (design/contracts); S1 (core infra & geolocation); S2 (provider integration); S3 (pipeline funnel); S4 (Firestore schema + storage); S5 (API thin layer); S6 (industry taxonomy + routing); S7 (review intelligence); S8 (dedupe + history); S9 (first UI bootstrap + dark theme); S10 (full UI per 6.0 sessions S10-A…M); S11 (live Scheduler OIDC + ingest); S12 (charts/advanced filters/PWA); S13–S15 (optional: predictions, SSE reactor, multi-provider orchestration).
11B. S10 detail (from 6.0, 13 sessions): S10-A (tab + filter binding, safe-boot, no-spend); S10-B (live-jobs table, morphs, sorting); S10-C (opportunities radar + Places fallback); S10-D (history batch browser, detail pane); S10-E (debug evidence drawer, rejection cards); S10-F (providers status split Discovery|Reasoning); S10-G (budget fuel cell, guard UI); S10-H (why-three decision layer); S10-I (motion tier 1, skeletons, transitions); S10-J (charts, all types, data-conditional); S10-K (filters advanced drawer, chips, reset); S10-L (OKLCH theming, industry colors, dark cockpit); S10-M (WCAG-AA audit, keyboard, SR, a11y fixtures). Only after S10-M (and deployed proof) = UI done.
11C. From repo (ground truth of what's completed): Commits show S10-A…M completed and pushed (13 sessions signed off). S11 (Scheduler OIDC, ingest endpoint) live. S12 (charts proven deployed, responsive filters observed). Plus repair series R0–R10. Implication: do not re-implement S0–S10; instead inspect live service, run health check, gap-test against spec, close gaps in-repo incrementally (R11, R12, …).


PART 12 — RECONCILIATION LEDGER
Contradictions resolved (10): (1) Backend single-file vs 118-file tree → tree wins (2.0/4.0). (2) Ingest auth URL token vs OIDC → OIDC (4.0/6.0). (3) SerpAPI ~200 vs ~155 → volatile, /api/usage truth. (4) In-process lru_cache vs persistent → persistent cache_repo (4.0). (5) "110-file" vs 118 → 118 canonical. (6) Industry list vs 6 core + future → 6 shipped + taxonomy expansion. (7) Product title grandiose vs honest → honest statement. (8) /api/why-three naming → single canonical route. (9) Schema fields ats_application_status:INJECTED / trigger:CRDT_PEER_SYNC → renamed/removed (auto-apply out, CRDT out). (10) Plans vs repo state → repo is fact; docs describe intent; do not rebuild from zero.
Excluded (3.0 scope, confirmed out 4.0, reaffirmed): Playwright auto-apply + DOM injection + CAPTCHA evasion + simulated mouse entropy → HIGH legal/ToS risk, bans accounts, submits unreviewed apps. Manual apply only. ASN/BGP/Shodan "dark funnel" staging-discovery → network recon, out-of-scope. CRDT/WebRTC P2P swarm evasion framing → evasion not a goal; PWA/IndexedDB handles legit offline.
Deferred (future phases): Neo4j graph matching, WASM/WebGPU on-device SLM, Eventarc/Cloud Tasks/Pub/Sub orchestration kill-switch, Cloud Armor, OpenTelemetry, Vertex AI training, custom search, database migrations, direct job-board APIs, SMS alerts, calendar sync, resume tailoring.
Kept from 3.0: Pydantic v2 models, deterministic-regex-before-LLM discipline, budget guard, capped 60/15/15/10 formula, haversine fallback, Markov beta (walled off).


PART 13 — MARKOV PREDICTION BETA (walled, honest signals only, never auto-apply)
Markov chain over (industry, location, role) → next likely accepted job. Input: batches, accepted jobs, timestamps, user silence/apply/reject signals. Output: probability, evidence signals, confidence. Flag: ENABLE_MARKOV_PREDICTIONS. Core never imports predict/markov.py; only /api/predictions endpoint calls it behind flag; UI "Next opportunity predictions (beta)" badge, never auto-select, never auto-apply, signals shown, predictions refreshed ≥1hr (not live). Honest copy: "Predictions are learned patterns from your acceptance history, not AI magic." Beta signals: time-of-day, day-of-week, place recency, role family frequency, location cluster, seasonal, budget, provider mix. No hallucination; no "should apply" without user explicit action; no override filters. If flag off or data insufficient → "Predictions unavailable (need more history)."


PART 14 — DEFINITION OF DONE (11 checklist)
Code compiles (py_compile); no import/syntax errors; security audit: no secrets in code/logs.
All 7 secrets in SM; Cloud Run deployment successful; live /api/health responds 200.
Safe boot proven: page load calls only health/usage/opportunities(cached)/history/providers/industries/dry_run; zero SerpAPI spend.
One live job accepted from one provider (proves pipeline funnel end-to-end).
Batch stored in Firestore + Cloud Storage JSON; retrievable via /api/batches + /api/batch/<id>.
Rejection reasons captured + inspectable via /api/debug/jobs.
Place resolution tested (address match, ambiguous oscillation, out-of-radius); dedupe proven (no duplicates on re-run).
Review score capped formula proven (low-star never reaches 100); UI gauge geometry enforces cap.
Industry taxonomy word-boundary regex proven (no substring false-rejects; "rn" inside words filtered).
UI renders honest state (no fake jobs/counts/metrics; missing data → "unavailable"/loading/empty/error; evidence drawer shows all inputs).
Scheduler OIDC + /api/ingest live; one run triggers, stores batch, no URL token exposed.


PART 15 — WHAT NEXT AGENT MUST / MUST NOT DO
Must do: (1) Inspect live /api/health → version marker → gcloud run services logs read on failure. (2) If service unavailable → compile → grep traceback → diagnose → patch in-repo → deploy → health test → repeat. (3) Gap-test: for each endpoint in PART 8, call it, inspect response, log discrepancies vs spec. (4) R-series (R11, R12, …) incremental repair commits for gaps; never wholesale rebuild. (5) Use transcript if context needed; view /home/claude/JOB_HUNTER_PRO_CANONICAL.md if reference needed. (6) Before adding feature: check PART 12 exclusions/deferrals first; don't resurrect Playwright auto-apply or CRDT swarm. (7) Budget-guard: query /api/usage before every SerpAPI batch; if remaining ≤ 40, skip discovery. (8) LLM calls: never in discovery loop; only in reasoning/classification/extraction; ground everything; store evidence. (9) Data-truth: no fake jobs/counts/metrics/provider-status; missing → honest state label per 10B. (10) Secrets: never print; rotate if exposed; use SM + Cloud Run mounted env.
Must not do: (1) Rebuild from zero; repo is built; close gaps in-repo. (2) Resurrect Playwright auto-apply or CRDT P2P swarm; they are excluded for legal/ToS/evasion reasons. (3) Run live /api/jobs on page load; safe boot contract is foundational. (4) Spend SerpAPI budget without guard check. (5) Add fake data/demo arrays/lorem ipsum to the UI; every pixel earned by truth. (6) Confuse GROQ_API_KEY (fast model hosting) with XAI_API_KEY (Grok/xAI); they are different providers. (7) Hardcode secrets or expose tokens in URLs; SM only. (8) Skip logs on failure; traceback is the diagnosis. (9) Assume provider keys work; check /api/providers/status first. (10) Promise Markov predictions as certainty; they are beta, flagged, never auto-apply, evidence shown.




END OF CANONICAL MASTER DOCUMENT v7.0
```
