You are operating inside the Job Hunter Pro repo.

MISSION:
Perform R3 — Provider Engine Pass 2.

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
- Do not touch ingest/OIDC in this session.
- This session only fixes:
  providers/search/adzuna.py
  providers/search/usajobs.py
  providers/search/jooble.py
  providers/search/careerjet.py
  and required config/tests/docs updates.

MANDATORY DOCUMENTS:
- docs/AI_JOB_AGENT_1.txt
- docs/AI_JOB_AGENT_2.txt
- docs/AI_JOB_AGENT_3.txt
- docs/AI_JOB_AGENT_4.txt
- docs/AI_JOB_AGENT_5_UIUX_Handoff.md
- docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
- docs/REPAIR_MATRIX.md

FILES TO INSPECT:
- providers/base.py
- providers/__init__.py
- providers/search/adzuna.py
- providers/search/usajobs.py
- providers/search/jooble.py
- providers/search/careerjet.py
- providers/search/themuse.py
- providers/search/serpapi_jobs.py
- models/search_result.py
- core/config.py
- core/http.py
- tests/test_provider_search_pass1.py

FILES ALLOWED TO CHANGE:
- providers/search/adzuna.py
- providers/search/usajobs.py
- providers/search/jooble.py
- providers/search/careerjet.py
- core/config.py only if missing required env fields
- tests/test_provider_search_pass2.py
- docs/REPAIR_MATRIX.md only to mark R3 status/proof
- scripts/current_truth_audit.py only if detection must be corrected

GOAL:
Replace the remaining provider return [] stubs with real dormant-until-configured providers:
- Adzuna
- USAJobs
- Jooble
- Careerjet

REQUIRED IMPLEMENTATION:
1. All providers must:
   - Return List[SearchResult].
   - Never search on import.
   - Return [] when required key/env values are missing.
   - Return [] on HTTP errors, malformed JSON, missing result arrays, or timeouts.
   - Never raise unhandled exceptions to callers.
   - Store the raw provider payload in raw.
   - Include provider key, query, title, source_url/url, snippet/description, source_name/company if available.
   - Use requests/core shared session if the project has one; otherwise use safe local requests with timeout.

2. Adzuna:
   - Requires ADZUNA_APP_ID and ADZUNA_APP_KEY in Config.
   - If Config fields do not exist, add them from env.
   - Parse fake Adzuna payload from tests.

3. USAJobs:
   - Requires USAJOBS_API_KEY and USAJOBS_EMAIL in Config.
   - If Config fields do not exist, add them from env.
   - Include required headers only inside search().
   - Parse fake USAJobs payload from tests.

4. Jooble:
   - Requires JOOBLE_API_KEY in Config.
   - If Config field does not exist, add it from env.
   - Parse fake Jooble payload from tests.

5. Careerjet:
   - Requires CAREERJET_AFFID in Config.
   - If Config field does not exist, add it from env.
   - Parse fake Careerjet payload from tests.

6. Tests:
   - Create tests/test_provider_search_pass2.py.
   - Use monkeypatch/fake session responses.
   - Do not call real external APIs.
   - Test each provider parses a fake successful payload into SearchResult.
   - Test missing key returns [] for each provider.
   - Test HTTP exception returns [] for each provider.
   - Test provider registry imports all providers.
   - Test no provider searches during import.

7. Truth audit:
   - After R3, RETURN_EMPTY_PROVIDER_COUNT should become 0.
   - PROVIDER_STUB_COUNT should remain 10.
   - PASS_COUNT should remain 5.
   - UNWIRED_ROUTE_COUNT may remain 7.

PROOF COMMANDS:
python3 -m py_compile providers/search/adzuna.py providers/search/usajobs.py providers/search/jooble.py providers/search/careerjet.py tests/test_provider_search_pass2.py
PYTHONPATH=. python3 tests/test_provider_search_pass1.py
PYTHONPATH=. python3 tests/test_provider_search_pass2.py
python3 scripts/current_truth_audit.py

AFTER SUCCESS:
Update docs/REPAIR_MATRIX.md:
- Mark R3 complete.
- Record files changed.
- Record proof commands.
- Record no deploy.
- Record no git push.
- Record no API spend.
- Record audit count changes.

Then run:
git diff --stat
git diff -- providers/search/adzuna.py providers/search/usajobs.py providers/search/jooble.py providers/search/careerjet.py core/config.py tests/test_provider_search_pass2.py docs/REPAIR_MATRIX.md scripts/current_truth_audit.py | sed -n '1,420p'

If successful:
git add providers/search/adzuna.py providers/search/usajobs.py providers/search/jooble.py providers/search/careerjet.py core/config.py tests/test_provider_search_pass2.py docs/REPAIR_MATRIX.md scripts/current_truth_audit.py
git commit -m "R3 implement remaining search providers"

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
