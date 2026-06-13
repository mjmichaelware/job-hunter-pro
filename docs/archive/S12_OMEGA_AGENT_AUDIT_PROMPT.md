@docs/AI_JOB_AGENT_5_UIUX_Handoff.md
@docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
@docs/S10_API_CONTRACT_MATRIX.md
@docs/S10_FINAL_PARITY_GATE.md
@docs/S10_DOC5_PARITY_TRACKER.md
@docs/S11_SCRIPT_PROOF.md
@docs/S11_SCRIPTS_AGENT_PROMPT.md

Proceed with S12-Omega predeploy audit only.

Do not deploy.
Do not run gcloud run deploy.
Do not create Scheduler jobs.
Do not call /api/ingest.
Do not call live /api/jobs.
Do not call live external providers.
Do not burn SerpAPI.
Do not touch secrets.
Do not print secrets.
Do not edit until all agents report.

Mandatory read-only agent order:
1. Use @s12-omega-architect for whole-system architecture audit.
2. Use @s12-security-auditor for secrets/OIDC/frontend safety audit.
3. Use @s12-backend-auditor for Python/Flask/import/dataflow audit.
4. Use @s12-frontend-auditor for UI/PWA/boot/service-worker audit.
5. Use @s12-script-auditor for scripts/deploy/Scheduler audit.

After agents report:
1. Inspect the repo directly.
2. Inspect the latest local audit report if present under audits/s12_omega_audit_*.md.
3. Produce a consolidated blocker list.

If blockers are found:
- fix only local code/docs/scripts required to make S12 safe.
- do not deploy.
- do not advance to real S12 deploy.
- after edits, run local proof commands again.

If no blockers are found:
- state that S12-Omega predeploy audit is clean.
- state that real S12 deployment can start only after explicit user confirmation.

Audit everything:
- every Python file
- every shell script
- every frontend JS file
- every template
- every CSS file
- service worker
- manifest
- Procfile
- requirements
- provider registry
- ingestion routes
- discovery provider classes
- reasoning provider classes
- storage/repository code
- industry seed path
- Cloud Run deploy script
- Scheduler OIDC script
- Secret Manager helper
- README/docs stage claims
- no-fake-data surfaces
- no-live-on-boot path
- no-token-in-URL path

Required final response:
1. Agents used.
2. Files inspected.
3. Local audit results.
4. Blockers found.
5. Fixes made if any.
6. Remaining warnings.
7. Explicit deployment readiness status.
8. Stop before actual deploy.
