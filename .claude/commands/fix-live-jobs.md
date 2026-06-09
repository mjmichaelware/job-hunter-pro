# /fix-live-jobs

Do not deploy.
Do not call live /api/jobs.
Do not call /api/ingest.
Do not print secrets.

Use these agents in order:
1. opus-architect
2. haiku-file-indexer
3. sonnet-route-surface-auditor
4. sonnet-provider-fanout-engineer
5. sonnet-job-visibility-engineer
6. sonnet-frontend-truth-engineer
7. sonnet-data-contract-auditor
8. sonnet-testing-engineer
9. opus-security-auditor
10. opus-final-reviewer

Inspect current code first. Trust current repo over stale docs.

Focus:
- search/federated.py provider fairness
- pipeline/reject.py hard rejection gates
- pipeline/normalize.py resolution flags
- api/index.py jobs assembler / dry_run / payload
- web/static/js and web/templates UI display

Proof:
bash .claude/scripts/safe_local_proof.sh

Stop after proof and show diff.
