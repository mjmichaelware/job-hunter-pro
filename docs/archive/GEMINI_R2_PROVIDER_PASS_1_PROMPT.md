You are operating inside the Job Hunter Pro repo.

MISSION:
Perform R2 — Provider Engine Pass 1.

ABSOLUTE RULES:
- Read all six authoritative Job Hunter Pro documents before editing.
- Read docs/REPAIR_MATRIX.md before editing.
- Read scripts/current_truth_audit.py before editing.
- Do not deploy.
- Do not git push.
- Do not call live /api/jobs.
- Do not call paid external APIs during tests.
- Do not expose secrets.
- Do not print secret values.
- Do not implement LLM reasoning providers in this session.
- Do not implement Adzuna, USAJobs, Jooble, or Careerjet in this session.
- This session only fixes:
  providers/search/themuse.py
  providers/search/serpapi_jobs.py
  providers/search/serpapi_organic.py
  and required tests/docs updates.

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
- providers/search/serpapi_jobs.py
- providers/search/serpapi_organic.py
- providers/search/themuse.py
- models/search_result.py
- core/config.py
- core/http.py
- search/budget.py
- search/usage_tracker.py
- tests/ if provider tests already exist

FILES ALLOWED TO CHANGE:
- providers/search/themuse.py
- providers/search/serpapi_jobs.py
- providers/search/serpapi_organic.py
- tests/test_provider_search_pass1.py
- docs/REPAIR_MATRIX.md only to mark R2 status/proof
- scripts/current_truth_audit.py only if its detection needs to recognize fixed providers accurately

GOAL:
Replace return [] stubs in The Muse, SerpAPI Jobs, and SerpAPI Organic providers with real, budget-aware provider implementations that return normalized SearchResult objects.

REQUIRED IMPLEMENTATION:
1. The Muse provider:
   - No API key required.
   - Must call The Muse public jobs API when search() is called.
   - Must parse results into models.search_result.SearchResult.
   - Must include provider="themuse".
   - Must include title, url/source_url, snippet/description, company/source_name if available, raw payload.
   - Must fail closed and return [] on HTTP errors, malformed data, or timeouts.
   - Must not raise unhandled exceptions.

2. SerPAPI Jobs provider:
   - Requires Config.SERPAPI_KEY.
   - Must not search if key missing.
   - Must respect available budget guard if existing search/budget.py exposes one.
   - Must call google_jobs engine only inside search().
   - Must parse jobs_results into SearchResult objects.
   - Must include provider="serpapi_jobs".
   - Must include query, title, url/source_url/apply link if available, snippet/description, source_name/via/company if available, raw payload.
   - Must fail closed and return [] on HTTP errors, missing key, budget block, or malformed data.

3. SerPAPI Organic provider:
   - Requires Config.SERPAPI_KEY.
   - Budget-gated/off by default if existing config has enable flag.
   - Must call SerpAPI organic Google search only inside search().
   - Must parse organic_results into SearchResult objects.
   - Must include provider="serpapi_organic".
   - Must fail closed and return [] on errors.
   - Must not run during app boot.

4. Tests:
   - Create tests/test_provider_search_pass1.py.
   - Use monkeypatch/fake session responses. Do NOT call real external APIs.
   - Test The Muse parses fake API payload into SearchResult.
   - Test SerpAPI Jobs parses fake jobs_results payload.
   - Test SerpAPI Organic parses fake organic_results payload.
   - Test missing API key returns [].
   - Test HTTP exception returns [].
   - Test providers do not search during import.
   - Test provider registry still imports.

5. Truth audit:
   - After R2, RETURN_EMPTY_PROVIDER_COUNT should drop by 3 if audit detects correctly.
   - Remaining return-empty providers should be Adzuna, USAJobs, Jooble, Careerjet.
   - PROVIDER_STUB_COUNT and PASS_COUNT are expected unchanged.

PROOF COMMANDS:
python3 -m py_compile providers/search/themuse.py providers/search/serpapi_jobs.py providers/search/serpapi_organic.py tests/test_provider_search_pass1.py
PYTHONPATH=. python3 tests/test_provider_search_pass1.py
python3 scripts/current_truth_audit.py

AFTER SUCCESS:
Update docs/REPAIR_MATRIX.md:
- Mark R2 complete.
- Record files changed.
- Record proof commands.
- Record no deploy.
- Record no git push.
- Record no API spend.
- Record audit count changes.

Then run:
git diff --stat
git diff -- providers/search/themuse.py providers/search/serpapi_jobs.py providers/search/serpapi_organic.py tests/test_provider_search_pass1.py docs/REPAIR_MATRIX.md scripts/current_truth_audit.py | sed -n '1,360p'

If successful:
git add providers/search/themuse.py providers/search/serpapi_jobs.py providers/search/serpapi_organic.py tests/test_provider_search_pass1.py docs/REPAIR_MATRIX.md scripts/current_truth_audit.py
git commit -m "R2 implement first real search providers"

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
