You are operating inside the Job Hunter Pro repo.

MISSION:
Perform R0 — Freeze + Truth Matrix — using ALL SIX Job Hunter Pro source documents as mandatory authority.

ABSOLUTE RULE:
You must read all six documents before making any plan, audit, code, or commit.
Do not summarize from memory.
Do not infer from filenames only.
Do not proceed if any of the six documents are missing.
Do not deploy.

FIRST ACTION:
Find and print the exact repo paths for all six authoritative documents:

Document 1: AI JOB AGENT 1.0 / Project Checkpoint 1
Document 2: AI JOB AGENT 2.0 / Project Blueprint
Document 3: AI JOB AGENT 3.0 / Project AIM / Omega Conglomerate
Document 4: AI JOB AGENT 4.0 / Project Plan / Definitive Convergence Workflow
Document 5: AI JOB AGENT 5.0 / UIUX Handoff
Document 6: AI JOB AGENT 6.0 / S10 UIUX Session Masterplan

Use shell discovery if needed:
find . -iname '*AI*JOB*AGENT*' -o -iname '*JOB*HUNTER*' -o -iname '*S10*' -o -iname '*PROJECT*'

MANDATORY STOP CONDITION:
If all six documents are not present inside the repo, stop and print:
MISSING_REQUIRED_DOCUMENTS
Then list exactly which document numbers are missing.
Do not create scripts.
Do not create docs/REPAIR_MATRIX.md.
Do not commit.

AFTER ALL SIX ARE FOUND:
Read all six documents completely enough to extract:
- target architecture
- confirmed working backend state
- build order
- proof workflow
- known placeholder/scaffold areas
- S10/S11/S12 rules
- UI data-truth rules
- deployment and budget rules
- exact desired endpoint surface
- multi-industry requirements
- provider requirements
- application tracker requirements
- LLM reasoning/web-search requirements
- OIDC ingest requirements

ABSOLUTE RULES:
- Do not deploy.
- Do not call live /api/jobs without dry_run=1.
- Do not expose secrets.
- Do not print secret values.
- Do not rewrite the app.
- Do not implement providers yet.
- This session only creates the repair matrix and audit script.

CURRENT KNOWN LIVE STATE TO VERIFY:
- S10 cockpit works.
- app.py dispatches real API traffic to api.index.
- api.index v8 backend works for food-service, Places, SerpAPI, history, usage.
- Modular providers/search files still return [].
- Reasoning providers still return provider_stub.
- ingest/oidc.py contains pass stubs.
- application tracker is model/repo shell, not live CRUD.
- multi-industry entrances exist but are not wired into execution.

DELIVERABLES:
1. Create scripts/current_truth_audit.py.
2. Create docs/REPAIR_MATRIX.md.

scripts/current_truth_audit.py must:
- Walk api/, providers/, search/, store/, models/, pipeline/, ingest/, industries/, web/static/js/, web/templates/.
- Count and print:
  STUB_COUNT
  PLACEHOLDER_ENDPOINT_COUNT
  RETURN_EMPTY_PROVIDER_COUNT
  PROVIDER_STUB_COUNT
  PASS_COUNT
  NOT_IMPLEMENTED_COUNT
  TODO_COUNT
  UNWIRED_ROUTE_COUNT
  SAFE_ENDPOINTS_PRESENT_COUNT
  RISKY_LIVE_ENDPOINTS_COUNT
- Print each finding with file, line number, classification, and reason.
- Never print secret values.
- Ignore harmless HTML input placeholder attributes.
- Ignore historical docs mentions unless they are active implementation.
- Treat return [] in provider search() as blocker.
- Treat provider_stub in reasoning providers as blocker.
- Treat pass in ingest/oidc.py as blocker.
- Treat api/index.py HTML placeholder attributes as non-blocking.
- Return exit code 0 even with blockers.

docs/REPAIR_MATRIX.md must include:
- Paths of all six documents read.
- Current Live Truth.
- Implemented Now.
- Stubbed / Fake / Placeholder.
- Built But Unwired.
- Missing Entirely.
- Session Plan R1-R10.
- For each session:
  files inspected
  files to change
  proof command
  no-deploy or deploy status
  risk level
  budget/API-spend risk
  dependency blockers

Session order:
R0 truth matrix
R1 industries
R2 provider engine pass 1
R3 provider engine pass 2
R4 federated search + budget/cache
R5 multi-industry pipeline
R6 application tracker
R7 OIDC ingest + scheduler
R8 LLM enrichment, not discovery
R9 API + frontend contract
R10 final deploy proof

AFTER WRITING:
Run:
python3 -m py_compile scripts/current_truth_audit.py
python3 scripts/current_truth_audit.py

Then update docs/REPAIR_MATRIX.md with actual counts from the audit script.

Then run:
git diff --stat
git diff -- scripts/current_truth_audit.py docs/REPAIR_MATRIX.md | sed -n '1,260p'

If successful:
git add scripts/current_truth_audit.py docs/REPAIR_MATRIX.md
git commit -m "R0 add six-document repair truth matrix"

FINAL RESPONSE:
List:
- all six document paths read
- files inspected
- files changed
- exact audit counts
- proof command output summary
- commit hash if committed
- confirm no deploy
Stop.
