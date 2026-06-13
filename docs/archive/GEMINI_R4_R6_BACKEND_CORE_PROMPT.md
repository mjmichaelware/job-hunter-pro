You are operating inside the Job Hunter Pro repo.

MISSION:
Perform combined R4-R6 local backend repair:
- R4 federated search + budget/cache
- R5 multi-industry pipeline wiring
- R6 application tracker CRUD

ABSOLUTE RULES:
- Read all six authoritative Job Hunter Pro documents before editing.
- Read docs/REPAIR_MATRIX.md before editing.
- Read scripts/current_truth_audit.py before editing.
- Do not deploy.
- Do not git push.
- Do not call live /api/jobs.
- Do not call external APIs during tests.
- Do not expose secrets.
- Do not print secret values.
- Do not implement LLM reasoning providers in this session.
- Do not touch OIDC ingest in this session.
- This is one combined local implementation session only.

MANDATORY DOCUMENTS:
- docs/AI_JOB_AGENT_1.txt
- docs/AI_JOB_AGENT_2.txt
- docs/AI_JOB_AGENT_3.txt
- docs/AI_JOB_AGENT_4.txt
- docs/AI_JOB_AGENT_5_UIUX_Handoff.md
- docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
- docs/REPAIR_MATRIX.md

CURRENT PROVEN STATE:
- R0 complete.
- R1 industries complete.
- R2/R3 search providers complete.
- RETURN_EMPTY_PROVIDER_COUNT is 0.
- PROVIDER_STUB_COUNT is still 10.
- PASS_COUNT is still 5.
- UNWIRED_ROUTE_COUNT is still 7.
- No deploy and no push should happen in this session.

FILES TO INSPECT:
- search/federated.py
- search/budget.py
- search/usage_tracker.py
- store/cache_repo.py
- store/repository.py
- store/firestore_client.py
- store/applications_repo.py
- pipeline/normalize.py
- pipeline/classify.py
- pipeline/run.py
- pipeline/dedupe.py
- pipeline/reject.py
- pipeline/resolve_place.py
- pipeline/score_match.py
- pipeline/score_review.py
- providers/__init__.py
- providers/base.py
- providers/search/*.py
- industries/*.py
- models/search_result.py
- models/job.py
- models/job_snapshot.py
- models/application.py
- models/enums.py
- api/applications.py
- api/providers.py
- api/industries.py
- api/jobs.py
- api/history.py
- app.py
- existing tests/

FILES ALLOWED TO CHANGE:
- search/federated.py
- search/budget.py
- search/usage_tracker.py
- store/cache_repo.py
- store/applications_repo.py
- pipeline/normalize.py
- pipeline/classify.py
- pipeline/run.py
- pipeline/dedupe.py
- pipeline/reject.py
- pipeline/score_match.py
- pipeline/score_review.py
- api/applications.py
- api/providers.py
- api/industries.py
- api/jobs.py
- app.py only if needed to expose safe non-live routes
- tests/test_federated_search.py
- tests/test_multi_industry_pipeline.py
- tests/test_applications_api.py
- scripts/current_truth_audit.py only if detection needs legitimate update
- docs/REPAIR_MATRIX.md

R4 REQUIREMENTS — FEDERATED SEARCH + BUDGET/CACHE:
1. search/federated.py must stop dummy behavior.
2. It must build query plans from:
   - industry route queries
   - base location
   - provider availability
3. It must call provider.search(query) only when explicitly asked by tests/runtime, never on import.
4. It must merge SearchResult objects.
5. It must dedupe by URL/title/source.
6. It must return structured plan and results.
7. It must handle provider exceptions fail-closed.
8. Budget guard must:
   - block SerpAPI providers when budget says blocked
   - allow no-key/free providers like The Muse
   - be testable without live SerpAPI
9. Cache repo must:
   - provide deterministic cache key
   - support in-memory fallback if Firestore unavailable
   - expose get/set methods
   - be safe in local tests

R5 REQUIREMENTS — MULTI-INDUSTRY PIPELINE:
1. pipeline/classify.py must use the R1 industries registry.
2. pipeline/normalize.py must accept SearchResult and raw dict shapes.
3. pipeline/dedupe.py must produce deterministic canonical keys.
4. pipeline/reject.py must produce structured rejection reasons.
5. pipeline/run.py must orchestrate:
   provider results → classify → normalize → dedupe → reject/accept
6. It must support all six industries:
   - food_service
   - hospitality
   - care_social
   - sales
   - customer_service
   - retail_ops
7. It must not call Google Maps/Places or SerpAPI in tests.
8. It must preserve the food-service exact token/phrase behavior and avoid the rn substring bug.

R6 REQUIREMENTS — APPLICATION TRACKER:
1. api/applications.py must stop placeholder behavior.
2. Implement CRUD-ish safe routes:
   - GET /api/applications
   - POST /api/applications
   - GET /api/applications/<job_id>
   - PATCH /api/applications/<job_id>
3. Use store/applications_repo.py.
4. If Firestore is unavailable locally, repo must use safe in-memory fallback for tests.
5. Application records must include:
   - job_id
   - status
   - notes
   - created_at
   - updated_at
6. Never fake existing applications.
7. Empty state is allowed if no records exist.

TEST REQUIREMENTS:
Create or update:
- tests/test_federated_search.py
- tests/test_multi_industry_pipeline.py
- tests/test_applications_api.py

Tests must:
- use fake providers and fake payloads
- not call real external APIs
- prove federated search merges and dedupes
- prove budget blocks SerpAPI and allows free provider
- prove multi-industry classification/normalization works for all six industries
- prove application CRUD works with in-memory repo/fallback
- prove app imports
- prove no live /api/jobs call is required

PROOF COMMANDS:
python3 -m py_compile search/federated.py search/budget.py search/usage_tracker.py store/cache_repo.py store/applications_repo.py pipeline/normalize.py pipeline/classify.py pipeline/run.py pipeline/dedupe.py pipeline/reject.py api/applications.py tests/test_federated_search.py tests/test_multi_industry_pipeline.py tests/test_applications_api.py
PYTHONPATH=. python3 tests/test_provider_search_pass1.py
PYTHONPATH=. python3 tests/test_provider_search_pass2.py
PYTHONPATH=. python3 tests/test_industries_registry.py
PYTHONPATH=. python3 tests/test_federated_search.py
PYTHONPATH=. python3 tests/test_multi_industry_pipeline.py
PYTHONPATH=. python3 tests/test_applications_api.py
python3 scripts/current_truth_audit.py

EXPECTED AUDIT AFTER R4-R6:
- RETURN_EMPTY_PROVIDER_COUNT should remain 0.
- PROVIDER_STUB_COUNT should remain 10.
- PASS_COUNT should remain 5.
- UNWIRED_ROUTE_COUNT should decrease if audit detects the now-wired application/search/industry paths.
- PLACEHOLDER_ENDPOINT_COUNT should remain 0.

AFTER SUCCESS:
Update docs/REPAIR_MATRIX.md:
- Mark R4, R5, and R6 complete.
- Record files changed.
- Record proof commands.
- Record no deploy.
- Record no git push.
- Record no API spend.
- Record audit count changes.

Then run:
git diff --stat
git diff -- search store pipeline api app.py tests docs/REPAIR_MATRIX.md scripts/current_truth_audit.py | sed -n '1,520p'

If successful:
git add search store pipeline api app.py tests docs/REPAIR_MATRIX.md scripts/current_truth_audit.py
git commit -m "R4-R6 wire federated search pipeline and applications"

Do not git push.

FINAL RESPONSE:
List:
- all six documents read
- files inspected
- files changed
- tests run
- audit count changes
- commit hash
- confirm no deploy
- confirm no git push
- confirm no live API spend
Stop.
