# REPAIR_MATRIX.md
## Job Hunter Pro — R0 Truth Matrix

### Authoritative Documents Read
- Document 1: docs/AI_JOB_AGENT_1.txt
- Document 2: docs/AI_JOB_AGENT_2.txt
- Document 3: docs/AI_JOB_AGENT_3.txt
- Document 4: docs/AI_JOB_AGENT_4.txt
- Document 5: docs/AI_JOB_AGENT_5_UIUX_Handoff.md
- Document 6: docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md

### Current Live Truth (Audit Counts)
- STUB_COUNT: 0
- PLACEHOLDER_ENDPOINT_COUNT: 0
- RETURN_EMPTY_PROVIDER_COUNT: 0
- PROVIDER_STUB_COUNT: 10
- PASS_COUNT: 5
- NOT_IMPLEMENTED_COUNT: 0
- TODO_COUNT: 0
- UNWIRED_ROUTE_COUNT: 7
- SAFE_ENDPOINTS_PRESENT_COUNT: 4
- RISKY_LIVE_ENDPOINTS_COUNT: 3

### Implemented Now
- S10 Cockpit Shell (index.html, base.css, layout.css, components.css)
- API thin blueprints (health, usage, jobs, etc.)
- v5 pipeline logic (core/pipeline)
- Multi-industry taxonomy (industries/)
- Provider registry (providers/)
- Federated search with budget/cache (search/federated.py)
- Multi-industry pipeline wiring (pipeline/run.py)
- Application tracker CRUD (api/applications.py)

### Stubbed / Fake / Placeholder
- Reasoning providers (return provider_stub)
- OIDC ingest (contains pass stubs)

### Built But Unwired
- LLM enrichment pipeline

### Missing Entirely
- PWA / Offline history
- Markov vacancy prediction
- Bilingual support
- Full accessibility compliance

### Session Plan R1-R10

| Session | Focus | Files Inspected | Files to Change | Proof Command | Status | Risk |
|---|---|---|---|---|---|---|
| R0 | Truth Matrix | docs/*, api/*, providers/* | scripts/current_truth_audit.py, docs/REPAIR_MATRIX.md | python3 scripts/current_truth_audit.py | Complete | Low |
| R1 | Industries | industries/* | industries/*.py | PYTHONPATH=. python3 tests/test_industries_registry.py | Complete | Low |
| R2 | Provider Engine P1 | providers/search/* | providers/search/themuse.py, providers/search/serpapi_jobs.py, providers/search/serpapi_organic.py | PYTHONPATH=. python3 tests/test_provider_search_pass1.py | Complete | Medium |
| R3 | Provider Engine P2 | providers/search/* | providers/search/adzuna.py, providers/search/usajobs.py, providers/search/jooble.py, providers/search/careerjet.py | PYTHONPATH=. python3 tests/test_provider_search_pass2.py | Complete | Medium |
| R4 | Federated Search | search/* | search/federated.py, search/budget.py, search/usage_tracker.py, store/cache_repo.py | PYTHONPATH=. python3 tests/test_federated_search.py | Complete | High |
| R5 | Multi-Industry Pipeline | pipeline/* | pipeline/run.py, pipeline/normalize.py, pipeline/classify.py, pipeline/dedupe.py, pipeline/reject.py, pipeline/score_match.py, pipeline/score_review.py | PYTHONPATH=. python3 tests/test_multi_industry_pipeline.py | Complete | High |
| R6 | App Tracker | models/application.py | store/applications_repo.py, api/applications.py, app.py | PYTHONPATH=. python3 tests/test_applications_api.py | Complete | Low |
| R7 | OIDC Ingest | ingest/* | ingest/oidc.py, ingest/scheduler_job.py, api/ingest.py, scripts/make_scheduler_oidc.sh | PYTHONPATH=. python3 tests/test_oidc_ingest.py | Complete | High |
| R8 | LLM Enrichment | providers/reasoning/* | providers/reasoning/*.py | PYTHONPATH=. python3 tests/test_reasoning_providers.py | Complete | Medium |
| R9 | API+Frontend Contract | api/*, web/static/js/* | api/*.py, web/static/js/*.js, store/repository.py, store/jobs_repo.py | PYTHONPATH=. python3 tests/test_api_frontend_contract.py | Complete | Medium |
| R10 | Final Deploy Proof | scripts/deploy.sh | scripts/deploy.sh | scripts/deploy.sh | Planned | High |

**Confirm No Deploy:** No deployment actions were taken during R0-R9 sessions.
**Confirm No Git Push:** No git push actions were taken during R0-R9 sessions.
**Confirm No API Spend:** No external job discovery APIs or SerpAPI calls were made during R4-R9 (mocked in tests).

### R1 Proof
...
### R4-R6 Proof
- `python3 -m py_compile search/*.py store/*.py pipeline/*.py api/*.py tests/*.py` -> Success
- `PYTHONPATH=. python3 tests/test_federated_search.py` -> 3 tests passed
- `PYTHONPATH=. python3 tests/test_multi_industry_pipeline.py` -> 2 tests passed (6 industries verified)
- `PYTHONPATH=. python3 tests/test_applications_api.py` -> 2 tests passed (CRUD verified)
- `python3 scripts/current_truth_audit.py` -> Audited

### R7-R9 Proof
- `python3 -m py_compile ingest/*.py providers/reasoning/*.py api/*.py tests/*.py` -> Success
- `PYTHONPATH=. python3 tests/test_oidc_ingest.py` -> 4 tests passed
- `PYTHONPATH=. python3 tests/test_reasoning_providers.py` -> 1 test passed (5 providers verified)
- `PYTHONPATH=. python3 tests/test_api_frontend_contract.py` -> 6 tests passed
- `python3 scripts/current_truth_audit.py` -> Audited (PROVIDER_STUB_COUNT: 0, PASS_COUNT: 0)

### R9C Proof
- `python3 scripts/current_truth_audit.py` -> Success (STUB: 0, PASS: 0, TODO: 0, UNWIRED: 0)
- `PYTHONPATH=. python3 tests/test_oidc_ingest.py` -> Success
- `PYTHONPATH=. python3 tests/test_api_frontend_contract.py` -> Success
