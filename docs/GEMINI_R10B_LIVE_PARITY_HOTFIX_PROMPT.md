You are operating inside the Job Hunter Pro repo.

MISSION:
Perform R10B — Live parity hotfix after deploy.

PROBLEM:
R10 deployed commit 6873221 successfully, but live endpoint proof shows data regression.

Evidence:
- /api/_surface says api_backend api.index:app, but placeholder_blueprint_registered true.
- /api/health returns only {"status":"ok"} instead of rich api.index health with version/maps/serpapi/batch_bucket.
- /api/usage returns simplified mock/safe data instead of api.index SerpAPI/GCS usage.
- /api/history returns {"batches":[]} instead of existing Cloud Storage batch history.
- /api/jobs?dry_run=1 returns mocked dry-run plan, not api.index budget-aware dry_run response.
- /api/why-three returns {"top3":[]} instead of api.index explanation.

ABSOLUTE RULES:
- Read all six authoritative Job Hunter Pro documents before editing.
- Read docs/REPAIR_MATRIX.md before editing.
- Read scripts/current_truth_audit.py before editing.
- Do not call live /api/jobs without dry_run=1.
- Do not expose secrets.
- Do not print secret values.
- Do not remove R0-R9 improvements.
- Do not fake data.
- The goal is live data parity, not a cosmetic pass.

MANDATORY DOCUMENTS:
- docs/AI_JOB_AGENT_1.txt
- docs/AI_JOB_AGENT_2.txt
- docs/AI_JOB_AGENT_3.txt
- docs/AI_JOB_AGENT_4.txt
- docs/AI_JOB_AGENT_5_UIUX_Handoff.md
- docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
- docs/REPAIR_MATRIX.md

FILES TO INSPECT:
- app.py
- api/__init__.py
- api/health.py
- api/usage.py
- api/jobs.py
- api/history.py
- api/opportunities.py
- api/research.py
- api/why_three.py
- api/index.py
- api/providers.py
- api/industries.py
- api/applications.py
- tests/test_api_frontend_contract.py
- scripts/current_truth_audit.py

FILES ALLOWED TO CHANGE:
- app.py
- api/health.py
- api/usage.py
- api/jobs.py
- api/history.py
- api/opportunities.py
- api/research.py
- api/why_three.py
- api/providers.py only if needed
- api/industries.py only if needed
- api/applications.py only if needed
- tests/test_api_frontend_contract.py
- docs/REPAIR_MATRIX.md

REQUIRED FIX:
1. Restore api.index-backed rich data for these routes:
   - /api/health
   - /api/usage
   - /api/history
   - /api/jobs
   - /api/jobs?dry_run=1
   - /api/why-three
   - /api/opportunities
   - /api/research/place
   - /api/batches
   - /api/batch/<path>
2. Keep R0-R9 modular improvements for:
   - /api/providers
   - /api/industries
   - /api/applications
   - frontend contract endpoints
3. /api/_surface must honestly report:
   - api_index_proxy_routes enabled
   - modular_routes enabled
   - placeholder_blueprint_registered false if placeholder blueprint is not registered, or explain exact meaning if true.
4. Do not allow placeholder endpoint responses.
5. Do not let frontend boot call live /api/jobs without dry_run=1.
6. Tests must prove:
   - /api/health has version, maps_enabled, serpapi_enabled, batch_bucket
   - /api/usage has serpapi and storage fields
   - /api/history response shape includes batch_count and data
   - /api/jobs?dry_run=1 has dry_run true or the real api.index dry-run contract
   - /api/providers still returns provider list with search + reasoning providers
   - /api/industries returns 6 industries
   - /api/applications returns application tracker shape
   - no safe endpoint returns placeholder, provider_stub, TODO, NotImplemented, or Traceback

PROOF COMMANDS:
python3 -m py_compile app.py api/health.py api/usage.py api/jobs.py api/history.py api/opportunities.py api/research.py api/why_three.py tests/test_api_frontend_contract.py
PYTHONPATH=. python3 tests/test_api_frontend_contract.py
python3 scripts/current_truth_audit.py

LOCAL MANUAL PROOF:
python3 - <<'PY'
import app, json
c = app.app.test_client()
for ep in ["/api/_surface","/api/health","/api/usage","/api/providers","/api/industries","/api/applications","/api/history","/api/jobs?dry_run=1","/api/why-three"]:
    r = c.get(ep)
    text = r.get_data(as_text=True)
    print(ep, r.status_code, text[:500].replace("\\n"," "))
PY

EXPECTED:
- Audit stays clean:
  STUB_COUNT 0
  PLACEHOLDER_ENDPOINT_COUNT 0
  RETURN_EMPTY_PROVIDER_COUNT 0
  PROVIDER_STUB_COUNT 0
  PASS_COUNT 0
  TODO_COUNT 0
  UNWIRED_ROUTE_COUNT 0
- Local /api/health includes rich api.index fields.
- Local /api/history has api.index shape, not only {"batches":[]}.

AFTER SUCCESS:
Update docs/REPAIR_MATRIX.md:
- Add R10B hotfix proof.
- Record regression cause.
- Record files changed.
- Record proof commands.
- Record deploy needed after this hotfix.

Then:
git diff --stat
git diff -- app.py api tests/test_api_frontend_contract.py docs/REPAIR_MATRIX.md | sed -n '1,520p'

If successful:
git add app.py api tests/test_api_frontend_contract.py docs/REPAIR_MATRIX.md
git commit -m "R10B restore api.index live data parity"

Do not git push unless explicitly instructed after local proof.

FINAL RESPONSE:
List:
- regression cause
- files changed
- local proof summary
- audit counts
- commit hash
- say whether ready for final push/deploy
Stop.
