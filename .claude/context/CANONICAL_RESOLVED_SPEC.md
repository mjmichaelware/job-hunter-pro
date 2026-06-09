# Canonical Resolved Spec — Job Hunter Pro

Single source of truth derived from `DOCUMENT_CONTRADICTION_MATRIX.md`. Subsequent map files (`CODEBASE_INDEX`, `ROUTE_MAP`, `DATA_FLOW_MAP`, `API_CONTRACTS`, `UI_CONTRACTS`, `PROVIDER_MATRIX`) compare the actual repo against this spec. `BUG_LEDGER.md` records gaps. `FINAL_PATCH_PLAN.md` proposes fixes.

When this spec conflicts with any raw doc, **this spec wins**. When this spec conflicts with `CLAUDE.md` / `PROJECT_DIGEST.md`, the project-level instructions win and this spec is updated to match.

---

## 0. Identity & environment

- Owner: Michael Ware.
- Repo: `/workspaces/Job_Hunter_Platform/job-hunter-pro` (Ubuntu); `~/Workspaces/Job_Hunter_Platform/job-hunter-pro` (Termux mirror).
- GCP project: `ai-job-agent-498702`. Cloud Run service: `job-hunter-pro`. Region: `us-central1`.
- Runtime: Flask + Gunicorn on Cloud Run; Python 3.11+.
- Dev: Android ARM64 Termux and Ubuntu proot.
- Email of record: `michaelware360@gmail.com` (per `PROJECT_DIGEST.md`).

## 1. Hard, never-negotiable rules

These are reflected in `CLAUDE.md` and reaffirmed here.

1. Never print, hardcode, commit, or expose secrets. Provider keys live in Secret Manager only.
2. Never put tokens in Scheduler URLs.
3. `/api/ingest` is protected by Cloud Scheduler OIDC. Do not call it unless Michael explicitly says to.
4. Do not call live `/api/jobs` (without `dry_run=1`) unless Michael explicitly says to.
5. Do not commit, push, or deploy unless Michael explicitly says to.
6. LLM providers are enrichment / classification / reasoning only — never job discovery.
7. Page boot must not spend live provider quota. Only safe endpoints + `?dry_run=1`.
8. No fake telemetry, jobs, provider counts, logs, charts, or success.
9. Inspect current code before patching; never blind-regex large files.
10. Compile before deploy; run `bash .claude/scripts/safe_local_proof.sh` before any deploy decision; after deploy, check `/api/health`; if health fails, check logs.

## 2. Architecture spine (canonical)

- **Persistence:** Firestore Native (free tier, confirmed live). Legacy GCS JSON archives may exist as read-only artifacts. **No Neo4j** (deferred, never created in current scope).
- **No CRDT, no WebRTC P2P, no WebGPU SLM, no Playwright auto-apply, no Cloud Armor / Eventarc / Cloud Tasks** in current scope.
- **Decoupled file tree** per Doc 2/4 is the target. Single-responsibility modules. The legacy fat `api/index.py` exists for compatibility and is being decomposed into `api/<route>.py` blueprints + a Flask factory.
- **Discovery vs reasoning split is physical:** `providers/search/` for retrieval; `providers/reasoning/` for LLM enrichment. The two must not cross.

## 3. Industry routes (canonical = 6)

| Key | Notes |
|---|---|
| `food_service` | Server / busser / host / dishwasher / cook etc. Strict token-boundary regex to avoid the historical `rn`-substring false-reject bug. |
| `hospitality` | Hotel F&B, banquet, front desk, housekeeping. |
| `sales` | Inbound, retail floor sales, account exec. |
| `customer_service` | Inbound support, scheduling, call-center. |
| `care_social` | Peer support (CPSS), BHT, case aide, recovery coach. Credential-aware. |
| `retail_ops` | Retail, warehouse, logistics. |

Doc 1's longer list ("12 industries") is post-core expansion. Doc 3's 4-industry subset is rejected as incomplete.

## 4. Providers (canonical)

### 4.1 Discovery / retrieval (7 + Google Places)
1. SerpAPI Jobs
2. SerpAPI Organic
3. Adzuna
4. USAJobs
5. Jooble
6. Careerjet
7. The Muse
8. Google Places / opportunities (geo — nearby business radar, not job listings per se)

Excluded: Doc 3's **ASN dark funnel via Shodan** — unauthorized recon; rejected outright.

Each provider is one file under `providers/search/<name>.py`, implementing a common ABC that returns a normalized `SearchResult`. Provider becomes "dormant" if its env key/secret is absent. The Muse needs no key → available day-one.

### 4.2 LLM reasoning (5)
1. OpenAI (`providers/reasoning/openai.py`)
2. Gemini (`providers/reasoning/gemini.py`)
3. Claude (`providers/reasoning/claude.py`)
4. Groq (`providers/reasoning/groq.py`) — Groq, not Grok. Distinct from item 5.
5. xAI / Grok (`providers/reasoning/xai.py`)

These classify / extract / score over text already retrieved. They never produce a candidate job listing of their own. Their grounded-search variants (Gemini Grounding, OpenAI web search, Claude web search, xAI web) are off by default and out of current scope.

## 5. Budget policy

- Threshold: `SERPAPI_MIN_SEARCHES_LEFT = 40`. Below threshold → skip SerpAPI discovery, return budget-guarded status, UI shows blocked-reactor state with cached-history fallback.
- Per scheduled batch: 4 SerpAPI calls. 4 batches/day (cron `0 */6 * * *`). 16 calls/day, 112/week.
- Live `serpapi_account_status` is fetched via `/api/usage`; the call itself does not count against discovery quota.
- Per-provider quotas configurable in env / config; never hardcoded in route handlers.

## 6. Live jobs visibility — the central defect rule

- Real provider hits must remain visible even when place / radius / transit resolution is incomplete.
- Missing-resolution becomes `resolution_flags` / `needs_resolution`, NOT hard rejection.
- Rejection reasons are still produced for actually-invalid candidates: `not_food_service`, `not_in_industry`, `ambiguous_place_resolution`, `duplicate`, `provider_error`, `budget_guard`, `missing_source_url`.
- UI renders three groups: **accepted**, **unresolved** (with flags), **rejected** (with reasons, in Debug Evidence tab).
- Provider fanout is fair: each available provider attempts before any single provider fills the raw cap. Per-provider per-batch cap < global raw cap.
- Source URL / apply URL preserved on every job that has them.
- Provider breakdown counts (raw, accepted, unresolved, rejected) are truthful and per-provider.

## 7. HTTP endpoint surface

### 7.1 UI-consumer surface (11 — frontend calls these)
| Endpoint | Safe boot? | Notes |
|---|---|---|
| `GET /api/health` | yes | Version marker + provider-enabled flags. |
| `GET /api/usage` | yes | SerpAPI account status, provider usage, budget remaining. |
| `GET /api/jobs?dry_run=1` | yes | Query plan, zero discovery spend. |
| `GET /api/jobs` | NO (explicit user action) | Live discovery. Spends provider quota. |
| `GET /api/opportunities` | yes (cached) | Google Places radar. |
| `GET /api/history?hours=N` / `?from=&to=` | yes | Stored batches. |
| `GET /api/research/place` | explicit only | Place Details fetch. |
| `GET /api/providers` (status) | yes | Per-provider config status (no secrets). |
| `GET /api/industries` | yes | Industry taxonomy metadata. |
| `GET /api/applications` | yes | Manual application tracker CRUD. |
| `POST /api/ingest` | **NEVER from UI** | OIDC-protected. Scheduler only. |
| `GET /api/why-three` | explicit only | Top-3 ranking explainer. |

### 7.2 Admin / debug surface (additional, per Doc 2/4)
- `GET /api/_surface` — route inventory + placeholder_blueprint flag.
- `GET /api/debug/jobs` — accepted/rejected/unresolved evidence.
- `GET /api/batches` / `GET /api/batch/<id>` — batch history.
- `GET /api/search/providers/status` and `GET /api/search/federated` — only if the federated router blueprint is wired in code.

Whether each endpoint actually exists is resolved in `ROUTE_MAP.md` against the live code.

## 8. Default load contract (safe boot)

On `DOMContentLoaded`:
- Initialize state, bind tabs, bind filters.
- Call only: `/api/health`, `/api/usage`, `/api/providers`, `/api/industries`, `/api/opportunities` (cached path), `/api/history?hours=24`, `/api/jobs?dry_run=1`.
- Never call on boot: live `/api/jobs`, `/api/ingest`, paid provider execution, any SerpAPI-burning path.

Live discovery requires an explicit user click on a clearly labeled "Run live discovery (may spend provider budget)" control. Confirm before firing.

## 9. UI/UX manifest (Doc 5 + Doc 6 reconciled)

- **8 tabs**: Overview, Live Jobs, Opportunities, History, Debug Evidence, Providers, Budget, Why Three.
- **No fake data**: forbidden copy list per Doc 5 (`sample_job`, `demo_metric`, `lorem_ipsum`, `fake_company`, `magic_AI`, `provider_active_without_status`, "AI found these jobs" without evidence, etc.).
- **Empty / loading / error / stale / partial / unavailable / not-configured / budget-guarded** states are first-class. Every render path has one.
- **State badges** with text + icon, never color alone (accessibility).
- **Evidence drawer** for each job/opportunity: raw_title, normalized_title, company, source provider id, industry scores, accepted/rejected status, rejection reasons, dedupe key, place resolution notes, review/match scores, budget cost, query seed, discovery mode, timestamp.
- **Review-score gauge** is geometry-capped at the value the rating allows (60/15/15/10 formula).
- **Budget reactor**: dry-run shows projected burn; live shows actual; hard-lock visible below `SERPAPI_MIN_SEARCHES_LEFT=40`.
- **Provider tab** split: Discovery vs Reasoning. LLMs labeled "reasoning only — never discovery".
- **Why Three tab**: only ranks when ≥3 valid candidates exist; otherwise "decision engine requires minimum n=3".
- **SSE pipeline reactor**: only animates when a real SSE endpoint exists; otherwise renders "stream unavailable" — never fake counts.
- **Bilingual**: pass-through English + Spanish where the source supplies it; no machine translation. Defer toggle to S10-L.
- **PWA + IndexedDB** deferred to S10-K.
- **WebGPU shaders / on-device SLM** deferred (progressive enhancement, feature-detected, not core).

## 10. Storage / data model (canonical entities)

Firestore Native collections (subset of Doc 2's blueprint, scoped to current need):

- `batches/{batch_id}` — created_at, trigger, version, budget, providers_used, rules, counts.
- `jobs/{canonical_key}` — title, company, industry, role_family, role_tags, source_url, apply_url, place_id, first_seen, last_seen, seen_count, **resolution_flags** (array of missing-resolution reasons), needs_resolution (bool).
- `jobs/{canonical_key}/snapshots/{ts}` — salary, description, commute_seconds, radius_miles, match_score, review_score, consistency, risk, batch_id.
- `places/{place_id}` — name, address, lat, lng, types, rating, review_count, business_status, updated_at.
- `places/{place_id}/reviews/{id}` — rating, text, author, relative_time, source_url.
- `rejections/{batch_id}/{id}` — reason, details, raw_title, raw_company.
- `applications/{job_id}` — status, notes, created_at, updated_at. Manual tracker only.
- `api_usage/{ts}` — provider, endpoint, cost_units, success, error.
- `industries/{key}` — label, queries, match, negative, role_families, credentials, background_sensitive.
- `cache/{hash}` — provider, query, industry, results, created_at, ttl. Stops API re-spend.

Canonical dedupe key for jobs: `sha256(normalized_title + normalized_company + normalized_address_or_place_id)`.

## 11. Security model

- OIDC service account: `job-hunter-scheduler@ai-job-agent-498702.iam.gserviceaccount.com` granted `roles/run.invoker`.
- `/api/ingest` verifies OIDC audience matches Cloud Run URL and email matches scheduler SA.
- Secrets in Secret Manager only, surfaced as env vars at runtime via Cloud Run `--set-secrets`.
- `add_key.sh` is the operator path for adding/rotating provider keys.
- GCS access uses `google-auth` `AuthorizedSession` for auto-refresh; no raw metadata-token use.
- Logs scrubbed of secrets. Never echo key values, never log full request URLs that might contain tokens.

## 12. Build stages (canonical)

Adopted from Doc 4 §C, with S10 sub-split from Doc 6:

| Stage | Output |
|---|---|
| S0 | Scaffold tree, OS layer healthy. |
| S1 | core/ + models/. |
| S2 | industries/ (6 routes). |
| S3 | providers/ (7 search + 5 reasoning). |
| S4 | geo/ (Maps family). |
| S5 | store/ (Firestore repos + cache). |
| S6 | pipeline/ (normalize, resolve_place, score, classify, dedupe, **reject vs flag**, run). |
| S7 | search/ (federated fanout + budget guard + usage tracker). |
| S8 | ingest/ (OIDC + scheduler handler). |
| S9 | api/ + app.py factory. First local boot. |
| S10 | web/ split into S10-A..S10-M per Doc 6. S10-A baseline reportedly committed. |
| S11 | scripts/ (add_key, deploy, scheduler_oidc, seed). |
| S12 | Deploy. Health 200. Endpoint proofs. Scheduler OIDC. One stored batch. |

Post-core (P-list): add free provider keys, wire LLM enrichment, resume tailoring, Neo4j/Markov/PWA — all opt-in, all behind flags, none active during this audit/repair cycle.

## 13. What this spec explicitly EXCLUDES from current scope

- Auto-apply / Playwright DOM injection.
- ASN dark funnel / Shodan recon.
- Neo4j AuraDB.
- CRDT P2P / WebRTC swarm.
- WebGPU on-device SLM inference.
- Cloud Armor / Eventarc / Cloud Tasks / OpenTelemetry / Pub/Sub kill-switch.
- LLM grounded-search variants as discovery sources.
- Markov vacancy prediction (P5, flag-gated).
- PWA / IndexedDB offline mode (S10-K).
- SSE pipeline animation without a real SSE endpoint.
- Any UI feature that fabricates data.

## 14. Definition of "core fix done" (acceptance criteria)

- [ ] `/api/health` returns 200 with version marker.
- [ ] `/api/jobs?dry_run=1` spends zero SerpAPI.
- [ ] `/api/jobs` (explicit) fans out across all available discovery providers fairly; no single provider monopolizes the raw cap.
- [ ] Jobs missing place / radius / transit return as `unresolved` with `resolution_flags`, not as silent rejects.
- [ ] `/api/providers` and `/api/industries` report truthful status.
- [ ] UI default load calls only the safe-boot endpoint set; no SerpAPI on page load.
- [ ] UI renders accepted + unresolved + rejected truthfully with evidence.
- [ ] Provider breakdown counts are real and per-provider.
- [ ] `source_url` / `apply_url` preserved where present.
- [ ] No secrets in code, logs, URLs, or commits.
- [ ] `bash .claude/scripts/safe_local_proof.sh` passes.

---

## 15. Authority hierarchy when this spec is ambiguous

1. `CLAUDE.md` / `PROJECT_DIGEST.md` (project-level instructions) — wins.
2. This spec (`CANONICAL_RESOLVED_SPEC.md`).
3. Current code (what actually runs) — source of truth for inventory questions; defects feed `BUG_LEDGER.md`.
4. Doc 5 / Doc 6 — UI/UX authority within scope.
5. Doc 4 — architecture / scope reconciliation.
6. Doc 2 — original decoupled blueprint.
7. Doc 1 — historical FACTS.
8. Doc 3 — ambition / explicitly subordinated by Doc 4.

If a new doc-vs-doc dispute appears, add a row to `DOCUMENT_CONTRADICTION_MATRIX.md`, decide the resolution, and update this spec.
