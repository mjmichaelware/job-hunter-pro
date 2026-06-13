@docs/S12_OMEGA_AGENT_AUDIT_PROMPT.md
@docs/S11_SCRIPT_PROOF.md
@docs/S10_FINAL_PARITY_GATE.md

Repair S12-Omega predeploy audit blockers only. Do not deploy.

Mandatory agents:
1. Use @s12-security-auditor to inspect ingest auth, secrets, .gcloudignore, and false positives.
2. Use @s12-backend-auditor to inspect api/index.py, core/config.py, app import path, and OIDC ingest readiness.
3. Use @s12-script-auditor to inspect scripts/s12_omega_audit.py and S11 scripts.
4. Use @s12-omega-architect for final whole-system readiness review.

Current local audit failures:
- Secret scan hit SHA256 rows in docs/MANIFEST.md: false positive.
- Secret scan hit scripts/s12_omega_audit.py regex strings: false positive.
- Ingest token scan found real legacy token logic in api/index.py and core/config.py.
- Ingest token scan also found historical docs and audit regex strings: false positives.
- import app failed because local Termux Python initially lacked Flask. Recheck after dependency install.
- .local/attic had old hardcoded secrets and was moved out of repo. Confirm .gcloudignore excludes .local and audits.

Hard rules:
- Do not deploy.
- Do not run gcloud run deploy.
- Do not call /api/ingest.
- Do not call live /api/jobs.
- Do not call live providers.
- Do not print secrets.
- Do not hardcode secrets.
- Do not use token-in-URL auth.
- /api/ingest must be OIDC-only or fail closed until OIDC verification is implemented.
- Do not leave legacy INGEST_TOKEN query-param auth in active app/config code.

Allowed files:
- api/index.py
- core/config.py
- auth/oidc.py if it already exists or if a minimal verifier already exists and needs wiring
- scripts/s12_omega_audit.py
- .gcloudignore
- .gitignore
- docs/S12_OMEGA_AGENT_AUDIT_PROMPT.md only if clarifying audit rules
- docs/S12_OMEGA_REPAIR_PROOF.md

Required fixes:
1. Remove or disable active INGEST_TOKEN / request.args token auth from /api/ingest.
2. Ensure /api/ingest is OIDC-only or explicit fail-closed when unsigned.
3. Ensure audit script ignores manifest SHA hashes and its own regex definitions.
4. Ensure audit script does not treat historical docs as active token implementation.
5. Ensure .local and audits are deploy-ignored.
6. Re-run python compile/import checks.
7. Re-run scripts/s12_omega_audit.py.
8. Create docs/S12_OMEGA_REPAIR_PROOF.md.

After editing:
- List files inspected.
- List files changed.
- Explain which blockers were real vs false positive.
- Show import app result.
- Show omega audit result.
- Confirm no deploy.
- Stop before real S12 deploy.
