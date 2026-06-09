# /fix-live-jobs

Fix the live jobs problem. Do not deploy.

Read all six documents from .claude/context.

Use these agents:
- orchestrator
- repo-archaeologist
- backend-auditor
- provider-fanout-engineer
- job-visibility-engineer
- frontend-truth-engineer
- data-contract-auditor
- security-auditor
- quota-budget-auditor
- testing-engineer
- code-reviewer
- deploy-auditor

Inspect:
- app.py
- api/index.py
- api/__init__.py
- api/ingest.py
- search/live_provider_bridge.py
- providers/search/*.py
- providers/__init__.py
- web/templates/index.html
- web/static/js/render_jobs.js
- web/static/js/live_engine_bridge.js
- web/static/js/live_truth_telemetry.js

Requirements:
- Real provider results must be visible even when address/radius/transit resolution is incomplete.
- Missing address/radius/transit must become resolution_flags, not hard rejection.
- All available SEARCH providers must be attempted fairly before one provider fills the cap.
- Preserve provider_breakdown and source_url evidence.
- LLM providers are enrichment/classification only, not discovery.
- Page boot must not run live discovery automatically.
- Do not call live /api/jobs.
- Do not call /api/ingest.
- Do not print secrets.
- Do not deploy.

Proof:
bash .claude/scripts/safe_local_proof.sh

Stop after proof and show diff.
