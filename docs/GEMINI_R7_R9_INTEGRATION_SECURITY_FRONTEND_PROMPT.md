You are operating inside the Job Hunter Pro repo.

MISSION:
Perform combined R7-R9 local integration repair:
- R7 OIDC ingest + scheduler boundary
- R8 LLM enrichment providers, not discovery
- R9 API + frontend contract wiring

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
- Do not hardcode secret values.
- Do not make LLMs discovery providers.
- LLMs enrich/classify retrieved text only.
- This is one combined local implementation session.

MANDATORY DOCUMENTS:
- docs/AI_JOB_AGENT_1.txt
- docs/AI_JOB_AGENT_2.txt
- docs/AI_JOB_AGENT_3.txt
- docs/AI_JOB_AGENT_4.txt
- docs/AI_JOB_AGENT_5_UIUX_Handoff.md
- docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
- docs/REPAIR_MATRIX.md

CURRENT PROVEN STATE:
- R0-R6 complete.
- Search providers are implemented.
- Industries are implemented.
- Federated search and multi-industry pipeline are implemented.
- Application tracker is implemented with local fallback.
- Remaining audit blockers:
  PROVIDER_STUB_COUNT: 10
  PASS_COUNT: 5
  UNWIRED_ROUTE_COUNT: 7

FILES TO INSPECT:
- ingest/oidc.py
- ingest/scheduler_job.py
- api/ingest.py
- scripts/make_scheduler_oidc.sh
- providers/reasoning/base.py
- providers/reasoning/openai.py
- providers/reasoning/gemini.py
- providers/reasoning/claude.py
- providers/reasoning/groq.py
- providers/reasoning/xai.py
- providers/__init__.py
- api/providers.py
- api/industries.py
- api/applications.py
- api/jobs.py
- api/usage.py
- api/history.py
- api/research.py
- api/why_three.py
- app.py
- web/static/js/api.js
- web/static/js/state.js
- web/static/js/render_overview.js
- web/static/js/render_jobs.js
- web/static/js/render_opportunities.js
- web/static/js/render_history.js
- web/static/js/render_providers.js
- web/static/js/render_budget.js
- web/static/js/render_debug_evidence.js
- web/static/js/render_why_three.js
- web/templates/index.html
- tests/

FILES ALLOWED TO CHANGE:
- ingest/oidc.py
- ingest/scheduler_job.py
- api/ingest.py
- scripts/make_scheduler_oidc.sh
- providers/reasoning/base.py
- providers/reasoning/openai.py
- providers/reasoning/gemini.py
- providers/reasoning/claude.py
- providers/reasoning/groq.py
- providers/reasoning/xai.py
- api/providers.py
- api/industries.py
- api/applications.py
- api/jobs.py
- api/usage.py
- api/history.py
- api/research.py
- api/why_three.py
- app.py
- web/static/js/api.js
- web/static/js/state.js
- web/static/js/render_overview.js
- web/static/js/render_jobs.js
- web/static/js/render_opportunities.js
- web/static/js/render_history.js
- web/static/js/render_providers.js
- web/static/js/render_budget.js
- web/static/js/render_debug_evidence.js
- web/static/js/render_why_three.js
- web/templates/index.html
- tests/test_oidc_ingest.py
- tests/test_reasoning_providers.py
- tests/test_api_frontend_contract.py
- scripts/current_truth_audit.py
- docs/REPAIR_MATRIX.md

R7 REQUIREMENTS — OIDC INGEST + SCHEDULER:
1. ingest/oidc.py must have no pass statements.
2. It must reject unsigned requests.
3. It must verify Bearer token structure in local tests.
4. If google-auth is installed, support real Google OIDC verification with:
   - expected audience
   - expected scheduler service account email if configured
5. If google-auth is not available locally, fail closed unless tests explicitly inject a fake verifier.
6. Do not accept request.args token.
7. api/ingest.py must call the OIDC verifier and fail closed.
8. scripts/make_scheduler_oidc.sh must print safe gcloud scheduler creation/update commands without printing secrets.

R8 REQUIREMENTS — LLM ENRICHMENT, NOT DISCOVERY:
1. Remove provider_stub outputs from all providers/reasoning/*.py.
2. Do not call external APIs during tests.
3. Providers must expose:
   - is_available()
   - classify(text_content, categories)
   - enrich(text_content)
4. Missing key returns unavailable/empty safe output.
5. With fake monkeypatched HTTP/client, classify/enrich parse deterministic mocked response.
6. Output must include:
   - provider
   - mode
   - confidence
   - evidence_required true
   - category or enrichment fields
   - source_text_hash or input_length
7. No provider may create job listings.
8. No provider may claim web search unless a real web-search/grounding API is explicitly implemented and tested.
9. R8 does not implement live web search. It implements enrichment only.

R9 REQUIREMENTS — API + FRONTEND CONTRACT:
1. Safe endpoints must expose real contract data:
   - /api/providers
   - /api/industries
   - /api/applications
   - /api/history
   - /api/jobs?dry_run=1
   - /api/usage
   - /api/why-three
2. Frontend api.js must point to correct endpoints.
3. Frontend renderers must not show “backend gap” when endpoint now works.
4. Frontend must still not call live /api/jobs on boot.
5. Live discovery must remain explicit user action.
6. Debug evidence/pipeline may show disconnected only if SSE endpoint absent; it must not claim backend gap for implemented endpoints.
7. Update script audit detection if UNWIRED_ROUTE_COUNT should decrease.

TEST REQUIREMENTS:
Create/update:
- tests/test_oidc_ingest.py
- tests/test_reasoning_providers.py
- tests/test_api_frontend_contract.py

Tests must:
- use fake requests/tokens/clients only
- not call external APIs
- prove unsigned ingest fails
- prove fake valid OIDC passes verifier path
- prove no request.args token auth
- prove reasoning providers no longer return provider_stub
- prove reasoning providers do not fabricate job listings
- prove safe API endpoints return non-placeholder JSON
- prove frontend API map contains safe endpoints
- prove boot/default API list avoids live /api/jobs

PROOF COMMANDS:
python3 -m py_compile ingest/oidc.py ingest/scheduler_job.py api/ingest.py providers/reasoning/base.py providers/reasoning/openai.py providers/reasoning/gemini.py providers/reasoning/claude.py providers/reasoning/groq.py providers/reasoning/xai.py tests/test_oidc_ingest.py tests/test_reasoning_providers.py tests/test_api_frontend_contract.py
PYTHONPATH=. python3 tests/test_provider_search_pass1.py
PYTHONPATH=. python3 tests/test_provider_search_pass2.py
PYTHONPATH=. python3 tests/test_industries_registry.py
PYTHONPATH=. python3 tests/test_federated_search.py
PYTHONPATH=. python3 tests/test_multi_industry_pipeline.py
PYTHONPATH=. python3 tests/test_applications_api.py
PYTHONPATH=. python3 tests/test_oidc_ingest.py
PYTHONPATH=. python3 tests/test_reasoning_providers.py
PYTHONPATH=. python3 tests/test_api_frontend_contract.py
python3 scripts/current_truth_audit.py

EXPECTED AUDIT AFTER R7-R9:
- RETURN_EMPTY_PROVIDER_COUNT: 0
- PROVIDER_STUB_COUNT: 0
- PASS_COUNT: 0
- PLACEHOLDER_ENDPOINT_COUNT: 0
- UNWIRED_ROUTE_COUNT should decrease or become 0 if audit is accurate.
- SAFE_ENDPOINTS_PRESENT_COUNT should stay >= 4.

AFTER SUCCESS:
Update docs/REPAIR_MATRIX.md:
- Mark R7, R8, and R9 complete.
- Record files changed.
- Record proof commands.
- Record no deploy.
- Record no git push.
- Record no API spend.
- Record audit count changes.

Then run:
git diff --stat
git diff -- ingest providers/reasoning api app.py web/static/js web/templates tests scripts/current_truth_audit.py docs/REPAIR_MATRIX.md scripts/make_scheduler_oidc.sh | sed -n '1,620p'

If successful:
git add ingest providers/reasoning api app.py web/static/js web/templates tests scripts/current_truth_audit.py docs/REPAIR_MATRIX.md scripts/make_scheduler_oidc.sh
git commit -m "R7-R9 wire OIDC reasoning providers and frontend contract"

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
