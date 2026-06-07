# Master Blueprint: Job Hunter Pro AI-Orchestrated Local Intelligence Platform

## 1. Project Identity and Core Metadata

This blueprint establishes the authoritative technical and operational framework for **Job Hunter Pro**, a high-persistence, budget-aware intelligence platform. The system is engineered for deployment on Google Cloud Run from an Android ARM64 Termux development environment, prioritizing cost-efficiency, deterministic data integrity, and transparent AI-assisted job intelligence.

| Metadata Category | Project Detail |
|---|---|
| Project Name | Job Hunter Pro |
| Owner | Michael Ware |
| GitHub Repository | mjmichaelware/job-hunter-pro |
| Google Cloud Project ID | ai-job-agent-498702 |
| Cloud Run Service | job-hunter-pro |
| Region | us-central1 |
| Public URL | https://job-hunter-pro-5t3wttw2ua-uc.a.run.app |
| Core Tech Stack | Flask, Gunicorn, Python 3.11+, Google Cloud SDK |
| Development Environment | Android ARM64 Termux |

## 2. Decoupled System Architecture

Job Hunter Pro uses a decoupled filesystem matrix built around single-responsibility modules. Business logic is isolated from the HTTP layer so the system can be tested locally, run predictably on Cloud Run, and survive scale-to-zero cycles without losing persisted intelligence.

| Directory | Responsibility |
|---|---|
| `core/` | Global configuration, logging, clock helpers, typed exceptions, shared utilities. |
| `geo/` | Google Maps API family boundaries, geocoding, places, distance matrix contracts, Haversine fallback math. |
| `industries/` | Decoupled industry taxonomy modules; one route file per industry. |
| `providers/` | Federated discovery and reasoning providers; dormant when keys are unavailable. |
| `models/` | Data ontology and canonical system models. |
| `store/` | Firestore persistence boundary and repository patterns. |
| `pipeline/` | Functional funnel transforming raw provider payloads into actionable job intelligence. |
| `search/` | Federated search orchestration, budget enforcement, usage tracking. |
| `ingest/` | OIDC-authenticated ingestion cycles triggered by Cloud Scheduler. |
| `api/` | Thin Flask HTTP blueprints; no business logic. |
| `web/` | Frontend templates, CSS tokens, JavaScript renderers, cockpit dashboard. |

## 3. Data Ontology and Model Schema

The platform is organized around deterministic mapping and explicit state. Raw provider payloads are normalized into canonical entities, enriched, scored, deduplicated, rejected or accepted, then persisted with an audit trail.

### Core Data Entities

| Entity | Purpose |
|---|---|
| Job / JobSnapshot | Canonical job identity and point-in-time attributes such as salary, commute, provider metadata. |
| Place / PlaceSnapshot | Business/place identity and temporal metrics such as rating, status, location, review context. |
| Review | Granular review evidence for review intelligence scoring. |
| Batch | Metadata for discovery runs, triggers, provider usage, and budget consumption. |
| Provider / SearchResult | Source metadata and raw retrieval payload tracking. |
| Rejection / Application | Audit trail for excluded results and personal application tracking. |
| APIUsage / IndustryTaxonomy | Cost metrics and industry-specific matching/cue rules. |

### Firestore Collections

| Collection | Primary Key | Description |
|---|---|---|
| `batches` | `batch_id` | Discovery run metadata, trigger type, provider mix, budget usage. |
| `jobs` | `canonical_key` | Core job records; canonical key derived from title/place/address context. |
| `places` | `place_id` | Validated business data including coordinates, rating, status. |
| `rejections` | `batch_id/id` | Audit logs for excluded raw results. |
| `applications` | `job_id` | Michael Ware’s personal application status and notes. |
| `api_usage` | `timestamp` | Provider-specific cost and success metrics. |
| `cache` | `hash` | Persistent query results to prevent redundant API spend. |

## 4. Multi-Industry and Provider Matrix

The system acts as a federated search router. Industry definitions provide cues and query seeds, but they are not allowed to prematurely hard-gate broad discovery. Discovery is recall-first; classification and scoring happen after retrieval.

### Industry Routes

| Industry | Strategy |
|---|---|
| Food Service | Cook, chef, dishwasher, kitchen, prep, server-adjacent roles; may involve Utah Food Handler or ServSafe requirements. |
| Hospitality | Hotel, front desk, banquet, guest services, event support; may involve SLED/background clearance. |
| Care / Social | DSP, peer support, case aide, behavioral health support; may involve BHT/CPSS, CPR, health clearance. |
| Customer Service | Inbound support, help desk, service desk, remote/hybrid support capability. |
| Sales | Retail transactions, account support, counter sales, relationship-driven roles. |
| Retail Ops | Logistics, warehouse, stock, floor operations, back-of-house retail support. |

### Provider Roles

| Discovery Providers | Reasoning Providers |
|---|---|
| SerpAPI, Adzuna, USAJobs, Jooble, The Muse, Careerjet | OpenAI, Gemini, Claude, Groq, xAI |
| Must retrieve source URLs and raw listings. | Reasoning and enrichment only; never initial job discovery. |

## 5. The Job Processing Pipeline

Raw data moves through an auditable funnel designed for high recall, late filtering, explicit rejection reasons, and deterministic persistence.

1. **Normalization:** Provider-specific payloads are mapped into a shared job shape.
2. **Place Resolution:** Physical locations are resolved through address, place, or local fallback contracts.
3. **Geospatial Scoring:** Haversine and distance-matrix style contracts support radius, walk, transit, and drive logic.
4. **Review Intelligence:** Ratings, review volume, sentiment cues, and consistency support quality scoring.
5. **Industry Classification:** Industry cues are interpreted after retrieval; classification uses the full candidate context, not title-only keyword gates.
6. **Deduplication:** Canonical key generation prevents redundant listings.
7. **Rejection Logic:** Excluded results receive explicit reasons such as duplicate, budget guard, provider error, missing source URL, ambiguous place resolution, outside radius, transit unavailable, or low-confidence fit.
8. **Persistence:** Validated batches, accepted records, rejections, usage, and cache entries are stored through the repository layer.

## 6. API Surface and Security Protocols

The API layer is intentionally thin. Routes expose transport contracts while business logic remains in pipeline, search, store, providers, geo, industries, and ingest modules.

### OIDC Security

`/api/ingest` is protected by Cloud Scheduler OIDC design. Plaintext token-in-URL patterns are forbidden. Requests must validate issuer, audience, and scheduler identity before ingestion is accepted.

### Endpoint Categories

| Category | Endpoints | Budget Behavior |
|---|---|---|
| Safe/default | `/api/health`, `/api/usage`, `/api/history`, `/api/industries`, provider/budget status surfaces | Zero live discovery burn. |
| Live/budget-active | `/api/jobs` when not dry-run, `/api/ingest`, live research/provider actions | Must be explicit and budget guarded. |

Current S9 route surface includes `/api/health`, `/api/usage`, `/api/jobs`, `/api/opportunities`, `/api/history`, `/api/research`, `/api/providers`, `/api/industries`, `/api/applications`, `/api/ingest`, and `/api/why-three`.

## 7. UI/UX Cockpit Rendering Laws

The frontend is a **Volumetric Intelligence Cockpit**. Visual spectacle must come from data truth, not fake demo values.

### Rendering Laws

| Law | Requirement |
|---|---|
| Data Truth | No sample jobs, demo metrics, fake charts, fake provider states, or invented listings. |
| Confidence Rendering | Confidence should affect visual emphasis; unvalidated or partial data should appear softer, lighter, or clearly incomplete. |
| Physical Cap Law | Score gauges must respect upstream ceilings; for example, a place with limited star rating cannot visually max out just because sentiment appears positive. |
| Shared-Element Transitions | Job cards and evidence drawers should feel connected through smooth transitions where supported. |
| Materiality | Use restrained glass, layered surfaces, OKLCH-compatible color thinking, and high-readability contrast. |

### Dashboard Tabs

The target dashboard surface contains: Overview, Live Jobs, Opportunities, History, Debug Evidence, Providers, Budget, and Why Three.

## 8. Build and Deployment Roadmap

Each stage requires proof before advancement.

| Stage | Goal | Proof Standard |
|---|---|---|
| S0 | Scaffold | Files/directories created; package compiles. |
| S1 | Core / Models | Models and core utilities import and instantiate. |
| S2 | Industries | Registry loads industry routes and taxonomies. |
| S3 | Providers | Provider registry and boundaries import cleanly. |
| S4 | Geo | Geo contracts and Haversine fallback validate locally. |
| S5 | Store | Repository contracts validate with fake/local storage. |
| S6 | Pipeline | Deterministic normalization, scoring, rejection, dedupe pass. |
| S7 | Search | Budget guard and query planning validate locally. |
| S8 | Ingest | OIDC boundary rejects invalid and accepts valid fake claim paths. |
| S9 | API/App | Flask app boots locally; full route surface is registered. |
| S10 | Web | All tabs switch; default boot performs zero live discovery burn. |
| S11 | Scripts | Secret Manager and deploy helper scripts validate dry-run behavior. |
| S12 | Deploy | Cloud Run deploy succeeds; production health returns 200 OK. |

## 9. FinOps and Operational Constraints

The system is budget-aware by design.

| Constraint | Rule |
|---|---|
| SerpAPI policy | No SerpAPI burn on page load. Live discovery must be explicit. |
| Budget guard | Discovery locks out or downgrades when minimum remaining budget is breached. |
| Default browsing | Cached, historical, usage, and dry-run surfaces remain available when live discovery is blocked. |
| Maintenance trace | Inspect logs, trace failure, compile locally, then redeploy only in the deployment stage. |

## 10. Future Expansion: Markov Vacancy Prediction

A future beta feature may introduce proactive lead generation through a loosely coupled prediction engine.

| Feature | Rule |
|---|---|
| Engine | Continuous-time Markov chain style attrition modeling. |
| Signals | Sentiment volatility, review drop-off, review velocity, place activity trends. |
| Decoupling | Prediction logic lives outside core discovery and does not pollute live listing counts. |
| UI | Predictions appear in a dedicated beta surface and remain clearly labeled as predictive, not confirmed listings. |

## Project Principle

Job Hunter Pro is not a scraper, not a generic job board, and not an LLM search toy. It is a budget-aware, evidence-driven, locally focused opportunity intelligence platform where discovery providers retrieve, reasoning providers enrich, the pipeline decides, the store remembers, the API exposes, and the cockpit explains.
