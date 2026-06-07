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
- RETURN_EMPTY_PROVIDER_COUNT: 7
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

### Stubbed / Fake / Placeholder
- Reasoning providers (return provider_stub)
- Search providers (return [])
- OIDC ingest (contains pass stubs)
- Application tracker (CRUD not live)

### Built But Unwired
- Multi-industry execution path
- Federated search budget guards
- LLM enrichment pipeline

### Missing Entirely
- PWA / Offline history
- Markov vacancy prediction
- Bilingual support
- Full accessibility compliance

### Session Plan R1-R10

| Session | Focus | Files Inspected | Files to Change | Proof Command | Status | Risk |
|---|---|---|---|---|---|---|
| R0 | Truth Matrix | docs/*, api/*, providers/* | scripts/current_truth_audit.py, docs/REPAIR_MATRIX.md | python3 scripts/current_truth_audit.py | Planned | Low |
| R1 | Industries | industries/* | industries/*.py | pytest tests/test_industries_registry.py | Planned | Low |
| R2 | Provider Engine P1 | providers/search/* | providers/search/*.py | pytest tests/test_providers_registry.py | Planned | Medium |
| R3 | Provider Engine P2 | providers/reasoning/* | providers/reasoning/*.py | pytest tests/test_providers_registry.py | Planned | Medium |
| R4 | Federated Search | search/* | search/federated.py, search/budget.py | python3 -m api.jobs | Planned | High |
| R5 | Multi-Industry Pipeline | pipeline/* | pipeline/run.py | python3 pipeline/run.py | Planned | High |
| R6 | App Tracker | models/application.py | store/applications_repo.py | pytest tests/test_applications.py | Planned | Low |
| R7 | OIDC Ingest | ingest/* | ingest/oidc.py, ingest/scheduler_job.py | python3 ingest/oidc.py | Planned | High |
| R8 | LLM Enrichment | pipeline/enrich.py | pipeline/run.py | python3 pipeline/run.py | Planned | Medium |
| R9 | API+Frontend Contract | api/*, web/static/js/* | api/index.py, web/static/js/api.js | curl /api/health | Planned | Medium |
| R10 | Final Deploy Proof | scripts/deploy.sh | scripts/deploy.sh | scripts/deploy.sh | Planned | High |

**Confirm No Deploy:** No deployment actions will be taken during R0-R9 sessions.
