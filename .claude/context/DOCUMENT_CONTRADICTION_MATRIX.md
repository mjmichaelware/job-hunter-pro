# Document Contradiction Matrix — Job Hunter Pro

Cross-comparison of `.claude/context/AI_JOB_AGENT_1.txt` through `AI_JOB_AGENT_6.md`. Documents are not automatically true; this matrix captures every material conflict and the proposed resolution.

Each row: contradiction ID, topic, doc-by-doc claim, **resolution**, evidence/rationale. Resolutions feed into `CANONICAL_RESOLVED_SPEC.md`.

Authority weighting (used as tiebreaker, not as an automatic winner):
- Doc 4 = reconciliation / build order (S0-S12) — strongest for architecture & scope.
- Doc 5 = supreme UI/UX authority (per project instructions).
- Doc 6 = S10 execution sequencing (sessions S10-A..S10-M).
- Doc 1 = historical FACTS (versions v3/v5, bugs found, env, providers seeded in Secret Manager).
- Doc 2 = original decoupled blueprint (Firestore Native, 118-file tree).
- Doc 3 = ambition / "Omega" — explicitly subordinated by Doc 4.
- **CLAUDE.md / PROJECT_DIGEST** = current canonical project instructions; override any doc claim that contradicts them.
- **Current code** = source of truth for what actually runs.

---

## C1. Auto-apply / Playwright headless DOM injection

| Doc | Claim |
|---|---|
| Doc 3 (§V) | Mandatory Playwright Stealth DOM mutation, auto-fills resume + contact, simulates mouse entropy, bypasses CAPTCHA. |
| Doc 4 (§A) | **EXCLUDED from core.** Legal/ToS risk, account-ban risk, submits applications never reviewed. Apply tracking stays MANUAL. |
| Doc 5 | Headline mentions "Headless Execution" but body has zero auto-apply UI; "Applications" tab is a manual tracker. |
| Doc 6 | Silent. |
| CLAUDE.md | Silent (does not authorize auto-apply). |

**Resolution: Doc 4 wins. No auto-apply, no Playwright, no headless DOM injection.** Doc 3's auto-apply is rejected. Doc 5's "Headless Execution" tagline is decorative copy, not a build requirement; the actual tab schema is manual.

**Evidence:** Doc 4 §A explicit exclusion + safety rationale; Doc 5 body schema for Applications tab specifies status tracking only (no submit action).

---

## C2. Neo4j AuraDB graph database

| Doc | Claim |
|---|---|
| Doc 3 | Mandatory bipartite Cypher topology; "Neural Resonance Score" via point.distance + skill weights. |
| Doc 2 | Firestore Native only. |
| Doc 4 (§A) | **DEFERRED.** "A second database to run and pay for; Firestore covers the matching need now." |
| Doc 5 | Mentions Markov + resonance match but in UI-only terms. |
| Doc 6 | Silent. |

**Resolution: Firestore Native is the persistence backend. Neo4j is deferred post-core (Doc 4's P-list).**

---

## C3. CRDT P2P swarm, WebRTC, WASM edge inference

| Doc | Claim |
|---|---|
| Doc 3 | Yjs/Automerge + WebRTC DataChannels + WebGPU on-device SLM. |
| Doc 4 (§A) | **DEFERRED.** Distributed-systems machinery for a fleet of devices; Michael is one person. |
| Doc 5 | Mentions "WebGPU on-device SLM preview" but feature-gated, with fallback. |
| Doc 6 | Treats premium GPU/SSE/edge tier as S10-J ("Premium Motion and Visual Enhancement Tier"), not core. |

**Resolution: Doc 4 wins. No CRDT, no P2P, no WebGPU SLM in current scope.** Doc 5's WebGPU mention is aspirational tier-2 progressive enhancement (per Doc 6 sequencing).

---

## C4. Cloud Armor / Eventarc / Cloud Tasks / OpenTelemetry / Pub/Sub kill-switch

| Doc | Claim |
|---|---|
| Doc 3 | All mandatory: Cloud Armor Layer-7 deny rules, Eventarc async enrichment, Cloud Tasks throttle queue, Pub/Sub billing kill-switch. |
| Doc 4 (§A) | **DEFERRED until core ships.** "Production-hardening for large-scale, under-attack traffic." |
| Doc 5 | UI-level budget reactor only (no GCP-side enforcement). |

**Resolution: Doc 4 wins. Defer all of these.** Application-side budget guard (Doc 1's `SERPAPI_MIN_SEARCHES_LEFT`) is sufficient for current scope.

---

## C5. SerpAPI search quota — 200 vs 155

| Doc | Claim |
|---|---|
| Doc 1 | "~200 SerpAPI searches left." |
| Doc 4 (§B) | "~155 SerpAPI searches left." |

**Resolution: Both are stale snapshots.** Authoritative source is live `/api/usage` (Doc 1 specified this exact endpoint to wrap `serpapi_account_status`). Planning floor: assume ≤150 searches. Budget policy is durable: 4 SerpAPI calls × 4 batches/day = 16/day. Threshold `SERPAPI_MIN_SEARCHES_LEFT = 40` (consistent across docs).

---

## C6. Industry routes — count and names

| Doc | Claim |
|---|---|
| Doc 1 | "Restaurants, hospitality, behavioral health, social services, customer service, retail, warehouses, delivery, healthcare support, education, trades, tech/admin" (illustrative, ~12). |
| Doc 3 | Lists 4: food_service, hospitality, care_social, customer_service. |
| Doc 4 (§B) | **6 industries:** food_service, hospitality, sales, customer_service, care_social, retail_ops. |
| Doc 5 | Same 6: food_service, hospitality, care_social, sales, customer_service, retail_ops. |
| Doc 6 | "Industry" filter referenced; same 6. |

**Resolution: 6 industry routes (Doc 4 + Doc 5 agree).** Doc 1's longer list is "expansion targets, later". Doc 3's 4 is a subset.

---

## C7. Discovery providers — set and Doc 3's "ASN dark funnel"

| Doc | Claim |
|---|---|
| Doc 1 | SerpAPI Jobs, SerpAPI Organic, Google Custom Search (if enabled), LLM grounded providers. |
| Doc 2/4 | **7 search providers:** SerpAPI Jobs, SerpAPI Organic, Adzuna, USAJobs, Jooble, Careerjet, The Muse. |
| Doc 3 | SerpAPI Jobs, Utah Open Data, **ASN dark funnel via Shodan**, The Muse (4 — "dark funnel" introduced here only). |
| Doc 5 | Discovery tab shows: SerpAPI Jobs, SerpAPI Organic, Adzuna, USAJobs, Jooble, Careerjet, TheMuse. |
| CLAUDE.md | "SerpAPI Jobs, SerpAPI Organic, Adzuna, USAJobs, Jooble, Careerjet, The Muse, Google Places/opportunities." |

**Resolution: 7 discovery providers (Doc 4 + Doc 5 + CLAUDE.md agree) + Google Places/opportunities as the "nearby business radar" surface (geo, not job-listing).** Doc 3's **ASN dark funnel via Shodan is REJECTED** — unauthorized network reconnaissance has no place in a personal job-hunter app and violates the safety law on quota + scope. Utah Open Data is acceptable as a regional add-on but is not in the canonical 7.

---

## C8. LLM reasoning providers — count and role

| Doc | Claim |
|---|---|
| Doc 1 | OpenAI, Gemini, Claude, Groq, xAI present; clarifies they do NOT search unless explicitly grounded. |
| Doc 4 (§B) | "5 LLM enrichment providers (reasoning only, never discovery)." |
| Doc 5 | Reasoning tab: OpenAI, Gemini, Claude, Groq, xAI. |
| CLAUDE.md | "LLMs are enrichment/classification only." |

**Resolution: 5 LLM reasoning providers, enrichment/classification only, never discovery.** Consistent across all sources. LLM grounded-search variants (Gemini Grounding, OpenAI web search, Claude web search, xAI web search) from Doc 1 §"Multi-Provider Search Expansion" are explicitly disabled by default per Doc 1's own provider on/off flags; do not enable in current scope.

---

## C9. HTTP endpoint surface — 11 vs 14 vs 17

| Doc | Claim |
|---|---|
| Doc 1 | 14 endpoints listed (incl. `/api/debug/jobs`, `/api/batches`, `/api/batch/<id>`, `/api/research/place`, `/api/search/providers/status`, `/api/search/federated`, `/api/why-three`). |
| Doc 2/4 | 17 endpoints (adds `/api/applications`, `/api/industries`, `/api/research/place`). |
| Doc 5/6 | 11 endpoints UI calls: `/api/health`, `/api/usage`, `/api/jobs`, `/api/opportunities`, `/api/history`, `/api/research`, `/api/providers`, `/api/industries`, `/api/applications`, `/api/ingest`, `/api/why-three`. |

**Resolution: Both lists are valid in different roles.**
- **UI-consumer surface (Doc 5/6):** 11 endpoints that the frontend calls during safe boot or explicit user actions.
- **Full backend surface (Doc 2/4):** 17 endpoints including admin/debug paths.

True endpoint inventory is **whatever the current code actually exposes** (verified in `ROUTE_MAP.md` task). Discrepancies between docs and code become bug-ledger entries; discrepancies between docs and docs are reconciled here by saying both sets are partially correct.

---

## C10. Persistence backend

| Doc | Claim |
|---|---|
| Doc 1 | GCS JSON batches initially; SQL or Firestore/BigQuery later. |
| Doc 2/4 | Firestore Native (free tier, confirmed live). |
| Doc 3 | Firestore + Neo4j AuraDB. |
| Doc 5 | UI assumes Firestore-backed history. |
| PROJECT_DIGEST | Firestore-leaning; legacy GCS may coexist. |

**Resolution: Firestore Native primary** (Doc 2/4/Digest agree). GCS JSON archive is legacy and may exist for prior batches — treat as read-only until a migration plan exists. Neo4j is deferred per C2.

---

## C11. Apply tracker semantics

| Doc | Claim |
|---|---|
| Doc 3 | `INJECTED` state set by Playwright auto-fill. |
| Doc 4 (§A) | **Manual.** User clicks Apply on the real apply URL; app records status. |
| Doc 5 | "Applications" tab: status-only renderer, no submit button. |

**Resolution: Manual apply tracker (Doc 4 + Doc 5 agree).** No auto-fill; no `INJECTED` state.

---

## C12. Page-load behavior (safe boot)

| Doc | Claim |
|---|---|
| Doc 1 | Homepage default calls usage / opportunities / history / dry-run only. No SerpAPI burn. |
| Doc 3 | Same intent (with billing kill-switch fallback). |
| Doc 4 | Same. |
| Doc 5 | Explicit "Safe API Map" — boot calls only health, usage, opportunities (cached), history, providers (status), industries, dry-run. **Forbidden on boot:** live `/api/jobs`, `/api/ingest`, paid provider execution, SerpAPI. |
| Doc 6 | Reinforces Doc 5; live action requires explicit user click. |
| CLAUDE.md | "Page boot must not run paid live discovery automatically." |

**Resolution: Consistent. SAFE BOOT IS LAW.** No live SerpAPI on page load, ever.

---

## C13. /api/ingest protection

| Doc | Claim |
|---|---|
| Doc 1 | Tokens-in-URL is insecure → switch to Cloud Scheduler OIDC; SA `job-hunter-scheduler@…iam` granted `roles/run.invoker`. |
| Doc 2/4 | Same. OIDC, no URL tokens. |
| Doc 3 | OIDC with audience + email verification + Cloud Armor rule restricting `/api/ingest` to internal IP range. |
| Doc 5/6 | UI must label `/api/ingest` as "OIDC-protected, POST-only, not called by UI." |
| CLAUDE.md | "`/api/ingest` must be protected by Cloud Scheduler OIDC." "Do not call `/api/ingest` unless Michael explicitly says to." |

**Resolution: Consistent. Cloud Scheduler OIDC.** Doc 3's Cloud Armor IP restriction is deferred per C4. UI does not call `/api/ingest` and labels it correctly.

---

## C14. Review score formula

| Doc | Claim |
|---|---|
| Doc 1 | Capped formula: rating 60% / count 15% / sentiment 15% / consistency 10%; low rating cannot reach 100. Earlier v5 formula was broken (IHOP 3.7 → 100). |
| Doc 3 | Same 60/15/15/10. |
| Doc 4 | Same; called out as kept-from-Doc-3 discipline. |
| Doc 5 | UI: radial gauge "physically incapable of filling past the ceiling its rating allows." |

**Resolution: Consistent. 60/15/15/10 capped formula, geometry-enforced cap in UI.**

---

## C15. Markov vacancy prediction

| Doc | Claim |
|---|---|
| Doc 3 | Mandatory continuous-time Markov chain on attrition. |
| Doc 4 (§H) | **Loosely coupled beta.** P5 post-core. Own module `predict/markov.py`, own collection `predictions/{place_id}`, own endpoint `/api/predictions`, own UI tab labeled Beta, off by default behind `ENABLE_PREDICTIONS`, never auto-apply. |
| Doc 5 | UI: "Probability Halos" radial glow, distinct from accepted jobs. |
| Doc 6 | Implies post-core. |

**Resolution: Doc 4 wins — Markov is P5 post-core, flag-gated, isolated module, never mixes with accepted jobs.** Doc 5 UI plan applies *only once* the feature ships.

---

## C16. Bilingual support

| Doc | Claim |
|---|---|
| Doc 5 | "Bilingual where the source supports it: English/Spanish, Russian optional, never machine-faked beyond what the source provides." |
| Other docs | Silent. |

**Resolution: Doc 5 wins (it is the UI authority). Pass-through only — surface English + Spanish when the discovery source returns both. No machine translation.** Defer the full toggle UI to S10-L per Doc 6.

---

## C17. PWA / IndexedDB offline mode

| Doc | Claim |
|---|---|
| Doc 3 | PWA + IndexedDB standards. |
| Doc 5 | "PWA shell with IndexedDB-cached batch history." |
| Doc 6 | **S10-K** — explicitly deferred to its own session. |

**Resolution: Doc 6 wins on sequencing. PWA is S10-K, not part of the current live-jobs-visibility fix.** Not blocking.

---

## C18. SSE pipeline stream

| Doc | Claim |
|---|---|
| Doc 3 | SSE pipeline streaming mandatory. |
| Doc 5 | "Pipeline reactor that user can watch breathe", real-time SSE. |
| Doc 6 (§10) | **If SSE endpoint exists, connect on user action; if not, render "pipeline stream unavailable" — do not animate fake counts.** |

**Resolution: Doc 6 wins. SSE is aspirational. Only wire if real endpoint exists. Otherwise render unavailable state — never fake live counts.** Consistent with `CLAUDE.md` ban on fake telemetry.

---

## C19. Sample / demo data in UI

| Doc | Claim |
|---|---|
| Doc 5 | "Forbidden copy: AI_found_these_jobs_without_evidence, sample_job, demo_metric, lorem_ipsum, fake_company, fake_count, magic_AI, instant_match, provider_active_without_status." |
| Doc 6 | Same forbidden list. |
| CLAUDE.md | "Do not fake telemetry, jobs, provider counts, logs, or success." |

**Resolution: Consistent. No fake/demo/sample data anywhere.** Any such code in the current repo is a bug-ledger entry.

---

## C20. Deploy / commit / push gating

| Doc | Claim |
|---|---|
| Doc 3 | Provides a "definitive" copy-paste deploy block. |
| Doc 4 | "No deploy before S12." |
| Doc 6 | "No deploy before S12." |
| CLAUDE.md | "Do not deploy unless Michael explicitly says deploy." |
| CODEX_TO_CLAUDE_HANDOFF | "Do not push unless Michael explicitly says push." |

**Resolution: CLAUDE.md wins. No deploy, no push, no commit without explicit Michael instruction.** Doc 3's block is reference material only; never invoked autonomously.

---

## C21. Cloud Scheduler frequency

| Doc | Claim |
|---|---|
| Doc 1 | Every 6 hours or manual. |
| Doc 3 | `0 */6 * * *`. |
| Doc 4 | 4 batches/day = every 6h, 4 SerpAPI calls each, 112/week. |

**Resolution: Consistent. Cron `0 */6 * * *`, 4 SerpAPI searches per batch.**

---

## C22. Default budget threshold and behavior

| Doc | Claim |
|---|---|
| Doc 1 | `SERPAPI_MIN_SEARCHES_LEFT = 40` (example). |
| Doc 3 | At `<40`: hard lock + UI downgrade to cached history. |
| Doc 5 | Same hard-lock + Houdini squircle "reactor lock." |

**Resolution: Consistent. Threshold = 40. Below threshold: skip SerpAPI discovery; UI shows blocked state with cached-history fallback.**

---

## C23. Resolution flags vs hard reject (live-jobs core defect)

| Doc | Claim |
|---|---|
| Doc 1 | Strict rejection reasons include `no_exact_restaurant_address_resolved`, `radius_unavailable`, `transit_unavailable` → these dropped real jobs. |
| Doc 4 | Implicitly preserves the strict-reject model (no explicit "convert to flag" instruction). |
| Doc 5 | "Live Jobs Tab" must render accepted listings + show "rejection risk flags"; **Debug Evidence Tab** must show rejection reasons as expandable evidence, never silent. |
| Doc 6 | "Real provider jobs must not disappear because address/radius/transit resolution failed. Missing resolution must become resolution_flags, not hard rejection." (also in PROJECT_DIGEST + CLAUDE.md) |
| CLAUDE.md | Same. "All available SEARCH providers must be attempted fairly before one provider fills the cap." |

**Resolution: Doc 6 + CLAUDE.md win — convert hard rejections (missing address/radius/transit) into `resolution_flags` / `needs_resolution` so the candidate stays visible.** This is the central defect under repair. Doc 1's reasons are still rejection reasons for non-resolution failures (not-food-service, ambiguous_place_resolution, budget_guard, duplicate) but missing-resolution becomes a flag, not a hard drop.

---

## C24. Provider fanout / fairness

| Doc | Claim |
|---|---|
| Doc 1 | Federated discovery router with per-provider quotas; no provider monopolizes the cap. |
| Doc 4 | Federated search dedupes by URL/title/company/place. |
| Doc 5 | Providers tab shows per-provider status, "last used", allowed actions; never "active without status." |
| CLAUDE.md | "All available SEARCH providers must be attempted fairly before one provider fills the cap." |

**Resolution: Consistent. Each available provider gets a turn before any single provider fills the global raw cap.** Implementation: round-robin or interleaved fanout; per-provider per-batch cap < global cap.

---

## C25. Houskeeping — duplicate raw document files

| Observation | Detail |
|---|---|
| Current state | `.claude/context/AI_JOB_AGENT_5.md` and `AI_JOB_AGENT_5.txt` are byte-identical (55,393 B). Same for `AI_JOB_AGENT_6.md`/`.txt` (22,571 B). |
| CLAUDE.md references | Only the `.md` variants are loaded. |

**Resolution: Not a contradiction, just stale duplicates.** Defer deletion until after the patch cycle; track as housekeeping low-priority item.

---

## C26. UI tab list — 8 tabs

| Doc | Tab list |
|---|---|
| Doc 5 | Overview, Live Jobs, Opportunities, History, Debug Evidence, Providers, Budget, Why Three. |
| Doc 6 | Same 8. |

**Resolution: Consistent. 8 tabs.**

---

## C27. Identity / contact in Doc 3

| Observation | Detail |
|---|---|
| Doc 3 §V | Hardcodes `michaelware433@yahoo.com` and `(801)-386-4047` into a Playwright injector. |
| PROJECT_DIGEST | User email: `michaelware360@gmail.com`. |
| Doc 3 hardcodes a personal phone in app blueprint copy. |

**Resolution: Doc 3 contact data is REJECTED — wrong email per `PROJECT_DIGEST`, and personal contact never belongs in app code regardless.** Auto-apply is excluded (C1), so this is moot, but flagged as a housekeeping note: never commit personal contact strings.

---

## Cross-cutting reconciliation summary

| Theme | Winner | Losing claims |
|---|---|---|
| Auto-apply / scraping | Doc 4 (manual only) | Doc 3 §V Playwright stealth, Doc 3 ASN dark funnel |
| Graph DB | Doc 4 (Firestore only, Neo4j deferred) | Doc 3 Neo4j mandatory |
| Distributed / edge | Doc 4 (deferred) | Doc 3 CRDT/P2P/WebGPU SLM mandatory |
| GCP hardening | Doc 4 (deferred) | Doc 3 Cloud Armor / Eventarc / Cloud Tasks |
| Discovery providers | Doc 4 + 5 + CLAUDE.md (7 + Google Places) | Doc 3 ASN dark funnel |
| LLM role | Doc 1 + 4 + 5 + CLAUDE.md (enrichment only) | Doc 3 (implicitly conflates) |
| UI behavior | Doc 5 + 6 (safe boot, evidence drawers, no fakes) | — |
| Live jobs visibility | CLAUDE.md + PROJECT_DIGEST + Doc 6 (resolution_flags, fair fanout) | Doc 1's strict-reject defaults |
| Gating | CLAUDE.md (explicit instruction required) | Doc 3 "definitive" deploy block |

---

## How to use this matrix

1. `CANONICAL_RESOLVED_SPEC.md` codifies every "winner" above as the single source of truth.
2. `BUG_LEDGER.md` records cases where current code violates the canonical spec.
3. `STUB_PLACEHOLDER_AUDIT.md` flags any code that materialized a losing claim (e.g. an auto-apply stub, a Neo4j client, a Playwright import).
4. `FINAL_PATCH_PLAN.md` proposes fixes derived from confirmed canonical-spec violations only.

Any future doc-vs-doc dispute should add a new C# row here rather than being resolved silently in code.
