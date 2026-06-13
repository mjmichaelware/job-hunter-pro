# S10-B API Contract Reality Matrix

This document maps the UI expectations defined in Document 5 against the actual payload fields exposed by the current backend (`api/*.py` blueprints and legacy `api/index.py` code). 

## 1. Endpoint Contract Matrix

| Endpoint | Method | Safety class | Boot allowed | UI tab depending on it | Payload fields expected by Document 5 | Payload fields actually returned or visible in code | Current status | Frontend action needed | Backend dependency |
|---|---|---|---|---|---|---|---|---|---|
| `/api/health` | GET | Safe | Yes | Overview | `status`, system health flags | Mounted: `{"status": "ok"}` <br> Legacy: `{"status": "ok", "version": ...}` | Partial | Render generic SAFE status if `status: ok` | Real system health checks |
| `/api/usage` | GET | Safe | Yes | Overview, Budget | `total_searches_left`, `monthly_usage`, quota details | Mounted: `{"message": "... placeholder"}` <br> Legacy: `{"status": "ok", "serpapi": {...}, "budget": {...}}` | Backend gap | Render "UNAVAILABLE" / fallback budget guard | Wire `serpapi_account_status` and output Doc 5 exact fields |
| `/api/opportunities` | GET | Safe | Yes (cached) | Opportunities, Overview | `opportunities` [array: `name`, `address`, `rating`, `industry`, `review_count`, `distance`, `commute`, `opportunity_strength`] | Mounted: `{"message": "... placeholder"}` <br> Legacy: `{"status": "success", "data": [...]}` (different schema) | Backend gap | Render "Scanning..." -> "No opportunities loaded" | Implement Google Places radar pipeline to output exact fields |
| `/api/history` | GET | Safe | Yes | History, Overview | `batches` [array: `batch_id`, `created_at`, `trigger`, `counts.accepted`, `counts.rejected`, `provider_mix`, `budget_per_batch`] | Mounted: `{"message": "... placeholder"}` <br> Legacy: returns `batches` array but missing `trigger`, `provider_mix`, `budget_per_batch` | Backend gap | Render empty state table ("No batch history exists yet") | Connect to Firestore/GCS and ensure missing schema fields |
| `/api/providers` | GET | Safe | Yes | Providers, Overview | `providers` [array: `name`, `type`, `status`, `configured`, `dormant/live`, `budget_guarded`, `last_used`] | Mounted: `{"message": "... placeholder"}` | Backend gap | Render empty state ("Missing Key" / dormant placeholders) | Create provider status aggregation endpoint |
| `/api/industries` | GET | Safe | Yes | Filter Drawer | Industry taxonomies metadata | Mounted: `{"message": "... placeholder"}` | Backend gap | Use hardcoded UI filters temporarily as fallback | Expose system taxonomies |
| `/api/applications` | GET | Safe | Yes | Live Jobs | User application status tracker | Mounted: `{"message": "... placeholder"}` | Backend gap | Omit from job cards temporarily / show no status | Connect to user app-state store |
| `/api/why-three` | GET | Safe | Yes | Why Three | `top3` [array: `title`, `company`, `resonance_score`, `why_included`, `why_excluded`, `evidence_matrix`] | Mounted: `{"message": "... placeholder"}` <br> Legacy: `{"status": "success", "data": [...]}` | Backend gap | Render empty/loading state ("Needs more history") | Build decision engine ranking & evidence generation |
| `/api/jobs?dry_run=1` | GET | Safe | Yes | Budget, Overview | `plan`, projected query cost, `jobs` [array] | Mounted: `{"message": "... placeholder"}` <br> Legacy: `{"status": "ok", "dry_run": True, "budget": {...}}` | Backend gap | Render "Failed to generate dry-run plan" on Budget tab | Build execution planner dry-run |
| `/api/jobs` | GET | Restricted | No | Live Jobs | `jobs` [array: `title`, `company`, `place`, `match_score`, `commute_matrix_seconds`, etc.] | Mounted: `{"message": "... placeholder"}` <br> Legacy: returns `data` array with basic fields, missing most Doc 5 requirements | Backend gap | Render empty/loading if called. Keep Live Discovery button hidden. | Wire full pipeline and ensure exact output fields |
| `/api/ingest` | POST | Restricted | No | (N/A - Scheduler) | (N/A for UI) | Mounted: `{"message": "Ingest endpoint (OIDC protected, placeholder)"}` | Supported (Stub) | None (Do not call from UI) | Connect to OIDC/Pipeline |

## 2. Specific Backend Gaps Found

- **Provider Status**: No endpoint provides the discovery vs. reasoning split, `configured` vs. `missing key` state, or `last_used` timestamps. The UI must render placeholder dormant states.
- **Industries**: The taxonomy is currently hardcoded in the frontend filters. There is no active API route returning these values.
- **Why-Three**: No endpoint exists that returns a structured `top3` array with comparative `why_included` and `evidence_matrix` fields.
- **Evidence Drawer Fields**: The legacy `jobs` schema does not contain `raw_title`, `normalized_title`, `rejection_reasons`, `dedupe_key`, `budget_cost`, `query_seed`, `discovery_mode`, or `role_family_scores`. The UI must handle `undefined` for these fields by rendering "Unavailable".
- **Budget Usage Fields**: Expected fields `monthly_usage` and `total_searches_left` are missing in the currently mounted routes. 
- **Dry-Run Query Plan Fields**: The expected `plan` object (with projected query cost and tree) does not exist yet. Legacy code only returned basic SerpAPI stats.
- **Applications**: No user application status tracking schema is implemented.
- **SSE/Pipeline Stream**: No SSE endpoint route (`text/event-stream`) is defined in the Flask backend. The UI's "Pipeline Reactor" must remain explicitly marked as inactive/disconnected.
- **Review Score Components**: No backend logic returns the 60/15/15/10 breakdown for the rating cap feature.
- **Place Resolution Notes**: No `place_resolution_notes` field exists in the returned legacy jobs, which prevents rendering the "resolution oscillation" trust animation.
- **Commute/Radius Fields**: The legacy `api/jobs` returned `radius_miles` but not `haversine_radius_miles` as expected by JS. It also lacks detailed `commute_matrix_seconds` bounding data expected by the frontend.

## 3. UI Implementation Rule for S10-C

Because nearly all necessary endpoints are mounted as `{"message": "... placeholder"}` in `api_bp`, the S10-C renderer upgrade must forcefully implement `try-catch` blocks and default values, aggressively rendering empty, unavailable, or locked states to ensure the application does not crash when parsing placeholder strings. *No data will be artificially mocked to bypass this reality.*