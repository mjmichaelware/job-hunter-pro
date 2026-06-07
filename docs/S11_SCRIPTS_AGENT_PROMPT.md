@docs/AI_JOB_AGENT_5_UIUX_Handoff.md
@docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
@docs/S10_API_CONTRACT_MATRIX.md
@docs/S10_FINAL_PARITY_GATE.md
@docs/S10_DOC5_PARITY_TRACKER.md

Proceed with S11 only.

Authoritative interpretation:
- Document 4 says S11 is scripts/.
- Document 2 says scripts/ contains operator helpers.
- S11 creates/proves scripts locally.
- S12 performs actual deploy, Cloud Run health proof, Scheduler OIDC creation, and stored batch proof.
- Do not deploy in S11.
- Do not create live Scheduler jobs in S11.
- Do not advance to S12.

Mandatory read-only agent order:
1. Use @s11-stage-planner to extract exact S11 requirements from docs.
2. Use @s11-codebase-investigator to inspect existing script files and repo deploy structure.
3. Use @s11-safety-auditor after edits and before final summary.
4. Agents are read-only. Main Gemini agent performs edits.

S11 required files:
- scripts/add_key.sh
- scripts/deploy.sh
- scripts/seed_industries.sh
- scripts/make_scheduler_oidc.sh
- docs/S11_SCRIPT_PROOF.md

Allowed optional docs:
- README.md only for script usage notes with no secrets.
- docs/S10_FINAL_PARITY_GATE.md only for one S11 handoff note.

Forbidden actions:
- Do not deploy.
- Do not run gcloud run deploy.
- Do not create or update Cloud Scheduler jobs live.
- Do not create or update Secret Manager secrets live.
- Do not print secrets.
- Do not hardcode secrets.
- Do not put tokens in Scheduler URLs.
- Do not call /api/ingest.
- Do not call live /api/jobs.
- Do not call SerpAPI or any live provider.
- Do not touch S10 UI files.
- Do not rewrite backend routes.
- Do not create fake data.
- Do not claim S12 readiness until local S11 proofs pass.

Script requirements:

scripts/add_key.sh:
- Termux-friendly bash.
- set -euo pipefail.
- supports --dry-run.
- safe usage text.
- validates secret name.
- never echoes secret value.
- reads secret from stdin or hidden prompt for real run.
- creates missing secret if needed.
- adds secret version with --data-file=-.
- prints only redacted command shape in dry-run.
- no secret temp files.

scripts/deploy.sh:
- Termux-friendly bash.
- set -euo pipefail.
- supports --dry-run.
- in S11 dry-run only.
- real execution later belongs to S12.
- before real deploy, must run compile checks.
- deploy target:
  project=ai-job-agent-498702
  service=job-hunter-pro
  region=us-central1
- must use Secret Manager references, not secret values.
- must not print secrets.
- must include post-deploy health/log proof commands for S12.
- must not call /api/ingest.

scripts/seed_industries.sh:
- Termux-friendly bash.
- set -euo pipefail.
- supports --dry-run.
- seeds industry taxonomy only if backend/store path exists.
- if missing backend/store path, reports backend gap and exits safely.
- no live discovery.
- no SerpAPI spend.
- no fake jobs.

scripts/make_scheduler_oidc.sh:
- Termux-friendly bash.
- set -euo pipefail.
- supports --dry-run.
- builds Cloud Scheduler OIDC command for S12.
- never puts token in URL.
- uses --oidc-service-account-email.
- uses --oidc-token-audience or correct OIDC audience argument supported by gcloud.
- validates PROJECT_ID, REGION, SERVICE_URL, SCHEDULER_SA, JOB_NAME, SCHEDULE.
- targets ${SERVICE_URL}/api/ingest.
- dry-run prints command shape only.
- real creation is S12, not S11.

docs/S11_SCRIPT_PROOF.md must include:
1. S11 purpose.
2. Files created/changed.
3. Agent findings.
4. Dry-run proof commands.
5. Secret safety proof.
6. Scheduler OIDC proof: no token in URL.
7. Deploy safety proof: deploy.sh exists but was not executed live.
8. Provider safety proof: no SerpAPI/live provider calls.
9. Backend gaps.
10. Stop before S12.

Required local proof commands to run:
- bash -n scripts/add_key.sh scripts/deploy.sh scripts/seed_industries.sh scripts/make_scheduler_oidc.sh
- scripts/add_key.sh --dry-run TEST_SECRET
- scripts/deploy.sh --dry-run
- scripts/seed_industries.sh --dry-run
- scripts/make_scheduler_oidc.sh --dry-run
- grep proof for no token URL, no hardcoded secrets, no live deploy execution
- python compile only if Python files changed

Before editing, respond with:
1. S11 objective.
2. Agent findings.
3. Existing scripts inspected.
4. Exact files to create/change.
5. Forbidden actions confirmed.

After editing, respond with:
1. Files inspected.
2. Files changed.
3. Script behavior summary.
4. Dry-run outputs summarized.
5. Secret safety proof.
6. Scheduler OIDC proof.
7. Deploy safety proof.
8. SerpAPI/provider proof.
9. Backend gaps.
10. Stop before S12.
