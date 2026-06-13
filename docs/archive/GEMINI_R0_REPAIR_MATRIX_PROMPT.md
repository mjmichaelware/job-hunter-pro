You are operating inside the Job Hunter Pro repo.

MISSION:
Perform R0 — Freeze + Truth Matrix.

ABSOLUTE RULES:
- Do not deploy.
- Do not call live /api/jobs without dry_run=1.
- Do not expose secrets.
- Do not print secret values.
- Do not rewrite the app.
- Do not implement providers yet.
- This session only creates the repair matrix and audit script.

PROJECT FACTS:
- Owner: Michael Ware.
- Repo: mjmichaelware/job-hunter-pro.
- GCP project: ai-job-agent-498702.
- Cloud Run service: job-hunter-pro.
- Region: us-central1.
- Current live state: S10 cockpit works, api.index v8 backend works, placeholders/stubs remain in modular providers/routes.

READ THESE IF PRESENT:
- docs/AI_JOB_AGENT_5_UIUX_Handoff.md
- docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
- docs/S10_API_CONTRACT_MATRIX.md
- docs/S10_DOC5_PARITY_TRACKER.md
- docs/S10_FINAL_PARITY_GATE.md
- docs/S11_SCRIPT_PROOF.md
- docs/S12_PROVIDER_READINESS.md
- docs/S12_OMEGA_REPAIR_PROOF.md
- all docs/AI_JOB_AGENT* files

KNOWN PROBLEM CLASSES TO VERIFY:
- api/*.py placeholder endpoints.
- providers/search/*.py search methods returning [].
- providers/reasoning/*.py returning provider_stub.
- ingest/oidc.py pass stubs.
- search/federated.py dummy behavior.
- application tracker model/repo exists but route is placeholder or not wired.
- multi-industry modules exist but are not wired into live search execution.
- frontend may have tabs for features that backend marks unavailable.

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
- Ignore docs historical mentions unless they are active implementation.
- Treat return [] in provider search() as blocker.
- Treat provider_stub in reasoning providers as blocker.
- Treat pass in ingest/oidc.py as blocker.
- Treat api/index.py HTML placeholder attributes as non-blocking.
- Return exit code 0 even with blockers.

docs/REPAIR_MATRIX.md must include:
- Current Live Truth
- Implemented Now
- Stubbed / Fake / Placeholder
- Built But Unwired
- Missing Entirely
- Session Plan R1-R10
- For each session:
  files inspected
  files to change
  proof command
  no-deploy or deploy status
  risk level
  budget/API-spend risk

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

Then update docs/REPAIR_MATRIX.md with actual counts.

Then run:
git diff --stat
git diff -- scripts/current_truth_audit.py docs/REPAIR_MATRIX.md | sed -n '1,260p'

If successful:
git add scripts/current_truth_audit.py docs/REPAIR_MATRIX.md
git commit -m "R0 add repair truth matrix and audit script"

FINAL RESPONSE:
List files inspected, files changed, exact counts, proof summary, commit hash, and confirm no deploy.
Stop.
