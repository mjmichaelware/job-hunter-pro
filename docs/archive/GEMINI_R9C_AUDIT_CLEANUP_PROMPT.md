You are operating inside the Job Hunter Pro repo.

MISSION:
Perform R9C — Audit-clean API/frontend/ingest contract cleanup before R10 deploy.

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
- This is a cleanup/proof session only.

CURRENT STATE:
R0-R9 are locally committed.
Latest local commit: b9fd6bc R7-R9 wire OIDC reasoning providers and frontend contract.
Audit still reports:
- TODO in api/ingest.py line 26
- UNWIRED_ROUTE_COUNT: 7
The audit findings only show the TODO, so UNWIRED_ROUTE_COUNT may be stale counting logic or unreported real blockers.

FILES TO INSPECT:
- api/ingest.py
- scripts/current_truth_audit.py
- app.py
- api/*.py
- web/static/js/api.js
- web/static/js/state.js
- web/static/js/render_*.js
- docs/REPAIR_MATRIX.md
- tests/test_oidc_ingest.py
- tests/test_api_frontend_contract.py

FILES ALLOWED TO CHANGE:
- api/ingest.py
- scripts/current_truth_audit.py
- tests/test_oidc_ingest.py
- tests/test_api_frontend_contract.py
- docs/REPAIR_MATRIX.md
- web/static/js/api.js only if endpoint map is genuinely wrong
- app.py only if a safe route is genuinely unwired

REQUIRED FIXES:
1. Remove the TODO blocker from api/ingest.py.
   - Do not replace it with another TODO/FIXME.
   - Keep OIDC fail-closed.
   - Keep request.args token auth disabled.
2. Investigate UNWIRED_ROUTE_COUNT.
   - If it is real, print and fix the exact unwired routes.
   - If it is stale/audit false positive, fix scripts/current_truth_audit.py so every counted unwired route is also printed as a finding.
   - Final audit must not silently count unwired routes without findings.
3. Safe endpoints must stay present:
   - /api/_surface
   - /api/health
   - /api/usage
   - /api/providers
   - /api/industries
   - /api/applications
   - /api/history
   - /api/jobs?dry_run=1
   - /api/why-three
4. Do not deploy.
5. Do not git push.

PROOF COMMANDS:
python3 -m py_compile api/ingest.py scripts/current_truth_audit.py tests/test_oidc_ingest.py tests/test_api_frontend_contract.py
PYTHONPATH=. python3 tests/test_oidc_ingest.py
PYTHONPATH=. python3 tests/test_api_frontend_contract.py
python3 scripts/current_truth_audit.py

EXPECTED FINAL AUDIT:
- STUB_COUNT: 0
- PLACEHOLDER_ENDPOINT_COUNT: 0
- RETURN_EMPTY_PROVIDER_COUNT: 0
- PROVIDER_STUB_COUNT: 0
- PASS_COUNT: 0
- TODO_COUNT: 0
- NOT_IMPLEMENTED_COUNT: 0
- UNWIRED_ROUTE_COUNT: 0 OR every unwired count must have a printed finding and a justified matrix entry.
If UNWIRED_ROUTE_COUNT remains nonzero, do not claim R10 readiness.

AFTER SUCCESS:
Update docs/REPAIR_MATRIX.md:
- Add R9C cleanup proof.
- Record whether UNWIRED_ROUTE_COUNT is 0 or justified.
- Confirm no deploy.
- Confirm no git push.
- Confirm no API spend.

Then run:
git diff --stat
git diff -- api/ingest.py scripts/current_truth_audit.py tests/test_oidc_ingest.py tests/test_api_frontend_contract.py docs/REPAIR_MATRIX.md web/static/js/api.js app.py | sed -n '1,360p'

If successful:
git add api/ingest.py scripts/current_truth_audit.py tests/test_oidc_ingest.py tests/test_api_frontend_contract.py docs/REPAIR_MATRIX.md web/static/js/api.js app.py
git commit -m "R9C clean audit blockers before deploy proof"

Do not git push.

FINAL RESPONSE:
List:
- files inspected
- files changed
- proof commands
- final audit counts
- commit hash
- confirm no deploy
- confirm no git push
- confirm no API spend
- say whether R10 is now clear or blocked
Stop.
